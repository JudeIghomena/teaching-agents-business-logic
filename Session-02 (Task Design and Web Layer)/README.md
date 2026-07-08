# Session Two: Task Design, Web Layer, and Prompt Engineering

> An agent that cannot be reached by a user is not an agent. Before you
> design tasks or write production prompts, you need to wire your agent
> into a web application, protect it with authentication, and persist
> conversation state. This session covers the web layer first, then the
> intelligence layer on top of it.

---

## What This Session Covers

Session Two picks up where Session One ends. Session One built the internal
infrastructure: the five layers, the project structure, the model config,
the tool registry, and the system message skeleton. Session Two adds two things:

1. The web layer that makes the agent accessible from a browser. This includes
   the Express route, SSE streaming, JWT authentication, and the database schema
   that stores conversation history.

2. The prompt intelligence layer. Once the agent is reachable, you need to know
   exactly what task it is solving, how to write prompts that produce consistent
   output, and how to measure and improve that output without breaking what works.

The three web layer documents come first because they are prerequisites for
everything else. You cannot evaluate an agent you cannot reach.

---

## Documents in This Session

```
Session-02 (Task Design and Web Layer)/
|
|-- 01-web-integration-layer.md
|       The journey of one user message from browser to agent and back.
|       Express route anatomy, SSE setup, Python agent stdin/stdout wiring,
|       and the boundary between web layer and agent layer.
|
|-- 02-database-schema-design.md
|       The sessions table that stores conversation history.
|       Schema design, query patterns, and why the web layer owns the DB,
|       not the agent.
|
|-- 03-jwt-and-authentication.md
|       How to issue and verify JSON Web Tokens.
|       Login route, token signing, algorithm pinning, and role guards.
|       What the agent can trust from the token and what it cannot.
|
|-- 04-task-decomposition.md
|       Breaking a business requirement into agent-sized tasks.
|       What one agent should and should not try to do in a single turn.
|       Applied to Matteo, Juli, and Tedd on the SCQ platform.
|
|-- 05-prompt-engineering-principles.md
|       How to write prompts that produce consistent, correct output.
|       Instruction clarity, chain-of-thought, and the five-section skeleton
|       from Session One applied to a real coaching task.
|
|-- 06-few-shot-examples.md
|       When and how to include examples in the prompt.
|       How many examples, what format, and what makes a good example
|       for each of the three SCQ agents.
|
|-- 07-output-format-control.md
|       Controlling what the agent returns: plain text, JSON, structured
|       fields, constrained vocabulary. When to use each and how to enforce it.
|
|-- 08-evaluation-methods.md
|       How to measure whether your agent is working.
|       Human eval, LLM-as-judge, regression suites, and golden datasets.
|
|-- 09-iteration-workflow.md
|       How to improve prompts systematically without breaking what works.
|       Version-controlled prompts, test suites, and diff-driven changes.
|
|-- assignments/
|       One assignment per document. Self-contained, step-by-step.
|       Start with 01-build-your-agent-route.md.
|
`-- starter-code/
        Per-topic code folders matching each document.
        starter-code/01-web-integration/
        starter-code/02-database-schema/
        starter-code/03-jwt-auth/
        Prompt templates, evaluation harness, and golden test dataset template.
```

---

## Prerequisites

Complete Session One before starting Session Two. Specifically:

- The five-layer agent must be running locally with `python main.py`
- You must have a working tool in `tool_registry.py`
- Your `agent/context.py` must have a real system prompt in all five sections
- Your `.env` file must have `ANTHROPIC_API_KEY` set

Session Two does not revisit the agent loop, tool registry, or system prompt
skeleton. Those are Session One topics. The focus here is on making the agent
accessible from a web application and making it behave correctly and consistently.

---

## The Build Arc

By the end of Session Two, you will have:

- An Express server with a working `/api/agent1/chat` route
- JWT authentication protecting every agent endpoint
- A sessions table storing conversation history in a database
- A well-decomposed task definition for your agent
- A system prompt that applies all five prompt engineering principles
- At least two few-shot examples in your prompt
- A scoring function that measures your agent's output quality
- A documented iteration log showing one measurable improvement

All of this builds directly on the SCQ platform. Matteo, Juli, and Tedd are
the agents you are wiring in. Session Three implements their full logic.

---

Copyright Janna AI Research Labs
