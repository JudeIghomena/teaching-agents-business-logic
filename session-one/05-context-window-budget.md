# Framework 06: Context Window Budget

> The context window is a fixed resource. Every token you spend is unavailable
> for something else. Budgeting it before you write the prompt prevents the most
> expensive mistakes in agent development.

---

## What the Context Window Actually Contains

Most developers think the context window holds "the conversation." It holds
much more, and every byte costs money and affects reasoning quality.

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONTEXT WINDOW (200,000 tokens)              │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  SYSTEM MESSAGE                          ~500,2,000 tok │    │
│  │  Role, rules, format instructions, escalation policy    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  TOOL SCHEMAS                            ~200,1,500 tok │    │
│  │  JSON schemas for every registered tool                 │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  DYNAMIC INJECTION                       ~100,2,000 tok │    │
│  │  Retrieved data, session state, user profile            │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  CONVERSATION HISTORY                   ~1,000,50,000+  │    │
│  │  User turns + assistant turns + tool results            │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  RESPONSE BUDGET                          set by you    │    │
│  │  max_tokens: what the model is allowed to generate     │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

The input context (everything above the response) is what you pay to send.
The output (the response) is what you pay to receive. Both count toward cost.

---

## The Budget Worksheet

Fill this in before writing your system message.

```
CONTEXT BUDGET WORKSHEET
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Model context limit:              ____________ tokens
(claude-sonnet-5 = 200,000 tokens)

Allocation:
  System message target:          ____________ tokens
  Tool schemas (estimate):        ____________ tokens
  Dynamic injection (per turn):   ____________ tokens
  History window target:          ____________ tokens
  Response budget (max_tokens):   ____________ tokens
                              ─────────────────────
  Total input + output:           ____________ tokens

Is total < model context limit?   YES / NO

If NO: reduce history window first, then trim dynamic injection,
then tighten the system message. Never reduce the response budget
below the longest output your agent might need to produce.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Worked Example: Customer Support Agent

```
Model: claude-sonnet-5 (200,000 token context limit)

System message:          800 tokens   (role + 8 rules + format block)
Tool schemas (3 tools):  600 tokens   (~200 tokens per tool schema)
Dynamic injection:       400 tokens   (customer record + session flags)
History window:        5,000 tokens   (last 10 exchanges, enough for continuity)
Response budget:       2,048 tokens   (support replies are rarely longer than this)
                      ─────────────
Total:                 8,848 tokens   well within the 200,000 limit

Assessment: healthy budget. History window can grow to 20,000+ tokens
before approaching any limit. No trimming needed for this agent.
```

---

## Worked Example: Document Analysis Agent

```
Model: claude-opus-4-8 (200,000 token context limit)

System message:          1,500 tokens  (complex role with many constraints)
Tool schemas (8 tools):  2,400 tokens  (~300 tokens per tool schema)
Dynamic injection:      40,000 tokens  (10 documents injected per run)
History window:         10,000 tokens  (multi-turn analysis sessions)
Response budget:         8,192 tokens  (long synthesis outputs expected)
                        ──────────────
Total:                  62,092 tokens  31% of the context limit

Assessment: fine for 10 documents. At 30 documents (~120,000 injected tokens)
this approaches the limit. Solution: chunk documents and process in batches
rather than injecting all at once.
```

---

## The Hierarchy of What to Cut

When your budget is tight, cut in this order:

```
1. Cut history first
   ──────────────────────────────────────────────────────
   History is the most elastic part of the budget. A well-summarised
   conversation at 3,000 tokens retains more information than a raw
   history at 10,000 tokens. Implement summarisation before trimming.

2. Cut dynamic injection second
   ──────────────────────────────────────────────────────
   Inject only what is needed for this specific turn, not everything
   you might possibly need. Lazy injection (retrieve when needed via
   a tool) uses less context than eager injection (inject everything upfront).

3. Tighten the system message third
   ──────────────────────────────────────────────────────
   Remove redundancy. Every sentence in the system message that repeats
   another sentence is wasted tokens. A tight 500-token system message
   outperforms a verbose 2,000-token one.

4. Never cut the response budget
   ──────────────────────────────────────────────────────
   Cutting max_tokens truncates the response mid-sentence. The model
   has no warning this is about to happen, it just stops. The user
   receives a broken output. This is the last lever, not the first.
```

---

## What Never Goes in Context

Some information should never be placed in the context window, regardless of
how much space is available:

| Never put in context | Why | Alternative |
|---|---|---|
| Raw database connection strings | Leaked in logs or responses | Load via env, never pass to model |
| Auth tokens or session cookies | Model may echo them in output | Pass user ID only; resolve auth server-side |
| Unvalidated user input in system role | Prompt injection vector | User input goes in user turn only, never system |
| Bulk PII (thousands of records) | Privacy risk + wasted tokens | Use tool to retrieve specific record on demand |
| Secrets, API keys | Model may include in output | Never. Not even as an example. |

The rule: if it should not appear in a log file, it should not appear in context.

---

## Dynamic Injection Pattern

Dynamic injection means adding turn-specific data to context at runtime,
not hardcoding it into the system message.

```python
# Bad: hardcoded user data in system message (stale, not personalised)
system_message = """
You are helping customer ID CUS-00001, John Smith, Gold tier, 14 purchases.
"""

