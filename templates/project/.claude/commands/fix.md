---
description: Fix a bug with the bug-loop protocol (reproduce → failing test → root cause → one fix)
argument-hint: [what's broken]
---

Problem reported: $ARGUMENTS

Do NOT start editing code yet. Hand this to the **debugger** subagent and make it follow its protocol:
reproduce → capture the exact error → failing test → root cause (numbered hypotheses) → one focused fix →
full checks green.

Rules while fixing:
- Work on a branch `fix/<short-name>`. One bug per branch.
- Never delete, skip or weaken a test to make it pass.
- If 2 hypotheses fail, revert to the last green commit (`git stash` or `git switch main`) and explain the
  situation to the owner in plain words with 2 options. Going back to working code is progress.

End with a 3-sentence plain explanation for the owner: what broke, why, how it's prevented from coming back.
