# Engineering playbook — Family Todo App

How real software gets built, shipped and grown — in plain words, **tailored to this project**.

**Your scale tier: Starter.** small user base — managed hosting and free tiers cover everything; keep it simple.

Legend: 🟢 **NOW** = do it from the start · 🟡 **LATER** = when the trigger in the note happens ·
⚪ **NOT NEEDED** = don't build it for this project (adding it would be over-engineering)

## At a glance

| Topic | For this project | Note |
|---|---|---|
| Git & version control | 🟢 NOW | Commit after every small working step. Never leave work uncommitted overnight. |
| GitHub, branches & pull requests | 🟢 NOW | One branch per feature or bug. The AI opens a PR; you (or the reviewer agent) approve it. |
| CI — continuous integration | 🟢 NOW | Keep CI green. Never disable a check to make it pass. |
| CD — continuous deployment & previews | 🟢 NOW | Connect the repo to the host once; test every PR on its preview link. |
| Environments — local, preview, production | 🟢 NOW | Local + PR previews + production. Use a separate dev database if the host allows it for free. |
| Secrets & API keys | 🟢 NOW | Rule is absolute from day one. If a key ever leaks: revoke it immediately, then create a new one. |
| Automated tests | 🟢 NOW | Unit tests for core logic + 1 end-to-end test of the main journey. |
| Database changes (migrations) | 🟢 NOW | All schema changes as migration files in git. |
| Backups & recovery | 🟢 NOW | Confirm the database host's automatic backups are ON; export data before risky changes. |
| Monitoring, error tracking & alerts | 🟡 LATER | Host logs are enough to start. Add free error tracking before sharing widely. |
| Security basics | 🟢 NOW | Auth checks on the server, RLS on, input validation, dependency updates. |
| Speed — caching & CDN | ⚪ NOT NEEDED | Your host already uses a CDN. Just keep images small and pages simple. |
| Vertical scaling (a bigger machine) | ⚪ NOT NEEDED | Free tiers are enough at this size. |
| Horizontal scaling (more machines) & load balancing | ⚪ NOT NEEDED | Not needed. But write stateless code from day one (no files saved on the server). |
| Background jobs & queues | ⚪ NOT NEEDED | Do things directly and keep them fast. For scheduled tasks (like reminder emails) use the host's built-in cron, not a queue system. |
| Containers (Docker) | ⚪ NOT NEEDED | Managed hosting runs your code without containers. |
| Kubernetes | ⚪ NOT NEEDED | Definitely not. Managed hosting does everything you need. |
| Cost control | 🟢 NOW | Budget alerts on every paid service; the AI asks before adding anything paid. |
| When production breaks (rollback) | 🟢 NOW | Know where the host's 'redeploy previous version' button is. |
| Accessibility & SEO | 🟢 NOW | Real labels on buttons/inputs, readable contrast, page titles. |

---

## Git & version control — 🟢 NOW

*Unlimited undo + a diary of every change, for the whole project.*

Git saves a snapshot ("commit") every time a piece of work is finished. If anything breaks, you can go back to the last snapshot that worked. Small, frequent commits with clear messages are the cheapest insurance there is.

**For Family Todo App:** Commit after every small working step. Never leave work uncommitted overnight.

## GitHub, branches & pull requests — 🟢 NOW

*Drafts on the side; the final copy only changes after a check.*

"main" is the version real users get. New work happens on a branch (a side copy). When it's ready, a pull request (PR) asks to merge it into main. The PR shows exactly what changed and runs the automatic checks first. This is what stops half-finished or broken code from reaching users.

**For Family Todo App:** One branch per feature or bug. The AI opens a PR; you (or the reviewer agent) approve it.

## CI — continuous integration — 🟢 NOW

*A robot inspector that checks every change before it's allowed in.*

Every pull request automatically runs lint (style & common mistakes), typecheck (wrong kinds of data), tests (does it still do what it should?) and a build (can it be deployed?), plus a scan for leaked passwords. A red ❌ means "don't merge yet". Already set up in .github/workflows/ci.yml.

**For Family Todo App:** Keep CI green. Never disable a check to make it pass.

## CD — continuous deployment & previews — 🟢 NOW

*Merging the PR is pressing 'publish'.*

Your host (e.g. Vercel, Railway, Render) watches GitHub. Each pull request gets its own preview link you can click and test. When a PR merges into main, the host deploys it to production automatically. No manual uploading, no "works on my machine".

**For Family Todo App:** Connect the repo to the host once; test every PR on its preview link.

## Environments — local, preview, production — 🟢 NOW

*Rehearsal room, dress rehearsal, live show.*

Local = your computer. Preview/staging = a private copy online for testing. Production = what real users see. Each has its own settings and ideally its own database, so testing never damages real data.

**For Family Todo App:** Local + PR previews + production. Use a separate dev database if the host allows it for free.

## Secrets & API keys — 🟢 NOW

*House keys: never taped to the front door.*

Passwords and API keys live in a .env file on your computer and in the host's "environment variables" settings — never in code or GitHub. Anything with a "public" prefix (like NEXT_PUBLIC_) ends up in the browser, so it must never be secret. Hooks, git hooks and CI all check for leaks.

**For Family Todo App:** Rule is absolute from day one. If a key ever leaks: revoke it immediately, then create a new one.

## Automated tests — 🟢 NOW

*A checklist a robot runs in seconds, every single time.*

