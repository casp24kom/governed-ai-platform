#!/usr/bin/env bash
set -euo pipefail

# Protected branch helper:
# - creates/switches to a feature branch (if on main)
# - commits staged changes
# - pushes branch
# - creates PR to main
#
# Usage:
#   scripts/ops/protected_pr.sh "Commit message"
#   scripts/ops/protected_pr.sh "Commit message" "pr-title"
#   scripts/ops/protected_pr.sh "Commit message" "pr-title" "branch-name"

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI is required. Install and run: gh auth login"
  exit 1
fi

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 \"commit message\" [pr title] [branch name]"
  exit 1
fi

COMMIT_MSG="$1"
PR_TITLE="${2:-$COMMIT_MSG}"
EXPLICIT_BRANCH="${3:-}"

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
TARGET_BRANCH="$CURRENT_BRANCH"

slugify() {
  echo "$1" \
    | tr '[:upper:]' '[:lower:]' \
    | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g; s/-+/-/g' \
    | cut -c1-40
}

if [[ -n "$EXPLICIT_BRANCH" ]]; then
  TARGET_BRANCH="$EXPLICIT_BRANCH"
elif [[ "$CURRENT_BRANCH" == "main" ]]; then
  TARGET_BRANCH="chore/$(slugify "$COMMIT_MSG")-$(date +%m%d%H%M)"
fi

if [[ "$CURRENT_BRANCH" != "$TARGET_BRANCH" ]]; then
  git checkout -b "$TARGET_BRANCH"
fi

if ! git diff --cached --quiet; then
  git commit -m "$COMMIT_MSG"
else
  echo "No staged changes found. Stage files first with git add ..."
  exit 1
fi

git push -u origin "$TARGET_BRANCH"

if gh pr view "$TARGET_BRANCH" >/dev/null 2>&1; then
  echo "PR already exists for branch $TARGET_BRANCH"
else
  gh pr create \
    --base main \
    --head "$TARGET_BRANCH" \
    --title "$PR_TITLE" \
    --body "Automated PR via scripts/ops/protected_pr.sh"
fi

echo "Done. Monitor checks with: gh pr checks --watch"
