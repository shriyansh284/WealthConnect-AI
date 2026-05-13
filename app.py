import streamlit as st
import requests
import json

# ── Config ──────────────────────────────────────────────────────────────────
API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="WealthConnect AI",
    page_icon="💼",
    layout="wide",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { border-radius: 8px; padding: 8px 20px; }
    .result-box {
        background: #f0f4ff;
        border-left: 4px solid #4F46E5;
        border-radius: 8px;
        padding: 16px;
        margin-top: 12px;
        white-space: pre-wrap;
        font-family: sans-serif;
        font-size: 14px;
        line-height: 1.6;
        color: #1a1a2e;
    }
    .approved-box {
        background: #f0fdf4;
        border-left: 4px solid #16a34a;
        border-radius: 8px;
        padding: 16px;
        margin-top: 12px;
        white-space: pre-wrap;
        font-size: 14px;
        line-height: 1.6;
        color: #1a2e1a;
    }
    .error-box {
        background: #fef2f2;
        border-left: 4px solid #dc2626;
        border-radius: 8px;
        padding: 12px;
        margin-top: 8px;
        font-size: 13px;
        color: #2e1a1a;
    }
    .step-badge {
        background: #4F46E5;
        color: white;
        border-radius: 20px;
        padding: 2px 12px;
        font-size: 12px;
        font-weight: 600;
        margin-right: 8px;
    }
    .health-ok  { color: #16a34a; font-weight: 600; }
    .health-err { color: #dc2626; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ── Helpers ──────────────────────────────────────────────────────────────────
def api_post(endpoint: str, payload: dict):
    try:
        r = requests.post(f"{API_BASE}{endpoint}", json=payload, timeout=60)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Cannot connect to API. Make sure `python main.py` is running on port 8000."
    except requests.exceptions.HTTPError as e:
        try:
            detail = e.response.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return None, f"API error {e.response.status_code}: {detail}"
    except Exception as e:
        return None, str(e)

def api_get(endpoint: str):
    try:
        r = requests.get(f"{API_BASE}{endpoint}", timeout=15)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Cannot connect to API."
    except Exception as e:
        return None, str(e)

def show_error(msg):
    st.markdown(f'<div class="error-box">⚠️ {msg}</div>', unsafe_allow_html=True)

def show_result(text, approved=False):
    cls = "approved-box" if approved else "result-box"
    st.markdown(f'<div class="{cls}">{text}</div>', unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Settings")
    st.caption("API connection")

    if st.button("Check API Health", use_container_width=True):
        data, err = api_get("/health")
        if err:
            st.markdown(f'<span class="health-err">Offline — {err}</span>', unsafe_allow_html=True)
        else:
            st.markdown(f'<span class="health-ok">Online ✓</span>', unsafe_allow_html=True)
            st.json(data)

    st.divider()
    st.subheader("RM & Client Details")
    st.caption("Used to personalize all messages")
    rm_name     = st.text_input("RM Name",     value="Rahul Sharma",  placeholder="Your name")
    client_name = st.text_input("Client Name", value="Amit Gupta",    placeholder="Client name")
    client_id   = st.text_input("Client ID",   value="CLIENT001")
    rm_id       = st.text_input("RM ID",       value="RM001")

    st.divider()
    st.caption("💡 Run `python main.py` before using this app.")

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📝 Insight → Draft",
    "✅ Review & Approve",
    "💬 Draft Message",
    "🔍 API Explorer",
])

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — Edit Insight (generate first draft)
# ════════════════════════════════════════════════════════════════════════════
with tab1:
    st.header("Insight → First Draft")
    st.caption("Paste a raw AI insight. The model will transform it into a polished client-ready message.")

    raw_insight = st.text_area(
        "Raw Insight",
        height=140,
        placeholder="e.g. Client's SIP returns dropped 8% due to market volatility. Suggest switching to balanced funds.",
        value=st.session_state.get("raw_insight_input", ""),
    )

    col1, col2 = st.columns([1, 3])
    with col1:
        generate_btn = st.button("Generate Draft ✨", type="primary", use_container_width=True)
    with col2:
        if st.button("Clear", use_container_width=True):
            for k in ["draft_result", "raw_insight_input"]:
                st.session_state.pop(k, None)
            st.rerun()

    if generate_btn:
        if not raw_insight.strip():
            show_error("Please enter a raw insight first.")
        else:
            st.session_state["raw_insight_input"] = raw_insight
            with st.spinner("Generating first draft..."):
                data, err = api_post("/edit-insight", {
                    "client_id":   client_id,
                    "raw_insight": raw_insight,
                    "rm_name":     rm_name,
                    "client_name": client_name,
                })
            if err:
                show_error(err)
            else:
                st.session_state["draft_result"] = data
                st.success("Draft generated!")

    if "draft_result" in st.session_state:
        d = st.session_state["draft_result"]
        st.subheader("Generated Draft")
        show_result(d.get("edited_insight", ""))

        st.divider()
        st.info("👉 Click below to send this draft to the Review & Approve tab.", icon="ℹ️")
        if st.button("Send to Review →", type="secondary"):
            draft_text = d.get("edited_insight", "")
            # KEY FIX: write into both keys — "review_insight" (our own) AND
            # "review_text_area" (the widget key in Tab 2) so Streamlit
            # immediately reflects the new value in the text area.
            st.session_state["review_insight"] = draft_text
            st.session_state["review_text_area"] = draft_text
            st.success("✅ Sent! Switch to the Review & Approve tab.")

        with st.expander("Raw API Response"):
            st.json(d)

# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — Review & Approve
# ════════════════════════════════════════════════════════════════════════════
with tab2:
    st.header("Review & Approve Draft")
    st.caption("Approve the message as-is, or give instructions to refine it further.")

    edited_insight = st.text_area(
        "Current Draft (editable)",
        height=220,
        value=st.session_state.get("review_insight", ""),
        placeholder="Paste or generate a draft from the Insight → Draft tab…",
        key="review_text_area",
    )

    st.divider()
    col_approve, col_refine = st.columns(2)

    # ── Approve ──
    with col_approve:
        st.markdown("#### ✅ Approve")
        st.caption("Send the message as-is to the client.")
        if st.button("Approve & Finalise", type="primary", use_container_width=True):
            if not edited_insight.strip():
                show_error("No draft to approve.")
            else:
                with st.spinner("Approving..."):
                    data, err = api_post("/process-insight", {
                        "client_id":      client_id,
                        "edited_insight": edited_insight,
                        "action":         "approve",
                        "rm_name":        rm_name,
                        "client_name":    client_name,
                    })
                if err:
                    show_error(err)
                else:
                    st.session_state["final_message"] = data.get("final_message", "")
                    st.success("Message approved!")

        if "final_message" in st.session_state:
            st.subheader("Final Message")
            show_result(st.session_state["final_message"], approved=True)
            st.download_button(
                "Download as .txt",
                data=st.session_state["final_message"],
                file_name="final_message.txt",
                mime="text/plain",
            )

    # ── Refine ──
    with col_refine:
        st.markdown("#### ✏️ Refine")
        st.caption("Give instructions and regenerate.")
        rm_instruction = st.text_area(
            "Refinement instruction",
            height=100,
            placeholder="e.g. Make it shorter and more urgent. Add a specific call-to-action for a meeting.",
        )
        if st.button("Refine Draft", type="secondary", use_container_width=True):
            if not edited_insight.strip():
                show_error("No draft to refine.")
            elif not rm_instruction.strip():
                show_error("Please enter a refinement instruction.")
            else:
                with st.spinner("Refining..."):
                    data, err = api_post("/process-insight", {
                        "client_id":      client_id,
                        "edited_insight": edited_insight,
                        "action":         "edit_again",
                        "rm_instruction": rm_instruction,
                        "rm_name":        rm_name,
                        "client_name":    client_name,
                    })
                if err:
                    show_error(err)
                else:
                    refined = data.get("edited_insight", "")
                    st.session_state["review_insight"] = refined
                    st.success("Refined! Text area above has been updated.")
                    st.rerun()

# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — Draft Message (chatbot)
# ════════════════════════════════════════════════════════════════════════════
with tab3:
    st.header("Draft Message")
    st.caption("Describe what you want in plain English — the model will draft a ready-to-send message.")

    query = st.text_area(
        "What message do you need?",
        height=120,
        placeholder="e.g. Draft a message for my client about SIP maturity and suggest reinvestment options with better returns.",
    )
    context = st.text_area(
        "Additional context (optional)",
        height=80,
        placeholder="e.g. Client is risk-averse, prefers WhatsApp-style communication, last contacted 3 months ago.",
    )

    if st.button("Draft Message ✨", type="primary"):
        if not query.strip():
            show_error("Please describe what message you need.")
        else:
            with st.spinner("Drafting message..."):
                payload = {
                    "rm_id":       rm_id,
                    "client_id":   client_id,
                    "query":       query,
                    "rm_name":     rm_name,
                    "client_name": client_name,
                }
                if context.strip():
                    payload["context"] = context
                data, err = api_post("/draft-message", payload)

            if err:
                show_error(err)
            else:
                drafted = data.get("drafted_message", "")
                st.success("Message drafted!")
                st.subheader("Drafted Message")
                show_result(drafted)

                st.download_button(
                    "Download as .txt",
                    data=drafted,
                    file_name="drafted_message.txt",
                    mime="text/plain",
                )

                if st.button("Send to Review →"):
                    st.session_state["review_insight"] = drafted
                    st.success("Sent to Review & Approve tab!")

                with st.expander("Raw API Response"):
                    st.json(data)

# ════════════════════════════════════════════════════════════════════════════
# TAB 4 — Raw API Explorer
# ════════════════════════════════════════════════════════════════════════════
with tab4:
    st.header("API Explorer")
    st.caption("Send raw JSON to any endpoint and inspect the full response.")

    endpoint = st.selectbox("Endpoint", [
        "POST /edit-insight",
        "POST /process-insight",
        "POST /draft-message",
        "GET /health",
        "GET /health/detailed",
        "GET /health/ready",
    ])

    default_payloads = {
        "POST /edit-insight": json.dumps({
            "client_id": "CLIENT001",
            "raw_insight": "Client SIP returns dropped 8% due to market volatility.",
            "rm_name": "Rahul Sharma",
            "client_name": "Amit Gupta"
        }, indent=2),
        "POST /process-insight": json.dumps({
            "client_id": "CLIENT001",
            "edited_insight": "Paste your edited insight here...",
            "action": "approve",
            "rm_name": "Rahul Sharma",
            "client_name": "Amit Gupta"
        }, indent=2),
        "POST /draft-message": json.dumps({
            "rm_id": "RM001",
            "client_id": "CLIENT001",
            "query": "Draft a message about SIP maturity and reinvestment options",
            "rm_name": "Rahul Sharma",
            "client_name": "Amit Gupta"
        }, indent=2),
    }

    is_get = endpoint.startswith("GET")
    path = "/" + endpoint.split("/", 1)[1]

    if not is_get:
        raw_json = st.text_area(
            "Request Body (JSON)",
            height=200,
            value=default_payloads.get(endpoint, "{}"),
        )

    if st.button("Send Request", type="primary"):
        if is_get:
            with st.spinner(f"GET {path}..."):
                data, err = api_get(path)
        else:
            try:
                payload = json.loads(raw_json)
            except json.JSONDecodeError as e:
                show_error(f"Invalid JSON: {e}")
                st.stop()
            with st.spinner(f"POST {path}..."):
                data, err = api_post(path, payload)

        if err:
            show_error(err)
        else:
            st.success("Response received")
            st.subheader("Response")
            st.json(data)

            # Pretty print any message field
            for key in ["edited_insight", "final_message", "drafted_message"]:
                if key in data:
                    st.subheader(f"Formatted: {key}")
                    show_result(data[key])
                    break