# Good: inject at runtime, resolved fresh each turn
def build_turn_context(customer_id: str) -> str:
    record = get_customer_record(customer_id)
    return (
        f"Current customer: {record['name']} "
        f"(ID: {record['customer_id']}, "
        f"Tier: {record['loyalty_tier']}, "
        f"Purchases this year: {record['purchases_this_year']})"
    )

# Injected as the first user message or appended to system message at session start
```

Dynamic injection keeps the base system message clean and reusable.
The customer-specific data is fresh every session.

---

## Sample: Budget Worksheet (Customisable)

```
CONTEXT BUDGET: [YOUR AGENT NAME]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Date: ____________
Model: ____________
Context limit: ____________ tokens

Component              Target tokens    Actual tokens (measure after writing)
──────────────────────────────────────────────────────────────────────────────
System message         ____________     ____________
Tool schemas           ____________     ____________
Dynamic injection      ____________     ____________
History window         ____________     ____________
Response budget        ____________     ____________
──────────────────────────────────────────────────────────────────────────────
TOTAL                  ____________     ____________

% of context limit used:  ____________%
Alert threshold: flag if > 60% (leaves headroom for larger tool results)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Measuring Actual Token Counts

After writing your system message and tool schemas, measure their actual size:

```python
# Rough estimate: 1 token ~= 4 characters in English
system_message = "..."
estimated_tokens = len(system_message) // 4
print(f"System message: ~{estimated_tokens} tokens")

# Precise count using the Anthropic SDK
from agent.infrastructure import client

response = client.messages.count_tokens(
    model="claude-sonnet-5",
    system=system_message,
    tools=TOOLS,
    messages=[{"role": "user", "content": "test"}],
)
print(f"Precise input token count: {response.input_tokens}")
```

Measure once after writing your system message and tool schemas. If the
number surprises you, the budget worksheet caught the problem early.

---

## Apply to Your Coding Agent

**Task:** Fill in your context budget numbers and add context management rules
to your CLAUDE.md that tell your coding agent what the budget targets are, what
must never enter the context window, and in what order to cut when the budget
is tight.

**Why this matters:** A coding agent working on your codebase may suggest
changes to how context is managed. Without written rules, those suggestions
may contradict your budget decisions, injecting more data than your model can
reason well about. With rules in CLAUDE.md, the coding agent reinforces your
context design instead of undermining it.

**Step 1: Fill in your budget numbers**

Use the worksheet from this document. The four numbers you need:

```
Model: [e.g. claude-sonnet-5, 200,000 token limit]
System message target: [e.g. 800 tokens]
Tool schemas total: [e.g. 600 tokens across 3 tools]
History window limit: [e.g. trim when estimated_tokens_used exceeds 80,000]
Response budget: [e.g. AGENT_MAX_TOKENS=2048]
Alert threshold: [e.g. flag if a single turn exceeds 60,000 input tokens]
```

**Step 2: Copy this template into CLAUDE.md**

```
## Context Management Rules

### Budget targets for this project
Model: [your model and context limit]
System message: keep under [N] tokens. Tighten if it grows beyond this.
Tool schemas: [N] tools registered, estimated [N] tokens total.
History window: trim when estimated_tokens_used exceeds [N].
Response budget: AGENT_MAX_TOKENS=[N] (do not reduce this).

### What must never enter the context window
- .env values or secrets (load via os.environ, never pass to the model)
- Auth tokens or session cookies (pass user_id only, resolve server-side)
- Bulk records fetched in advance (use a tool to retrieve specific records on demand)
- Unvalidated user input in the system message role (user input goes in user turn only)

### History trimming rule (from agent/context.py)
When estimated_tokens_used exceeds the limit, trim using this pattern:
- Keep the first 2 messages (original user intent)
- Keep the last 10 messages (recent state)
- Drop the middle
Do not truncate from the beginning only: losing original intent causes
the model to answer confidently about the wrong thing.

### Cut order when budget is tight
1. Reduce history window first (most elastic, least impact on reasoning)
2. Reduce dynamic injection second (inject only what this specific turn needs)
3. Tighten the system message third (remove redundant or repeated rules)
4. Never reduce AGENT_MAX_TOKENS (truncated responses are worse than shorter history)
```

**Step 3: Fill in your actual numbers**

Replace every bracket with the real numbers from your completed worksheet. If
you have not filled in the worksheet yet, measure your system message and tool
schemas now using the token counting code from this document. It takes under
five minutes and prevents expensive surprises when the agent runs at scale.

**Step 4: Paste into CLAUDE.md**

Open your project CLAUDE.md. Add the completed block under `## Context
Management Rules`.

**Step 5: Apply to your coding tool**

For Claude Code: paste into CLAUDE.md. When Claude Code suggests adding data
to the context, it will check these rules first. The cut order is especially
useful: Claude Code will reduce history before touching the system message.

For Cursor: paste into `.cursorrules`.

For Codex: add to the workspace system prompt.

**What you now have:** A coding agent that respects your context budget. It
will not suggest injecting large datasets into context, it knows the correct
trim order, and it will never suggest reducing `max_tokens` as a first move.

---

Copyright Janna AI Research Labs
