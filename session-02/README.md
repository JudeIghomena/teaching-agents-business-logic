# Session Two: Task Design, Prompt Engineering, and Evaluation

> Before you write production prompts, you need to know exactly what task
> the agent is solving, how to measure whether it is working, and how to
> improve it without breaking what already works.

**Status: Coming after Session One**

---

## What This Session Covers

Session Two picks up where Session One ends. Session One built the internal
infrastructure: the five layers, the project structure, the model config,
the tool registry, and the system message skeleton. Session Two builds the
intelligence layer on top of that foundation.

You cannot write a good prompt for a task you have not precisely defined.
You cannot improve a prompt without a way to measure it. You cannot evaluate
without a repeatable test suite. This session covers all three in order.

---

## Planned Documents

```
session-02/
├── 01-task-decomposition.md
│     Breaking a business requirement into agent-sized tasks.
│     What one agent should and should not try to do in a single turn.
│
├── 02-prompt-engineering-principles.md
│     How to write prompts that produce consistent, correct output.
│     Instruction clarity, chain-of-thought, few-shot examples.
│
├── 03-few-shot-examples.md
│     When and how to include examples in the prompt.
│     How many examples, what format, what makes a good example.
│
├── 04-output-format-control.md
│     Controlling what the agent returns: plain text, JSON, structured
│     fields, constrained vocabulary. When to use each.
│
├── 05-evaluation-methods.md
│     How to measure whether your agent is working.
│     Human eval, LLM-as-judge, regression suites, golden datasets.
│
├── 06-iteration-workflow.md
│     How to improve prompts systematically without breaking what works.
│     Version-controlled prompts, test suites, diff-driven changes.
│
└── starter-code/
      Prompt templates, evaluation harness, golden test dataset template.
```

---

## Prerequisites

Complete Session One before starting Session Two. Specifically, have the
starter-code agent running with your own tools and system message in place.

Session Two assumes you have the infrastructure working. It does not teach
you how to set up the agent loop or tool registry. Those are Session One topics.
The focus here is entirely on what you tell the agent to do and how you know
it is doing it correctly.

---

Copyright Janna AI Research Labs
