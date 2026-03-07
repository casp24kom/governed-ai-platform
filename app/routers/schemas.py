from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class RagRequest(BaseModel):
    user_id: str = "demo"
    question: str
    topk: int = 5
    topic: Optional[str] = Field(default=None, max_length=64)


class DqRequest(BaseModel):
    user_id: str = "demo"
    dbt_run_results: dict
    ge_validation: dict


class EvalIngest(BaseModel):
    run_id: str
    base_url: str
    n_cases: int
    metrics: Dict[str, Any]
    extra: Dict[str, Any] = Field(default_factory=dict)
    failures: Any = Field(default_factory=list)
