import json, time
from typing import Optional
import requests
from .base_client import AIClientError, AIResponse, BaseAIClient
from .prompts import PROMPT_VERSION, SYSTEM_PROMPT
from .schemas import validate_payload

class DeepSeekClient(BaseAIClient):
    def __init__(self, api_key: str, base_url: str, model: str, timeout: int = 30, retries: int = 2, session: Optional[requests.Session] = None):
        self.api_key, self.base_url, self.model, self.timeout, self.retries = api_key, base_url.rstrip("/"), model, timeout, retries
        self.session = session or requests.Session()

    def parse_recruitment_message(self, text: str) -> AIResponse:
        started = time.perf_counter(); last_error = None
        for attempt in range(self.retries + 1):
            try:
                response = self.session.post(self.base_url + "/chat/completions", headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}, json={"model": self.model, "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": text}], "temperature": 0, "response_format": {"type": "json_object"}}, timeout=self.timeout)
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
                records = validate_payload(json.loads(content))
                return AIResponse(records, "deepseek", self.model, PROMPT_VERSION, int((time.perf_counter() - started) * 1000))
            except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
                last_error = exc
                if attempt < self.retries: time.sleep(0.2 * (attempt + 1))
        raise AIClientError(f"DeepSeek parse failed after {self.retries + 1} attempts: {last_error}")
