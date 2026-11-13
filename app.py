import streamlit as st
from hireflow.db import init_db, seed_demo_data, seed_status_dictionary
from hireflow.queries import QueryService
from hireflow.services import RecruitmentService
from hireflow.ui import inject_theme

st.set_page_config(page_title="HireFlow AI", page_icon="✦", layout="wide", initial_sidebar_state="expanded")
inject_theme(); init_db(); seed_status_dictionary()
if "seeded" not in st.session_state:
    seed_demo_data(); st.session_state.seeded=True

PAGES={"总览":"dashboard","AI 智能采集":"ai_intake","候选人管理":"candidates","招聘流程看板":"recruitment_board","提醒中心":"reminders","招聘分析":"analytics","数据管理":"data_tools"}
with st.sidebar:
    st.markdown('<div class="hf-brand">HireFlow AI</div>', unsafe_allow_html=True)
    st.caption("Recruiting intelligence workspace")
    choice=st.radio("导航", list(PAGES), label_visibility="collapsed")
    st.divider()
    from hireflow.config import get_settings
    st.caption("AI 模式：" + ("DeepSeek" if get_settings().ai_enabled else "Mock 模拟"))
    st.caption("V2 · Phase 3")

qs=QueryService(); service=RecruitmentService(); module=PAGES[choice]
if module == "dashboard":
    from app_pages.dashboard import render; render(qs)
elif module == "ai_intake":
    from app_pages.ai_intake import render; render(service)
elif module == "review_center":
    from app_pages.review_center import render; render(service, qs)
elif module == "candidates":
    from app_pages.candidates import render; render(qs)
elif module == "recruitment_board":
    from app_pages.recruitment_board import render; render(qs)
elif module == "reminders":
    from app_pages.reminders import render; render(qs)
elif module == "bad_cases":
    from app_pages.bad_cases import render; render(qs)
elif module == "analytics":
    from app_pages.analytics import render; render(qs)
elif module == "data_tools":
    from app_pages.data_tools import render; render()
else:
    from app_pages.settings import render; render(qs)
