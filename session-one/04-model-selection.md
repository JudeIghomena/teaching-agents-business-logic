# Framework 04: Model Selection

> Choosing a model is not a preference, it is an engineering decision with
> measurable consequences for cost, latency, and correctness. Make it
> deliberately before you write the first line of code.

---

## The Core Trade-off

Every model sits somewhere on two axes:

```
                    HIGH CAPABILITY
                         │
              Fable 5    │   Opus 4.8
              (creative) │   (complex reasoning)
                         │
  LOW COST ─────────────┼───────────────── HIGH COST
  LOW LATENCY           │              HIGH LATENCY
                         │
              Haiku 4.5  │   Sonnet 5
              (fast/cheap)│  (balanced, default choice)
                         │
                    LOW CAPABILITY
```

No model is universally best. The right model is the one whose capability
ceiling matches your task's requirements, and no higher.

---

## Model Reference (Anthropic, July 2026)

| Model | ID | Best for | Relative cost | Typical latency |
|---|---|---|---|---|
| Haiku 4.5 | `claude-haiku-4-5-20251001` | Classification, extraction, simple Q&A, high-volume routing | Lowest | Fastest |
| Sonnet 5 | `claude-sonnet-5` | Multi-step reasoning, tool use, business logic, code | Medium | Medium |
| Opus 4.8 | `claude-opus-4-8` | Deep analysis, nuanced judgment, long-document synthesis | High | Slower |
| Fable 5 | `claude-fable-5` | Creative generation, narrative, style-sensitive writing | Medium | Medium |

Always pin the full model ID in your `.env`. Do not use shorthand aliases like
`"claude-sonnet"`, these resolve to different snapshots over time and produce
inconsistent behaviour.

---

## Decision Tree: Which Model for My Task?

Work through this top to bottom. Stop at the first match.

```
Is the task purely creative (story, marketing copy, brand voice)?
  YES → claude-fable-5
  NO  → continue

Does the task require deep synthesis across many documents,
nuanced legal/ethical judgment, or multi-hour research chains?
  YES → claude-opus-4-8
  NO  → continue

Is this a high-volume, repetitive task (classify 10,000 emails,
extract fields from forms, route tickets, answer FAQs)?
  YES → claude-haiku-4-5-20251001
  NO  → continue

Default → claude-sonnet-5
```

Sonnet 5 is the right default for the vast majority of business logic agents:
tool use, multi-step reasoning, code generation, structured output, decision
support. Only diverge when the decision tree above gives you a clear signal.

---

## Multi-Model Pipelines

Some agent workflows benefit from using different models at different stages.
This is called a multi-model pipeline and it is a legitimate pattern, not over-engineering.

**Example: Document Processing Pipeline**

```
Stage 1: Extract raw data from 500 documents
  Model: claude-haiku-4-5-20251001
  Why: Cheap, fast, extraction is straightforward
  Cost saving: ~70% cheaper than Sonnet for this stage

Stage 2: Reason about extracted data, apply business rules
  Model: claude-sonnet-5
  Why: This is where accuracy matters most
  No cost saving sacrificed here

Stage 3: Write final summary report for executive audience
  Model: claude-fable-5 (or claude-sonnet-5)
  Why: Polished prose matters here, Fable excels at tone
```

**When to use a multi-model pipeline:**
- Stage 1 is high-volume preprocessing (use Haiku)
- Stage 2 is the critical reasoning step (use Sonnet or Opus)
- Stage 3 is presentation/formatting (use Fable or Sonnet)

**When NOT to use it:**
- Your pipeline has only one logical stage
- The overhead of coordinating multiple models outweighs the savings
- You are still in early development (get it working with one model first)

---

## Common Mistakes

**Mistake 1: Using the most capable model by default**

Using Opus 4.8 for every task because "it is the best" is like using a
hospital-grade autoclave to clean a coffee cup. It works, but the cost
and time are disproportionate to the need.

**Mistake 2: Using the cheapest model to save money and then wondering why accuracy is low**

Haiku is not suitable for multi-step reasoning with tool use. If your agent
is making wrong decisions, check the model before blaming the prompt.

**Mistake 3: Not pinning the model ID**

`claude-sonnet` is not a pinned model ID. New weights can ship under the
same short name. Pin the full ID. Accept upgrades deliberately, not
accidentally.

