import json
import streamlit as st
from hireflow.services import RecruitmentService
from hireflow.queries import QueryService
from hireflow.ui import page_header, status_label

def render(service=None, qs=None):
    page_header("AI 待审核工作台", "审核通过后才会创建候选人档案和招聘事件")
    service=service or RecruitmentService(); qs=qs or QueryService()
    tabs=st.tabs(["待确认","已修改","已驳回","已过期"])
    for tab,status in zip(tabs,["pending","modified","rejected","expired"]):
        with tab:
            rows=qs.reviews(status)
            if not rows: st.info("暂无记录")
            for review in rows:
                with st.container(border=True):
                    data=json.loads(review.output_json or "[]"); first=data[0] if data else {}
                    st.markdown(f"**审核 #{review.id}** · {first.get('name') or '未识别'} · {first.get('position') or '未填写'}")
                    st.caption(f"来源：{review.mode} / {review.model or '未知'} · 创建：{review.created_at}")
                    st.json(data, expanded=False)
                    if status == "pending":
                        with st.form(f"review_{review.id}"):
                            decision=st.selectbox("处理", ["confirmed","modified","rejected"], format_func=lambda x:{"confirmed":"确认入库","modified":"修改后入库","rejected":"驳回"}[x])
                            name=st.text_input("姓名", first.get("name") or "")
                            position=st.text_input("岗位", first.get("position") or "")
                            reason=st.text_input("驳回原因（驳回时填写）")
                            if st.form_submit_button("提交审核", type="primary"):
                                records=data
                                if decision == "modified":
                                    records=[{**first,"name":name,"position":position}]
                                try:
                                    service.review(review.id, decision, records=records, reason=reason or None); st.success("审核已提交"); st.rerun()
                                except Exception as exc: st.error(f"审核未完成：{exc}")
