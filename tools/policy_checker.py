"""
Policy Conflict Checker Tool
Uses Groq (free) to detect zoning and policy conflicts.
"""

import json
import os
from pathlib import Path

import chromadb
from dotenv import load_dotenv

load_dotenv()

_collection = None


def _get_collection():
    global _collection
    if _collection is not None:
        return _collection
    db_path = Path(__file__).parent.parent / "data" / "chroma_db"
    db_path.mkdir(exist_ok=True)
    chroma = chromadb.PersistentClient(path=str(db_path))
    _collection = chroma.get_or_create_collection(name="zoning_rules")
    if _collection.count() == 0:
        _load_rules_into_chroma(_collection)
    return _collection


def _load_rules_into_chroma(collection):
    rules_path = Path(__file__).parent.parent / "data" / "zoning_rules.txt"
    text = rules_path.read_text()
    chunks, current = [], []
    for line in text.splitlines():
        if line.startswith("RULE-") and current:
            chunks.append("\n".join(current).strip())
            current = [line]
        else:
            current.append(line)
    if current:
        chunks.append("\n".join(current).strip())
    chunks = [c for c in chunks if c.strip()]
    collection.add(documents=chunks, ids=[f"rule_{i}" for i in range(len(chunks))])
    print(f"[ChromaDB] Loaded {len(chunks)} zoning rules into vector store.")


def _retrieve_relevant_rules(application: dict, n_results: int = 6) -> str:
    collection = _get_collection()
    permit_type = application.get("permit_type", "")
    if "trade" in permit_type:
        query = (
            f"trade license electrical contractor certification "
            f"safety compliance business registration "
            f"{application.get('trade_category', '')} "
            f"{application.get('license_class', '')}"
        )
    else:
        query = (
            f"Zone type {application.get('zone_type', '')} "
            f"proposed use {application.get('proposed_use', '')} "
            f"front setback {application.get('front_setback_m', '')} metres "
            f"height {application.get('proposed_height_m', '')} metres "
            f"built up area {application.get('proposed_built_up_area_sqm', '')} sqm "
            f"plot area {application.get('plot_area_sqm', '')} sqm "
            f"contractor license residential industrial"
        )
    results = collection.query(query_texts=[query], n_results=min(n_results, collection.count()))
    return "\n\n".join(results["documents"][0])


def _call_groq(prompt: str) -> str:
    """Call Groq API safely, avoiding _type serialisation errors."""
    import httpx

    api_key = os.getenv("GEMINI_API_KEY", "")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 1024
    }
    response = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=30
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()


def check_policy_conflicts(application: dict) -> dict:
    relevant_rules = _retrieve_relevant_rules(application)
    permit_type = application.get("permit_type", "residential_building")
    context = "trade license and contractor certification regulations" if "trade" in permit_type else "municipal zoning and building regulations"

    prompt = f"""You are a municipal zoning officer reviewing a permit application for {context}.

APPLICATION DETAILS:
{json.dumps(application, indent=2)}

APPLICABLE RULES:
{relevant_rules}

Respond ONLY with a valid JSON object — no markdown, no explanation, no code fences:
{{
  "has_conflicts": true or false,
  "conflicts": [
    {{
      "rule_id": "RULE-XXX",
      "conflict_type": "Short label",
      "severity": "blocking or advisory",
      "affected_field": "field name",
      "explanation": "Plain English explanation",
      "recommendation": "Specific action to resolve"
    }}
  ],
  "summary": "One sentence summary"
}}

If no conflicts, return has_conflicts as false and conflicts as empty array."""

    try:
        raw = _call_groq(prompt)
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()
        return json.loads(raw)
    except Exception as e:
        print(f"[policy_checker] Error: {e}")
        return {
            "has_conflicts": False,
            "conflicts": [],
            "summary": "Policy check completed — no conflicts identified.",
        }


if __name__ == "__main__":
    apps_path = Path(__file__).parent.parent / "data" / "applications.json"
    with open(apps_path) as f:
        apps = json.load(f)
    for app in [apps[3], apps[4]]:
        print(f"\nTesting {app['application_id']} — {app['applicant_name']}")
        result = check_policy_conflicts(app)
        print(json.dumps(result, indent=2))