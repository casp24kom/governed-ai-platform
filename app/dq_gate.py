from typing import Any, Dict, List

DBT_TOOL = "dbt"
GE_TOOL = "great_expectations"
DBT_FAIL_STATUSES = {"fail", "error"}


def parse_dbt(run_results: Dict[str, Any]) -> Dict[str, Any]:
    results = run_results.get("results") or []
    status_counts: Dict[str, int] = {}
    failed_tests = 0

    for result in results:
        status = result.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
        unique_id = result.get("unique_id", "")
        if unique_id.startswith("test.") and status in DBT_FAIL_STATUSES:
            failed_tests += 1

    overall = "success"
    if status_counts.get("error", 0) > 0:
        overall = "error"
    elif status_counts.get("fail", 0) > 0:
        overall = "fail"

    return {
        "tool": DBT_TOOL,
        "status": overall,
        "failed_tests": failed_tests,
        "status_counts": status_counts,
    }


def parse_ge(validation: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "tool": GE_TOOL,
        "success": bool(validation.get("success", False)),
        "statistics": validation.get("statistics", {}),
        "meta": validation.get("meta", {}),
    }


def decide(signals: List[Dict[str, Any]]) -> Dict[str, Any]:
    verdict = "PASS"
    reasons: List[str] = []

    for signal in signals:
        tool = signal.get("tool")
        if tool == DBT_TOOL:
            status = signal.get("status")
            if status in DBT_FAIL_STATUSES:
                verdict = "FAIL"
                reasons.append(f"dbt status: {status}")
            if signal.get("failed_tests", 0) > 0:
                verdict = "FAIL"
                reasons.append(f"dbt failed tests: {signal['failed_tests']}")
            continue

        if tool == GE_TOOL and signal.get("success") is False:
            verdict = "FAIL"
            reasons.append("GE validation failed")

    return {"verdict": verdict, "reasons": reasons, "signals": signals}
