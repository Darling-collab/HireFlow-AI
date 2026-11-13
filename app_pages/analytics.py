import pandas as pd
import plotly.express as px
import streamlit as st
from hireflow.queries import QueryService
from hireflow.ui import page_header, status_label

def render(qs=None):
    page_header("招聘分析报告", "指标来自当前数据库；AI 报告能力将在真实聚合基础上继续扩展")
    qs=qs or QueryService(); counts=qs.status_counts(); src=qs.source_counts(); c1,c2=st.columns(2)
    with c1:
        st.subheader("阶段分布"); df=pd.DataFrame({"阶段":[status_label(k) for k in counts],"人数":list(counts.values())}); st.plotly_chart(px.bar(df,x="阶段",y="人数",color_discrete_sequence=["#7c3aed"]), width="stretch") if not df.empty else st.info("暂无数据")
    with c2:
        st.subheader("渠道分布"); df=pd.DataFrame({"渠道":[x or "未知" for x in src],"人数":list(src.values())}); st.plotly_chart(px.pie(df,names="渠道",values="人数"), width="stretch") if not df.empty else st.info("暂无数据")
    st.info("当前为数据库模板分析模式；未配置 DeepSeek 时不会伪装成 AI 结论。")
