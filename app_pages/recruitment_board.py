import streamlit as st
from hireflow.queries import QueryService
from hireflow.ui import page_header, status_label

def render(qs=None):
    page_header("招聘流程看板", "按标准阶段查看候选人分布；状态变更继续由业务引擎校验")
    qs=qs or QueryService(); rows=qs.candidates(); columns=["invited","screening_passed","first_round_passed","second_round_passed","final_round_passed","offer_sent","offer_accepted","hired"]
    cols=st.columns(len(columns))
    for col,status in zip(cols,columns):
        with col:
            st.markdown(f"**{status_label(status)}**")
            cards=[x for x in rows if x.status_key==status]; st.caption(f"{len(cards)} 人")
            for c in cards:
                with st.container(border=True): st.markdown(f"**{c.name}**\n\n{c.position or '未填写'}\n\n`#{c.id}`")
