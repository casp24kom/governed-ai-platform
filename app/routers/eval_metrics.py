import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.config import settings
from app.snowflake_conn import get_sf_connection
from app.snowflake_eval import insert_eval_run

from .helpers import (
    extract_doc_ids,
    is_grounded_response,
    is_hallucination,
    mrr_at_k,
    normalize_variant,
    p95,
    recall_at_k,
    topic_match,
)
from .rag import rag_injection_test, run_rag_pipeline
from .schemas import EvalIngest, RagRequest

router = APIRouter(tags=["evaluation"])
LOGGER = logging.getLogger(__name__)


@router.get("/metrics")
def metrics() -> Dict[str, Any]:
    try:
        with get_sf_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                      RUN_ID,
                      RUN_TS,
                      APP_ENV,
                      BASE_URL,
                      N_CASES,
                      METRICS,
                      EXTRA
                    FROM GOV_AI_PLATFORM.AUDIT.EVAL_RUNS
                    ORDER BY RUN_TS DESC
                    LIMIT 1
                    """
                )
                row = cur.fetchone()

        if row:
            run_id, run_ts, app_env, base_url, n_cases, metrics_variant, extra_variant = row
            run_ts_out = run_ts.isoformat() if isinstance(run_ts, datetime) else str(run_ts)
            return {
                "run_id": run_id,
                "run_ts": run_ts_out,
                "app_env": app_env,
                "base_url": base_url,
                "n_cases": int(n_cases) if n_cases is not None else 0,
                "metrics": normalize_variant(metrics_variant) or {},
                "extra": normalize_variant(extra_variant) or {},
                "failures": [],
            }
    except Exception as exc:
        LOGGER.warning("Failed to read latest metrics from Snowflake: %s", exc)

    metrics_path = Path(__file__).resolve().parent.parent / "static" / "metrics_latest.json"
    if not metrics_path.exists():
        return JSONResponse(
            status_code=404,
            content={"error": "No metrics available yet. Run scripts/eval/run_eval.py first."},
        )

    try:
        return json.loads(metrics_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return JSONResponse(status_code=500, content={"error": f"Failed to read metrics: {exc}"})


@router.post("/eval/ingest")
def eval_ingest(payload: EvalIngest) -> Dict[str, Any]:
    try:
        insert_eval_run(
            run_id=payload.run_id,
            app_env=settings.app_env,
            base_url=payload.base_url,
            n_cases=payload.n_cases,
            metrics=payload.metrics,
            extra=payload.extra,
            failures=payload.failures,
        )
        return {"status": "ok", "run_id": payload.run_id}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to insert eval run: {exc}") from exc


@router.post("/eval/run")
def eval_run() -> Dict[str, Any]:
    cases_path = Path(__file__).resolve().parent.parent / "static" / "eval_cases.json"
    if not cases_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"eval_cases.json not found at {cases_path}. Put it in app/static/eval_cases.json",
        )

    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    topk = 5

    results = []
    latencies = []
    run_ts = datetime.now(timezone.utc)
    run_id = f"eval-{int(run_ts.timestamp())}"

    for case in cases:
        case_id = case["id"]
        question = case["question"]
        expected_topic = (case.get("expected_topic") or "general").strip()
        expected_allow = bool(case.get("expected_allow", False))
        expected_doc_ids_any = case.get("expected_doc_ids_any") or []

        try:
            resp = run_rag_pipeline(
                RagRequest(user_id="eval", question=question, topk=topk, topic=None),
                bypass_hard_guards=False,
            )
        except Exception as exc:
            results.append(
                {
                    "id": case_id,
                    "expected": case,
                    "observed": {"error": str(exc)},
                    "flags": {
                        "pass_allow": False,
                        "pass_topic": False,
                        "recall5": 0,
                        "mrr5": 0.0,
                        "grounded": False,
                        "hallucination": False,
                    },
                }
            )
            continue

        policy = resp.get("policy") or {}
        allow = bool(policy.get("allow_generation", False))
        doc_ids = extract_doc_ids(resp.get("citations") or [])

        r5 = recall_at_k(expected_doc_ids_any, doc_ids, 5)
        mrr5_value = mrr_at_k(expected_doc_ids_any, doc_ids, 5)

        grounded = is_grounded_response(resp)
        hallucination = is_hallucination(resp)

        latency = resp.get("latency_ms")
        if isinstance(latency, (int, float)):
            latencies.append(float(latency))

        results.append(
            {
                "id": case_id,
                "expected": case,
                "observed": {"policy": policy, "doc_ids": doc_ids[:topk]},
                "flags": {
                    "pass_allow": allow == expected_allow,
                    "pass_topic": topic_match(expected_topic, policy),
                    "recall5": r5,
                    "mrr5": mrr5_value,
                    "grounded": grounded,
                    "hallucination": hallucination,
                },
            }
        )

    total = len(results)
    allow_acc = sum(1 for r in results if r["flags"]["pass_allow"]) / total if total else 0.0
    topic_acc = sum(1 for r in results if r["flags"]["pass_topic"]) / total if total else 0.0
    recall5_avg = sum(r["flags"]["recall5"] for r in results) / total if total else 0.0
    mrr5_avg = sum(r["flags"]["mrr5"] for r in results) / total if total else 0.0
    grounded_rate = sum(1 for r in results if r["flags"]["grounded"]) / total if total else 0.0
    hallucination_rate = sum(1 for r in results if r["flags"]["hallucination"]) / total if total else 0.0
    p95_latency = p95(latencies)

    injection_suite = rag_injection_test()

    out = {
        "run_id": run_id,
        "run_ts": run_ts.isoformat(),
        "app_env": settings.app_env,
        "base_url": "local",
        "n_cases": total,
        "metrics": {
            "recall_at_5": round(recall5_avg, 4),
            "mrr_at_5": round(mrr5_avg, 4),
            "grounded_answer_rate": round(grounded_rate, 4),
            "hallucination_rate": round(hallucination_rate, 4),
            "allow_deny_accuracy": round(allow_acc, 4),
            "prompt_injection_pass_rate": injection_suite.get("pass_rate"),
            "p95_latency_ms": int(p95_latency) if p95_latency else None,
            "tool_call_success_rate": None,
        },
        "extra": {
            "topic_accuracy": round(topic_acc, 4),
            "latency_ms_count": len(latencies),
            "injection_suite": injection_suite,
        },
        "failures": [
            r
            for r in results
            if (not r["flags"]["pass_allow"])
            or (not r["flags"]["pass_topic"])
            or (r["flags"]["recall5"] == 0)
            or r["flags"]["hallucination"]
        ],
    }

    try:
        with get_sf_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO GOV_AI_PLATFORM.AUDIT.EVAL_RUNS
                    (RUN_ID, RUN_TS, APP_ENV, BASE_URL, N_CASES, METRICS, EXTRA)
                    SELECT %s, %s, %s, %s, %s, PARSE_JSON(%s), PARSE_JSON(%s)
                    """,
                    (
                        out["run_id"],
                        out["run_ts"],
                        out["app_env"],
                        out["base_url"],
                        out["n_cases"],
                        json.dumps(out["metrics"]),
                        json.dumps(out["extra"]),
                    ),
                )
    except Exception as exc:
        out["extra"]["snowflake_insert_error"] = str(exc)

    try:
        metrics_path = Path(__file__).resolve().parent.parent / "static" / "metrics_latest.json"
        metrics_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    except Exception as exc:
        out["extra"]["file_write_error"] = str(exc)

    return out
