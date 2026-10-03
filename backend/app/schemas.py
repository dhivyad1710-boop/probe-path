from typing import List, Optional
from pydantic import BaseModel


class DiagnoseRequest(BaseModel):
    url: str = ""


class Evidence(BaseModel):
    step: str
    status: str  # success | warning | failed | info
    message: str


class TimelineEvent(BaseModel):
    timestamp: str
    step: str
    result: str


class DiagnoseResponse(BaseModel):
    target: str
    status: str  # healthy | warning | failed | unknown
    http_status: Optional[int] = None
    response_time_ms: Optional[int] = None
    dns_ok: Optional[bool] = None
    connectivity_ok: Optional[bool] = None
    diagnosis: str
    possible_causes: List[str] = []
    recommendation: str
    evidence: List[Evidence]
    timeline: List[TimelineEvent]
