# Session 01: The Frameworks

> You cannot build a reliable AI agent without a mental model of what you are
> building. This session gives you eleven frameworks. Every technical decision
> you make in Sessions 02 through 06 connects back to one of them.

---

## The Platform You Are Building

Across all six sessions you are building the **SCQ Simulation Portal**, an
AI-powered coaching application for MBA students working on consulting capstone cases.

The platform has three AI coaching agents:

- **Matteo** guides students through the SCQ framework (Situation, Complication, Question)
  using Socratic questioning. He never gives answers. He asks the right question.
- **Juli** guides students through Monroe's Motivated Sequence to build a persuasive
  business recommendation across five structured stages.
- **Tedd** evaluates completed student deliverables against the 5 Cs rubric (Clear,
  Concise, Compelling, Credible, Consistent) and returns a scored rubric with feedback.

You will not build these agents yet. Session 01 gives you the foundation every
agent needs, regardless of what it does. Sessions 02 and 03 are where Matteo,
Juli, and Tedd come to life.

Read the full platform description before starting Session 02:
[Session-02: Platform Overview](../Session-02%20(Task%20Design%20and%20Web%20Layer)/00-platform-overview.md)

---

## What This Session Covers

Session 01 is about the eleven frameworks that underpin every AI agent you will
ever build. Not theory. Decisions and implementations. Each framework answers a
specific question you will face when building any agent.

| Framework | File | The question it answers |
|---|---|---|
| 01 | 01-agent-mental-model.md | What are the five layers every agent has? |
| 02 | 02-project-structure.md | How do you organise files so the agent stays maintainable? |
| 03 | 03-model-selection.md | Which Anthropic model do you choose and why? |
| 04 | 04-context-window-budget.md | How do you manage the context window without running out of space? |
| 05 | 05-environment-config.md | How do you handle secrets and configuration safely? |
| 06 | 06-tool-design.md | How do you give the model the ability to take actions in the world? |
| 07 | 07-system-prompt-skeleton.md | How do you write a system prompt that produces consistent behaviour? |
| 08 | 08-internal-setup.md | How do the five layers connect into a running agent? |
| 09 | 09-memory-and-state.md | How does the agent remember what happened before? |
| 10 | 10-observability.md | How do you know what the agent is doing and whether it is working? |
| 11 | 11-security-baseline.md | How do you prevent the most common security failures in agent code? |

---

## What You Will Have at the End of Session 01

A working standalone AI agent with:
- Five-layer project structure (Infrastructure, Model Config, Tool Registry, Context, Prompt)
- A real system prompt in five sections (ROLE, SCOPE, RULES, FORMAT, ESCALATION)
- At least one registered tool with a complete JSON schema and dispatcher entry
- Three-tier memory (in-context history, session store, persistent JSON store)
- Structured turn logging with token counts and tool call traces
- A CLAUDE.md that any coding agent can read to understand the project
- A passing security audit on all five baseline checks

This agent is not yet Matteo, Juli, or Tedd. It is the pattern that all three
will follow. When you build the SCQ platform in Session 02, you are replacing
the placeholder content in this agent with the real coaching logic.

---

## How to Use This Session

Each framework document covers one decision. Read it, then complete the
matching assignment in the `assignments/` folder. The assignment produces
working code that you keep. Do not skip assignments. Each one builds directly
on the previous one.

The `starter-code/` folder contains the base project you will extend throughout
this session. Copy it to your working directory before starting Framework 01.

Every framework document ends with a **Using Claude Code Desktop App** section
that gives you the exact prompt to use when implementing that framework. If you
are using Cursor or Codex instead, refer to the **Apply to Your Coding Agent**
section in each document.

---

## Prerequisites

- Python 3.11 or later installed
- An Anthropic API key (get one at console.anthropic.com)
- A code editor (Claude Code desktop app, Cursor, or VS Code with Codex)
- Completed the Installation Guide in `Installation Guide/`

If you have not set up your coding agent yet, start there:
- [Getting started with Claude Code CLI](Installation%20Guide/00a-getting-started-cli.md)
- [Getting started with Claude Code Desktop App](Installation%20Guide/00b-getting-started-desktop-app.md)

---

## How Session 01 Connects to the Rest of the Course

```
Session 01 (this session)
  You build: the eleven frameworks as a working standalone agent
  You learn: mental models, project structure, security baseline
       |
       v
Session 02
  You apply: the frameworks to a real web application
  You build: Express web layer, JWT auth, database, Matteo's prompt
       |
       v
Session 03
  You implement: full logic for Matteo, Juli, and Tedd
  You build: all three agents running on the platform
       |
       v
Session 04
  You harden: security across the full platform
  You build: rate limiting, input validation, IDOR prevention, test suite
       |
       v
Session 05
  You coordinate: the three agents working together
  You build: the orchestration layer and handoff logic
       |
       v
Session 06
  You ship: the platform to production
  You build: deployment config, monitoring, cost controls
```

Every session adds a layer to the same platform. Nothing is thrown away.
The agent you build in Session 01 is still running inside the platform in Session 06.

---

## Start Here

[Framework 01: The Agent Mental Model](01-agent-mental-model.md)

---

Copyright Janna AI Research Labs
