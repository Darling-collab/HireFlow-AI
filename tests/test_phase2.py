import json
from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from hireflow.ai.base_client import AIResponse, AIClientError
from hireflow.ai.mock_client import MockAIClient
from hireflow.ai.deepseek_client import DeepSeekClient
from hireflow.ai.schemas import CandidateExtraction
from hireflow.engine import Clock, RecruitmentEngine
from hireflow.models import Base, AIReviewRecord, BadCase, Candidate, RawMessage, RecruitmentEvent, Reminder

@pytest.fixture()
def factory():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)

class FixedClient:
    def __init__(self, records): self.records = records
    def parse_recruitment_message(self, text): return AIResponse(self.records, "mock", "test-model", "test-prompt-v1", 1)

def rec(name="张三", position="后端工程师", status="invited", **kwargs):
    return CandidateExtraction(name=name, position=position, status_key=status, status_raw=kwargs.pop("status_raw", status), **kwargs).validate()

def test_standard_message_and_raw_persistence(factory):
    engine = RecruitmentEngine(factory, FixedClient([rec()]))
    raw_id, review_id, response = engine.ingest_message("张三 应聘 后端工程师")
    with factory() as s:
        assert s.get(RawMessage, raw_id).content == "张三 应聘 后端工程师"
        assert s.get(AIReviewRecord, review_id).review_status == "pending"
        assert response.records[0].name == "张三"

def test_multi_candidate_message(factory):
    client = MockAIClient()
    response = client.parse_recruitment_message("姓名：张三\n职位：后端工程师\n---\n姓名：李四\n职位：数据分析师")
    assert len(response.records) == 2

@pytest.mark.parametrize("bad", [CandidateExtraction(position="后端", status_key="invited"), CandidateExtraction(name="张三", status_key="invited")])
def test_missing_required_fields_become_bad_case(factory, bad):
    engine = RecruitmentEngine(factory, FixedClient([bad.validate()]))
    _, review_id, _ = engine.ingest_message("缺失字段")
    assert engine.review(review_id, "confirmed") == []
    with factory() as s: assert s.query(BadCase).count() == 1

def test_unknown_status_is_bad_case(factory):
    item = rec(status=None, status_raw="神秘阶段")
    engine = RecruitmentEngine(factory, FixedClient([item]))
    _, review_id, _ = engine.ingest_message("未知状态")
    assert engine.review(review_id, "confirmed") == []
    with factory() as s: assert s.query(BadCase).filter_by(reason="UNKNOWN_STATUS").count() == 1

def test_non_recruitment_message_is_retained(factory):
    response = MockAIClient().parse_recruitment_message("今天天气不错")
    assert response.records[0].missing_fields

def test_invalid_json_client_error_is_not_mock_success(factory):
    class Broken:
        def parse_recruitment_message(self, text): raise AIClientError("invalid JSON")
    engine = RecruitmentEngine(factory, Broken())
    with pytest.raises(AIClientError): engine.ingest_message("坏 JSON")
    with factory() as s:
        assert s.query(RawMessage).one().parse_status == "failed"
        assert s.query(BadCase).one().reason == "AI_PARSE_FAILED"

def test_deepseek_timeout_retries_and_raises():
    import requests
    class TimeoutSession:
        def __init__(self): self.calls = 0
        def post(self, *args, **kwargs): self.calls += 1; raise requests.Timeout("timeout")
    session = TimeoutSession()
    with pytest.raises(AIClientError): DeepSeekClient("key", "https://example.com", "model", retries=2, session=session).parse_recruitment_message("x")
    assert session.calls == 3

def test_confirm_creates_candidate_event_and_operation(factory):
    engine = RecruitmentEngine(factory, FixedClient([rec()]))
    _, review_id, _ = engine.ingest_message("确认消息")
    ids = engine.review(review_id, "confirmed")
    with factory() as s:
        assert len(ids) == 1
        assert s.query(Candidate).count() == 1
        assert s.query(RecruitmentEvent).count() == 1

def test_hr_modification_is_persisted(factory):
    engine = RecruitmentEngine(factory, FixedClient([rec()]))
    _, review_id, _ = engine.ingest_message("修改消息")
    engine.review(review_id, "modified", [{"name": "改名", "position": "产品经理", "status_key": "invited", "status_raw": "待邀约"}])
    with factory() as s: assert s.query(Candidate).one().name == "改名"

