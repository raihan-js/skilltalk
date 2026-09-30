# Launch checklist — Family Todo App

Go through this with the AI (`/ship` covers the per-change part). Tick everything before telling the world.

## Works
- [ ] Every must-have feature works on the live site, on phone and desktop
- [ ] The main user journey has an end-to-end test that runs in CI
- [ ] Error messages are friendly, in plain words; nothing shows a blank screen or raw error
- [ ] A fresh user can sign up / start without help (ask someone who's never seen it)

## Safe
- [ ] `security-auditor` agent run: no 🔴 or 🟠 left
- [ ] No secrets in the repo (CI secret scan green); production keys only in the host's settings
- [ ] Row Level Security ON for every Supabase table, with tests for "user A can't see user B's data"
- [ ] Login, logout and account recovery tested; sign-up/login rate-limited

## Recoverable
- [ ] Database backups ON and one test restore done
- [ ] You know how to roll back (host's "redeploy previous version" or revert the PR)
- [ ] Budget alerts set on every paid service ($0/month)

## Findable & fair
- [ ] Page titles and descriptions set; custom domain connected with HTTPS
- [ ] Basic accessibility: labels, contrast, keyboard navigation
- [ ] README explains in plain words how to run, deploy and where each secret goes
