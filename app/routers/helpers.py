import ast
import json
import re
from typing import Any, Dict, List, Optional

CITATION_TAG_RE = re.compile(r"\[[A-Z0-9\-]+?\|.+?#chunk\d+\]")


def normalize_variant(value: Any) -> Any:
    """
    Normalize Snowflake VARIANT values to JSON-serializable Python objects.
    """
    if value is None:
        return None

    if isinstance(value, (dict, list, int, float, bool)):
        return value

    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            return json.loads(stripped)
        except Exception:
            pass
        try:
            return ast.literal_eval(stripped)
        except Exception:
            return {"_raw": value}

    try:
        return json.loads(str(value))
    except Exception:
        return {"_raw": str(value)}


def mask_value(value: Optional[str], *, keep_prefix: int = 3, keep_suffix: int = 2) -> Optional[str]:
    """
    Mask sensitive values while leaving minimal context for debugging.
    """
    if value is None:
        return None
    if len(value) <= (keep_prefix + keep_suffix):
        return "*" * len(value)
    suffix = value[-keep_suffix:] if keep_suffix > 0 else ""
    return f"{value[:keep_prefix]}{'*' * (len(value) - keep_prefix - keep_suffix)}{suffix}"


def extract_doc_ids(citations: Optional[List[Dict[str, Any]]]) -> List[str]:
    out: List[str] = []
    for citation in citations or []:
        doc_id = citation.get("DOC_ID")
        if doc_id:
            out.append(str(doc_id))
    return out


def recall_at_k(expected_any: List[str], retrieved_doc_ids: List[str], k: int) -> int:
    if not expected_any:
        return 1
    topk = retrieved_doc_ids[:k]
    return 1 if any(doc_id in topk for doc_id in expected_any) else 0


def mrr_at_k(expected_any: List[str], retrieved_doc_ids: List[str], k: int) -> float:
    if not expected_any:
        return 1.0
    topk = retrieved_doc_ids[:k]
    for i, doc in enumerate(topk, start=1):
        if doc in expected_any:
            return 1.0 / i
    return 0.0


def topic_match(expected_topic: str, policy: Dict[str, Any]) -> bool:
    actual = (policy.get("topic") or "general").strip()
    suggested = (policy.get("suggested_topic") or "").strip()
    if actual == expected_topic:
        return True
    return actual == "general" and bool(suggested) and suggested == expected_topic


def is_grounded_response(resp: Dict[str, Any]) -> bool:
    policy = resp.get("policy") or {}
    allow = bool(policy.get("allow_generation", False))
    mode = (policy.get("mode") or "").strip().lower()
    citations = resp.get("citations") or []
    answer = (resp.get("answer") or "").strip()

    return allow and mode == "grounded" and bool(citations) and bool(CITATION_TAG_RE.search(answer))


def is_hallucination(resp: Dict[str, Any]) -> bool:
    policy = resp.get("policy") or {}
    allow = bool(policy.get("allow_generation", False))
    answer = (resp.get("answer") or "").strip().lower()
    citations = resp.get("citations") or []

    if not allow or not answer:
        return False
    if "cannot answer from approved sources" in answer:
        return False
    return (not citations) or (not CITATION_TAG_RE.search(resp.get("answer") or ""))


def p95(values: List[float]) -> float:
    if not values:
        return 0.0
    vals = sorted(values)
    idx = int(round(0.95 * (len(vals) - 1)))
    return float(vals[idx])
