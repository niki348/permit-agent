"""
Permit Screening Agent — Streamlit Web Application
PS192 · Government & Public Services · Permit Approval
Supports: pre-loaded samples, JSON upload, PDF upload
"""

import json
import re
import tempfile
from pathlib import Path

import streamlit as st

from agent import run_agent, load_all_applications

st.set_page_config(
    page_title="Permit Screening Agent — Nagar City",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
/* ── Layout ── */
.block-container { padding-top: 0.5rem !important; padding-bottom: 1rem; }
header[data-testid="stHeader"] { height: 0 !important; display: none !important; }
#MainMenu, footer { visibility: hidden; }

/* ── App header bar ── */
.app-header { background: linear-gradient(90deg, #0f2640 0%, #1a3557 100%); padding: 14px 24px; border-radius: 0 0 10px 10px; margin-bottom: 1rem; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 2px 12px rgba(0,0,0,0.3); }
.app-header-title { font-size: 1.15rem; font-weight: 700; color: #ffffff; letter-spacing: 0.02em; }
.app-header-sub { font-size: 0.78rem; color: #7eb8e8; margin-top: 2px; }
.app-header-badge { background: rgba(255,255,255,0.1); color: #7eb8e8; padding: 4px 12px; border-radius: 99px; font-size: 0.75rem; font-weight: 600; border: 1px solid rgba(126,184,232,0.3); }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { gap: 4px; background: #0d1a2a; padding: 6px 8px; border-radius: 10px; margin-bottom: 1rem; overflow-x: auto; flex-wrap: nowrap; }
.stTabs [data-baseweb="tab"] { padding: 8px 18px !important; border-radius: 8px !important; font-size: 0.85rem !important; font-weight: 500 !important; color: #7eb8e8 !important; background: transparent !important; white-space: nowrap; border: none !important; }
.stTabs [aria-selected="true"] { background: #1a3557 !important; color: #ffffff !important; }
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }
.stTabs [data-baseweb="tab-border"] { display: none !important; }

/* ── Status badges ── */
.badge-ready    { display:inline-block; background:#0d2e18; color:#4ade80; padding:14px 20px; border-radius:10px; font-size:1.1rem; font-weight:700; border-left:5px solid #22c55e; width:100%; margin-bottom:4px; }
.badge-revision { display:inline-block; background:#2e2000; color:#fbbf24; padding:14px 20px; border-radius:10px; font-size:1.1rem; font-weight:700; border-left:5px solid #f59e0b; width:100%; margin-bottom:4px; }
.badge-blocked  { display:inline-block; background:#2e0d0d; color:#f87171; padding:14px 20px; border-radius:10px; font-size:1.1rem; font-weight:700; border-left:5px solid #ef4444; width:100%; margin-bottom:4px; }

/* ── Detail cards ── */
.detail-card { background:#111e2d; border:1px solid #1e3348; border-radius:10px; padding:12px 16px; margin-bottom:8px; color:#d4e4f4 !important; font-size:0.87rem; line-height:1.9; }
.detail-card b { color:#7eb8e8 !important; }
.detail-card code { background:#1a3557; color:#93c5fd; padding:2px 7px; border-radius:4px; font-size:0.8rem; }

/* ── Type badge ── */
.type-badge { display:inline-flex; align-items:center; gap:6px; background:#0f2640; color:#7eb8e8; padding:4px 14px; border-radius:99px; font-size:0.78rem; font-weight:600; margin-bottom:10px; letter-spacing:0.04em; border:1px solid #1e3f6a; }

/* ── Section label ── */
.section-label { font-size:0.72rem; font-weight:600; color:#4a7aaa; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:6px; margin-top:14px; }

/* ── Conflict cards ── */
.conflict-wrap { background:#141008; border:1px solid #2a1e06; border-radius:10px; padding:14px 16px; margin-bottom:10px; }
.conflict-wrap.blocking { border-left:4px solid #ef4444; }
.conflict-wrap.advisory { border-left:4px solid #f59e0b; }
.rule-tag { display:inline-block; background:#0f2640; color:#93c5fd; padding:3px 9px; border-radius:5px; font-size:0.75rem; font-weight:700; margin-right:6px; letter-spacing:0.03em; }
.conflict-body { font-size:0.84rem; color:#aaa; margin-top:8px; line-height:1.7; }
.conflict-rec { font-size:0.84rem; color:#7eb8e8; margin-top:8px; padding-top:6px; border-top:1px solid #2a1e06; }

/* ── Action items ── */
.action-item { background:#0a1929; border:1px solid #1e3348; border-radius:8px; padding:9px 14px; margin-bottom:6px; font-size:0.86rem; color:#c8ddf0; line-height:1.6; }

/* ── Meta info ── */
.meta-info { font-size:0.79rem; color:#5a7a9a; margin:6px 0 12px; padding:6px 0; border-bottom:1px solid #1a2a3a; }

/* ── Officer summary ── */
.officer-label { font-size:0.72rem; font-weight:600; color:#4a7aaa; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:6px; margin-top:10px; }
.officer-box { background:#091523; border:1px solid #1a3557; border-radius:10px; padding:14px 18px; font-size:0.87rem; color:#93c5fd; line-height:1.8; }

/* ── Template box ── */
.template-box { background:#091523; border:1px solid #1a3557; border-radius:8px; padding:14px; font-family:monospace; font-size:0.76rem; color:#7eb8e8; line-height:1.8; white-space:pre-wrap; overflow-x:auto; max-height:320px; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] { background: #0a1929 !important; border-right: 1px solid #1a2a3a; }
section[data-testid="stSidebar"] .stMarkdown p { color: #a0b8cc; font-size: 0.85rem; }

/* ── Metrics ── */
[data-testid="metric-container"] { background: #111e2d; border: 1px solid #1e3348; border-radius: 8px; padding: 10px 14px; }
[data-testid="stMetricValue"] { color: #ffffff !important; }
[data-testid="stMetricLabel"] { color: #7eb8e8 !important; font-size: 0.78rem !important; }

/* ── Expanders ── */
.streamlit-expanderHeader { background: #111e2d !important; border-radius: 8px !important; font-size: 0.88rem !important; }
.streamlit-expanderContent { background: #0d1a2a !important; border-radius: 0 0 8px 8px !important; }

/* ── Download button ── */
.stDownloadButton button { background: #1a3557 !important; color: #7eb8e8 !important; border: 1px solid #2d5a8e !important; border-radius: 8px !important; font-weight: 500 !important; }
.stDownloadButton button:hover { background: #2d5a8e !important; color: #ffffff !important; }

/* ── Divider ── */
hr { border-color: #1a2a3a !important; }
</style>
""", unsafe_allow_html=True)

# ── Custom header (replaces Streamlit default) ──
st.markdown("""
<div class="app-header">
  <div>
    <div class="app-header-title">🏛️ Nagar City Municipal Corporation</div>
    <div class="app-header-sub">Permit Screening Agent &nbsp;·&nbsp; PS192 · Government & Public Services · Agentic AI</div>
  </div>
  <div class="app-header-badge">Permit Approval System</div>
</div>
""", unsafe_allow_html=True)

# ── Templates for download ──
BUILDING_TEMPLATE = {
    "application_id": "APP-CUSTOM-001",
    "permit_type": "residential_building",
    "applicant_name": "Your Full Name",
    "applicant_contact": "+91-9000000000",
    "property_address": "House No, Street, Sector, Nagar City",
    "plot_number": "NC-SX-XXXX",
    "zone_type": "R1 or R2",
    "proposed_use": "Residential - Single Family",
    "plot_area_sqm": 250,
    "proposed_built_up_area_sqm": 150,
    "proposed_height_m": 9.0,
    "front_setback_m": 4.5,
    "side_setback_m": 1.5,
    "rear_setback_m": 3.0,
    "contractor_license_id": "CONT-NC-XXXX-XXXX",
    "contractor_license_expiry": "2027-12-31",
    "insurance_certificate": True,
    "site_plan_attached": True,
    "architect_seal": True,
    "signature_date": "2026-07-12"
}

TRADE_TEMPLATE = {
    "application_id": "TL-CUSTOM-001",
    "permit_type": "electrical_trade_license",
    "applicant_name": "Business or Individual Name",
    "applicant_contact": "+91-9000000000",
    "business_address": "Unit No, Street, Sector, Nagar City",
    "trade_category": "Electrical Works",
    "license_class": "Class A - High Voltage or Class B - Low Voltage",
    "master_electrician_name": "Master Electrician Full Name",
    "master_electrician_cert": "ME-NC-XXXX-XXXX",
    "master_electrician_cert_expiry": "2027-12-31",
    "business_registration_number": "BRN-NC-XXXX-XXXX",
    "insurance_certificate": True,
    "safety_compliance_cert": True,
    "tool_calibration_cert": True,
    "signature_date": "2026-07-12"
}


def load_history():
    p = Path("data/history.json")
    if p.exists():
        with open(p) as f:
            try:
                return json.load(f)
            except:
                return []
    return []


def extract_from_pdf(uploaded_file) -> dict:
    """Extract permit application fields from a PDF using PyPDF2 + regex."""
    try:
        import PyPDF2
    except ImportError:
        st.error("PyPDF2 not installed. Run: pip install PyPDF2")
        return {}

    reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""

    text_lower = text.lower()

    def find_val(patterns, default=""):
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return default

    def find_bool(keywords):
        for kw in keywords:
            if kw.lower() in text_lower:
                return True
        return False

    # Determine permit type from content
    is_trade = any(w in text_lower for w in ["trade license", "electrical", "master electrician", "license class"])

    if is_trade:
        return {
            "application_id": f"PDF-TL-{abs(hash(text)) % 9000 + 1000}",
            "permit_type": "electrical_trade_license",
            "applicant_name": find_val([r"(?:applicant|business|company)\s*name[:\s]+([A-Za-z\s]+?)(?:\n|$)", r"name[:\s]+([A-Za-z\s]{3,50})(?:\n|$)"]),
            "applicant_contact": find_val([r"(?:contact|phone|mobile)[:\s]+([\+\d\s\-]{8,15})"]),
            "business_address": find_val([r"(?:business|office)\s*address[:\s]+(.+?)(?:\n|$)"]),
            "trade_category": find_val([r"(?:trade|work)\s*category[:\s]+(.+?)(?:\n|$)"], "Electrical Works"),
            "license_class": find_val([r"(?:license|licence)\s*class[:\s]+(.+?)(?:\n|$)"]),
            "master_electrician_name": find_val([r"master\s*electrician[:\s]+([A-Za-z\s]+?)(?:\n|$)"]),
            "master_electrician_cert": find_val([r"(?:cert|certificate)\s*(?:no|number|id)[:\s]+([\w\-]+)"]),
            "master_electrician_cert_expiry": find_val([r"(?:cert|certificate)\s*expiry[:\s]+([\d\-\/]+)"]),
            "business_registration_number": find_val([r"(?:business|reg)\s*(?:reg|registration)\s*(?:no|number)[:\s]+([\w\-]+)"]),
            "insurance_certificate": find_bool(["insurance certificate", "insurance: yes", "insurance attached"]),
            "safety_compliance_cert": find_bool(["safety compliance", "safety cert", "safety: yes"]),
            "tool_calibration_cert": find_bool(["calibration cert", "tool calibration", "calibration: yes"]),
            "signature_date": find_val([r"(?:signature|signed|date)[:\s]+([\d\-\/]+)"]),
            "_extracted_text": text[:500]
        }
    else:
        def find_num(patterns, default=0.0):
            for pat in patterns:
                m = re.search(pat, text, re.IGNORECASE)
                if m:
                    try:
                        return float(m.group(1).replace(",", ""))
                    except:
                        pass
            return default

        return {
            "application_id": f"PDF-APP-{abs(hash(text)) % 9000 + 1000}",
            "permit_type": "residential_building",
            "applicant_name": find_val([r"(?:applicant|owner)\s*name[:\s]+([A-Za-z\s]+?)(?:\n|$)"]),
            "applicant_contact": find_val([r"(?:contact|phone|mobile)[:\s]+([\+\d\s\-]{8,15})"]),
            "property_address": find_val([r"(?:property|site)\s*address[:\s]+(.+?)(?:\n|$)"]),
            "plot_number": find_val([r"plot\s*(?:no|number)[:\s]+([\w\-]+)"]),
            "zone_type": find_val([r"zone[:\s]+([A-Z0-9]+)", r"zoning[:\s]+([A-Z0-9]+)"], "R2"),
            "proposed_use": find_val([r"proposed\s*use[:\s]+(.+?)(?:\n|$)"], "Residential - Single Family"),
            "plot_area_sqm": find_num([r"plot\s*area[:\s]+([\d,\.]+)"]),
            "proposed_built_up_area_sqm": find_num([r"built[\s\-]*up\s*area[:\s]+([\d,\.]+)"]),
            "proposed_height_m": find_num([r"(?:building\s*)?height[:\s]+([\d\.]+)"]),
            "front_setback_m": find_num([r"front\s*setback[:\s]+([\d\.]+)"]),
            "side_setback_m": find_num([r"side\s*setback[:\s]+([\d\.]+)"]),
            "rear_setback_m": find_num([r"rear\s*setback[:\s]+([\d\.]+)"]),
            "contractor_license_id": find_val([r"contractor\s*(?:license|licence)\s*(?:id|no)[:\s]+([\w\-]+)"]),
            "contractor_license_expiry": find_val([r"(?:license|licence)\s*expiry[:\s]+([\d\-\/]+)"]),
            "insurance_certificate": find_bool(["insurance certificate", "insurance: yes", "insurance attached"]),
            "site_plan_attached": find_bool(["site plan attached", "site plan: yes", "site plan enclosed"]),
            "architect_seal": find_bool(["architect seal", "architect: yes", "sealed drawings"]),
            "signature_date": find_val([r"(?:signature|signed)\s*date[:\s]+([\d\-\/]+)"]),
            "_extracted_text": text[:500]
        }


def run_screening_ui(application: dict, source_label: str):
    """Shared UI for running the agent and displaying results."""
    permit_type = application.get("permit_type", "residential_building")
    is_trade = "trade" in permit_type

    col_left, col_right = st.columns([1, 1.5], gap="large")

    with col_left:
        st.markdown("### Application Details")
        type_label = "🔧 Electrical Trade License" if is_trade else "🏗️ Residential Building Permit"
        st.markdown(f'<div class="type-badge">{type_label}</div>', unsafe_allow_html=True)
        st.caption(f"Source: {source_label}")

        st.markdown("**Applicant**")
        name = application.get("applicant_name") or "—"
        contact = application.get("applicant_contact") or "—"
        st.markdown(f'<div class="detail-card"><b>{name}</b><br>{contact}</div>', unsafe_allow_html=True)

        if is_trade:
            addr = application.get("business_address") or "—"
            reg = application.get("business_registration_number") or "—"
            st.markdown("**Business**")
            st.markdown(f'<div class="detail-card">{addr}<br>Reg No: <code>{reg}</code></div>', unsafe_allow_html=True)

            st.markdown("**Trade Details**")
            cat = application.get("trade_category") or "—"
            cls = application.get("license_class") or "—"
            st.markdown(f'<div class="detail-card">Category: {cat}<br>Class: <b>{cls}</b></div>', unsafe_allow_html=True)

            st.markdown("**Master Electrician**")
            me = application.get("master_electrician_name") or "Not provided"
            cert = application.get("master_electrician_cert") or "Not provided"
            exp = application.get("master_electrician_cert_expiry") or "—"
            st.markdown(f'<div class="detail-card">Name: {me}<br>Cert: <code>{cert}</code><br>Expiry: {exp}</div>', unsafe_allow_html=True)

            ins = "✅" if application.get("insurance_certificate") else "❌"
            saf = "✅" if application.get("safety_compliance_cert") else "❌"
            cal = "✅" if application.get("tool_calibration_cert") else "❌"
            st.markdown("**Documents**")
            st.markdown(f'<div class="detail-card">Insurance: {ins} &nbsp; Safety Cert: {saf} &nbsp; Calibration: {cal}</div>', unsafe_allow_html=True)
        else:
            addr = application.get("property_address") or "—"
            plot = application.get("plot_number") or "Not provided"
            zone = application.get("zone_type") or "—"
            st.markdown("**Property**")
            st.markdown(f'<div class="detail-card">{addr}<br>Plot: <code>{plot}</code> &nbsp; Zone: <b>{zone}</b></div>', unsafe_allow_html=True)

            use = application.get("proposed_use") or "—"
            bua = application.get("proposed_built_up_area_sqm") or "—"
            pa = application.get("plot_area_sqm") or "—"
            ht = application.get("proposed_height_m") or "—"
            fs = application.get("front_setback_m") or "—"
            st.markdown("**Proposed Development**")
            st.markdown(f'<div class="detail-card">Use: {use}<br>Built-up: {bua} m² on {pa} m² plot<br>Height: {ht} m &nbsp;|&nbsp; Front Setback: {fs} m</div>', unsafe_allow_html=True)

            lid = application.get("contractor_license_id") or "Not provided"
            lexp = application.get("contractor_license_expiry") or "Not provided"
            ins = "✅" if application.get("insurance_certificate") else "❌"
            spl = "✅" if application.get("site_plan_attached") else "❌"
            arc = "✅" if application.get("architect_seal") else "❌"
            st.markdown("**Contractor & Documents**")
            st.markdown(f'<div class="detail-card">License: <code>{lid}</code> (Expiry: {lexp})<br>Site Plan: {spl} &nbsp; Insurance: {ins} &nbsp; Architect Seal: {arc}</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown("### Screening Results")
        run_btn = st.button("🔍 Run Screening", type="primary", use_container_width=True, key=f"run_{application.get('application_id','custom')}")

        if not run_btn:
            st.info("Review the application details on the left, then click **Run Screening**.")
            return

        # Save to temp data if custom
        app_id = application.get("application_id", "CUSTOM-001")
        apps_path = Path("data/applications.json")
        with open(apps_path) as f:
            all_apps = json.load(f)

        # Add or update custom application
        existing_ids = [a["application_id"] for a in all_apps]
        if app_id not in existing_ids:
            all_apps.append(application)
            with open(apps_path, "w") as f:
                json.dump(all_apps, f, indent=2)

        status_container = st.empty()
        log = []

        def cb(msg):
            log.append(f"→ {msg}")
            status_container.markdown(
                "<br>".join(f'<small style="color:#7eb8e8">{m}</small>' for m in log),
                unsafe_allow_html=True
            )

        with st.spinner("Agent running..."):
            try:
                report = run_agent(app_id, status_callback=cb)
            except Exception as e:
                st.error(f"Agent error: {e}")
                return

        status_container.empty()

        # Remove custom app from file after screening
        if app_id not in [a["application_id"] for a in load_all_applications()[:9]]:
            with open(apps_path) as f:
                all_apps = json.load(f)
            all_apps = [a for a in all_apps if a["application_id"] != app_id or a["application_id"] in [x["application_id"] for x in load_all_applications()[:9]]]
            with open(apps_path, "w") as f:
                json.dump(all_apps, f, indent=2)

        status = report["overall_status"]
        icon = {"READY": "✅", "NEEDS REVISION": "⚠️", "BLOCKED": "🚫"}.get(status, "")
        css = {"READY": "badge-ready", "NEEDS REVISION": "badge-revision", "BLOCKED": "badge-blocked"}.get(status, "badge-revision")
        st.markdown(f'<div class="{css}">{icon} &nbsp;{status}<br><span style="font-weight:400;font-size:0.88rem">{report["status_reason"]}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="meta-info">ID: {report["application_id"]} &nbsp;|&nbsp; {report["permit_type"]} &nbsp;|&nbsp; {report["screened_at"]} &nbsp;|&nbsp; {report["processing_time_seconds"]}s</div>', unsafe_allow_html=True)

        if report.get("officer_summary"):
            st.markdown(f'<div class="officer-label">OFFICER SUMMARY</div><div class="officer-box">{report["officer_summary"]}</div>', unsafe_allow_html=True)

        st.markdown("---")

        comp = report["completeness"]
        n_issues = len(comp["missing_fields"]) + len(comp["invalid_fields"])
        comp_label = "✅ Passed" if comp["is_complete"] else f"❌ {n_issues} issue(s) found"
        with st.expander(f"📋 Completeness Check — {comp_label}", expanded=not comp["is_complete"]):
            st.caption(comp["summary"])
            if comp["missing_fields"]:
                st.markdown("**Missing required fields / documents:**")
                for m in comp["missing_fields"]:
                    st.markdown(f'<div class="action-item">❌ <b>{m["field"]}</b> — {m["description"]}</div>', unsafe_allow_html=True)
            if comp["invalid_fields"]:
                st.markdown("**Invalid fields:**")
                for i in comp["invalid_fields"]:
                    st.markdown(f'<div class="action-item">⚠️ <b>{i["field"]}</b> — {i["reason"]}</div>', unsafe_allow_html=True)
            for w in comp.get("warnings", []):
                st.warning(w)
            if comp["is_complete"] and not comp.get("warnings"):
                st.success("All required fields and documents are present and valid.")

        policy = report["policy_conflicts"]
        n_conf = len(policy["conflicts"])
        pol_label = "✅ No conflicts detected" if not policy["has_conflicts"] else f"❌ {n_conf} conflict(s) found"
        with st.expander(f"📜 Policy & Regulatory Check — {pol_label}", expanded=policy["has_conflicts"]):
            st.caption(policy["summary"])
            for c in policy["conflicts"]:
                sev = c.get("severity", "advisory")
                sev_cls = "blocking" if sev == "blocking" else "advisory"
                sev_label = "🔴 Blocking" if sev == "blocking" else "🟡 Advisory"
                st.markdown(f"""<div class="conflict-wrap {sev_cls}">
                    <span class="rule-tag">{c.get('rule_id','N/A')}</span>
                    <b>{c.get('conflict_type','')}</b> &nbsp;<small>{sev_label}</small>
                    <div class="conflict-body"><b>Field:</b> <code style="background:#2d1f0a;color:#f0c070;padding:1px 5px;border-radius:3px">{c.get('affected_field','')}</code><br>{c.get('explanation','')}</div>
                    <div class="conflict-rec">💡 {c.get('recommendation','')}</div>
                </div>""", unsafe_allow_html=True)
            if not policy["has_conflicts"]:
                st.success("No zoning, policy, or regulatory conflicts detected.")

        with st.expander("📌 Recommended Next Actions", expanded=True):
            for i, a in enumerate(report["recommended_actions"], 1):
                st.markdown(f'<div class="action-item"><b>{i}.</b> {a}</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.download_button(
            label="⬇️ Download Permit Readiness Report (JSON)",
            data=json.dumps(report, indent=2),
            file_name=f"permit_report_{report['application_id']}.json",
            mime="application/json",
            use_container_width=True
        )


# ── Load apps ──
apps = load_all_applications()
building_apps = [a for a in apps if a["permit_type"] == "residential_building"]
trade_apps = [a for a in apps if "trade" in a["permit_type"]]
building_opts = {f"{a['application_id']} — {a['applicant_name']}": a["application_id"] for a in building_apps}
trade_opts = {f"{a['application_id']} — {a['applicant_name']}": a["application_id"] for a in trade_apps}
all_opts = {**building_opts, **trade_opts}

# ── Main tabs ──
tab_screen, tab_upload, tab_history = st.tabs(["📋 Screen Application", "📤 Upload Application", "📂 Screening History"])

# ═══════════════════════════════════════
# TAB 1 — PRE-LOADED SCREENING
# ═══════════════════════════════════════
with tab_screen:
    # Application selector — inline, no sidebar needed
    st.markdown("#### Select Application to Screen")
    sel_col1, sel_col2 = st.columns([2, 1], gap="small")
    with sel_col1:
        building_label = "🏗️ Building Permits"
        trade_label = "🔧 Trade Licenses"
        group_opts = {building_label: list(building_opts.keys()), trade_label: list(trade_opts.keys())}
        selected_label = st.selectbox(
            "Choose an application:",
            options=list(all_opts.keys()),
            label_visibility="collapsed"
        )
        selected_id = all_opts[selected_label]
    with sel_col2:
        history_quick = load_history()
        if history_quick:
            total_q = len(history_quick)
            ready_q = sum(1 for h in history_quick if h["overall_status"] == "READY")
            blocked_q = sum(1 for h in history_quick if h["overall_status"] == "BLOCKED")
            st.markdown(f'<div class="detail-card" style="padding:8px 12px;font-size:0.82rem">📊 Screened: <b>{total_q}</b> &nbsp;·&nbsp; ✅ {ready_q} &nbsp;·&nbsp; 🚫 {blocked_q}</div>', unsafe_allow_html=True)

    st.markdown("---")

    selected_app = next(a for a in apps if a["application_id"] == selected_id)
    permit_type = selected_app.get("permit_type", "residential_building")
    is_trade = "trade" in permit_type

    col_left, col_right = st.columns([1, 1.5], gap="large")

    with col_left:
        st.markdown("### Application Details")
        type_label = "🔧 Electrical Trade License" if is_trade else "🏗️ Residential Building Permit"
        st.markdown(f'<div class="type-badge">{type_label}</div>', unsafe_allow_html=True)

        st.markdown("**Applicant**")
        st.markdown(f'<div class="detail-card"><b>{selected_app["applicant_name"]}</b><br>{selected_app["applicant_contact"]}</div>', unsafe_allow_html=True)

        if is_trade:
            st.markdown("**Business**")
            st.markdown(f'<div class="detail-card">{selected_app.get("business_address","—")}<br>Reg No: <code>{selected_app.get("business_registration_number","—")}</code></div>', unsafe_allow_html=True)
            st.markdown("**Trade Details**")
            st.markdown(f'<div class="detail-card">Category: {selected_app.get("trade_category","—")}<br>Class: <b>{selected_app.get("license_class","—")}</b></div>', unsafe_allow_html=True)
            st.markdown("**Master Electrician**")
            st.markdown(f'<div class="detail-card">Name: {selected_app.get("master_electrician_name","—") or "Not provided"}<br>Cert: <code>{selected_app.get("master_electrician_cert","—") or "Not provided"}</code><br>Expiry: {selected_app.get("master_electrician_cert_expiry","—")}</div>', unsafe_allow_html=True)
            ins = "✅" if selected_app.get("insurance_certificate") else "❌"
            saf = "✅" if selected_app.get("safety_compliance_cert") else "❌"
            cal = "✅" if selected_app.get("tool_calibration_cert") else "❌"
            st.markdown("**Documents**")
            st.markdown(f'<div class="detail-card">Insurance: {ins} &nbsp; Safety Cert: {saf} &nbsp; Calibration: {cal}</div>', unsafe_allow_html=True)
        else:
            st.markdown("**Property**")
            st.markdown(f'<div class="detail-card">{selected_app.get("property_address","—")}<br>Plot: <code>{selected_app.get("plot_number","—") or "Not provided"}</code> &nbsp; Zone: <b>{selected_app.get("zone_type","—")}</b></div>', unsafe_allow_html=True)
            st.markdown("**Proposed Development**")
            st.markdown(f'<div class="detail-card">Use: {selected_app.get("proposed_use","—")}<br>Built-up: {selected_app.get("proposed_built_up_area_sqm","—")} m² on {selected_app.get("plot_area_sqm","—")} m² plot<br>Height: {selected_app.get("proposed_height_m","—")} m &nbsp;|&nbsp; Front Setback: {selected_app.get("front_setback_m","—")} m</div>', unsafe_allow_html=True)
            ins = "✅" if selected_app.get("insurance_certificate") else "❌"
            spl = "✅" if selected_app.get("site_plan_attached") else "❌"
            arc = "✅" if selected_app.get("architect_seal") else "❌"
            st.markdown("**Contractor & Documents**")
            st.markdown(f'<div class="detail-card">License: <code>{selected_app.get("contractor_license_id","—") or "Not provided"}</code> (Expiry: {selected_app.get("contractor_license_expiry","—") or "Not provided"})<br>Site Plan: {spl} &nbsp; Insurance: {ins} &nbsp; Architect Seal: {arc}</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown("### Screening Results")
        run_btn = st.button("🔍 Run Screening", type="primary", use_container_width=True, key="run_preloaded")

        if not run_btn:
            st.info("Select an application and click **Run Screening** to begin.")
        else:
            status_container = st.empty()
            log = []

            def cb(msg):
                log.append(f"→ {msg}")
                status_container.markdown(
                    "<br>".join(f'<small style="color:#7eb8e8">{m}</small>' for m in log),
                    unsafe_allow_html=True
                )

            with st.spinner("Agent running..."):
                try:
                    report = run_agent(selected_id, status_callback=cb)
                except Exception as e:
                    st.error(f"Agent error: {e}")
                    st.stop()

            status_container.empty()

            status = report["overall_status"]
            icon = {"READY": "✅", "NEEDS REVISION": "⚠️", "BLOCKED": "🚫"}.get(status, "")
            css = {"READY": "badge-ready", "NEEDS REVISION": "badge-revision", "BLOCKED": "badge-blocked"}.get(status, "badge-revision")
            st.markdown(f'<div class="{css}">{icon} &nbsp;{status}<br><span style="font-weight:400;font-size:0.88rem">{report["status_reason"]}</span></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="meta-info">ID: {report["application_id"]} &nbsp;|&nbsp; {report["permit_type"]} &nbsp;|&nbsp; {report["screened_at"]} &nbsp;|&nbsp; {report["processing_time_seconds"]}s</div>', unsafe_allow_html=True)

            if report.get("officer_summary"):
                st.markdown(f'<div class="officer-label">OFFICER SUMMARY</div><div class="officer-box">{report["officer_summary"]}</div>', unsafe_allow_html=True)

            st.markdown("---")

            comp = report["completeness"]
            n_issues = len(comp["missing_fields"]) + len(comp["invalid_fields"])
            comp_label = "✅ Passed" if comp["is_complete"] else f"❌ {n_issues} issue(s) found"
            with st.expander(f"📋 Completeness Check — {comp_label}", expanded=not comp["is_complete"]):
                st.caption(comp["summary"])
                if comp["missing_fields"]:
                    st.markdown("**Missing required fields / documents:**")
                    for m in comp["missing_fields"]:
                        st.markdown(f'<div class="action-item">❌ <b>{m["field"]}</b> — {m["description"]}</div>', unsafe_allow_html=True)
                if comp["invalid_fields"]:
                    st.markdown("**Invalid fields:**")
                    for i in comp["invalid_fields"]:
                        st.markdown(f'<div class="action-item">⚠️ <b>{i["field"]}</b> — {i["reason"]}</div>', unsafe_allow_html=True)
                for w in comp.get("warnings", []):
                    st.warning(w)
                if comp["is_complete"] and not comp.get("warnings"):
                    st.success("All required fields and documents are present and valid.")

            policy = report["policy_conflicts"]
            n_conf = len(policy["conflicts"])
            pol_label = "✅ No conflicts detected" if not policy["has_conflicts"] else f"❌ {n_conf} conflict(s) found"
            with st.expander(f"📜 Policy & Regulatory Check — {pol_label}", expanded=policy["has_conflicts"]):
                st.caption(policy["summary"])
                for c in policy["conflicts"]:
                    sev = c.get("severity", "advisory")
                    sev_cls = "blocking" if sev == "blocking" else "advisory"
                    sev_label = "🔴 Blocking" if sev == "blocking" else "🟡 Advisory"
                    st.markdown(f"""<div class="conflict-wrap {sev_cls}">
                        <span class="rule-tag">{c.get('rule_id','N/A')}</span>
                        <b>{c.get('conflict_type','')}</b> &nbsp;<small>{sev_label}</small>
                        <div class="conflict-body"><b>Field:</b> <code style="background:#2d1f0a;color:#f0c070;padding:1px 5px;border-radius:3px">{c.get('affected_field','')}</code><br>{c.get('explanation','')}</div>
                        <div class="conflict-rec">💡 {c.get('recommendation','')}</div>
                    </div>""", unsafe_allow_html=True)
                if not policy["has_conflicts"]:
                    st.success("No zoning, policy, or regulatory conflicts detected.")

            with st.expander("📌 Recommended Next Actions", expanded=True):
                for i, a in enumerate(report["recommended_actions"], 1):
                    st.markdown(f'<div class="action-item"><b>{i}.</b> {a}</div>', unsafe_allow_html=True)

            st.markdown("---")
            st.download_button(
                label="⬇️ Download Permit Readiness Report (JSON)",
                data=json.dumps(report, indent=2),
                file_name=f"permit_report_{report['application_id']}.json",
                mime="application/json",
                use_container_width=True,
                key="dl_preloaded"
            )

# ═══════════════════════════════════════
# TAB 2 — UPLOAD APPLICATION
# ═══════════════════════════════════════
with tab_upload:
    st.markdown("### Upload Your Own Application")
    st.markdown("Upload a permit application as a **JSON file** or a **PDF form** to screen it through the agent.")

    upload_col, template_col = st.columns([1, 1], gap="large")

    with template_col:
        st.markdown("#### Download Templates")
        st.caption("Use these templates to create your own application file.")

        t1, t2 = st.tabs(["🏗️ Building Permit", "🔧 Trade License"])
        with t1:
            st.download_button(
                label="⬇️ Download Building Permit Template (JSON)",
                data=json.dumps(BUILDING_TEMPLATE, indent=2),
                file_name="building_permit_template.json",
                mime="application/json",
                use_container_width=True
            )
            st.markdown('<div class="template-box">' + json.dumps(BUILDING_TEMPLATE, indent=2)[:600] + "\n..." + '</div>', unsafe_allow_html=True)
        with t2:
            st.download_button(
                label="⬇️ Download Trade License Template (JSON)",
                data=json.dumps(TRADE_TEMPLATE, indent=2),
                file_name="trade_license_template.json",
                mime="application/json",
                use_container_width=True
            )
            st.markdown('<div class="template-box">' + json.dumps(TRADE_TEMPLATE, indent=2)[:600] + "\n..." + '</div>', unsafe_allow_html=True)

    with upload_col:
        st.markdown("#### Upload Application File")
        upload_type = st.radio("File type:", ["JSON", "PDF"], horizontal=True)

        if upload_type == "JSON":
            uploaded = st.file_uploader("Upload JSON application file", type=["json"], label_visibility="collapsed")
            if uploaded:
                try:
                    application = json.loads(uploaded.read())
                    if "application_id" not in application:
                        application["application_id"] = f"UPLOAD-{abs(hash(uploaded.name)) % 9000 + 1000}"
                    if "permit_type" not in application:
                        st.warning("permit_type not found in file. Defaulting to residential_building.")
                        application["permit_type"] = "residential_building"
                    st.success(f"✅ File loaded — {application.get('applicant_name','Unknown')} ({application['application_id']})")
                    st.session_state["uploaded_app"] = application
                except json.JSONDecodeError as e:
                    st.error(f"Invalid JSON file: {e}")

        else:
            st.info("Upload a PDF permit application form. The agent will extract fields automatically using text recognition.")
            uploaded = st.file_uploader("Upload PDF application file", type=["pdf"], label_visibility="collapsed")
            if uploaded:
                with st.spinner("Extracting fields from PDF..."):
                    application = extract_from_pdf(uploaded)
                if application:
                    st.success(f"✅ PDF processed — {len([v for v in application.values() if v and v != 0])} fields extracted")
                    if application.get("_extracted_text"):
                        with st.expander("📄 Extracted text preview"):
                            st.text(application["_extracted_text"])
                        del application["_extracted_text"]
                    st.session_state["uploaded_app"] = application

        if "uploaded_app" in st.session_state:
            st.markdown("---")
            run_screening_ui(st.session_state["uploaded_app"], f"Uploaded {upload_type} file")

# ═══════════════════════════════════════
# TAB 3 — HISTORY
# ═══════════════════════════════════════
with tab_history:
    st.markdown("### Screening History")
    history = load_history()

    if not history:
        st.info("No applications screened yet.")
    else:
        total = len(history)
        ready = sum(1 for h in history if h["overall_status"] == "READY")
        revision = sum(1 for h in history if h["overall_status"] == "NEEDS REVISION")
        blocked = sum(1 for h in history if h["overall_status"] == "BLOCKED")
        avg_time = round(sum(h.get("processing_time_seconds", 0) for h in history) / total, 1)

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total Screened", total)
        m2.metric("Ready", ready)
        m3.metric("Needs Revision", revision)
        m4.metric("Blocked", blocked)
        m5.metric("Avg Time", f"{avg_time}s")

        st.markdown("---")
        filter_status = st.selectbox("Filter by status:", ["All", "READY", "NEEDS REVISION", "BLOCKED"])
        filtered = history if filter_status == "All" else [h for h in history if h["overall_status"] == filter_status]

        for h in reversed(filtered):
            status_color = {"READY": "#28a745", "NEEDS REVISION": "#ffc107", "BLOCKED": "#dc3545"}.get(h["overall_status"], "#888")
            icon = {"READY": "✅", "NEEDS REVISION": "⚠️", "BLOCKED": "🚫"}.get(h["overall_status"], "")
            with st.expander(f"{icon} {h['application_id']} — {h['applicant_name']} · {h['overall_status']} · {h['screened_at']}"):
                c1, c2, c3, c4 = st.columns(4)
                c1.markdown(f"**Status**<br><span style='color:{status_color};font-weight:700'>{h['overall_status']}</span>", unsafe_allow_html=True)
                c2.markdown(f"**Permit Type**<br>{h.get('permit_type','—')}", unsafe_allow_html=True)
                c3.markdown(f"**Issues Found**<br>{h['total_issues']}", unsafe_allow_html=True)
                c4.markdown(f"**Processing Time**<br>{h.get('processing_time_seconds','—')}s", unsafe_allow_html=True)