# Framework 01: The Agent Mental Model

> Before you write a single prompt, you must understand what you are actually building.
> This document establishes the foundational mental model for every agent you will ever create.

---

## What an Agent Actually Is

Most developers think of an agent as "a prompt plus a loop." That is wrong, and it leads to
agents that are brittle, slow, and impossible to debug.

An agent is a **stateful reasoning process** with four hard boundaries:

```
┌─────────────────────────────────────────────────────────────────┐
│                        AGENT BOUNDARY                           │
│                                                                 │
│   Context Window     ─── What the model can see RIGHT NOW       │
│   Tool Registry      ─── What the model is allowed to do        │
│   Memory Layer       ─── What persists between turns            │
│   Execution Loop     ─── How long it keeps reasoning            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
         ▲                                              │
         │  inputs (user message, tool results)         │ outputs
         │                                              ▼
   External World                               External World
   (APIs, DBs, files)                           (responses, actions)
```

None of these four layers are prompts. The prompt lives *inside* the context window.
It is one input among several. If you design the other three layers poorly, no prompt
will save you.

---

## The Five Layers You Build Before Any Prompt

Think of agent setup as five concentric layers. You build from outside in.
Only the innermost layer is the prompt.

```
Layer 5 (outermost):  Infrastructure
                      API client, keys, rate limits, retry logic, logging

Layer 4:              Model Configuration
                      Which model, max tokens, temperature, stop sequences

Layer 3:              Tool Registry
                      What tools exist, their schemas, their permissions

Layer 2:              Context Architecture
                      System message skeleton, memory injection points,
                      conversation history shape

Layer 1 (innermost):  The Prompt
                      The actual instructions you write for the specific task
```

When an agent underperforms, the bug is almost always in Layers 3, 4, or 5 —
not Layer 1. Most developers only look at Layer 1.

---

## Why This Order Matters

### Layer 5 first: Infrastructure

If your client is misconfigured, every token you generate is wasted.
Infrastructure failures are silent: the model runs, output is generated,
and then the response is dropped, corrupted, or retried at cost.

Infrastructure includes:
- API client initialisation (timeouts, retries, connection pooling)
- Secret management (never hardcoded — loaded from env at runtime)
- Rate limit awareness (requests per minute, tokens per minute)
- Structured logging (you cannot debug what you cannot observe)

### Layer 4: Model Configuration

The model you choose sets a hard ceiling on what the agent can do.
This is not about "better" or "worse" — it is about matching capability
to task. Sending a simple classification task to the most capable model
wastes money and increases latency. Sending a multi-step reasoning task
to a fast-but-small model produces wrong answers confidently.

Configuration decisions made here:
- Model ID (pinned, not dynamic — prevents surprise behaviour on model updates)
- `max_tokens` (controls cost and response length — never leave this uncapped)
- `temperature` (0.0 for deterministic business logic, higher for creative tasks)
- Stop sequences (where the model should stop generating)

### Layer 3: Tool Registry

Tools are the agent's hands. A tool that is not registered does not exist
to the agent, even if the function exists in your codebase. A tool that is
registered but poorly described will be called incorrectly.

The tool registry is built before the prompt because:
- Tools constrain what the agent can *attempt* to do
- Tool schemas teach the agent what inputs are valid
- Tool permissions define what the agent is *allowed* to do (different from what it can attempt)

### Layer 2: Context Architecture

The context window is not infinite. Even when it is large, filling it
inefficiently degrades reasoning quality. Context architecture means:
- Deciding what the system message contains (and what it does not)
- Deciding how conversation history is managed (full, windowed, summarised)
- Deciding where dynamic information is injected (user profile, session state, retrieved data)
- Deciding what is NEVER put in context (secrets, PII, unvalidated user input in system role)

### Layer 1: The Prompt

Only now — with infrastructure stable, model configured, tools registered,
and context shaped — do you write the prompt.

This is the layer that most tutorials start with. You now understand why
starting here is like writing dialogue for a film before designing the set,
hiring the crew, or deciding what story you are telling.

---

## The Agent Execution Cycle

Once all five layers are in place, the agent runs in a loop:

```
1. Receive input (user message, event, scheduled trigger)
         │
         ▼
2. Build context (inject memory, retrieve relevant data, attach history)
         │
         ▼
3. Call model (with tools registered, config applied)
         │
         ▼
4. Inspect response
         ├── Text response only → return to user / caller
         └── Tool call requested → execute tool, append result, go to step 3
         │
         ▼
5. Store relevant output to memory layer
         │
         ▼
6. Return final response
```

Notice that step 3 may repeat multiple times before step 6. This is the
"agentic loop." It is not magic — it is the model requesting tool execution
until it has enough information to give a final answer.

Your infrastructure (Layer 5) must handle this loop correctly:
- Each iteration consumes tokens
- Each tool call adds latency
- Unbounded loops burn money and can hang your system

Always design with a `max_iterations` cap.

---

## The Golden Rule

> The quality of an agent's output is determined 80% by the quality of its
> internal setup, and 20% by the quality of its prompts.

Invest in Layers 2-5 before you write a single word of Layer 1.

---

## What Comes Next

The next document (`02-internal-setup.md`) translates this mental model into
concrete code. You will build each of the five layers from scratch, with
annotated examples in Python using the Anthropic SDK.

---

Copyright Janna AI Research Labs
