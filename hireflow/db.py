from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from .config import get_settings
from .models import Base, Candidate, StatusDictionary

settings = get_settings()
if settings.database_url.startswith("sqlite"):
    Path("data").mkdir(exist_ok=True)
    connect_args = {"check_same_thread": False}
else:
    connect_args = {"connect_timeout": 10}
engine = create_engine(settings.database_url, connect_args=connect_args, pool_pre_ping=True, pool_recycle=1800)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

def init_db(): Base.metadata.create_all(engine)

def health_check() -> bool:
    with engine.connect() as connection:
        return connection.execute(text("SELECT 1")).scalar_one() == 1

def seed_status_dictionary():
    statuses = [("invited", "已邀约"), ("screening_passed", "初筛通过"), ("first_round_passed", "一面通过"), ("second_round_passed", "二面通过"), ("final_round_passed", "终面通过"), ("offer_sent", "Offer 已发"), ("offer_accepted", "Offer 已接受"), ("hired", "已入职"), ("withdrawn", "已放弃"), ("rejected", "已淘汰"), ("talent_pool", "人才池储备")]
    with SessionLocal() as session:
        existing = {row.code for row in session.query(StatusDictionary).all()}
        for code, label in statuses:
            if code not in existing: session.add(StatusDictionary(code=code, label=label))
        session.commit()

def seed_demo_data():
    from datetime import date, timedelta
    with SessionLocal() as session:
        if session.query(Candidate).count(): return
        session.add_all([Candidate(name="李小雨", email="xiaoyu@example.com", position="Python 后端工程师", source="Boss直聘", status="screening", follow_up_date=date.today()), Candidate(name="王明", email="wangming@example.com", position="数据分析师", source="内推", status="interview", follow_up_date=date.today() + timedelta(days=1)), Candidate(name="陈晨", position="产品经理", source="LinkedIn", status="hired")])
        session.commit()
