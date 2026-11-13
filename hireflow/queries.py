from datetime import date, datetime, timedelta, timezone
from sqlalchemy import func
from .db import SessionLocal
from .models import AIReviewRecord, BadCase, Candidate, RecruitmentEvent, Reminder, Position, StatusDictionary

class QueryService:
    def __init__(self, session_factory=SessionLocal): self.session_factory = session_factory
    def candidates(self, query="", status=None):
        with self.session_factory() as s:
            q=s.query(Candidate).order_by(Candidate.updated_at.desc())
            if query: q=q.filter((Candidate.name.ilike(f"%{query}%")) | (Candidate.position.ilike(f"%{query}%")) | (Candidate.email.ilike(f"%{query}%")))
            if status: q=q.filter(Candidate.status_key == status)
            return q.all()
    def reviews(self, status="pending"):
        with self.session_factory() as s: return s.query(AIReviewRecord).filter(AIReviewRecord.review_status == status).order_by(AIReviewRecord.created_at.desc()).all()
    def review(self, review_id):
        with self.session_factory() as s: return s.get(AIReviewRecord, review_id)
    def events(self, candidate_id=None, limit=50):
        with self.session_factory() as s:
            q=s.query(RecruitmentEvent).order_by(RecruitmentEvent.created_at.desc())
            if candidate_id: q=q.filter(RecruitmentEvent.candidate_id == candidate_id)
            return q.limit(limit).all()
    def reminders(self, status=None):
        with self.session_factory() as s:
            q=s.query(Reminder).order_by(Reminder.due_at.asc())
            return q.filter(Reminder.status == status).all() if status else q.all()
    def bad_cases(self):
        with self.session_factory() as s: return s.query(BadCase).order_by(BadCase.created_at.desc()).all()
    def statuses(self):
        with self.session_factory() as s: return s.query(StatusDictionary).filter(StatusDictionary.is_active.is_(True)).order_by(StatusDictionary.id).all()
    def metrics(self):
        with self.session_factory() as s:
            now=datetime.now(timezone.utc); month_start=now.replace(day=1,hour=0,minute=0,second=0,microsecond=0).replace(tzinfo=None)
            return {"candidates": s.query(func.count(Candidate.id)).scalar() or 0, "new_this_month": s.query(func.count(Candidate.id)).filter(Candidate.created_at >= month_start).scalar() or 0, "pending_reviews": s.query(func.count(AIReviewRecord.id)).filter(AIReviewRecord.review_status == "pending").scalar() or 0, "interviews": s.query(func.count(Candidate.id)).filter(Candidate.status_key.in_(["first_round_passed","second_round_passed","final_round_passed"])).scalar() or 0, "offers": s.query(func.count(Candidate.id)).filter(Candidate.status_key.in_(["offer_sent","offer_accepted"])).scalar() or 0, "hired": s.query(func.count(Candidate.id)).filter(Candidate.status_key == "hired").scalar() or 0, "positions": s.query(func.count(Position.id)).filter(Position.status == "open").scalar() or 0}
    def status_counts(self):
        with self.session_factory() as s: return dict(s.query(Candidate.status_key, func.count(Candidate.id)).group_by(Candidate.status_key).all())
    def source_counts(self):
        with self.session_factory() as s: return dict(s.query(Candidate.source, func.count(Candidate.id)).group_by(Candidate.source).all())
