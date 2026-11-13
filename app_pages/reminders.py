import pandas as pd
import streamlit as st
from hireflow.queries import QueryService
from hireflow.ui import page_header

def render(qs=None):
    page_header("提醒中心", "查看审核超时和候选人跟进任务")
    qs=qs or QueryService(); rows=qs.reminders(); status=st.segmented_control("状态", ["全部","待处理","已完成"], default="全部")
    if status != "全部": rows=[r for r in rows if r.status == ("pending" if status=="待处理" else "completed")]
    if not rows: st.info("暂无提醒")
    else: st.dataframe(pd.DataFrame([{"ID":r.id,"候选人":r.candidate_id or "—","截止时间":r.due_at,"状态":r.status,"内容":r.message or "—"} for r in rows]), width="stretch", hide_index=True)
