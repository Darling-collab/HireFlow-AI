from dataclasses import dataclass
from typing import List
from .schemas import CandidateExtraction

class AIClientError(RuntimeError): pass

@dataclass
class AIResponse:
    records: List[CandidateExtraction]
    mode: str
    model: str
    prompt_version: str
    latency_ms: int

class BaseAIClient:
    def parse_recruitment_message(self, text: str) -> AIResponse:
        raise NotImplementedError
