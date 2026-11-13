import pandas as pd
import plotly.express as px
import streamlit as st
from hireflow.queries import QueryService
from hireflow.ui import kpi, page_header, status_label

def render(qs=QueryService()):
    page_header("招聘总览", "用真实招聘数据掌握团队节奏")
    m=qs.metrics(); cols=st.columns(7)
    for col,(label,key) in zip(cols,[("开放岗位","positions"),("候选人","candidates"),("本月新增","new_this_month"),("待审核","pending_reviews"),("面试中","interviews"),("Offer","offers"),("已入职","hired")]):
        with col: kpi(label,m[key])
    st.divider(); c1,c2=st.columns(2)
    counts=qs.status_counts(); order=["invited","screening_passed","first_round_passed","second_round_passed","final_round_passed","offer_sent","offer_accepted","hired"]
    with c1:
        st.subheader("招聘漏斗"); df=pd.DataFrame({"阶段":[status_label(x) for x in order],"人数":[counts.get(x,0) for x in order]}); st.plotly_chart(px.bar(df,x="阶段",y="人数",text="人数",color_discrete_sequence=["#2563eb"]), width="stretch")
    with c2:
        st.subheader("招聘渠道"); src=qs.source_counts(); df=pd.DataFrame({"渠道":[x or "未知" for x in src],"人数":list(src.values())}); st.plotly_chart(px.pie(df,names="渠道",values="人数",color_discrete_sequence=["#2563eb","#7c3aed","#14b8a6","#f59e0b"]), width="stretch") if not df.empty else st.info("暂无渠道数据")
    st.subheader("最近招聘动态")
    events=qs.events(limit=8)
    if events: st.dataframe(pd.DataFrame([{"事件":e.event_type,"候选人 ID":e.candidate_id,"阶段":status_label(e.status_key),"时间":e.created_at} for e in events]), width="stretch", hide_index=True)
    else: st.info("暂无招聘事件")
