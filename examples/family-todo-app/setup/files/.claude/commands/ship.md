---
description: Ship safely — review, security check, PR, green CI, merge, verify production
---

Ship the current branch. Stop and report in plain words at the first failing step.

1. Run all local checks (lint, typecheck, tests, build — see Commands in CLAUDE.md). All green.
2. **code-reviewer** subagent: fix every "must fix".
3. If this touches logins, user data, payments, uploads or AI: **security-auditor** subagent; fix 🔴 and 🟠.
4. Update PROGRESS.md and, if behaviour changed, README.md.
5. Push the branch and open/update the PR: `gh pr create --fill` (or `gh pr view --web` if it exists).
   Write the PR description for a non-technical reader: what changed, how to test, any risk.
6. Wait for CI: `gh pr checks --watch`. If it fails, fix the cause (never disable the check).
7. Tell the owner: "Ready to merge — here's the preview link (if the host makes one) and what to check."
   Merge only when the owner says yes: `gh pr merge --squash --delete-branch`.
8. After merge, confirm the production deploy finished and do a 1-minute smoke test of the main flow.
   If production is broken: roll back first (host's "redeploy previous" or `git revert`), investigate second.
