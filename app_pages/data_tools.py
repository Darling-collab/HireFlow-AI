import io, json
import pandas as pd
import streamlit as st
from hireflow.import_export import ALIASES, ImportService, export_dataframe
from hireflow.queries import QueryService
from hireflow.ui import page_header

def render():
    page_header("数据管理","先预览、映射和校验，再执行事务级导入")
    importer=ImportService(); qs=QueryService(); tab1,tab2=st.tabs(["导入数据","导出数据"])
    with tab1:
        upload=st.file_uploader("上传 CSV / Excel",type=["csv","xlsx","xls"])
        if upload:
            try: df=pd.read_csv(upload) if upload.name.lower().endswith(".csv") else pd.read_excel(upload)
            except Exception as exc: st.error(f"文件读取失败：{exc}"); return
            st.caption(f"共 {len(df)} 行，预览前 20 行"); st.dataframe(df.head(20),width="stretch",hide_index=True)
            suggested=importer.suggest_mapping(df.columns); st.subheader("字段映射")
            mapping={}; cols=list(df.columns); grid=st.columns(3)
            for i,field in enumerate(ALIASES):
                options=["不导入"]+cols; default=options.index(suggested[field]) if suggested[field] in options else 0
                mapping[field]=grid[i%3].selectbox(field,options,index=default,key=f"map_{field}")
                if mapping[field]=="不导入": mapping[field]=None
            if st.button("校验数据",type="primary"):
                st.session_state.import_report=importer.validate(df,mapping)
            report=st.session_state.get("import_report")
            if report:
                a,b,c,d=st.columns(4); a.metric("文件总行数",report["total"]); b.metric("可导入",len(report["valid"])); c.metric("重复",len(report["duplicates"])); d.metric("错误",len(report["errors"]))
                issues=report["duplicates"]+report["errors"]
                if issues:
                    issue_df=pd.DataFrame([{"行号":x["row"],"原因":x["reason"],"姓名":x["data"].get("name"),"岗位":x["data"].get("position")} for x in issues]); st.dataframe(issue_df,width="stretch",hide_index=True); st.download_button("下载错误报告",issue_df.to_csv(index=False).encode("utf-8-sig"),"import-errors.csv","text/csv")
                confirm=st.checkbox("我确认导入校验通过的记录，重复记录默认跳过")
                if st.button("确认导入",type="primary",disabled=not confirm or not report["valid"]):
                    try: count=importer.import_valid(report); st.success(f"成功写入 {count} 条；重复 {len(report['duplicates'])} 条；错误 {len(report['errors'])} 条")
                    except Exception as exc: st.error(f"数据库写入失败，事务已回滚：{exc}")
    with tab2:
        df=export_dataframe(qs.candidates()); st.caption(f"当前可导出 {len(df)} 条候选人")
        excel=io.BytesIO(); df.to_excel(excel,index=False)
        st.download_button("导出 Excel",excel.getvalue(),"hireflow-candidates.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.download_button("导出 CSV",df.to_csv(index=False).encode("utf-8-sig"),"hireflow-candidates.csv","text/csv")
        try: markdown=df.to_markdown(index=False)
        except ImportError: markdown=df.to_csv(index=False)
        st.download_button("导出 Markdown",markdown,"hireflow-candidates.md","text/markdown")
