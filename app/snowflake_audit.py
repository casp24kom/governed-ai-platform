import json
import logging
from typing import Any

from app.snowflake_conn import get_sf_connection

LOGGER = logging.getLogger(__name__)
DQ_AUDIT_INSERT_SQL = (
    "INSERT INTO GOV_AI_PLATFORM.AUDIT.DQ_GATE_RUNS "
    "(RUN_ID, TS, USER_ID, VERDICT, REASONS, TOOL_SIGNALS, TICKET_DRAFT, RUNBOOK_DRAFT, LATENCY_MS) "
    "SELECT ?, CURRENT_TIMESTAMP(), ?, ?, PARSE_JSON(?), PARSE_JSON(?), PARSE_JSON(?), PARSE_JSON(?), ?"
)


def audit_dq(
    run_id: str,
    user_id: str,
    verdict: str,
    reasons: Any,
    signals: Any,
    ticket: Any,
    runbook: Any,
    latency_ms: int,
) -> None:
    """
    Persist DQ gate outcomes for auditability and post-incident analysis.
    Critical: schema and payload shape must remain compatible with downstream reporting.
    """
    params = (
        run_id,
        user_id,
        verdict,
        json.dumps(reasons),
        json.dumps(signals),
        json.dumps(ticket),
        json.dumps(runbook),
        int(latency_ms),
    )

    with get_sf_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(DQ_AUDIT_INSERT_SQL, params)
            LOGGER.debug("Inserted DQ audit row for run_id=%s, rowcount=%s", run_id, cur.rowcount)
