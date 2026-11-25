"""
Permit Screening Agent — Core Orchestration
Uses Groq via direct HTTP (avoids SDK _type serialisation bug).
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path

import httpx
from dotenv import load_dotenv

from tools.completeness import check_completeness
from tools.policy_checker import check_policy_conflicts

load_dotenv()

SYSTEM_PROMPT = """You are an official Permit Screening Agent for Nagar City Municipal Corporation.
You screen building permits and trade license applications.
You are ADVISORY only — you never approve or reject permits, only assess and report."""

PERMIT_TYPE_LABELS = {
    "residential_building": "Residential Building Permit",
    "electrical_trade_license": "Electrical Trade License"
}


def _call_groq(messages: list) -> str:
    """Call Groq API directly via HTTP to avoid SDK _type serialisation errors."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    response = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": "llama-3.3-70b-versatile", "messages": messages, "temperature": 0.1, "max_tokens": 512},
        timeout=30
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def load_application(application_id: str) -> dict:
    apps_path = Path(__file__).parent / "data" / "applications.json"
    with open(apps_path) as f:
        apps = json.load(f)
    for app in apps:
        if app["application_id"] == application_id:
            return app
    raise ValueError(f"Application {application_id} not found.")


def load_all_applications() -> list:
    apps_path = Path(__file__).parent / "data" / "applications.json"
    with open(apps_path) as f:
        return json.load(f)


def _determine_status(completeness: dict, policy: dict) -> tuple:
    has_blocking_completeness = any(
        i["severity"] == "blocking"
        for i in completeness.get("missing_fields", []) + completeness.get("invalid_fields", [])
    )
    has_blocking_policy = any(
        c.get("severity") == "blocking"
        for c in policy.get("conflicts", [])
    )
    has_advisory = (
        any(i["severity"] == "advisory"
            for i in completeness.get("missing_fields", []) + completeness.get("invalid_fields", []))
        or any(c.get("severity") == "advisory" for c in policy.get("conflicts", []))
        or bool(completeness.get("warnings"))
    )

    if has_blocking_completeness or has_blocking_policy:
        reasons = []
        if has_blocking_completeness:
            reasons.append("blocking completeness issues")
        if has_blocking_policy:
            reasons.append("blocking policy conflicts")
        return "BLOCKED", f"Application cannot proceed — {' and '.join(reasons)} found."
    elif not completeness["is_complete"] or has_advisory:
        return "NEEDS REVISION", "Application requires corrections before it can be processed."
    else:
        return "READY", "Application is complete and no policy conflicts detected. Ready for officer review."


def save_to_history(report: dict):
    history_path = Path(__file__).parent / "data" / "history.json"
    entry = {
        "application_id": report["application_id"],
        "applicant_name": report["applicant_name"],
        "permit_type": report["permit_type"],
        "overall_status": report["overall_status"],
        "screened_at": report["screened_at"],
        "processing_time_seconds": report["processing_time_seconds"],
        "total_issues": (
            len(report["completeness"]["missing_fields"]) +
            len(report["completeness"]["invalid_fields"]) +
            len(report["policy_conflicts"]["conflicts"])
        ),
        "has_policy_conflicts": report["policy_conflicts"]["has_conflicts"]
    }
    history = []
    if history_path.exists():
        with open(history_path) as f:
            try:
                history = json.load(f)
            except:
                history = []
    history = [h for h in history if h["application_id"] != report["application_id"]]
    history.append(entry)
    with open(history_path, "w") as f:
        json.dump(history, f, indent=2)


