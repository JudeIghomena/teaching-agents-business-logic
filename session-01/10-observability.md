# Framework 10: Observability

> You cannot debug what you cannot see. Agent behaviour is invisible without
> structured logging. Every production agent must be fully observable.

---

## Why Agents Need Observability

Agents are non-deterministic. Given the same input, they may take different
tool call paths to reach the same answer. When something goes wrong, you need
to answer:

- What did the user send?
- What did the model decide to do?
- Which tools were called, in what order, with what inputs?
- What did each tool return?
- How many iterations did the loop run?
- How many tokens were consumed?
- What was the final output?

Without structured logging, the answer to all of these is: "I don't know."

---

## The Agent Log Schema

Every turn of an agent session should emit at minimum these structured events:

```python
# The complete log schema for one agent session

{
    # Session-level fields (emitted once at session start)
    "session_id": "ses_abc123",
    "user_id": "usr_xyz789",
    "agent_role": "customer_support",
    "model": "claude-sonnet-5",
    "started_at": "2026-07-02T14:00:00Z",

    # Turn-level fields (emitted once per user message)
    "turn": {
        "turn_number": 1,
        "user_input_length_chars": 142,
        "iterations": 2,            # How many model calls this turn required
        "total_input_tokens": 1840,
        "total_output_tokens": 312,
        "duration_ms": 3240,
        "final_stop_reason": "end_turn",

        # Tool calls made during this turn (one entry per tool call)
        "tool_calls": [
            {
                "iteration": 1,
                "tool_name": "get_customer_record",
                "input": {"customer_id": "CUS-00042891"},
                "success": True,
                "duration_ms": 45,
            },
            {
                "iteration": 2,
                "tool_name": "apply_discount",
                "input": {
                    "customer_id": "CUS-00042891",
                    "discount_percent": 15,
                    "reason": "complaint_resolution",
                },
                "success": True,
                "duration_ms": 38,
            },
        ],

        # Final response (length only, never log the full content if it contains PII)
        "response_length_chars": 284,
        "response_preview": "I have applied a 15% discount...",  # First 80 chars only
    }
}
```

---

## Implementing Structured Logging

```python
# agent/observability.py

import time
import uuid
import logging
from dataclasses import dataclass, field
from typing import Any


logger = logging.getLogger("agent.observability")


@dataclass
class TurnTrace:
    """
    Collects observability data across one full agent turn (potentially
    multiple model calls and tool calls).
    """
    session_id: str
    turn_number: int
    started_at: float = field(default_factory=time.time)

    iterations: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    tool_calls: list[dict] = field(default_factory=list)
    final_stop_reason: str = ""
    error: str | None = None


def start_turn(session_id: str, turn_number: int) -> TurnTrace:
    return TurnTrace(session_id=session_id, turn_number=turn_number)


def record_iteration(trace: TurnTrace, input_tokens: int, output_tokens: int, stop_reason: str) -> None:
    trace.iterations += 1
    trace.total_input_tokens += input_tokens
    trace.total_output_tokens += output_tokens
    trace.final_stop_reason = stop_reason


def record_tool_call(
    trace: TurnTrace,
    tool_name: str,
    tool_input: dict,
    result: Any,
    duration_ms: int,
    success: bool,
) -> None:
    trace.tool_calls.append({
        "iteration": trace.iterations,
        "tool_name": tool_name,
        "input": tool_input,
        "success": success,
        "duration_ms": duration_ms,
    })


def emit_turn(trace: TurnTrace, response_preview: str = "") -> None:
    duration_ms = int((time.time() - trace.started_at) * 1000)

    logger.info("agent_turn_complete", extra={
        "session_id": trace.session_id,
        "turn_number": trace.turn_number,
        "iterations": trace.iterations,
        "total_input_tokens": trace.total_input_tokens,
        "total_output_tokens": trace.total_output_tokens,
        "tool_calls_count": len(trace.tool_calls),
        "tool_calls": trace.tool_calls,
        "final_stop_reason": trace.final_stop_reason,
        "duration_ms": duration_ms,
        "response_preview": response_preview[:80] if response_preview else "",
        "error": trace.error,
    })
```

---

## Integrating Observability into the Runner

```python
# agent/runner.py: with observability integrated

from agent.observability import start_turn, record_iteration, record_tool_call, emit_turn
import time

def run_agent(user_message: str, context: ConversationContext, session_id: str, turn_number: int) -> str:
    trace = start_turn(session_id=session_id, turn_number=turn_number)

    add_user_turn(context, user_message)
    trim_history_if_needed(context)

    iteration = 0
    while iteration < config.max_iterations:
        iteration += 1

        response = client.messages.create(
            model=config.model_id,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            system=context.system_message,
            tools=TOOLS,
            messages=context.messages,
        )

        record_iteration(
            trace,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            stop_reason=response.stop_reason,
        )

        if response.stop_reason == "end_turn":
            final_text = next(b.text for b in response.content if hasattr(b, "text"))
            add_assistant_turn(context, final_text)
            emit_turn(trace, response_preview=final_text)
            return final_text

        if response.stop_reason == "tool_use":
            context.messages.append({"role": "assistant", "content": response.content})
            tool_results = []

            for block in response.content:
                if block.type == "tool_use":
                    tool_start = time.time()
                    try:
                        result = dispatch_tool(block.name, block.input)
                        success = True
                    except Exception as e:
                        result = {"error": str(e)}
                        success = False

                    tool_duration_ms = int((time.time() - tool_start) * 1000)
                    record_tool_call(trace, block.name, block.input, result, tool_duration_ms, success)

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    })

            context.messages.append({"role": "user", "content": tool_results})
            continue

    trace.error = "max_iterations_reached"
    emit_turn(trace)
    return "The agent reached its iteration limit without producing a final answer."
```

