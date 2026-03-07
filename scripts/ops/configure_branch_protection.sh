#!/usr/bin/env bash
set -euo pipefail

# Configures GitHub branch protection for main branch.
# Requires: gh auth login with admin/repo permissions.

REPO="${1:-}"
BRANCH="${2:-main}"

if [[ -z "$REPO" ]]; then
  REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner)"
fi

if [[ -z "$REPO" ]]; then
  echo "Unable to resolve repo. Pass explicitly: owner/repo"
  exit 1
fi

echo "Applying branch protection to ${REPO}:${BRANCH}"

payload_file="$(mktemp)"
cat > "$payload_file" <<'JSON'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["test", "audit"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "required_approving_review_count": 1
  },
  "restrictions": null,
  "required_conversation_resolution": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_linear_history": false,
  "lock_branch": false,
  "allow_fork_syncing": true
}
JSON

gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  "/repos/${REPO}/branches/${BRANCH}/protection" \
  --input "$payload_file"

rm -f "$payload_file"

echo "Branch protection configured."
