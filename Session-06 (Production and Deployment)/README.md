# Session Six: Production and Deployment

> Getting an agent working locally is 20% of the work. Getting it running
> reliably in production, at scale, with real users, real costs, and real
> failures is the other 80%. Session Six covers that gap.

---

## Framework Mapping

Session 06 applies frameworks at the deployment and operations level. The
platform is fully built; this session makes it shippable.

| Session-06 Document | Applies These Frameworks |
|---|---|
| 00-session-overview.md | Read first. Build recap, what production means for an agent platform. |
| 01-prepare-for-deployment.md | Framework 05 (Environment Config) + Framework 02 (Project Structure) |
| 02-deploy-the-platform.md | Framework 02 (Project Structure) + Framework 08 (Internal Setup) |
| 03-add-production-monitoring.md | Framework 10 (Observability) + Framework 01 (Agent Mental Model) |
| 04-control-costs.md | Framework 04 (Context Window Budget) + Framework 10 (Observability) |
| 05-final-platform-review.md | All eleven frameworks reviewed in the context of the complete platform |

---

## Documents in This Session

```
Session-06 (Production and Deployment)/
|
|-- 00-session-overview.md
|       Read this first. What production means for an agent platform.
|       Token costs at scale. The final CLAUDE.md. The six-session arc.
|
|-- 01-prepare-for-deployment.md
|       Framework 05 + 02. Production environment variables, a GET /api/health
|       endpoint that checks the database, a pre-deploy checklist covering
|       npm audit, secret scan, test suite, and CORS configuration.
|
|-- 02-deploy-the-platform.md
|       Framework 02 + 08. Deploying to Railway with persistent SQLite storage
|       via a Railway Volume. Python agent setup on the production server.
|       HTTPS and custom domain. Database backup strategy.
|
|-- 03-add-production-monitoring.md
|       Framework 10 + 01. Extended TurnTrace with time-to-first-token and
|       token counts. Structured error logging. In-process error rate tracking.
|       Alert trigger when the 5-minute error rate exceeds 5 percent.
|
|-- 04-control-costs.md
|       Framework 04 + 10. Per-student token budget enforced at the
|       orchestrator. total_tokens column on the users table. Hard limit
|       returns a user-facing message. Anthropic prompt caching for system
|       prompts. Professor cost dashboard endpoint.
|
|-- 05-final-platform-review.md
|       All frameworks. A complete audit of the six-session platform: every
|       architectural decision, every rule in CLAUDE.md, every layer and why
|       it exists. The final CLAUDE.md and handoff documentation.
|
|-- assignments/
|   |-- 01-prepare-for-deployment.md
|   |-- 02-deploy-the-platform.md
|   |-- 03-add-production-monitoring.md
|   |-- 04-control-costs.md
|   |-- 05-final-platform-review.md
|   `-- README.md
|
`-- starter-code/
    |-- CLAUDE.md          Definitive operating brief for the complete platform
    |-- .env.example       Full production environment variable list
    |-- package.json       Version 0.6.0, no new runtime dependencies
    `-- requirements.txt   Python dependencies unchanged
```

---

## What You Will Have at the End

- A deployed SCQ Simulation Portal accessible at a public HTTPS URL
- A GET /api/health endpoint that verifies the database is reachable
- Structured production logs with time-to-first-token and token counts per turn
- Per-student token budgets enforced at the orchestrator level
- Anthropic prompt caching active on all three agent system prompts
- A professor-facing cost endpoint showing cohort token usage
- The definitive CLAUDE.md covering the complete six-session platform

---

## How This Session Relates to Others

| Session | What it added |
|---|---|
| Session 01 | Eleven frameworks. Five-layer agent. Tools, memory, observability, security baseline. |
| Session 02 | Web layer. Express, JWT, SQLite, Matteo prompt engineered. |
| Session 03 | Three agents. Matteo, Juli, Tedd with full coaching logic. |
| Session 04 | Security. Rate limiting, validation, IDOR prevention, security test suite. |
| Session 05 | Coordination. Orchestrator, stage progression, cross-agent context, HITL. |
| Session 06 | Production. Deployment, monitoring, cost controls, final documentation. |

---

Copyright Janna AI Research Labs