**Mistake 4: Switching models without re-evaluating the prompt**

Different models have different response tendencies. A prompt tuned for Sonnet
may produce worse output on Opus, and vice versa. When you upgrade models,
run your test suite against the new model before deploying.

---

## Sample: Model Config Customisation

In your `.env`, set the model for your specific use case:

```bash
# For a high-volume document classifier
AGENT_MODEL=claude-haiku-4-5-20251001
AGENT_MAX_TOKENS=512           # Short output, just the classification label
AGENT_TEMPERATURE=0.0          # Must be deterministic

# For a business logic reasoning agent
AGENT_MODEL=claude-sonnet-5
AGENT_MAX_TOKENS=4096          # Room for multi-step reasoning + explanation
AGENT_TEMPERATURE=0.0          # Business decisions must be deterministic

# For a research synthesis agent
AGENT_MODEL=claude-opus-4-8
AGENT_MAX_TOKENS=8192          # Long synthesis outputs
AGENT_TEMPERATURE=0.2          # Slight variance acceptable in synthesis prose

# For a content generation agent
AGENT_MODEL=claude-fable-5
AGENT_MAX_TOKENS=4096
AGENT_TEMPERATURE=0.7          # Creative variance is desired here
```

---

## Apply to Your Coding Agent

**Task:** Add a model routing rule to your CLAUDE.md so your coding agent knows
which model to use for which type of task, and never suggests changing the model
without a clear engineering reason.

**Why this matters:** Without routing rules, a coding agent asked to "make this
faster" might suggest switching to Haiku when the task requires Sonnet-level
reasoning, or suggest Opus when Haiku would do. Written routing rules anchor
every model suggestion to your actual requirements.

**Step 1: Answer the four questions first**

Before writing the rule, answer these:
1. What is your agent's primary task? (classify / reason / synthesise / create)
2. What is the expected request volume? (10/day vs 10,000/day changes the choice)
3. What does a wrong answer cost in your domain? (low cost = Haiku acceptable)
4. Does correctness or creativity matter more?

**Step 2: Copy this template**

```
## Model Routing Rules

### Primary model for this project
AGENT_MODEL=claude-sonnet-5
Reason: [write your reason: e.g. "multi-step reasoning with tool use"]

### When to suggest a model change (propose to me, do not change unilaterally)

Change to claude-haiku-4-5-20251001 if:
- The task is purely classification or extraction (no multi-step reasoning)
- Volume exceeds [your threshold] requests per day (cost matters at scale)
- Output is a label, flag, or structured field (not a full explanation)

Change to claude-opus-4-8 if:
- Input is more than 50,000 tokens (many documents to synthesise)
- Task requires nuanced legal, ethical, or domain-expert judgment
- Latency tolerance is high and accuracy is critical

Change to claude-fable-5 if:
- Task is creative: marketing copy, narrative, brand-voice writing
- Style matters more than factual precision

### When NOT to suggest a model change
- Do not suggest downgrading to save cost without confirming task requirements
- Do not suggest upgrading without showing why the current model is insufficient
- Never change AGENT_MODEL in .env or model_config.py without my instruction

### Temperature rule
- Business logic tasks: AGENT_TEMPERATURE=0.0 (deterministic, always)
- Creative tasks: AGENT_TEMPERATURE=0.7 (only when model is claude-fable-5)
- Never raise temperature for reasoning tasks: wrong answers with variance
  are worse than correct answers without it
```

**Step 3: Fill in the brackets**

In the "primary model" section, write the actual reason for your choice, using
the four answers you wrote in Step 1. In the Haiku condition, write your actual
volume threshold.

**Step 4: Paste into CLAUDE.md**

Open your project CLAUDE.md. Add the completed block under `## Model Routing
Rules`. It should come after the project structure section.

**Step 5: Apply to your coding tool**

For Claude Code: the model routing rules are now session context. When you ask
Claude Code to optimise the agent or reduce costs, it will check these rules
before suggesting any model change.

For Cursor: paste into `.cursorrules`. Cursor will reference the routing rules
when you ask about performance or cost.

For Codex: add to the workspace system prompt as a constraint on model
recommendations.

**What you now have:** Your coding agent has written justification for the
current model choice and explicit conditions under which a change is appropriate.
Model suggestions become engineering proposals backed by your requirements, not
guesses based on what sounds better.

---

Copyright Janna AI Research Labs
