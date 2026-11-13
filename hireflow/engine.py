import hashlib, json
from datetime import datetime, timedelta, timezone
from typing import Callable, Iterable, Optional
from .ai import AIClientError, DeepSeekClient, MockAIClient
from .ai.schemas import CandidateExtraction
from .config import get_settings
from .db import SessionLocal
from .models import AIReviewRecord, BadCase, Candidate, RawMessage, Reminder, RecruitmentEvent, OperationLog, utc_now

STATUS_TRANSITIONS = {
    None: {"invited", "talent_pool"},
    "invited": {"screening_passed", "withdrawn", "rejected", "talent_pool"},
    "screening_passed": {"first_round_passed", "withdrawn", "rejected", "talent_pool"},
    "first_round_passed": {"second_round_passed", "withdrawn", "rejected", "talent_pool"},
    "second_round_passed": {"final_round_passed", "withdrawn", "rejected", "talent_pool"},
    "final_round_passed": {"offer_sent", "withdrawn", "rejected", "talent_pool"},
    "offer_sent": {"offer_accepted", "withdrawn", "rejected"},
    "offer_accepted": {"hired", "withdrawn"},
    "talent_pool": {"invited", "rejected", "withdrawn"},
    "hired": set(), "withdrawn": set(), "rejected": set(),
    "pending_confirmation": set(),
}

class Clock:
    def __init__(self, now: Optional[Callable[[], datetime]] = None): self._now = now or (lambda: datetime.now(timezone.utc))
    def now(self):
        value = self._now(); return value if value.tzinfo else value.replace(tzinfo=timezone.utc)

def build_ai_client():
    settings = get_settings()
    if settings.ai_mode == "deepseek":
        if not settings.deepseek_api_key: raise AIClientError("AI_MODE=deepseek requires DEEPSEEK_API_KEY")
        return DeepSeekClient(settings.deepseek_api_key, settings.deepseek_base_url, settings.deepseek_model)
    return MockAIClient()

