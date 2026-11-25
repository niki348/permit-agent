"""
Completeness Checker Tool
Pure Python — no API calls. Validates permit applications against checklist schema.
Supports multiple permit types via separate checklist files.
"""

import json
from datetime import date, datetime
from pathlib import Path


def load_checklist(permit_type: str) -> dict:
    base = Path(__file__).parent.parent / "data"
    if permit_type == "electrical_trade_license":
        path = base / "checklist_trade.json"
    else:
        path = base / "checklist.json"
    with open(path) as f:
        return json.load(f)


def check_completeness(application: dict) -> dict:
    permit_type = application.get("permit_type", "residential_building")
    checklist = load_checklist(permit_type)
    missing_fields = []
    invalid_fields = []
    warnings = []

    for field_def in checklist["required_fields"]:
        field = field_def["field"]
        field_type = field_def["type"]
        value = application.get(field)

        if value is None or value == "" or value == 0:
            missing_fields.append({
                "field": field,
                "description": field_def["description"],
                "severity": "blocking"
            })
            continue

        if field_type == "date":
            try:
                parsed = datetime.strptime(str(value), "%Y-%m-%d").date()
                if "expiry" in field and parsed < date.today():
                    invalid_fields.append({
                        "field": field,
                        "value": str(value),
                        "reason": f"Date has expired ({value}). A current, valid date is required.",
                        "severity": "blocking"
                    })
            except ValueError:
                invalid_fields.append({
                    "field": field,
                    "value": str(value),
                    "reason": "Invalid date format. Expected YYYY-MM-DD.",
                    "severity": "blocking"
                })

        if field_type == "number" and isinstance(value, (int, float)):
            if value <= 0:
                invalid_fields.append({
                    "field": field,
                    "value": value,
                    "reason": "Value must be a positive number.",
                    "severity": "blocking"
                })

    for doc_def in checklist["required_documents"]:
        field = doc_def["field"]
        value = application.get(field)
        if not value:
            missing_fields.append({
                "field": field,
                "description": doc_def["description"],
                "severity": "blocking"
            })

    if permit_type == "residential_building":
        built_up = application.get("proposed_built_up_area_sqm", 0)
        plot = application.get("plot_area_sqm", 1)
        if built_up and plot:
            far = built_up / plot
            if far > 0.8:
                warnings.append(f"Proposed FAR ({far:.2f}) is high — verify against zoning rules.")

    is_complete = len(missing_fields) == 0 and len(invalid_fields) == 0

    return {
        "is_complete": is_complete,
        "missing_fields": missing_fields,
        "invalid_fields": invalid_fields,
        "warnings": warnings,
        "summary": (
            "All required fields and documents are present and valid."
            if is_complete
            else f"Found {len(missing_fields)} missing field(s) and {len(invalid_fields)} invalid field(s)."
        )
    }


if __name__ == "__main__":
    apps_path = Path(__file__).parent.parent / "data" / "applications.json"
    with open(apps_path) as f:
        apps = json.load(f)
    for app in apps:
        result = check_completeness(app)
        status = "PASS" if result["is_complete"] else "FAIL"
        print(f"[{status}] {app['application_id']} — {app['applicant_name']}: {result['summary']}")
        for m in result["missing_fields"]:
            print(f"        MISSING: {m['field']} — {m['description']}")
        for i in result["invalid_fields"]:
            print(f"        INVALID: {i['field']} — {i['reason']}")