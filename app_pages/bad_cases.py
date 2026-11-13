import pandas as pd
import streamlit as st
from hireflow.queries import QueryService
from hireflow.ui import page_header

def render(qs=None):
    page_header("BadCase 管理中心", "所有异常都保留原始上下文，便于复盘和修正")
    qs=qs or QueryService(); rows=qs.bad_cases()
    if not rows: st.success("暂无异常记录"); return
    reasons=sorted({r.reason for r in rows}); selected=st.multiselect("异常分类", reasons, default=reasons)
    rows=[r for r in rows if r.reason in selected]
    st.dataframe(pd.DataFrame([{"ID":r.id,"类型":r.reason,"候选人":r.candidate_id or "—","原始状态":r.raw_status or "—","原因":r.resolution or "—","时间":r.created_at} for r in rows]), width="stretch", hide_index=True)
