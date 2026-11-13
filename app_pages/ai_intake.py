import json
import streamlit as st
from hireflow.parsers import extract_upload
from hireflow.queries import QueryService
from hireflow.services import RecruitmentService
from hireflow.ui import page_header, status_label

st.markdown("""<style>
.hf-review-card{border:1px solid #e3e8f0;border-radius:16px;background:#fff;padding:1.05rem 1.15rem;margin:.6rem 0 1rem;box-shadow:0 5px 18px rgba(15,23,42,.05)}
.hf-review-head{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #eef2f7;padding-bottom:.7rem;margin-bottom:.8rem}
.hf-review-name{font-size:1.05rem;font-weight:700;color:#102a43}.hf-review-job{color:#64748b;font-size:.9rem;margin-left:.45rem}
.hf-review-status{font-size:.78rem;color:#2563eb;background:#eff6ff;border-radius:999px;padding:.25rem .55rem}
.hf-field-label{color:#64748b;font-size:.75rem;margin-bottom:.15rem}.hf-field-value{color:#102a43;font-size:.92rem;min-height:1.4rem}
.hf-complete{background:#f0fdf4;border:1px solid #bbf7d0;color:#166534;border-radius:10px;padding:.55rem .7rem;font-size:.83rem}
.hf-missing{background:#fff7ed;border:1px solid #fed7aa;color:#9a3412;border-radius:10px;padding:.55rem .7rem;font-size:.83rem}
.hf-review-actions{border-top:1px solid #eef2f7;padding-top:.8rem;margin-top:.8rem}
</style>""", unsafe_allow_html=True)

def _review_card(review, service):
    data=json.loads(review.output_json or "[]")
    for i,item in enumerate(data):
        with st.container(border=True):
            name=item.get('name') or '姓名待补全'; position=item.get('position') or '岗位待补全'; missing=item.get('missing_fields',[])
            st.markdown(f'<div class="hf-review-head"><div><span class="hf-review-name">{name}</span><span class="hf-review-job">{position}</span></div><span class="hf-review-status">待审核</span></div>', unsafe_allow_html=True)
            cols=st.columns(5)
            fields=[("联系电话",item.get('phone') or '待补全'),("邮箱",item.get('email') or '待补全'),("招聘阶段",status_label(item.get('status_key')) if item.get('status_key') else item.get('status_raw') or '待确认'),("招聘结果",item.get('result') or '待确认'),("招聘来源",item.get('source') or '消息导入')]
            for col,(label,value) in zip(cols,fields):
                col.markdown(f'<div class="hf-field-label">{label}</div><div class="hf-field-value">{value}</div>', unsafe_allow_html=True)
            if missing:
                st.markdown(f'<div class="hf-missing">信息待补全：{"、".join(missing)}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="hf-complete">信息完整，可以提交审核</div>', unsafe_allow_html=True)
            st.markdown('<div class="hf-review-actions"></div>', unsafe_allow_html=True)
            a,b,c=st.columns(3)
            if a.button("确认入库", key=f"confirm_{review.id}_{i}", type="primary", width="stretch", disabled=bool(missing)):
                try: service.review(review.id,"confirmed",records=[item]); st.success("已确认入库"); st.rerun()
                except Exception as exc: st.error(f"未能入库：{exc}")
            if b.button("修改信息", key=f"modify_{review.id}_{i}", width="stretch"):
                st.session_state[f"edit_{review.id}_{i}"]=True
            if c.button("驳回记录", key=f"reject_{review.id}_{i}", width="stretch"):
                service.review(review.id,"rejected",records=[item],reason="HR 在采集中心驳回"); st.warning("已保留为异常记录"); st.rerun()
            if st.session_state.get(f"edit_{review.id}_{i}"):
                with st.form(f"edit_form_{review.id}_{i}"):
                    name=st.text_input("姓名",item.get("name") or ""); position=st.text_input("岗位",item.get("position") or ""); phone=st.text_input("手机号",item.get("phone") or ""); email=st.text_input("邮箱",item.get("email") or "")
                    if st.form_submit_button("提交修改"):
                        service.review(review.id,"modified",records=[{**item,"name":name,"position":position,"phone":phone,"email":email}]); st.success("已修改并入库"); st.rerun()

def render(service=None, qs=None):
    page_header("AI 智能采集中心", "文本、表格和文档先解析为审核卡片，确认后才进入正式招聘数据")
    service=service or RecruitmentService(); qs=qs or QueryService()
    tab1,tab2=st.tabs(["采集与审核","异常记录"])
    with tab1:
        left,right=st.columns([1.05,1])
        with left:
            source=st.selectbox("来源类型",["手动粘贴","邮件","招聘平台","内部转发"])
            raw=st.text_area("招聘消息",height=230,placeholder="姓名：张三\n职位：Python 后端工程师\n阶段：已邀约")
            upload=st.file_uploader("或上传文本 / CSV / Excel / PDF / Word / 图片",type=["txt","md","csv","xlsx","xls","pdf","docx","png","jpg","jpeg"])
            if upload:
                preview,status=extract_upload(upload); st.caption(f"{upload.name} · {status}")
                if status == "parsed": raw=preview; st.text_area("解析预览",preview,height=120,disabled=True)
                else: st.warning(status)
            if st.button("开始 AI 解析",type="primary",width="stretch"):
                if not raw.strip(): st.error("请输入消息或上传可解析文件")
                else:
                    try:
                        rid,review_id,response=service.ingest_message(raw,source,upload.name if upload else None); st.session_state.last_review_id=review_id; st.markdown('<div class="hf-complete">消息已提交，请完成候选人信息审核</div>', unsafe_allow_html=True)
                    except Exception as exc: st.error(f"解析失败：{exc}")
        with right:
            st.subheader("待审核记录")
            pending=qs.reviews("pending")
            if not pending: st.info("暂无待审核记录")
            for review in pending[:10]:
                _review_card(review,service)
    with tab2:
        bad=qs.bad_cases()
        if not bad: st.success("暂无异常记录")
        for item in bad[:20]:
            with st.expander(f"{item.reason} · {item.created_at}"):
                st.write(item.resolution or "请查看原始消息记录")