Unit tests check small pieces; end-to-end tests click through the app like a user. Tests are what stop the "fix one thing, break another" loop. Rule: every bug fix comes with a test that would have caught it.

**For Family Todo App:** Unit tests for core logic + 1 end-to-end test of the main journey.

## Database changes (migrations) — 🟢 NOW

*Renovation plans, not knocking walls down at random.*

When the shape of your data changes (a new column, a new table), it's done with a migration: a small script saved in git that changes the database step by step, the same way on every environment. Never edit the production database by hand.

**For Family Todo App:** All schema changes as migration files in git.

## Backups & recovery — 🟢 NOW

*A spare key kept at a friend's house — and checking it actually opens the door.*

A backup is a copy of your data from which you can restore after a mistake or outage. A backup you've never restored is only a hope: test restoring once.

**For Family Todo App:** Confirm the database host's automatic backups are ON; export data before risky changes.

## Monitoring, error tracking & alerts — 🟡 LATER

*Smoke detectors: you find out before your users tell you.*

Error tracking (e.g. Sentry, free tier) records every crash with details. Uptime checks ping your site every minute and message you if it's down. Logs are the app's diary for investigating problems.

**For Family Todo App:** Host logs are enough to start. Add free error tracking before sharing widely.

## Security basics — 🟢 NOW

*Locks on every door, not just the front one.*

The server must check who is asking on every request (the browser can be faked). Validate all input on the server. With Supabase, Row Level Security must be ON for every table. Keep dependencies updated (Dependabot opens PRs for you).

**For Family Todo App:** Auth checks on the server, RLS on, input validation, dependency updates.

## Speed — caching & CDN — ⚪ NOT NEEDED

*Keeping popular items on the shelf by the door instead of in the basement.*

A CDN stores copies of your site on servers around the world so pages load fast everywhere. Caching remembers answers so the database isn't asked the same question 1,000 times.

**For Family Todo App:** Your host already uses a CDN. Just keep images small and pages simple.

## Vertical scaling (a bigger machine) — ⚪ NOT NEEDED

*Swapping your car for a bigger truck.*

Giving a server or database more CPU and memory. Simple — usually a slider in the host's dashboard — but it has a ceiling and costs more. Almost always the right FIRST move when things get slow.

**For Family Todo App:** Free tiers are enough at this size.

## Horizontal scaling (more machines) & load balancing — ⚪ NOT NEEDED

*Opening more checkout lanes instead of making one cashier faster.*

Running several copies of your server with a load balancer spreading visitors between them. It only works if the server is "stateless": nothing important stored in its memory or local disk — sessions, files and data live in the database or file storage. Serverless hosts (like Vercel) do this for you automatically.

**For Family Todo App:** Not needed. But write stateless code from day one (no files saved on the server).

## Background jobs & queues — ⚪ NOT NEEDED

*Taking a ticket at the deli instead of blocking the counter.*

Slow work (sending emails, long AI calls, generating reports) is put in a queue and done in the background, so the user isn't stuck waiting and failures can be retried.

**For Family Todo App:** Do things directly and keep them fast. For scheduled tasks (like reminder emails) use the host's built-in cron, not a queue system.

## Containers (Docker) — ⚪ NOT NEEDED

*A shipping container: the app plus everything it needs, packed identically everywhere.*

Docker packs your app with its exact environment so it runs the same on any computer or cloud. Useful for custom servers; unnecessary on platforms like Vercel.

**For Family Todo App:** Managed hosting runs your code without containers.

## Kubernetes — ⚪ NOT NEEDED

*An automated port that manages thousands of shipping containers — powerful, and a full-time job.*

Kubernetes runs many containers across many machines, restarts crashed ones and scales them. It's the right tool for big systems with many services and a dedicated operations team. For almost every new product it's expensive over-engineering — the AI should NOT add it unless this playbook says NOW.

**For Family Todo App:** Definitely not. Managed hosting does everything you need.

## Cost control — 🟢 NOW

*A spending limit on the credit card.*

Cloud and AI services bill by usage, and bugs (like an infinite loop calling an AI API) can create surprise bills. Set budget alerts and hard limits wherever the provider allows it.

**For Family Todo App:** Budget alerts on every paid service; the AI asks before adding anything paid.

## When production breaks (rollback) — 🟢 NOW

*Fire drill: everyone knows the exits before there's smoke.*

First restore service, then investigate. Most hosts can redeploy the previous version in one click; otherwise revert the pull request. Then find the root cause and add a test so it can't happen again.

**For Family Todo App:** Know where the host's 'redeploy previous version' button is.

## Accessibility & SEO — 🟢 NOW

*Ramps and signposts: everyone can get in, and people can find the building.*

Accessibility means the site works with keyboards, screen readers and for people with low vision (labels, contrast, alt text). SEO means search engines understand your pages (titles, descriptions, fast load).

**For Family Todo App:** Real labels on buttons/inputs, readable contrast, page titles.

---

## The golden rule of scaling

Scale in this order, and only when you *measure* a problem (slow pages, errors, costs):
1. Fix the code (a missing database index fixes most "slowness").
2. Vertical: upgrade the plan (bigger database / server).
3. Cache what's read often.
4. Horizontal: more server copies (automatic on serverless hosts — keep code stateless).
5. Split out background jobs.
6. Only then: containers → orchestration (Kubernetes) → multiple services.

Every step up adds cost and complexity. Most successful products stay at steps 1–4 for years.
