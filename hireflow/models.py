from datetime import date, datetime, timezone
from typing import Optional
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

def utc_now(): return datetime.now(timezone.utc)
class Base(DeclarativeBase): pass

class Candidate(Base):
    __tablename__ = "candidates"
    __table_args__ = (Index("ix_candidates_status", "status"), Index("ix_candidates_follow_up_date", "follow_up_date"))
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(200))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    position: Mapped[Optional[str]] = mapped_column(String(200))
    source: Mapped[Optional[str]] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(40), default="new", nullable=False)
    status_key: Mapped[Optional[str]] = mapped_column(String(40))
    status_raw: Mapped[Optional[str]] = mapped_column(String(100))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    follow_up_date: Mapped[Optional[date]] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    last_activity_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    def to_dict(self): return {"id": self.id, "name": self.name, "email": self.email, "phone": self.phone, "position": self.position, "source": self.source, "status": self.status, "status_key": self.status_key, "status_raw": self.status_raw, "notes": self.notes, "follow_up_date": self.follow_up_date}

class RecruitmentEvent(Base):
    __tablename__ = "recruitment_events"
    __table_args__ = (Index("ix_recruitment_events_candidate_created", "candidate_id", "created_at"), UniqueConstraint("dedupe_key", name="uq_recruitment_events_dedupe_key"))
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(60), nullable=False)
    payload: Mapped[Optional[str]] = mapped_column(Text)
    dedupe_key: Mapped[Optional[str]] = mapped_column(String(200))
    status_key: Mapped[Optional[str]] = mapped_column(String(40))
    raw_expression: Mapped[Optional[str]] = mapped_column(Text)
    event_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

def _simple(name, cols):
    return type(name, (Base,), {"__tablename__": cols.pop("__tablename__", name.lower()), **cols})

class RawMessage(Base):
    __tablename__ = "raw_messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[Optional[int]] = mapped_column(ForeignKey("candidates.id"))
    source: Mapped[str] = mapped_column(String(100), default="unknown")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), unique=True)
    filename: Mapped[Optional[str]] = mapped_column(String(255))
    received_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    parse_status: Mapped[Optional[str]] = mapped_column(String(30), default="pending")
    parse_error: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

class AIReviewRecord(Base):
    __tablename__ = "ai_review_records"
    id: Mapped[int] = mapped_column(primary_key=True)
    raw_message_id: Mapped[Optional[int]] = mapped_column(ForeignKey("raw_messages.id"))
    candidate_id: Mapped[Optional[int]] = mapped_column(ForeignKey("candidates.id"))
    mode: Mapped[str] = mapped_column(String(30))
    input_json: Mapped[Optional[str]] = mapped_column(Text)
    output_json: Mapped[Optional[str]] = mapped_column(Text)
    review_status: Mapped[str] = mapped_column(String(30), default="pending")
    reviewer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    modified_json: Mapped[Optional[str]] = mapped_column(Text)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)
    model: Mapped[Optional[str]] = mapped_column(String(100))
    prompt_version: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

class Reminder(Base):
    __tablename__ = "reminders"
    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[Optional[int]] = mapped_column(ForeignKey("candidates.id"))
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30), default="pending")
    message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

class BadCase(Base):
    __tablename__ = "bad_cases"
    id: Mapped[int] = mapped_column(primary_key=True)
    raw_message_id: Mapped[Optional[int]] = mapped_column(ForeignKey("raw_messages.id"))
    candidate_id: Mapped[Optional[int]] = mapped_column(ForeignKey("candidates.id"))
    reason: Mapped[str] = mapped_column(Text)
    raw_status: Mapped[Optional[str]] = mapped_column(String(100))
    resolution: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

class StatusDictionary(Base):
    __tablename__ = "status_dictionary"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True)
    label: Mapped[str] = mapped_column(String(80))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class DictionaryChangeRequest(Base):
    __tablename__ = "dictionary_change_requests"
    id: Mapped[int] = mapped_column(primary_key=True)
    requested_value: Mapped[str] = mapped_column(String(80))
    reason: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

class SyncTask(Base):
    __tablename__ = "sync_tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(60))
    status: Mapped[str] = mapped_column(String(30), default="pending")
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[Optional[str]] = mapped_column(Text)

class OperationLog(Base):
    __tablename__ = "operation_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(80))
    entity_type: Mapped[Optional[str]] = mapped_column(String(80))
    entity_id: Mapped[Optional[int]] = mapped_column(Integer)
    details: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

class Position(Base):
    __tablename__ = "positions"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

class Role(Base):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(200), unique=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(120))
    role_id: Mapped[Optional[int]] = mapped_column(ForeignKey("roles.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