class RecruitmentEngine:
    def __init__(self, session_factory=SessionLocal, ai_client=None, clock=None):
        self.session_factory, self.ai_client, self.clock = session_factory, ai_client or build_ai_client(), clock or Clock()

    def ingest_message(self, content: str, source: str = "unknown", filename: Optional[str] = None):
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        with self.session_factory() as session:
            raw = RawMessage(content=content, source=source, filename=filename, content_hash=digest, received_at=self.clock.now(), parse_status="pending")
            session.add(raw); session.flush()
            try:
                response = self.ai_client.parse_recruitment_message(content)
                raw.parse_status = "parsed"
                review = AIReviewRecord(raw_message_id=raw.id, mode=response.mode, model=response.model, prompt_version=response.prompt_version, input_json=json.dumps({"content": content}, ensure_ascii=False), output_json=json.dumps([r.to_dict() for r in response.records], ensure_ascii=False), review_status="pending")
                session.add(review); session.commit(); return raw.id, review.id, response
            except Exception as exc:
                raw.parse_status, raw.parse_error = "failed", str(exc)
                session.add(BadCase(raw_message_id=raw.id, reason="AI_PARSE_FAILED", resolution=str(exc)))
                session.commit(); raise

    def review(self, review_id: int, decision: str, records: Optional[Iterable[dict]] = None, reviewer_id: Optional[int] = None, reason: Optional[str] = None):
        if decision not in {"confirmed", "modified", "rejected"}: raise ValueError("invalid review decision")
        with self.session_factory() as session:
            review = session.get(AIReviewRecord, review_id)
            if not review: raise ValueError("review not found")
            if review.review_status == "expired": raise ValueError("expired review cannot be confirmed")
            if decision == "rejected":
                review.review_status, review.rejection_reason, review.reviewer_id, review.reviewed_at = decision, reason, reviewer_id, self.clock.now()
                session.add(BadCase(raw_message_id=review.raw_message_id, reason="HR_REJECTED", resolution=reason))
                session.commit(); return []
            payload = list(records) if records is not None else json.loads(review.output_json or "[]")
            review.review_status, review.modified_json, review.reviewer_id, review.reviewed_at = decision, json.dumps(payload, ensure_ascii=False), reviewer_id, self.clock.now()
            created = []
            for item in payload:
                extraction = CandidateExtraction(**{k: item.get(k) for k in CandidateExtraction.__dataclass_fields__ if k in item}).validate()
                if extraction.missing_fields:
                    session.add(BadCase(raw_message_id=review.raw_message_id, reason="REQUIRED_FIELD_MISSING", raw_status=extraction.status_raw, resolution=",".join(extraction.missing_fields))); continue
                if not extraction.status_key:
                    session.add(BadCase(raw_message_id=review.raw_message_id, reason="UNKNOWN_STATUS", raw_status=extraction.status_raw)); continue
                created.append(self._apply_event(session, review, extraction))
            session.commit(); return created

    def _apply_event(self, session, review, extraction: CandidateExtraction):
        matches = []
        if extraction.phone: matches = session.query(Candidate).filter(Candidate.phone == extraction.phone).all()
        if not matches and extraction.email: matches = session.query(Candidate).filter(Candidate.email == extraction.email).all()
        if not matches and extraction.name and extraction.position: matches = session.query(Candidate).filter(Candidate.name == extraction.name, Candidate.position == extraction.position).all()
        if len(matches) > 1:
            session.add(BadCase(raw_message_id=review.raw_message_id, reason="CANDIDATE_MATCH_CONFLICT", resolution=extraction.name)); session.commit(); raise ValueError("candidate match conflict")
        candidate = matches[0] if matches else Candidate(name=extraction.name, email=extraction.email, phone=extraction.phone, position=extraction.position, status="new", status_key=extraction.status_key, status_raw=extraction.status_raw, created_at=self.clock.now(), updated_at=self.clock.now())
        if not matches: session.add(candidate); session.flush()
        current = candidate.status_key
        if matches and extraction.status_key not in STATUS_TRANSITIONS.get(current, set()):
            session.add(BadCase(raw_message_id=review.raw_message_id, candidate_id=candidate.id, reason="ILLEGAL_STATUS_TRANSITION", raw_status=extraction.status_raw, resolution=f"{current}->{extraction.status_key}")); session.commit(); raise ValueError("illegal status transition")
        candidate.status_key, candidate.status_raw, candidate.updated_at, candidate.last_activity_at = extraction.status_key, extraction.status_raw, self.clock.now(), self.clock.now()
        event_key = hashlib.sha256(f"{review.raw_message_id}:{extraction.name}:{extraction.status_key}".encode()).hexdigest()
        event = RecruitmentEvent(candidate_id=candidate.id, event_type="recruitment_update", status_key=extraction.status_key, raw_expression=extraction.raw_expression, payload=json.dumps(extraction.to_dict(), ensure_ascii=False), dedupe_key=event_key, event_time=self.clock.now(), created_at=self.clock.now())
        session.add(event); session.add(OperationLog(action="recruitment_event_confirmed", entity_type="candidate", entity_id=candidate.id, details=event_key, created_at=self.clock.now()))
        return candidate.id

    def process_timeouts(self):
        now = self.clock.now()
        with self.session_factory() as session:
            reviews = session.query(AIReviewRecord).filter(AIReviewRecord.review_status == "pending").all()
            for review in reviews:
                if not review.created_at: continue
                created = review.created_at if review.created_at.tzinfo else review.created_at.replace(tzinfo=timezone.utc)
                age = now - created
                if age >= timedelta(hours=48): review.review_status = "expired"
                elif age >= timedelta(hours=24): session.add(Reminder(candidate_id=review.candidate_id, due_at=now, status="pending", message="AI 审核已超过 24 小时", created_at=now))
            session.commit()
