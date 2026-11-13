from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

ALLOWED_STATUS_KEYS = {"invited", "screening_passed", "first_round_passed", "second_round_passed", "final_round_passed", "offer_sent", "offer_accepted", "hired", "withdrawn", "rejected", "talent_pool"}

@dataclass
class CandidateExtraction:
    name: Optional[str] = None
    position: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status_key: Optional[str] = None
    status_raw: Optional[str] = None
    result: Optional[str] = None
    event_time: Optional[str] = None
    raw_expression: Optional[str] = None
    missing_fields: List[str] = field(default_factory=list)

    def validate(self):
        if self.status_key and self.status_key not in ALLOWED_STATUS_KEYS:
            raise ValueError(f"unknown status_key: {self.status_key}")
        self.missing_fields = [f for f in ("name", "position") if not getattr(self, f)]
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "position": self.position, "email": self.email, "phone": self.phone, "status_key": self.status_key, "status_raw": self.status_raw, "result": self.result, "event_time": self.event_time, "raw_expression": self.raw_expression, "missing_fields": self.missing_fields}

def validate_payload(payload: Any) -> List[CandidateExtraction]:
    if not isinstance(payload, dict): raise ValueError("AI response must be an object")
    records = payload.get("candidates", payload.get("records"))
    if records is None: records = [payload]
    if not isinstance(records, list): raise ValueError("candidates must be a list")
    return [CandidateExtraction(**{k: item.get(k) for k in CandidateExtraction.__dataclass_fields__ if k in item}).validate() for item in records if isinstance(item, dict)]
