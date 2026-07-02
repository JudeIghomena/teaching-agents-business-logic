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

## Your Turn

For the agent you are building, answer these before moving to document 05:

1. What is the primary task? (classify / reason / synthesise / create)
2. What is the expected volume? (10 requests/day vs 10,000/day changes the model choice)
3. What does a wrong answer cost? (low cost = Haiku acceptable; high cost = use Sonnet or Opus)
4. Does correctness or creativity matter more?

Write these down. They justify your model choice in code review.

---

Copyright Janna AI Research Labs
