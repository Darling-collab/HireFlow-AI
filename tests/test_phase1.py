from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from hireflow.models import Base, Candidate, RecruitmentEvent

@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as session:
        yield session
        session.rollback()
    engine.dispose()

def test_candidate_and_event_relationship_by_id(session):
    candidate = Candidate(name="测试候选人", status="new", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
    session.add(candidate); session.flush()
    session.add(RecruitmentEvent(candidate_id=candidate.id, event_type="message_received", dedupe_key="test-1")); session.commit()
    assert session.get(Candidate, candidate.id).name == "测试候选人"
    assert session.query(RecruitmentEvent).count() == 1

def test_duplicate_event_is_rejected(session):
    candidate = Candidate(name="重复事件", status="new", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
    session.add(candidate); session.flush()
    session.add_all([RecruitmentEvent(candidate_id=candidate.id, event_type="x", dedupe_key="same"), RecruitmentEvent(candidate_id=candidate.id, event_type="x", dedupe_key="same")])
    with pytest.raises(IntegrityError): session.commit()

def test_transaction_rolls_back(session):
    session.add(Candidate(name="回滚候选人", status="new", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)))
    session.rollback()
    assert session.query(Candidate).count() == 0
