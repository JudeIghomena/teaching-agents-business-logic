# Session 06: Production

> The platform is built, hardened, and coordinated. Session 06 is the last mile:
> preparing it for real students, real traffic, and real consequences when something
> goes wrong. By the end of this session, what you have built is shippable.

---

## Where You Are in the Build

By the end of Session 05 you have:
- A single `/api/chat` orchestrator endpoint routing students to the right agent
- Stage progression logic managed by the platform, not the student
- Cross-agent context handoffs: Matteo's SCQ feeds Juli, Juli's work feeds Tedd
- Failure handling with retry and fallback
- A passing end-to-end test covering the full student journey
- A hardened, tested, audited platform

Session 06 is about deploying that platform so real students can use it, monitoring
it so you know when something is wrong, and controlling costs so it does not
become expensive to run at scale.

---

## What This Session Covers

Session 06 applies Frameworks 04 (Context Window Budget) and 10 (Observability)
at the production level. In development, token costs and response times are
something you notice. In production, they determine whether the platform is
affordable and whether students have a good experience.

| Document | What it builds |
|---|---|
| 00-session-overview.md (this file) | Build recap, session scope, what you will have |
| 01-prepare-for-deployment.md | Environment variables, health check, build scripts |
| 02-deploy-the-platform.md | Deploy to Railway or Render with production config |
| 03-add-production-monitoring.md | Error alerting, token tracking, response time logging |
| 04-control-costs.md | Per-user token budget, hard limits, cost dashboard |
| 05-final-platform-review.md | Full review: what was built across all six sessions and why |

**What you will have at the end of Session 06:**
A deployed SCQ Simulation Portal accessible via a public URL. Production monitoring
that alerts you when an error rate spikes. Per-student token budgets that prevent
any one student from consuming a disproportionate share of API cost. A final
CLAUDE.md and HANDOFF.md that document the complete platform for any future
developer or coding agent session that picks it up.

**Previous session:** [Session 05 - Multi-Agent](../Session-05%20(Multi-Agent)/00-session-overview.md)
**This is the final session.**

---

## What Production Means for an Agent Platform

Deploying a web API is familiar. Deploying an AI agent platform has additional
considerations that do not apply to standard web applications.

**Token costs scale with usage.**
Every student message costs tokens. A class of 60 students each running a
20-turn session with Matteo costs roughly 60 x 20 x 1,500 tokens = 1.8 million
tokens per cohort. At claude-haiku-4-5 pricing, that is manageable. If the
prompt or history management is wrong and input tokens balloon, it becomes
expensive quickly. Monitoring token counts per session is not optional.

**Latency is visible.**
Students see the agent thinking. A response that takes 8 seconds to start
streaming feels broken even if it eventually arrives. Production monitoring
must track time-to-first-token, not just total response time.

**Failures are student-facing.**
When a database query fails or the Anthropic API times out, a student gets a
broken coaching session. Error handling must return a clear, actionable message
and the platform must record what happened so you can replay the failure.

**The model can change.**
Anthropic updates models. A model that was `claude-haiku-4-5-20251001` may be
deprecated. Your CLAUDE.md and deployment config must make the model configurable
via environment variable so a model change does not require a code deploy.

---

## The Final CLAUDE.md

Session 06 produces the definitive CLAUDE.md for the SCQ Simulation Portal.
It describes the complete platform: all three agents, the orchestrator, the database,
the security layer, the evaluation suite, and the deployment configuration.

Any developer or coding agent starting work on this platform after Session 06
reads that CLAUDE.md and has a complete picture of everything that was built,
every decision that was made, and every rule that must be followed.

The final CLAUDE.md lives in `starter-code/CLAUDE.md` of Session 06. It supersedes
the Session 02 version.

---

## The Six-Session Arc: What Was Built

Looking back across all six sessions:

| Session | What was added |
|---|---|
| 01 | Eleven frameworks. A standalone agent with five layers, tools, memory, logging, security baseline. |
| 02 | Web layer. Express server, JWT auth, database, Matteo's prompt engineered and iterated. |
| 03 | Three agents. Matteo, Juli, and Tedd running on the platform with full coaching logic. |
| 04 | Security. Rate limiting, input validation, IDOR prevention, security test suite. |
| 05 | Coordination. Orchestrator, stage progression, cross-agent context, failure handling. |
| 06 | Production. Deployment, monitoring, cost controls, final review and documentation. |

The agent you built in Framework 08 of Session 01 is still running at the core
of the platform. Every session added a layer. Nothing was thrown away. That is
the point: foundations matter, and a strong foundation makes everything else easier.

---

## Before You Start

Confirm these are all true before opening the first document:

- [ ] `POST /api/chat` routes correctly to Matteo, Juli, and Tedd based on student stage
- [ ] The full student journey (all three stages) completes without errors
- [ ] The security audit from Session 04 still passes
- [ ] All three agent evaluation suites pass at 90% or above
- [ ] Your CLAUDE.md reflects the full platform including the orchestrator

---

## Start Here

[Build 01: Prepare for Deployment](01-prepare-for-deployment.md)

---

Copyright Janna AI Research Labs
