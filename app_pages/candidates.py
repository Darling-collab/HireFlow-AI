import pandas as pd
import streamlit as st
from hireflow.queries import QueryService
from hireflow.services import CandidateService
from hireflow.ui import page_header, status_label

def render(qs=None, service=None):
    page_header("候选人管理", "搜索、筛选和查看完整招聘历史")
    qs=qs or QueryService(); service=service or CandidateService()
    a,b,c=st.columns([2,1,1]); query=a.text_input("搜索姓名、岗位或邮箱"); statuses=qs.statuses(); selected=b.selectbox("状态",["全部"]+[x.code for x in statuses],format_func=lambda x:"全部" if x=="全部" else status_label(x)); st.button("新增候选人", type="primary", disabled=True, help="下一迭代接入表单")
    rows=qs.candidates(query, None if selected=="全部" else selected)
    if not rows: st.info("暂无匹配候选人"); return
    st.dataframe(pd.DataFrame([{"ID":x.id,"姓名":x.name,"岗位":x.position or "—","邮箱":x.email or "—","电话":("****"+x.phone[-4:] if x.phone and len(x.phone)>4 else x.phone or "—"),"阶段":status_label(x.status_key or x.status),"来源":x.source or "—","跟进日期":x.follow_up_date} for x in rows]), width="stretch", hide_index=True)
    st.subheader("候选人详情")
    chosen=st.selectbox("选择候选人", rows, format_func=lambda x:f"#{x.id} {x.name} · {x.position or '未填写'}")
    if chosen:
        def fmt(value): return value.strftime("%Y年%m月%d日") if hasattr(value, "strftime") else (value or "—")
        st.markdown(f"**{chosen.name}**　`{status_label(chosen.status_key or chosen.status)}`")
        st.write(f"岗位：{chosen.position or '—'}　来源：{chosen.source or '—'}　邮箱：{chosen.email or '—'}　手机号：{'****'+chosen.phone[-4:] if chosen.phone and len(chosen.phone)>4 else chosen.phone or '—'}")
        st.write(f"创建于：{fmt(chosen.created_at)}　最近更新：{fmt(chosen.updated_at)}　下次跟进：{fmt(chosen.follow_up_date)}")
        if chosen.notes: st.markdown("**备注**\n\n" + chosen.notes)
        events=qs.events(chosen.id)
        st.caption("招聘时间线")
        st.dataframe(pd.DataFrame([{"事件":e.event_type,"阶段":status_label(e.status_key),"时间":e.created_at,"原始表达":e.raw_expression or "—"} for e in events]), width="stretch", hide_index=True) if events else st.info("暂无招聘事件")
