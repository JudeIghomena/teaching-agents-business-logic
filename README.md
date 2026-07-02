# Teaching: Business Case Logic with AI Coding Agents

A living reference library for building business-grade logic and agent workflows
using Claude Code and the Anthropic Agent SDK.

Maintained by Jude Ighomena / Janna AI Research Labs.

---

## How This Repo Works

Content is organised into six sessions. Read them in order.
Each session has:
- **Documents (MD files)** — the explanation, the why, the concepts
- **Starter code** — a runnable Python project you copy and customise immediately

Security gets its own dedicated session (Session Two) because it applies to
everything that follows. It is not a checkbox — it is a discipline.

---

## Sessions

### Session One — Frameworks
Everything you build and understand before writing a single prompt.

| # | Document | What you learn |
|---|---|---|
| 01 | [agent-mental-model](session-one/01-agent-mental-model.md) | The 5-layer model and execution cycle |
| 02 | [internal-setup](session-one/02-internal-setup.md) | All 5 layers in annotated Python |
| 03 | [project-structure](session-one/03-project-structure.md) | Folder layout and structural rules |
| 04 | [model-selection](session-one/04-model-selection.md) | Decision tree: Haiku vs Sonnet vs Opus vs Fable |
| 05 | [environment-config](session-one/05-environment-config.md) | Env vars, secrets, pre-run checklist |
| 06 | [context-window-budget](session-one/06-context-window-budget.md) | Token budget worksheet |
| 07 | [tool-design](session-one/07-tool-design.md) | Schema design, enum, error returns, dispatcher |
| 08 | [system-prompt-skeleton](session-one/08-system-prompt-skeleton.md) | 5-section anatomy and fill-in template |
| 09 | [memory-and-state](session-one/09-memory-and-state.md) | 3-tier memory model with code |
| 10 | [observability](session-one/10-observability.md) | Structured logging and alert thresholds |
| 11 | [security-baseline](session-one/11-security-baseline.md) | Minimum security controls every agent needs |

Starter code: [session-one/starter-code/](session-one/starter-code/)

**Status: Complete**

---

### Session Two — Security
The dedicated security session. Covers every agent-specific attack surface,
defence pattern, testing method, and incident response playbook.
Baked into every session that follows — and studied on its own here first.

See [session-two/README.md](session-two/README.md) for the full plan.

Planned documents: threat model, prompt injection deep-dive, tool security,
auth and authorisation, data privacy, output security, secrets management,
rate limiting and abuse prevention, security testing, incident response.

Starter code: adversarial prompt suite, sanitiser, rate limiter, auth middleware.

**Status: Coming next**

---

### Session Three — Task Design, Prompt Engineering, and Evaluation
How to define what the agent should do, write prompts that do it reliably,
and measure whether it is working.

See [session-three/README.md](session-three/README.md) for the full plan.
**Status: Coming after Session Two**

---

### Session Four — Business Case Logic
Approval workflows, pricing engines, routing rules, data validation.
Real business logic patterns with complete worked examples and runnable code.

See [session-four/README.md](session-four/README.md) for the full plan.
**Status: Coming after Session Three**

---

### Session Five — Multi-Agent Systems
Orchestrators, specialist agents, human-in-the-loop, parallel execution.
How to coordinate a team of agents on workflows too complex for one agent.

See [session-five/README.md](session-five/README.md) for the full plan.
**Status: Coming after Session Four**

---

### Session Six — Production
Deployment, cost management, rate limiting, error handling, monitoring.
Everything that only matters once real users are involved.

See [session-six/README.md](session-six/README.md) for the full plan.
**Status: Coming after Session Five**

---

## Learning Path

```
Session One    Build the foundation correctly
      │
      ▼
Session Two    Understand and apply security before building anything real
      │
      ▼
Session Three  Write and evaluate prompts that work reliably
      │
      ▼
Session Four   Apply to real business cases with production-ready code
      │
      ▼
Session Five   Scale to multi-agent systems and complex workflows
      │
      ▼
Session Six    Ship to production with confidence
```

---

## Principles

- Every concept is grounded in working code
- Every design decision is explained, not assumed
- Security is a first-class session, not a footnote
- Each session builds on the previous — read in order

---

Copyright Janna AI Research Labs