def run_agent(application_id: str, status_callback=None) -> dict:
    start_time = time.time()
    application = load_application(application_id)
    permit_type = application.get("permit_type", "residential_building")
    permit_label = PERMIT_TYPE_LABELS.get(permit_type, permit_type.replace("_", " ").title())

    if status_callback:
        status_callback(f"Loaded {permit_label} — {application['applicant_name']} ({application_id})")

    # Step 1 — Completeness check
    if status_callback:
        status_callback("Step 1 of 3 — Running completeness check...")
    completeness_result = check_completeness(application)
    if status_callback:
        status = "passed" if completeness_result["is_complete"] else f"{len(completeness_result['missing_fields'])} missing, {len(completeness_result['invalid_fields'])} invalid"
        status_callback(f"Completeness check complete — {status}")

    # Step 2 — Policy check
    if status_callback:
        status_callback("Step 2 of 3 — Checking policy and regulatory conflicts...")
    try:
        policy_result = check_policy_conflicts(application)
    except Exception as e:
        print(f"Policy check warning: {e}")
        policy_result = {"has_conflicts": False, "conflicts": [], "summary": "Policy check could not be completed."}
    if status_callback:
        n = len(policy_result.get("conflicts", []))
        status_callback(f"Policy check complete — {n} conflict(s) found")

    # Step 3 — Synthesise
    if status_callback:
        status_callback("Step 3 of 3 — Agent synthesising findings...")

    overall_status, status_reason = _determine_status(completeness_result, policy_result)

    address_key = "property_address" if "property_address" in application else "business_address"
    synthesis_prompt = f"""You are a permit screening agent for Nagar City Municipal Corporation.

Application: {application.get('applicant_name')} — {application.get(address_key, '')}
Permit type: {permit_label}
Overall status: {overall_status}
Completeness: {completeness_result['summary']}
Policy: {policy_result.get('summary', 'No conflicts detected.')}
Total issues: {len(completeness_result['missing_fields']) + len(completeness_result['invalid_fields']) + len(policy_result.get('conflicts', []))}

Write a 2-sentence professional officer summary. Be specific about findings and next steps."""

    try:
        officer_summary = _call_groq([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": synthesis_prompt}
        ])
    except Exception as e:
        print(f"Synthesis warning: {e}")
        officer_summary = f"{permit_label} screened — status: {overall_status}. {status_reason}"

    # Build recommended actions
    actions = []
    for m in completeness_result.get("missing_fields", []):
        actions.append(f"Provide missing: {m['field']} — {m['description']}")
    for i in completeness_result.get("invalid_fields", []):
        actions.append(f"Correct: {i['field']} — {i['reason']}")
    for c in policy_result.get("conflicts", []):
        actions.append(f"[{c.get('rule_id', 'N/A')}] {c.get('recommendation', '')}")
    if not actions:
        actions.append("No corrections required. Forward to officer queue for final review.")

    report = {
        "application_id": application_id,
        "applicant_name": application.get("applicant_name", ""),
        "address": application.get("property_address", application.get("business_address", "")),
        "permit_type": permit_label,
        "permit_type_raw": permit_type,
        "zone_type": application.get("zone_type", "N/A"),
        "overall_status": overall_status,
        "status_reason": status_reason,
        "officer_summary": officer_summary,
        "completeness": {
            "is_complete": completeness_result["is_complete"],
            "summary": completeness_result["summary"],
            "missing_fields": completeness_result.get("missing_fields", []),
            "invalid_fields": completeness_result.get("invalid_fields", []),
            "warnings": completeness_result.get("warnings", [])
        },
        "policy_conflicts": {
            "has_conflicts": policy_result.get("has_conflicts", False),
            "summary": policy_result.get("summary", ""),
            "conflicts": policy_result.get("conflicts", [])
        },
        "recommended_actions": actions,
        "screened_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "processing_time_seconds": round(time.time() - start_time, 1)
    }

    save_to_history(report)

    if status_callback:
        status_callback(f"Done — Status: {overall_status}")

    return report


if __name__ == "__main__":
    import sys
    app_id = sys.argv[1] if len(sys.argv) > 1 else "APP-001"
    print(f"\nRunning agent on {app_id}...\n")
    report = run_agent(app_id, status_callback=lambda msg: print(f"  > {msg}"))
    print(f"\n{'='*60}")
    print(f"  Status    : {report['overall_status']}")
    print(f"  Reason    : {report['status_reason']}")
    print(f"  Summary   : {report['officer_summary']}")
    print(f"  Screened  : {report['screened_at']} ({report['processing_time_seconds']}s)")
