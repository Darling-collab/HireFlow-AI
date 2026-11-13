import streamlit as st
from hireflow.config import get_settings
from hireflow.db import engine, health_check
from hireflow.queries import QueryService
from hireflow.ui import page_header, status_label

def render(qs=None):
    page_header("系统设置", "查看运行模式、模型信息、数据库连接和标准状态")
    s=get_settings(); a,b,c=st.columns(3)
    a.metric("运行环境", s.app_env); b.metric("AI 模式", "DeepSeek" if s.ai_enabled else "Mock 模拟"); c.metric("数据库", "正常" if health_check() else "异常")
    st.subheader("连接信息"); st.code(f"dialect={engine.dialect.name}\nmodel={s.deepseek_model}\nbase_url={s.deepseek_base_url}\nprompt_version=hireflow-recruitment-v2.1")
    st.subheader("标准状态字典")
    rows=(qs or QueryService()).statuses(); st.table([{"code":x.code,"label":x.label} for x in rows])
    st.caption("权限配置和密钥修改不在普通 HR 页面开放。")
