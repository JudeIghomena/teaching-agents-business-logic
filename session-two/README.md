# Session Two — Task Design, Prompt Engineering, and Evaluation

> Before you write prompts, you need to know what task you are actually solving,
> whether your prompts are working, and how to measure improvement.

**Status: Coming next**

---

## What This Session Covers

Session Two picks up where Session One ends. Session One built the internal
infrastructure. Session Two builds the intelligence layer — the prompts,
task definitions, and evaluation methods that make the agent perform reliably.

---

## Planned Documents

```
session-two/
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

Complete Session One before starting Session Two.
Specifically, have a working `starter-code/` agent running with your own tools
and system message before attempting prompt engineering.

You cannot engineer a prompt for a task you have not defined.
You cannot evaluate a prompt without a working agent to evaluate.

---

Copyright Janna AI Research Labs
