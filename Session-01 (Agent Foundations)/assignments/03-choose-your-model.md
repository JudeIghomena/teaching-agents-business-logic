# Assignment 03: Choose Your Model

**What you are building:** The model selection decision for your agent, documented in model_config.py and CLAUDE.md
**Why it matters:** The wrong model choice costs money on every call or produces unreliable output. This decision is made once per project and affects every agent interaction.
**Time estimate:** 20 minutes
**Reads with:** 03-model-selection.md

---

## What You Are Going To Do

You are going to choose the right model for your agent's task, set it in model_config.py, and document the routing rule in your CLAUDE.md so your coding agent never changes the model without a reason.

---

## Step 1: Identify Your Task Type

Answer these three questions about your agent:

1. Does your agent make decisions that must always produce the same output for the same input? (yes/no)
2. Does your agent need to reason across more than 10 steps or across a long document? (yes/no)
3. Does your agent handle simple, repetitive tasks like classification or short summaries? (yes/no)

Use your answers to pick a starting model:

| Your answers | Starting model |
|---|---|
| Q1 yes, Q3 yes | claude-haiku-4-5 (fast, cheap, deterministic tasks) |
| Q1 yes, Q2 yes | claude-sonnet-5 (complex reasoning, moderate cost) |
| Q2 yes, creative output needed | claude-opus-4-8 (most capable, highest cost) |
| Unsure | claude-sonnet-5 (safe default for most business logic) |

---

## Step 2: Set the Model in model_config.py

Open `agent/model_config.py` and update the model ID:

```python
# agent/model_config.py

MODEL = "claude-haiku-4-5"          # or claude-sonnet-5 or claude-opus-4-8
MAX_TOKENS = 2048                    # adjust for your task
TEMPERATURE = 0.0                    # 0.0 for deterministic, 0.3-0.7 for creative
```

Temperature rules:
- 0.0: use for classification, routing, approval decisions, any task where the same input should always produce the same output
- 0.3: use for coaching, guidance, or tasks that benefit from slight variation
- 0.7 and above: use only for creative tasks like writing or brainstorming

---

## Step 3: Document the Model Routing Rule in CLAUDE.md

Open your CLAUDE.md and find the "Model Routing" section. Fill in your specific routing rule:

```
## Model Routing

Primary model: claude-haiku-4-5

Switch to claude-sonnet-5 when: [describe the condition that warrants more capability]
Switch back to claude-haiku-4-5 when: [describe the condition for switching back]

Temperature: 0.0
Reason: [one sentence explaining why this temperature is correct for your task]
```

Be specific. "When the task is complex" is not a routing rule. "When the input document exceeds 5,000 words" is a routing rule.

---

## Step 4: Verify the Model Is Active

Run your agent and confirm it is using the model you set:

```bash
python main.py
```

In a separate terminal or by adding a temporary print statement, verify the model name:

```python
# Temporarily add to main.py to confirm
from agent.model_config import MODEL
print(f"Using model: {MODEL}")
```

Remove the print statement after confirming. Do not leave debug output in production code.

---

## You Are Done When

- [ ] `agent/model_config.py` has your chosen model ID, max tokens, and temperature set
- [ ] Your CLAUDE.md Model Routing section has a specific switching rule (not a vague one)
- [ ] Your CLAUDE.md has a one-sentence reason for the temperature choice
- [ ] `python main.py` runs with the new model and returns a response
- [ ] You have not hardcoded the model name anywhere except model_config.py

---

## If You Get Stuck

"Model not found" error: check the exact model ID spelling. Use one of these exactly as written: `claude-haiku-4-5`, `claude-sonnet-5`, `claude-opus-4-8`.

Responses feel inconsistent between runs: temperature may be above 0.0. Set it to 0.0 and retest.

Responses are cut off mid-sentence: increase MAX_TOKENS. Start at 4096 if you are seeing this.

---

## Next Assignment

[04-budget-your-context-window.md](04-budget-your-context-window.md)

---

Copyright Janna AI Research Labs
