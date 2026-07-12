# Assignment 10: Add Observability

**What you are building:** Structured logging and a turn trace that records every agent interaction with enough detail to debug failures without guessing
**Why it matters:** When your agent gives a wrong answer or calls the wrong tool in production, you need to know exactly what it received, what it decided, and what it returned. Without structured logs you are guessing. With them you can replay any failure in under five minutes.
**Time estimate:** 30 minutes
**Reads with:** 10-observability.md

---

## What You Are Going To Do

You are going to add structured logging to your agent loop, create a TurnTrace record for every interaction, and set up a simple log output that captures what you need to debug any failure.

---

## What to Log and What Not to Log

Log these:
- Every tool call: name, arguments, result status
- Turn start and end: timestamp, message length, stop reason
- Token counts: input tokens, output tokens
- Errors: full error with context

Never log these:
- The content of secret environment variables
- Full user messages if they may contain PII
- Raw API responses from third-party services
- Passwords, tokens, or keys of any kind

---

## Step 1: Create the TurnTrace Dataclass

Add a trace structure to `agent/infrastructure.py`:

```python
# Add to agent/infrastructure.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class TurnTrace:
    turn_id: str
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    message_length: int = 0
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    tool_calls: list = field(default_factory=list)
    stop_reason: str = ""
    error: Optional[str] = None
    duration_ms: int = 0

    def log(self):
        logger = get_logger()
        logger.info("turn_complete", extra={
            "turn_id": self.turn_id,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "tool_calls": self.tool_calls,
            "stop_reason": self.stop_reason,
            "duration_ms": self.duration_ms,
            "error": self.error
        })
```

---

## Step 2: Instrument Your Agent Loop

Update `agent/runner.py` to populate a TurnTrace for every call:

```python
import time
import uuid
from agent.infrastructure import TurnTrace

def run_agent_loop(user_message: str, history: list = None) -> str:
    history = history or []
    trace = TurnTrace(
        turn_id=str(uuid.uuid4())[:8],
        message_length=len(user_message),
        model=MODEL
    )
    start = time.time()

    try:
        system = build_system_message()
        messages = trim_history(history) + [{"role": "user", "content": user_message}]
        client = get_client()

        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system,
            tools=TOOLS,
            messages=messages
        )

        trace.input_tokens = response.usage.input_tokens
        trace.output_tokens = response.usage.output_tokens
        trace.stop_reason = response.stop_reason

        while response.stop_reason == "tool_use":
            tool_calls = [b for b in response.content if b.type == "tool_use"]
            tool_results = []

            for call in tool_calls:
                fn = TOOL_DISPATCH.get(call.name)
                result = fn(**call.input) if fn else {"error": f"Unknown tool: {call.name}"}
                trace.tool_calls.append({
                    "name": call.name,
                    "success": "error" not in result
                })
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": call.id,
                    "content": str(result)
                })

            messages = messages + [
                {"role": "assistant", "content": response.content},
                {"role": "user", "content": tool_results}
            ]
            response = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=system,
                tools=TOOLS,
                messages=messages
            )
            trace.stop_reason = response.stop_reason

        return response.content[0].text

    except Exception as e:
        trace.error = str(e)
        raise

    finally:
        trace.duration_ms = int((time.time() - start) * 1000)
        trace.log()
```

---

## Step 3: Set Alert Thresholds in Your CLAUDE.md

Add output format rules to your CLAUDE.md:

```
## Output Format and Observability

Logging rule: log every tool call with name and success/failure status.
Never log secrets, full user messages containing PII, or raw API responses.

Alert thresholds (investigate if these are hit):
- Response time above 8,000 ms: model may be overloaded or prompt too long
- Input tokens above 80% of context limit: history trimming may be failing
- Tool call failure rate above 10% in one session: tool implementation has a bug
- stop_reason = "max_tokens" more than once per session: MAX_TOKENS is too low

Test failure protocol: stop immediately, log the failure with turn_id,
do not return a partial response, surface the error cleanly to the user.
```

---

## Step 4: Run and Review a Log

Run your agent, send three messages including one that triggers a tool, then review what was logged:

```bash
python main.py 2>&1 | grep "turn_complete"
```

You should see one JSON log line per turn showing token counts, tool calls, stop reason, and duration. If you do not see it, check that `trace.log()` is being called in the `finally` block.

---

## Step 5: Simulate a Slow Turn

Add a deliberate delay to one tool to test what a slow response looks like in your logs:

```python
import time

def get_order_status(order_id: str) -> dict:
    time.sleep(2)  # Simulate a slow API call
    return {"order_id": order_id, "status": "shipped"}
```

Run the agent, check the log. You should see `duration_ms` above 2000. Remove the sleep after confirming the log captures it correctly.

---

## You Are Done When

- [ ] `TurnTrace` dataclass is in infrastructure.py
- [ ] `run_agent_loop` populates and logs a trace for every turn
- [ ] Token counts appear in every log line
- [ ] Tool call names and success/failure appear in the log
- [ ] Duration in milliseconds appears in the log
- [ ] Your CLAUDE.md has alert thresholds and a test failure protocol
- [ ] No secrets or raw user messages appear in any log line

---

## If You Get Stuck

`extra` fields not appearing in log output: your logger may not be configured to include extra fields. Switch to `print(json.dumps(vars(trace)))` temporarily to confirm the trace is being populated.

`usage` attribute missing on response: you may be using an older version of the Anthropic SDK. Run `pip install --upgrade anthropic`.

Duration is always 0: the `finally` block must run even when an exception is raised. Confirm the `start = time.time()` line runs before the try block, not inside it.

---

## Next Assignment

[11-run-a-security-audit.md](11-run-a-security-audit.md)

---

Copyright Janna AI Research Labs
