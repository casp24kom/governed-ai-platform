import logging
import time
import uuid
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from app.agentcore_client import call_agentcore
from app.dq_gate import decide, parse_dbt, parse_ge
from app.snowflake_audit import audit_dq

from .schemas import DqRequest

router = APIRouter(tags=["dq"])
LOGGER = logging.getLogger(__name__)


@router.post("/dq/evaluate")
def dq_evaluate(req: DqRequest) -> Dict[str, Any]:
    run_id = str(uuid.uuid4())
    start = time.time()
    stage = "start"

    try:
        stage = "parse_dbt"
        dbt_signal = parse_dbt(req.dbt_run_results)

        stage = "parse_ge"
        ge_signal = parse_ge(req.ge_validation)

        stage = "decide"
        decision = decide([dbt_signal, ge_signal])

        stage = "call_agentcore"
        agent_out = call_agentcore(decision)

        latency_ms = int((time.time() - start) * 1000)

        stage = "audit_dq"
        audit_dq(
            run_id,
            req.user_id,
            decision["verdict"],
            decision["reasons"],
            decision["signals"],
            agent_out.get("ticket", {}),
            agent_out.get("runbook", {}),
            latency_ms,
        )

        return {
            "run_id": run_id,
            "verdict": decision["verdict"],
            "reasons": decision["reasons"],
            "signals": decision["signals"],
            "ticket_draft": agent_out.get("ticket", {}),
            "runbook_draft": agent_out.get("runbook", {}),
            "latency_ms": latency_ms,
        }
    except Exception as exc:
        LOGGER.info("DQ request: %s", req.model_dump())
        LOGGER.exception("DQ evaluate failed stage=%s run_id=%s", stage, run_id)
        raise HTTPException(status_code=500, detail=f"{stage}: {exc}") from exc
