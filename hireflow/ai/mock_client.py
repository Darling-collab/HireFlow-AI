import re, time
from .base_client import AIResponse, BaseAIClient
from .prompts import PROMPT_VERSION
from .schemas import CandidateExtraction

class MockAIClient(BaseAIClient):
    model = "mock-recruitment-v2"
    def parse_recruitment_message(self, text: str) -> AIResponse:
        started = time.perf_counter(); blocks = re.split(r"\n\s*[-—]{2,}\s*\n|\n(?=候选人[：:])", text)
        records = []
        for block in blocks:
            if not block.strip(): continue
            def find(pattern):
                m = re.search(pattern, block, re.I)
                return (m.group(1) if m and m.lastindex else m.group(0)).strip() if m else None
            raw_status = find(r"(?:状态|阶段|进展)[：:]?([^\n]+)")
            mapping = {"待邀约": "invited", "已邀约": "invited", "初筛通过": "screening_passed", "一面通过": "first_round_passed", "二面通过": "second_round_passed", "终面通过": "final_round_passed", "offer": "offer_sent", "已入职": "hired", "已淘汰": "rejected", "已放弃": "withdrawn", "人才池": "talent_pool"}
            status_key = next((v for k, v in mapping.items() if raw_status and k in raw_status), None)
            name = find(r"(?:姓名|候选人)[：:]?\s*([^\n，,]+)")
            if not name:
                first = next((x.strip() for x in block.splitlines() if x.strip()), "")
                name = None if ("招聘" in first or "岗位" in first) else first
            records.append(CandidateExtraction(name=name, position=find(r"(?:应聘职位|职位|岗位)[：:]?\s*([^\n]+)"), email=find(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}"), phone=find(r"1[3-9]\d{9}"), status_key=status_key, status_raw=raw_status, result=find(r"(?:结果|结论)[：:]?\s*([^\n]+)"), raw_expression=raw_status, event_time=find(r"(20\d{2}[-/]\d{1,2}[-/]\d{1,2})")).validate())
        return AIResponse(records, "mock", self.model, PROMPT_VERSION, int((time.perf_counter() - started) * 1000))
