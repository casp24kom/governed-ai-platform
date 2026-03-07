#!/usr/bin/env bash
set -euo pipefail

# Trigger and monitor the "Deploy App Runner" GitHub Actions workflow from CLI.
#
# Examples:
#   scripts/ops/deploy_via_gh.sh dev
#   scripts/ops/deploy_via_gh.sh dev --ref main
#   scripts/ops/deploy_via_gh.sh prod --image-tag rel-20260307-1200
#   scripts/ops/deploy_via_gh.sh dev --service-arn arn:aws:apprunner:... --ecr-repository myrepo

WORKFLOW_NAME="Deploy App Runner"
ENVIRONMENT="${1:-}"

if [[ -z "$ENVIRONMENT" ]]; then
  echo "Usage: $0 <dev|prod> [--ref <branch>] [--image-tag <tag>] [--service-arn <arn>] [--ecr-repository <name>]"
  exit 1
fi
shift

REF="main"
IMAGE_TAG=""
SERVICE_ARN=""
ECR_REPOSITORY=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --ref)
      REF="${2:-}"
      shift 2
      ;;
    --image-tag)
      IMAGE_TAG="${2:-}"
      shift 2
      ;;
    --service-arn)
      SERVICE_ARN="${2:-}"
      shift 2
      ;;
    --ecr-repository)
      ECR_REPOSITORY="${2:-}"
      shift 2
      ;;
    *)
      echo "Unknown arg: $1"
      exit 1
      ;;
  esac
done

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI not found. Install GitHub CLI first."
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "gh is not authenticated. Run: gh auth login"
  exit 1
fi

# Build workflow dispatch flags
ARGS=(
  workflow run "$WORKFLOW_NAME"
  --ref "$REF"
  -f "environment=$ENVIRONMENT"
)

if [[ -n "$IMAGE_TAG" ]]; then
  ARGS+=(-f "image_tag=$IMAGE_TAG")
fi
if [[ -n "$SERVICE_ARN" ]]; then
  ARGS+=(-f "service_arn=$SERVICE_ARN")
fi
if [[ -n "$ECR_REPOSITORY" ]]; then
  ARGS+=(-f "ecr_repository=$ECR_REPOSITORY")
fi

echo "Triggering workflow '$WORKFLOW_NAME' on ref '$REF' for environment '$ENVIRONMENT'..."
# shellcheck disable=SC2068
gh ${ARGS[@]}

# Give Actions API a moment to register the run
sleep 3

RUN_ID="$(gh run list --workflow "$WORKFLOW_NAME" --branch "$REF" --limit 1 --json databaseId -q '.[0].databaseId')"
if [[ -z "$RUN_ID" || "$RUN_ID" == "null" ]]; then
  echo "Could not resolve run id. Check manually: gh run list --workflow \"$WORKFLOW_NAME\""
  exit 1
fi

echo "Watching run id: $RUN_ID"
gh run watch "$RUN_ID" --exit-status

echo "Run completed. Showing summary:"
gh run view "$RUN_ID"
