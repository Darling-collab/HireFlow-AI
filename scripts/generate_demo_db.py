"""Create isolated, repeatable demo data; never writes data/hireflow.db."""
import argparse, random, sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from hireflow.models import Base, Candidate, RecruitmentEvent, Reminder, Position, BadCase

POSITIONS=["Python 后端工程师","Java 后端工程师","前端开发工程师","测试开发工程师","数据开发工程师","数据分析师","算法工程师","大模型应用研发工程师","AI 产品经理","产品经理","UI 设计师","运维工程师","客户端开发工程师","运营专员","人力资源专员"]
CHANNELS=["Boss直聘","猎聘","智联招聘","前程无忧","LinkedIn","内部员工推荐","校园招聘","公司官网","社交招聘渠道"]
STAGES=["invited","screening_passed","first_round_passed","second_round_passed","final_round_passed","offer_sent","offer_accepted","hired","withdrawn","rejected","talent_pool"]
FAMILY=["林","周","陈","许","沈","顾","唐","徐","苏","韩","宋","江","梁","叶","温","程","陆","傅","方","郑","沈","沈","谢","何","罗","彭","蒋","袁","邵","白"]
GIVEN=["雨桐","亦辰","思远","嘉宁","若涵","明轩","婉清","子墨","念安","景行","知夏","承宇","书瑶","星辰","予安","嘉言","清妍","景川","以宁","明哲","语嫣","昊然","安然","修远","可心","宇轩","诗涵","泽宇","欣怡","浩然"]

def main():
    p=argparse.ArgumentParser(); p.add_argument("--output",default="data/hireflow-demo.db"); p.add_argument("--count",type=int,default=500); args=p.parse_args()
    output=Path(args.output).resolve(); real=Path("data/hireflow.db").resolve()
    if output==real: raise SystemExit("Refusing to write the real work database")
    engine=create_engine(f"sqlite:///{output}"); Base.metadata.create_all(engine); Session=sessionmaker(bind=engine)
    with Session() as s:
        if s.query(Candidate).count(): print(f"demo database already populated: {output}"); return
        for title in POSITIONS: s.add(Position(title=title,description="演示岗位",status="open"))
        now=datetime.now(timezone.utc); rng=random.Random(20261112); names=[f"{rng.choice(FAMILY)}{rng.choice(GIVEN)}{i:03d}" for i in range(args.count)]
        candidates=[]
        for i,name in enumerate(names):
            stage=rng.choices(STAGES,weights=[10,15,16,12,8,7,5,6,5,10,6])[0]; created=now-timedelta(days=rng.randint(0,180)); follow=date.today()+timedelta(days=rng.randint(-14,14)); c=Candidate(name=name,email=f"demo{i:03d}@example.com",phone=f"139{i:08d}",position=rng.choice(POSITIONS),source=rng.choice(CHANNELS),status="new",status_key=stage,status_raw=stage,follow_up_date=follow,notes="演示数据",created_at=created,updated_at=created,last_activity_at=created); s.add(c); s.flush(); candidates.append(c)
            path={"screening_passed":["invited"],"first_round_passed":["invited","screening_passed"],"second_round_passed":["invited","screening_passed","first_round_passed"],"final_round_passed":["invited","screening_passed","first_round_passed","second_round_passed"],"offer_sent":["invited","screening_passed","first_round_passed","second_round_passed","final_round_passed"],"offer_accepted":["invited","screening_passed","first_round_passed","second_round_passed","final_round_passed","offer_sent"],"hired":["invited","screening_passed","first_round_passed","second_round_passed","final_round_passed","offer_sent","offer_accepted"]}.get(stage,[])+[stage]
            for j,evstage in enumerate(path):
                evtime=created+timedelta(days=j+1); s.add(RecruitmentEvent(candidate_id=c.id,event_type="stage_update",status_key=evstage,raw_expression="演示招聘事件",dedupe_key=f"demo-{i}-{j}",event_time=evtime,created_at=evtime))
            if i<180: s.add(Reminder(candidate_id=c.id,due_at=datetime.combine(follow,datetime.min.time(),tzinfo=timezone.utc),status="pending" if i<80 else "completed",message="演示跟进任务",created_at=created))
        for i in range(8): s.add(BadCase(reason="DEMO_UNKNOWN_STATUS" if i%2 else "DEMO_MISSING_FIELD",raw_status="演示异常",resolution="演示数据，不进入候选人统计",created_at=now-timedelta(days=i)))
        s.commit()
        print(f"created isolated demo database: {output} candidates={len(candidates)} events={s.query(RecruitmentEvent).count()} reminders={s.query(Reminder).count()} positions={s.query(Position).count()}")
if __name__=="__main__": main()
