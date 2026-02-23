#!/usr/bin/env python3
import os, json, uuid
import boto3
from botocore.exceptions import ClientError
from botocore.eventstream import EventStreamError

AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-2")
AGENT_ID = os.getenv("AGENT_ID")
AGENT_ALIAS_ID = os.getenv("AGENT_ALIAS_ID")
INPUT_TEXT = os.getenv("INPUT_TEXT", "Hello")
ENABLE_TRACE = os.getenv("ENABLE_TRACE", "true").lower() in ("1","true","yes","y")

if not AGENT_ID or not AGENT_ALIAS_ID:
    raise SystemExit("Set AGENT_ID and AGENT_ALIAS_ID env vars")

def dump_event(evt: dict):
    # Each event is a dict with a single key like: "chunk", "trace", "internalServerException", etc.
    print("\n=== EVENT ===")
    print(json.dumps(evt, indent=2, default=str)[:12000])

def main():
    session = boto3.Session(region_name=AWS_REGION)
    sts = session.client("sts")
    print("CallerIdentity:", json.dumps(sts.get_caller_identity(), indent=2))

    brt = session.client("bedrock-agent-runtime", region_name=AWS_REGION)
    print("Bedrock Agent Runtime endpoint:", brt.meta.endpoint_url)

    session_id = os.getenv("SESSION_ID", str(uuid.uuid4()))
    print("Using sessionId:", session_id)
    print("Invoking agent... enableTrace=", ENABLE_TRACE)

    try:
        resp = brt.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=AGENT_ALIAS_ID,
            sessionId=session_id,
            inputText=INPUT_TEXT,
            enableTrace=ENABLE_TRACE,
        )

        # Stream events
        for evt in resp["completion"]:
            dump_event(evt)

    except EventStreamError as e:
        # This is where you currently only see the generic AccessDeniedException
        print("\nEventStreamError:", str(e))
        if hasattr(e, "response"):
            print("EventStreamError.response:", json.dumps(e.response, indent=2, default=str))
        return 2

    except ClientError as e:
        print("\nClientError:", e)
        return 2

    return 0

if __name__ == "__main__":
    raise SystemExit(main())