# Session Two: Applying the Frameworks to a Real Web Application

> Session One gave you eleven frameworks. Session Two is where you apply them.
> The SCQ platform is the build thread. Matteo, Juli, and Tedd are the agents
> you are wiring in. Every document in this session takes a framework from
> Session One and shows you exactly what it looks like in production code.

---

## The Principle

In Session One you built a standalone agent running in a Python file.
That is a valid starting point but it is not how agents work in the real world.
In the real world:

- The agent lives inside a web application
- Every request must be authenticated before the agent sees it
- Conversation history must be stored in a database, not held in memory
- Responses stream to the browser token by token, not returned all at once
- The coding agent (Claude Code, Cursor, or Codex) that works on this project
  needs a clear CLAUDE.md that maps the architecture so it can operate without confusion

Session Two does not introduce new frameworks. It applies the eleven you already
know to a live Express server and a real database. The SCQ platform is the context
that makes every decision concrete.

---

## Framework Mapping

Each document in this session maps directly to one or more frameworks from Session One.
That mapping is intentional. When you build something in Session Two, you should
be able to point back to the framework that governs it.

| Session-02 Document | Applies These Frameworks |
|---|---|
| 00-platform-overview.md | Read first. Introduces the SCQ Simulation Portal, Matteo, Juli, and Tedd. |
| 01-web-integration-layer.md | Framework 08 (Internal Setup) + Framework 02 (Project Structure) |
| 02-database-schema-design.md | Framework 09 (Memory and State) |
| 03-jwt-and-authentication.md | Framework 11 (Security Baseline) + Framework 05 (Environment Config) |
| 04-task-decomposition.md | Framework 01 (Agent Mental Model) |
| 05-prompt-engineering-principles.md | Framework 07 (System Prompt Skeleton) + Framework 04 (Context Window Budget) |
| 06-few-shot-examples.md | Framework 07 (System Prompt Skeleton) |
| 07-output-format-control.md | Framework 07 (System Prompt Skeleton) + Framework 03 (Model Selection) |
| 08-evaluation-methods.md | Framework 10 (Observability) |
| 09-iteration-workflow.md | Framework 10 (Observability) + Framework 04 (Context Window Budget) |

---

## Documents in This Session

```
Session-02 (Task Design and Web Layer)/
|
|-- 00-platform-overview.md
|       Read this first. Describes the SCQ Simulation Portal: what it is,
|       who it serves, and what Matteo, Juli, and Tedd each do.
|       The student's journey through all three stages explained.
|       Maps every Session-01 framework to where it lives in this platform.
|
|-- 01-web-integration-layer.md
|       Frameworks 08 and 02 applied to the SCQ platform.
|       The five-layer agent from Session One now lives inside an Express server.
|       Express route, SSE streaming, Python agent wiring, and the boundary
|       between what the web layer owns and what the agent owns.
|
|-- 02-database-schema-design.md
|       Framework 09 (Memory and State) applied to the SCQ platform.
|       The JSON file from Session One becomes a real database table.
|       Sessions table schema, conversation history query pattern, and
|       why the web layer owns the database, not the agent.
|
|-- 03-jwt-and-authentication.md
|       Framework 11 (Security Baseline) + Framework 05 (Environment Config).
|       Every agent endpoint must be protected before any agent logic runs.
|       Login route, JWT signing with HS256, algorithm pinning, and role guards
|       for student vs professor access on the SCQ platform.
|
|-- 04-task-decomposition.md
|       Framework 01 (Agent Mental Model) applied to Matteo, Juli, and Tedd.
|       What exactly is each agent's job? What does a single turn look like?
|       Where does one agent stop and the next one start?
|       Breaking the SCQ coaching task into agent-sized pieces.
|
|-- 05-prompt-engineering-principles.md
|       Framework 07 (System Prompt Skeleton) + Framework 04 (Context Budget).
|       The five-section skeleton from Session One applied to a real coaching task.
|       How to write prompts that produce consistent output without consuming
|       the entire context window.
|
|-- 06-few-shot-examples.md
|       Framework 07 (System Prompt Skeleton) - the examples section.
|       When to include examples, how many, what format, and what makes
|       a good example for Matteo's SCQ coaching style vs Tedd's peer review rubric.
|
|-- 07-output-format-control.md
|       Framework 07 + Framework 03 (Model Selection).
|       Controlling what the agent returns: coaching questions vs structured
|       rubric scores vs plain narrative. When each format is right and
|       how to enforce it without adding tokens.
|
|-- 08-evaluation-methods.md
|       Framework 10 (Observability) applied to agent quality.
|       How to measure whether Matteo is asking the right questions.
|       LLM-as-judge, regression suites, and golden datasets for the SCQ platform.
|
|-- 09-iteration-workflow.md
|       Framework 10 (Observability) + Framework 04 (Context Window Budget).
|       How to improve a prompt without breaking what already works.
|       Version-controlled prompts, test suites, and diff-driven iteration.
|
|-- assignments/
|       One assignment per document. Self-contained, step-by-step.
|       Each assignment produces working code that extends the SCQ platform.
|       Start with 01-build-your-agent-route.md.
|
`-- starter-code/
        Per-topic code folders. One folder per document.
        starter-code/01-web-integration/
        starter-code/02-database-schema/
        starter-code/03-jwt-auth/
        starter-code/04-task-decomposition/
        starter-code/05-prompt-engineering/
        starter-code/06-few-shot-examples/
        starter-code/07-output-format/
        starter-code/08-evaluation/
        starter-code/09-iteration/
```

---

## CLAUDE.md Evolves With the Build

Your CLAUDE.md from Session One described a standalone Python agent.
By the end of Session Two it must describe the full SCQ platform: the Express
server, the database, the JWT flow, and the three agent files.

Every coding agent working on this project reads CLAUDE.md first. If the
architecture grows in Session Two but CLAUDE.md does not, the next coding agent
session will work from an incomplete picture and make incorrect assumptions.

Update your CLAUDE.md as you complete each document. The starter-code folder
for this session includes a running CLAUDE.md diff that shows what to add at
each step.

---

## Prerequisites

Complete all eleven assignments in Session One before starting here.
Specifically:

- Your five-layer agent runs with `python main.py`
- You have at least one working tool in `tool_registry.py`
- Your `agent/context.py` has a real five-section system prompt
- Your `.env` has `ANTHROPIC_API_KEY` set and is gitignored
- You have run the Session One security audit

Session Two assumes the foundation works. It does not revisit the agent loop,
tool registry, or system prompt skeleton. Those are Session One topics.

---

## What You Will Have Built by the End

A working SCQ platform web layer:
- Express server with authenticated `/api/agent1/chat` route
- JWT login route with HS256 signing and role fields
- Sessions table storing full conversation history
- Three decomposed task definitions: one per agent (Matteo, Juli, Tedd)
- A system prompt for Matteo that applies all five prompt engineering principles
- Few-shot examples for at least one agent
- A scoring function that measures output quality
- One documented iteration cycle with a measurable improvement
- An updated CLAUDE.md that describes the full platform architecture

Session Three implements the full logic of all three agents on top of this foundation.

---

Copyright Janna AI Research Labs
