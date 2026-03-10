import os

from fastapi import APIRouter, Depends, HTTPException

from app.config import settings
from app.snowflake_conn import get_sf_connection
from app.snowflake_rag import generate_answer_in_snowflake

from .rag import _make_polite_preface
from .security import require_debug_access
from .helpers import mask_value

router = APIRouter(tags=["debug"], dependencies=[Depends(require_debug_access)])


@router.get("/debug/dq_audit_last")
def dq_audit_last():
    dq_audit_table = f"{settings.sf_database}.{settings.sf_audit_schema}.DQ_GATE_RUNS"
    sql = """
    SELECT RUN_ID, TS, USER_ID, VERDICT, LATENCY_MS
    FROM {table}
    ORDER BY TS DESC
    LIMIT 10
    """.format(table=dq_audit_table)
    with get_sf_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
    return {"rows": rows}


@router.get("/debug/sf")
def debug_sf():
    return {
        "SF_SECRET_ID": mask_value(os.getenv("SF_SECRET_ID")),
        "SF_PRIVATE_KEY_PEM_B64_len": len(os.getenv("SF_PRIVATE_KEY_PEM_B64", "")),
        "SF_PRIVATE_KEY_PEM_PATH": mask_value(os.getenv("SF_PRIVATE_KEY_PEM_PATH", ""), keep_prefix=8, keep_suffix=0),
    }


@router.post("/debug/ai")
def debug_ai():
    question = "What do I do before maintenance?"
    chunks = [
        {
            "DOC_ID": "SYN-ISO-001",
            "DOC_NAME": "Synthetic SOP: Isolation",
            "CHUNK_ID": 1,
            "CHUNK_TEXT": "Apply lockout/tagout before maintenance. Verify zero energy state.",
            "DOC_TOPIC": "isolation_loto",
            "DOC_RISK_TIER": "LOW",
        }
    ]
    answer = generate_answer_in_snowflake(question, chunks)
    preface = _make_polite_preface(question, topic="isolation_loto", risk_tier="LOW", had_chunks=True)
    return {"answer": f"{preface}\n\n{answer}"}


@router.get("/debug/env")
def debug_env():
    return {
        "SF_ACCOUNT_IDENTIFIER": mask_value(os.getenv("SF_ACCOUNT_IDENTIFIER")),
        "SF_ACCOUNT_URL": mask_value(os.getenv("SF_ACCOUNT_URL"), keep_prefix=10, keep_suffix=4),
        "SF_USER": mask_value(os.getenv("SF_USER")),
        "settings.sf_account_identifier": mask_value(settings.sf_account_identifier),
        "settings.sf_account_url": mask_value(settings.sf_account_url, keep_prefix=10, keep_suffix=4),
        "settings.sf_user": mask_value(settings.sf_user),
    }


@router.get("/debug/sql")
def debug_sql():
    with get_sf_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT CURRENT_ACCOUNT(), CURRENT_REGION(), CURRENT_VERSION()")
            row = cur.fetchone()

    if row is None:
        raise HTTPException(status_code=500, detail="Snowflake returned no rows for debug query")

    account, region, version = row
    return {"account": account, "region": region, "version": version}
