---
description: Plan a feature properly before building it (small steps, tests first, plain-language summary)
argument-hint: [what you want to add]
---

The owner wants: $ARGUMENTS

1. Use the **architect** subagent to make a plan that fits the project skill and its scale tier.
2. Show the owner the plan in plain words: what they'll get, the steps, how they'll test each one,
   any cost or risk. Ask for a yes/no (or changes) before writing code.
3. After approval: create a branch `git switch -c feat/<short-name>`, use the **test-writer** subagent to
   write the tests that define "done", then build step by step. Commit after each green step.
4. Finish with the **code-reviewer** subagent, fix its "must fix" list, push the branch and open a PR with
   `gh pr create --fill`. Update PROGRESS.md.