---

## What to Alert On

Set up alerts on these log patterns. These indicate something is wrong in production:

| Condition | Alert threshold | What it means |
|---|---|---|
| `iterations` > 8 | Any occurrence | Agent is looping, check tool return values |
| `total_input_tokens` > 100,000 | Any occurrence | Context budget not respected, check history trimming |
| `error = "max_iterations_reached"` | > 1% of turns | Agent cannot complete tasks, check tool schemas |
| `tool_calls_count` = 0 and `iterations` > 1 | Any occurrence | Model is re-calling itself without tools, prompt issue |
| `duration_ms` > 30,000 | Any occurrence | Turn taking > 30s, check for hanging tool calls |
| Any `success: false` in `tool_calls` | > 5% of tool calls | Tool implementation errors |

---

## What NOT to Log

Logging the wrong things is as dangerous as not logging enough.

```
NEVER LOG:
[ ] Full content of user messages (may contain PII)
[ ] Full content of assistant responses (may echo PII from user)
[ ] Customer names, emails, phone numbers, addresses
[ ] Discount amounts tied to individual customers (financial PII)
[ ] API keys, auth tokens, or secrets (obvious)
[ ] Full tool inputs when they contain sensitive fields
    (log the tool name and safe fields only)

SAFE TO LOG:
[ ] Session ID (non-PII reference)
[ ] User ID (internal reference, not name)
[ ] Token counts
[ ] Duration
[ ] Tool names
[ ] Stop reasons
[ ] Error types (not error messages that may include PII)
[ ] Response length (not content)
[ ] First 80 characters of response (check for PII before enabling this)
```

---

## Sample: Observability Config Checklist

```
OBSERVABILITY CHECKLIST: [YOUR AGENT NAME]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[ ] Structured logger configured (not print statements)
[ ] session_id generated and attached to all log events in a session
[ ] TurnTrace (or equivalent) collects iteration count, token usage, tool calls
[ ] Each tool call logged: name, success/fail, duration_ms
[ ] Turn emitted at completion: iterations, tokens, duration, stop_reason
[ ] Alerts defined for: max_iterations reached, high token count, tool failures
[ ] PII fields excluded from all log entries
[ ] Log level set per environment (DEBUG local, INFO staging, WARNING prod)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Apply to Your Coding Agent

**Task:** Add structured output rules to your CLAUDE.md that tell your coding
agent how to format completions, what to say when a test fails, and what your
logging code must and must never output.

**Why this matters:** A coding agent that narrates every step is slow to scan
and hard to act on. One that makes changes silently is hard to trust. Written
format rules calibrate the right balance: structured summaries for completions,
brief explanations for reasoning, and explicit log hygiene to prevent accidental
PII exposure in your agent's own logging code.

**Step 1: Copy this template into CLAUDE.md**

```
## Output Format Rules

### When completing a task
Always end with a structured completion summary in this exact format:
  Changed: [filename:line range or function name]
  What changed: [one sentence describing the change]
  Test result: [passed N/N tests | failed: test name and error | not run]
  Next: [what should be done next, or "nothing, task complete"]

Do not narrate the implementation steps. Show the completion summary only.

### When explaining code
Plain language only. No markdown bold (**text**) or italic (*text*).
No em dashes. If structure is needed, use a numbered list.
Keep explanations under 100 words unless I ask for more detail.

### When proposing a change
Show only the lines that change, not the entire file.
Format: filename.py, lines N-M, then the specific change.
State the reason in one sentence before showing the change.

### Logging code rules
When writing or modifying logging calls in this project:
- Never log full user message content (may contain PII)
- Never log tool inputs that include customer names, emails, or account IDs
- Safe to log: token counts, durations, tool names, stop reasons, session IDs
- Log response preview at 80 characters maximum, never the full response
- Log level in production must be WARNING or above, never DEBUG in production

### When a test fails
1. State the failing test name exactly as printed
2. State the error message exactly as printed
3. Propose one specific fix with the file and line number
4. Do not proceed with other changes until the test passes
```

**Step 2: Adjust the completion summary format**

If you prefer different fields in the completion summary, change them now. The
structure matters more than the exact words. What you need in every completion:
what changed, where it changed, whether tests passed, and what is next.

**Step 3: Paste into CLAUDE.md**

Open your project CLAUDE.md. Add this block under `## Output Format Rules`. It
should come after the memory rules section.

**Step 4: Apply to your coding tool**

For Claude Code: format rules are honoured from CLAUDE.md natively. Claude Code
will apply the completion summary format after every task and follow the logging
code rules when writing observability code for your agent.

For Cursor: paste into `.cursorrules`. Cursor will apply the format to its
responses and follow the logging hygiene rules.

For Codex: add to the workspace system prompt.

**What you now have:** A coding agent that produces consistent, scannable output.
Every task ends with a structured summary. Every explanation is brief. Every
logging change it makes to your codebase follows the PII hygiene rules from
this document. You spend less time reading and more time reviewing what changed.

---

Copyright Janna AI Research Labs
