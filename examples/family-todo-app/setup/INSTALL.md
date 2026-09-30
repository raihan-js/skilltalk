# Milestone 0 — Engineering foundation (the agent does this; don't ask the owner to)

Set up the safety net **before** writing any feature code. Only two things need the owner: logging in to
GitHub (and the host) in a browser, and pasting secrets into `.env`. Everything else you do yourself,
explaining each step in one plain sentence as you go.

`SKILL_DIR` = the folder containing this skill (`.claude/skills/family-todo-app` in the project, or
`~/.claude/skills/family-todo-app`). Find it with: `ls -d .claude/skills/family-todo-app ~/.claude/skills/family-todo-app 2>/dev/null`.

## 1. Check tools
Check `git --version`, `python3 --version` (the safety hooks are Python), `gh --version` (GitHub CLI), `node --version` (LTS) and `npm --version`.
If something is missing, tell the owner the ONE install command for their operating system and why it's needed.
(Windows: if `python3` isn't found but `python` is, replace `python3` with `python` in `.claude/settings.json` after step 3.)

## 2. Create the app skeleton
Use the official Next.js starter with TypeScript, ESLint, Tailwind and the App Router, npm as package manager (e.g. `npx create-next-app@latest <folder> --ts --eslint --tailwind --app --use-npm` — check `--help` for the current flags).
If the starter refuses to run in a non-empty folder, create it in a temporary folder and move the files in.
Then make sure these scripts exist and work (add the dev tools if needed — this is not optional):
`lint`, `typecheck` (`tsc --noEmit`), `test` (`vitest run` — must not start watch mode),
`build`, `format` (`prettier --write .`). Dev tools: `prettier`, `vitest`, `@testing-library/react`, and `@playwright/test` for one end-to-end test of the main journey.
Add one trivial passing test so the pipeline is proven end to end.

## 3. Install the foundation
```bash
python3 "$SKILL_DIR/setup/bootstrap.py" .
```
This copies (never overwriting your existing files — it merges `.gitignore`, `CLAUDE.md`, `AGENTS.md`
and `.claude/settings.json`): hooks, settings, helper agents and commands in `.claude/`, git hooks,
GitHub CI + Dependabot + PR/issue templates, `.editorconfig`, `.env.example`, `PROGRESS.md`, and the playbooks
into `docs/skilltalk/`. It also runs `git init -b main` if needed and `git config core.hooksPath .githooks`.

## 4. Prove the safety net works
```bash
echo '{"tool_input":{"command":"git push origin main"}}' | python3 .claude/hooks/guard_bash.py; echo "exit=$?"   # expect exit=2
npm run lint && npm run typecheck && npm test && npm run build                                                       # expect all green
```

## 5. GitHub
1. `gh auth status` — if not logged in, ask the owner to run `gh auth login` (browser login, 1 minute).
2. First commit on main: `git add -A && git commit -m "chore: project foundation"`.
3. `gh repo create family-todo-app --private --source . --push` (creating main with the first push is allowed).
4. Protect main (requires green CI before merging):
   ```bash
   gh api -X PUT "repos/{owner}/{repo}/branches/main/protection" --input - <<'EOF'
   {"required_status_checks":{"strict":true,"contexts":["checks"]},"enforce_admins":false,
    "required_pull_request_reviews":null,"restrictions":null}
   EOF
   ```
   If GitHub answers that this needs a paid plan (private repos on free accounts), tell the owner it's optional:
   the local pre-push hook and CI already protect main.
5. From now on: every change on a branch → PR → green CI → merge.

## 6. Hosting (continuous deployment)
Ask the owner to import the GitHub repo at vercel.com/new (free Hobby plan) — one click, their account.
Then: every PR gets a preview link, and merging into main deploys to production automatically.
Add production environment variables in Vercel → Project → Settings → Environment Variables.

## 7. Finish
Tick Milestone 0 in PROGRESS.md, commit on a branch, open the PR, and tell the owner in plain words:
"Your project now has a safety net: …" — list what's installed in 5 short bullets (see `references/ai-workflow.md`).
