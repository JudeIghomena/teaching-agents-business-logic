# Session Five — Production

> Getting an agent working locally is 20% of the work. Getting it running
> reliably in production — at scale, with real users, real costs, and real
> failures — is the other 80%. Session Five covers that gap.

**Status: Coming after Session Four**

---

## What This Session Covers

Session Five is the deployment and operations layer. Every document addresses
a problem that only appears once you leave the development environment.

---

## Planned Documents

```
session-five/
├── 01-deployment-patterns.md
│     How to host an agent backend: serverless functions, long-running
│     servers, containers, managed platforms (Railway, AWS, GCP).
│     Tradeoffs: cold start vs always-on, stateless vs stateful.
│
├── 02-cost-management.md
│     How to predict, monitor, and control API costs at scale.
│     Token budgeting in production. Cost per session calculation.
│     Caching strategies that reduce spend without hurting quality.
│
├── 03-rate-limiting-and-quotas.md
│     Per-user and per-endpoint rate limits for agent APIs.
│     Anthropic tier limits and how to work within them.
│     Queue-based architectures for burst workloads.
│
├── 04-error-handling-in-production.md
│     What happens when the model returns an unexpected stop reason.
│     How to handle 529 (overloaded), 400 (bad request), timeout.
│     Graceful degradation: what the user sees when the agent fails.
│
├── 05-prompt-versioning.md
│     Managing prompt changes in production without breaking live users.
│     Feature flags for prompts, canary deployments, rollback strategy.
│
├── 06-monitoring-and-alerting.md
│     What to monitor: error rate, p95 latency, token usage, tool
│     failure rate, cost per day. How to set up alerts that fire on
│     the right signals without alert fatigue.
│
└── starter-code/
      Docker deployment config, Railway config, cost tracking module,
      production-grade error handler.
```

---

## Prerequisites

Complete Sessions One through Four.
Production concerns are meaningless until you have a working, evaluated,
multi-capable agent to deploy. Do not skip ahead.

---

Copyright Janna AI Research Labs
