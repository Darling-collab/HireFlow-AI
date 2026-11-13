import streamlit as st

STATUS_LABELS = {"invited":"待邀约","screening_passed":"初筛通过","first_round_passed":"一面通过","second_round_passed":"二面通过","final_round_passed":"终面通过","offer_sent":"Offer 已发","offer_accepted":"Offer 已接受","hired":"已入职","withdrawn":"已放弃","rejected":"已淘汰","talent_pool":"人才池储备","pending_confirmation":"待确认"}

def inject_theme():
    st.markdown("""<style>
    :root{--hf-navy:#102a43;--hf-blue:#2563eb;--hf-purple:#7c3aed;--hf-muted:#64748b;--hf-bg:#f6f8fb}
    .stApp{background:var(--hf-bg)} .block-container{max-width:1440px;padding-top:2rem}
    [data-testid="stSidebar"]{background:#102a43} [data-testid="stSidebar"] *{color:#e8f0f7}
    .hf-brand{font-size:1.35rem;font-weight:700;letter-spacing:-.03em;color:#fff;padding:.5rem 0 1.2rem}
    .hf-kpi{background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:1rem 1.1rem;box-shadow:0 4px 16px rgba(15,23,42,.04)}
    .hf-kpi-label{color:#64748b;font-size:.82rem}.hf-kpi-value{font-size:1.8rem;font-weight:700;color:#102a43;margin-top:.25rem}
    .hf-card{background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:1.1rem;margin-bottom:1rem}
    .hf-pill{display:inline-block;border-radius:999px;padding:.2rem .55rem;background:#eef2ff;color:#4338ca;font-size:.75rem;font-weight:600}
    h1,h2,h3{color:#102a43;letter-spacing:-.02em}
    </style>""", unsafe_allow_html=True)

def page_header(title, subtitle="", action=None):
    left, right = st.columns([3,1])
    with left:
        st.title(title)
        if subtitle: st.caption(subtitle)
    with right:
        if action: action()

def kpi(label, value):
    st.markdown(f'<div class="hf-kpi"><div class="hf-kpi-label">{label}</div><div class="hf-kpi-value">{value}</div></div>', unsafe_allow_html=True)

def status_label(code): return STATUS_LABELS.get(code, code or "未分类")
