# Assignment 04: Budget Your Context Window

**What you are building:** A context budget allocation for your agent, documented in CLAUDE.md and enforced in context.py
**Why it matters:** An agent that fills its context window mid-conversation silently degrades or crashes. Allocating the budget in advance means you control what gets cut and in what order before it becomes a problem.
**Time estimate:** 25 minutes
**Reads with:** 04-context-window-budget.md

---

## What You Are Going To Do

You are going to calculate how many tokens each part of your agent's context needs, allocate a budget across the four main consumers, and configure the history trimming rule in context.py.

---

## Step 1: Find Your Model's Context Limit

Look up the limit for the model you chose in Assignment 03:

| Model | Context limit |
|---|---|
| claude-haiku-4-5 | 200,000 tokens |
| claude-sonnet-5 | 200,000 tokens |
| claude-opus-4-8 | 200,000 tokens |

Write this number into your CLAUDE.md under "Context Window Budget":

```
Model context limit: 200,000 tokens
```

---

## Step 2: Estimate the Size of Each Consumer

The four things that consume context are:

1. System prompt: the instructions you write in Assignment 07
2. Tool schemas: the JSON descriptions of your tools from Assignment 06
3. Conversation history: accumulated message pairs from past turns
4. Working space: the current user message and the model's response

Estimate each:

| Consumer | Rough estimate |
|---|---|
| System prompt | Count your words and multiply by 1.3. A 300-word prompt is about 400 tokens. |
| Tool schemas | Each tool schema is roughly 100-200 tokens. Multiply by number of tools. |
| Conversation history | Each turn pair is roughly 200-500 tokens. Decide how many turns to keep. |
| Working space | Reserve at least 4,000 tokens for the current turn and response. |

Fill in the table in your CLAUDE.md:

```
Allocation:
- System prompt: [X] tokens reserved
- Tool schemas: [X] tokens reserved
- Conversation history: [X] tokens reserved (last [N] turns)
- Working space: 4,000 tokens reserved
```

---

## Step 3: Write the Trimming Rule

History is the only consumer that grows over time. You must define a rule for cutting it when the budget fills.

Open `agent/context.py` and find the history trimming section. Set your maximum history length:

```python
# agent/context.py

MAX_HISTORY_TURNS = 10   # keep last 10 message pairs (20 messages)

def trim_history(messages: list) -> list:
    """Keep only the most recent MAX_HISTORY_TURNS pairs."""
    if len(messages) <= MAX_HISTORY_TURNS * 2:
        return messages
    return messages[-(MAX_HISTORY_TURNS * 2):]
```

Choose MAX_HISTORY_TURNS based on your agent's task:
- Short task (single request, no follow-up needed): 4-6 turns
- Coaching or multi-step task (context from earlier turns matters): 10-15 turns
- Long-running session (student works through a full exercise): 20 turns

---

## Step 4: Document the Cut Order in CLAUDE.md

Add the cut order to your CLAUDE.md. This tells your coding agent what to remove first if the budget overflows:

```
Cut order when over budget:
  1. Tool results older than 3 turns
  2. Old assistant turns beyond the history limit
  3. Old user turns beyond the history limit

Never cut:
  - The system message
  - The current user turn
  - Tool schemas
```

---

## Step 5: Verify Trimming Works

Add a quick test to confirm trimming behaves correctly:

```python
# Run this in a Python shell or as a temporary test script

from agent.context import trim_history

# Create fake history with 30 message pairs (60 messages)
fake_history = []
for i in range(30):
    fake_history.append({"role": "user", "content": f"Message {i}"})
    fake_history.append({"role": "assistant", "content": f"Response {i}"})

trimmed = trim_history(fake_history)
print(f"Before: {len(fake_history)} messages")
print(f"After:  {len(trimmed)} messages")
print(f"Expected: {MAX_HISTORY_TURNS * 2} messages")
```

The after count should match your MAX_HISTORY_TURNS multiplied by 2.

---

## You Are Done When

- [ ] Your CLAUDE.md shows the context limit for your chosen model
- [ ] Your CLAUDE.md has a specific token allocation across all four consumers
- [ ] `agent/context.py` has a MAX_HISTORY_TURNS value set
- [ ] The trimming test confirms history is cut to the correct length
- [ ] Your CLAUDE.md documents the cut order and what never gets cut

---

## If You Get Stuck

Not sure how many tokens your system prompt will use: write a rough draft now and count the words. Divide by 0.75 for a token estimate. You will refine this in Assignment 07.

Unsure how many tools to plan for: budget 5 tools at 150 tokens each (750 tokens) as a placeholder. Update after Assignment 06.

---

## Next Assignment

[05-configure-your-environment.md](05-configure-your-environment.md)

---

Copyright Janna AI Research Labs
