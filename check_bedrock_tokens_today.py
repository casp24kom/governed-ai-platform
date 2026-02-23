#!/usr/bin/env python3
import argparse
import datetime as dt
from dataclasses import dataclass
from typing import List, Optional

import boto3


@dataclass
class MetricSpec:
    namespace: str
    metric_name: str
    dimensions: List[dict]


def utc_midnight_range():
    now = dt.datetime.now(dt.timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return start, now


def sum_metric(cw, spec: MetricSpec, start: dt.datetime, end: dt.datetime, period_s: int = 300) -> float:
    resp = cw.get_metric_statistics(
        Namespace=spec.namespace,
        MetricName=spec.metric_name,
        Dimensions=spec.dimensions,
        StartTime=start,
        EndTime=end,
        Period=period_s,
        Statistics=["Sum"],
    )
    return float(sum(p.get("Sum", 0.0) for p in resp.get("Datapoints", [])))


def main():
    ap = argparse.ArgumentParser(description="Summarize Amazon Bedrock token usage since midnight UTC via CloudWatch.")
    ap.add_argument("--region", default="ap-southeast-2", help="AWS region (default: ap-southeast-2)")
    ap.add_argument("--mode", choices=["runtime", "agent"], default="runtime",
                    help="runtime=AWS/Bedrock metrics; agent=AWS/Bedrock/Agents metrics")
    ap.add_argument("--model-id", required=True, help="Bedrock modelId (e.g., anthropic.claude-3-5-sonnet-20240620-v1:0)")
    ap.add_argument("--operation", default="InvokeAgent",
                    help="Agent operation dimension value (default: InvokeAgent). Only used in --mode agent.")
    args = ap.parse_args()

    cw = boto3.client("cloudwatch", region_name=args.region)

    start, end = utc_midnight_range()

    if args.mode == "runtime":
        # AWS/Bedrock runtime metrics use ModelId dimension.  [oai_citation:4‡AWS Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/monitoring.html?utm_source=chatgpt.com)
        dims = [{"Name": "ModelId", "Value": args.model_id}]
        ns = "AWS/Bedrock"
    else:
        # AWS/Bedrock/Agents supports dimensions like Operation + ModelId, etc.  [oai_citation:5‡AWS Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/monitoring-agents-cw-metrics.html?utm_source=chatgpt.com)
        dims = [{"Name": "Operation", "Value": args.operation}, {"Name": "ModelId", "Value": args.model_id}]
        ns = "AWS/Bedrock/Agents"

    in_spec = MetricSpec(namespace=ns, metric_name="InputTokenCount", dimensions=dims)
    out_spec = MetricSpec(namespace=ns, metric_name="OutputTokenCount", dimensions=dims)

    input_tokens = sum_metric(cw, in_spec, start, end)
    output_tokens = sum_metric(cw, out_spec, start, end)
    total = input_tokens + output_tokens

    print(f"Range (UTC): {start.isoformat()} -> {end.isoformat()}")
    print(f"Namespace: {ns}")
    print(f"Dimensions: {dims}")
    print(f"InputTokenCount (Sum):  {int(input_tokens)}")
    print(f"OutputTokenCount (Sum): {int(output_tokens)}")
    print(f"TOTAL tokens today:      {int(total)}")

    # Heuristic “renewed” indicator:
    # If you were throttled yesterday and TOTAL is near-zero after UTC midnight, you’re likely in the new window.
    if total < 100:
        print("\nHeuristic: token usage is very low today (UTC). If you were throttled yesterday, your window likely reset.")
    else:
        print("\nHeuristic: token usage today (UTC) is non-trivial; if you’re still throttled, you may be hitting a limit.")


if __name__ == "__main__":
    main()