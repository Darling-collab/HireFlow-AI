import io, re
from datetime import datetime
import pandas as pd
from .db import SessionLocal
from .models import Candidate

ALIASES={"name":["姓名","候选人姓名","name"],"position":["应聘岗位","岗位","职位","position"],"phone":["手机号","联系电话","联系方式","phone"],"email":["邮箱","邮箱地址","email"],"source":["招聘渠道","渠道","来源","source"],"status_key":["招聘阶段","当前状态","状态","status","status_key"],"follow_up_date":["跟进时间","跟进日期","follow_up_date"],"notes":["备注","notes"]}
VALID={"invited","screening_passed","first_round_passed","second_round_passed","final_round_passed","offer_sent","offer_accepted","hired","withdrawn","rejected","talent_pool","pending_confirmation"}

class ImportService:
    def __init__(self,session_factory=SessionLocal): self.session_factory=session_factory
    def suggest_mapping(self,columns):
        return {field:next((c for c in columns if str(c).strip().lower() in [a.lower() for a in aliases]),None) for field,aliases in ALIASES.items()}
    def validate(self,df,mapping):
        valid=[]; errors=[]; duplicates=[]
        with self.session_factory() as s:
            phones={x[0] for x in s.query(Candidate.phone).filter(Candidate.phone.isnot(None)).all()}; emails={x[0] for x in s.query(Candidate.email).filter(Candidate.email.isnot(None)).all()}; pairs={(x.name,x.position) for x in s.query(Candidate).all()}
        for idx,row in df.fillna("").iterrows():
            data={k:str(row[v]).strip() if v and v in row else "" for k,v in mapping.items()}; problems=[]
            if not data.get("name"): problems.append("姓名为空")
            if not data.get("position"): problems.append("岗位为空")
            if data.get("email") and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$",data["email"]): problems.append("邮箱格式错误")
            if data.get("phone") and not re.match(r"^1[3-9]\d{9}$",data["phone"]): problems.append("手机号格式错误")
            status=data.get("status_key") or "invited"; data["status_key"]=status
            if status not in VALID: problems.append("招聘阶段不合法")
            if data.get("follow_up_date"):
                try: data["follow_up_date"]=pd.to_datetime(data["follow_up_date"]).date()
                except Exception: problems.append("跟进日期格式错误")
            duplicate=(data.get("phone") and data["phone"] in phones) or (data.get("email") and data["email"] in emails) or ((data.get("name"),data.get("position")) in pairs)
            if duplicate: duplicates.append({"row":int(idx)+2,"data":data,"reason":"疑似重复候选人"})
            elif problems: errors.append({"row":int(idx)+2,"data":data,"reason":"；".join(problems)})
            else: valid.append({"row":int(idx)+2,"data":data})
        return {"total":len(df),"valid":valid,"duplicates":duplicates,"errors":errors}
    def import_valid(self,report):
        with self.session_factory() as s:
            try:
                for item in report["valid"]:
                    d=item["data"]; s.add(Candidate(name=d["name"],position=d["position"],phone=d.get("phone") or None,email=d.get("email") or None,source=d.get("source") or "批量导入",status="new",status_key=d["status_key"],status_raw=d["status_key"],follow_up_date=d.get("follow_up_date") or None,notes=d.get("notes") or None))
                s.commit(); return len(report["valid"])
            except Exception: s.rollback(); raise

def export_dataframe(candidates):
    columns=["姓名","应聘岗位","招聘阶段","招聘渠道","手机号","邮箱","跟进日期","备注"]
    return pd.DataFrame([{"姓名":c.name,"应聘岗位":c.position,"招聘阶段":c.status_key or c.status,"招聘渠道":c.source,"手机号":c.phone,"邮箱":c.email,"跟进日期":c.follow_up_date,"备注":c.notes} for c in candidates], columns=columns)
