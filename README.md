# Teaching: Business Case Logic with AI Coding Agents

A living reference library for building business-grade logic and agent workflows
using Claude Code, Codex, and the Anthropic Agent SDK.

Maintained by Jude Ighomena / Janna AI Research Labs.

---

## Structure

Content is organised into sessions. Each session is a self-contained learning unit
with explanatory documents (MD files) and runnable code samples to customise.

```
session-one/      Frameworks — everything you build before writing a prompt
session-two/      Requirements — task design, prompt engineering, evaluation
session-three/    Business Logic — routing, approvals, pricing, validation
session-four/     Multi-Agent — orchestration, HITL, agent teams
session-five/     Production — deployment, monitoring, cost management
```

---

## Session One: Frameworks

Everything you need to understand and set up before writing a single prompt.

| File | Topic |
|---|---|
| [01-agent-mental-model.md](session-one/01-agent-mental-model.md) | The 5-layer model and why setup outranks the prompt |
| [02-internal-setup.md](session-one/02-internal-setup.md) | All 5 layers in annotated Python code |
| [03-project-structure.md](session-one/03-project-structure.md) | Folder layout, naming conventions, structural rules |
| [04-model-selection.md](session-one/04-model-selection.md) | Decision tree: Haiku vs Sonnet vs Opus vs Fable |
| [05-environment-config.md](session-one/05-environment-config.md) | Env vars, secrets, pre-run checklist |
| [06-context-window-budget.md](session-one/06-context-window-budget.md) | Token budgeting worksheet before writing the prompt |
| [07-tool-design.md](session-one/07-tool-design.md) | Tool schema design, enum, error returns, dispatcher |
| [08-system-prompt-skeleton.md](session-one/08-system-prompt-skeleton.md) | The 5-section anatomy and fill-in template |
| [09-memory-and-state.md](session-one/09-memory-and-state.md) | Three tiers of memory, promotion patterns |
| [10-observability.md](session-one/10-observability.md) | Structured logging, tracing, alert thresholds |
| [11-security-baseline.md](session-one/11-security-baseline.md) | Prompt injection, tool scoping, output sanitisation |

Runnable scaffold: [session-one/scaffold/](session-one/scaffold/)

---

## How to Use

Read session-one in order from document 01 to 11.
Each document ends with a customisation task or checklist before moving to the next.

---

## Principles

- Every concept is grounded in working code
- Every design decision is explained, not assumed
- Security and correctness are built in from the start, not added later
- Documents are updated as agent capabilities evolve

---

Copyright Janna AI Research Labs
