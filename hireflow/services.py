import io, json, os, re
from datetime import date, timedelta
import pandas as pd
import requests
from .db import SessionLocal, Candidate

class RecruitmentService:
    """V2 event-driven facade; V1 services below remain available for compatibility."""
    def __init__(self, *args, **kwargs):
        from .engine import RecruitmentEngine
        self.engine = RecruitmentEngine(*args, **kwargs)
    def ingest_message(self, content, source="unknown", filename=None):
        return self.engine.ingest_message(content, source, filename)
    def review(self, review_id, decision, records=None, reviewer_id=None, reason=None):
        return self.engine.review(review_id, decision, records, reviewer_id, reason)
    def process_timeouts(self):
        return self.engine.process_timeouts()

class CandidateService:
    STATUSES = ["new", "screening", "interview", "offer", "hired", "rejected"]
    def list(self, query=""):
        with SessionLocal() as s:
            rows = s.query(Candidate).order_by(Candidate.created_at.desc()).all()
            if query: rows = [c for c in rows if query.lower() in " ".join(filter(None, [c.name,c.email,c.position,c.source])).lower()]
            return rows
    def create(self, name, email="", phone="", position="", source="消息导入", notes=""):
        with SessionLocal() as s:
            c=Candidate(name=name,email=email,phone=phone,position=position,source=source,notes=notes,status="new",follow_up_date=date.today()); s.add(c); s.commit(); return c
    def update(self, cid, **fields):
        with SessionLocal() as s:
            c=s.get(Candidate,cid)
            for k,v in fields.items(): setattr(c,k,v)
            s.commit()
    def due_followups(self):
        return [c for c in self.list() if c.follow_up_date and c.follow_up_date <= date.today() and c.status not in ("hired","rejected")]
    def to_excel(self):
        out=io.BytesIO(); pd.DataFrame([c.to_dict() for c in self.list()]).to_excel(out,index=False); return out.getvalue()
    def to_markdown(self):
        df = pd.DataFrame([c.to_dict() for c in self.list()])
        try:
            return df.to_markdown(index=False)
        except ImportError:
            headers = list(df.columns)
            lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
            lines.extend("| " + " | ".join(str(row.get(h, "")) for h in headers) + " |" for _, row in df.iterrows())
            return "\n".join(lines)
    def import_dataframe(self, df):
        count=0
        for _,r in df.fillna("").iterrows():
            if r.get("name"): self.create(str(r.get("name")),str(r.get("email","")),str(r.get("phone","")),str(r.get("position","")),str(r.get("source","导入")),str(r.get("notes",""))); count+=1
        return count

class MessageService:
    def parse(self, raw):
        key=os.getenv("DEEPSEEK_API_KEY")
        if key:
            try:
                r=requests.post(os.getenv("DEEPSEEK_BASE_URL","https://api.deepseek.com")+"/chat/completions",headers={"Authorization":f"Bearer {key}"},json={"model":os.getenv("DEEPSEEK_MODEL","deepseek-chat"),"messages":[{"role":"system","content":"Extract JSON fields name,email,phone,position,source,notes from recruiting message."},{"role":"user","content":raw}],"temperature":0},timeout=30); r.raise_for_status(); data=json.loads(r.json()["choices"][0]["message"]["content"]); data["mode"]="deepseek"; return data
            except Exception: pass
        def find(pattern):
            m=re.search(pattern,raw,re.I)
            return (m.group(1) if m.lastindex else m.group(0)).strip() if m else ""
        lines=[x.strip() for x in raw.splitlines() if x.strip()]
        return {"name": find(r"(?:姓名|^)(?:：|:|\s)?([^\n：:]+)") or (lines[0] if lines else ""), "email": find(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}"), "phone": find(r"1[3-9]\d{9}"), "position": find(r"(?:应聘职位|职位|岗位)[：:]?([^\n]+)"), "source": find(r"(?:来源)[：:]?([^\n]+)") or "消息导入", "notes": raw, "mode":"mock"}

class ReportService:
    def generate(self, period):
        rows=CandidateService().list(); df=pd.DataFrame([c.to_dict() for c in rows]); counts=df.status.value_counts().to_dict() if not df.empty else {}
        return f"# HireFlow AI {period}\n\n生成时间：{date.today()}\n\n## 概览\n\n- 候选人总数：{len(rows)}\n- 状态分布：`{counts}`\n- 待跟进：{len(CandidateService().due_followups())}\n\n## 建议\n\n优先处理待跟进候选人，并为面试阶段候选人补充下一步动作。"
