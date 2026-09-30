---
description: Plain-language status report — what's done, what's next, what's risky, what it costs
---

Give the owner a short status report (max ~15 lines, no jargon):

1. **Done** — milestones/features finished (from PROGRESS.md and `git log --oneline -15`).
2. **Now** — what's in progress and on which branch; any open PR and its CI status (`gh pr list`, `gh pr checks`).
3. **Next** — the next 1–2 steps from the build plan.
4. **Health** — are lint, typecheck, tests and build green right now? Any known bugs?
5. **Money** — services in use and expected monthly cost vs. the budget in the project skill.
6. **Needs you** — anything the owner must do (paste a key, approve a PR, make a decision).
Then update PROGRESS.md if it's out of date.