def test_hr_rejection_is_retained(factory):
    engine = RecruitmentEngine(factory, FixedClient([rec()]))
    _, review_id, _ = engine.ingest_message("驳回消息")
    engine.review(review_id, "rejected", reason="信息不完整")
    with factory() as s:
        assert s.query(AIReviewRecord).one().review_status == "rejected"
        assert s.query(BadCase).one().reason == "HR_REJECTED"

def test_phone_match_and_no_name_merge(factory):
    engine = RecruitmentEngine(factory, FixedClient([rec(name="张三", phone="13800138000")]))
    _, review_id, _ = engine.ingest_message("首次")
    engine.review(review_id, "confirmed")
    engine.ai_client = FixedClient([rec(name="不同姓名", phone="13800138000", status="screening_passed")])
    _, review_id, _ = engine.ingest_message("二次")
    engine.review(review_id, "confirmed")
    with factory() as s: assert s.query(Candidate).count() == 1

def test_duplicate_event_is_blocked(factory):
    engine = RecruitmentEngine(factory, FixedClient([rec()]))
    _, review_id, _ = engine.ingest_message("重复")
    engine.review(review_id, "confirmed")
    with pytest.raises(IntegrityError):
        with factory() as s:
            s.add(RecruitmentEvent(candidate_id=1, event_type="x", dedupe_key="same")); s.add(RecruitmentEvent(candidate_id=1, event_type="x", dedupe_key="same")); s.commit()

def test_illegal_transition_is_rejected(factory):
    engine = RecruitmentEngine(factory, FixedClient([rec(status="invited", phone="13800138000")]))
    _, review_id, _ = engine.ingest_message("初始")
    engine.review(review_id, "confirmed")
    engine.ai_client = FixedClient([rec(status="hired")])
    _, review_id, _ = engine.ingest_message("越级")
    with pytest.raises(ValueError): engine.review(review_id, "confirmed")
    with factory() as s: assert s.query(BadCase).filter_by(reason="ILLEGAL_STATUS_TRANSITION").count() == 1

def test_24_hour_reminder(factory):
    now = datetime(2026, 1, 2, tzinfo=timezone.utc)
    engine = RecruitmentEngine(factory, FixedClient([rec()]), Clock(lambda: now))
    _, review_id, _ = engine.ingest_message("提醒")
    with factory() as s: s.get(AIReviewRecord, review_id).created_at = now - timedelta(hours=24); s.commit()
    engine.process_timeouts()
    with factory() as s: assert s.query(Reminder).count() == 1

def test_48_hour_expiry(factory):
    now = datetime(2026, 1, 3, tzinfo=timezone.utc)
    engine = RecruitmentEngine(factory, FixedClient([rec()]), Clock(lambda: now))
    _, review_id, _ = engine.ingest_message("过期")
    with factory() as s: s.get(AIReviewRecord, review_id).created_at = now - timedelta(hours=48); s.commit()
    engine.process_timeouts()
    with factory() as s: assert s.query(AIReviewRecord).one().review_status == "expired"

def test_transaction_rolls_back_on_illegal_transition(factory):
    engine = RecruitmentEngine(factory, FixedClient([rec(status="invited", phone="13800138000")]))
    _, review_id, _ = engine.ingest_message("回滚")
    engine.ai_client = FixedClient([rec(status="hired", phone="13800138000")])
    with factory() as s: s.add(Candidate(name="已有", position="后端", phone="13800138000", status="new", status_key="invited")); s.commit()
    _, review_id, _ = engine.ingest_message("回滚事件")
    with pytest.raises(ValueError): engine.review(review_id, "confirmed")
    with factory() as s: assert s.query(RecruitmentEvent).count() == 0

def test_historical_events_query(factory):
    engine = RecruitmentEngine(factory, FixedClient([rec()]))
    _, review_id, _ = engine.ingest_message("历史")
    engine.review(review_id, "confirmed")
    with factory() as s: assert s.query(RecruitmentEvent).order_by(RecruitmentEvent.created_at).count() == 1
