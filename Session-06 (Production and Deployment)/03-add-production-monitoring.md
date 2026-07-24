# Build 03: Add Production Monitoring

**Frameworks applied:** 10 (Observability) + 01 (Agent Mental Model)

---

## What to Monitor and Why

In Session 01, Framework 10 introduced the TurnTrace for logging individual
agent turns. In development, you read logs to understand what the agent is
doing. In production, you read logs to understand what went wrong and when.

Four metrics determine whether the platform is working well for students:

| Metric | Why it matters | Alert if |
|---|---|---|
| Error rate | Broken sessions drive students away | > 5% of requests in 5 minutes |
| Time-to-first-token | Students perceive latency before the stream starts | > 4 seconds p95 |
| Input tokens per turn | Rising input tokens means history is not being trimmed | > 3,000 per turn |
| Tool call failure rate | A failed tool call usually produces an incorrect agent response | > 2% |

These four metrics are observable from the logs you already generate. This
document adds the measurements you are missing: time-to-first-token, token
counts extracted from the SSE stream, and an in-process error counter.

---

## Extended TurnTrace

Session 05 extended TurnTrace with stage coordination fields. Session 06
extends it with performance and cost fields:

```js
{
  // From Session 01
  turn_id: string,
  agent_id: string,
  user_id: string,
  tool_calls: array,

  // From Session 05
  stage_before: string,
  agent_selected: string,
  stage_after: string,
  context_tokens: number,

  // New in Session 06
  input_tokens: number,      // from Anthropic usage field
  output_tokens: number,     // from Anthropic usage field
  time_to_first_token_ms: number,  // ms between SSE start and first token
  total_latency_ms: number,  // ms from request to done event
  error: boolean,            // true if agent exited non-zero
}
```

The Anthropic API returns token counts in the `usage` field of the final
message event in the stream. The Python agent already receives this. Pass
it back in the SSE `done` event:

Update `agent/runner.py` to extract token counts from the streaming response
and include them in the completion output:

```python
input_tokens = 0
output_tokens = 0

for event in response:
    if hasattr(event, 'usage') and event.usage:
        input_tokens = getattr(event.usage, 'input_tokens', 0)
        output_tokens = getattr(event.usage, 'output_tokens', 0)

# Write token counts to stdout as a final JSON line after the stream ends
import json, sys
sys.stdout.write(f'\n__USAGE__:{json.dumps({"input_tokens": input_tokens, "output_tokens": output_tokens})}\n')
sys.stdout.flush()
```

In `server/src/lib/agentCaller.js`, parse the usage line in the stdout
handler and include it in the `done` event:

```js
let usageData = null;
const USAGE_PREFIX = '__USAGE__:';

python.stdout.on('data', (chunk) => {
  const text = chunk.toString();
  if (text.includes(USAGE_PREFIX)) {
    const usageLine = text.split(USAGE_PREFIX)[1];
    try { usageData = JSON.parse(usageLine.trim()); } catch {}
    // Do not stream the usage line to the client
    const tokensBefore = text.split(USAGE_PREFIX)[0];
    if (tokensBefore) {
      fullResponse += tokensBefore;
      res.write(`data: ${JSON.stringify({ token: tokensBefore })}\n\n`);
    }
  } else {
    fullResponse += text;
    res.write(`data: ${JSON.stringify({ token: text })}\n\n`);
  }
});
```

---

## Time-to-First-Token Measurement

Time-to-first-token is the delay between when the HTTP request arrives and
when the first SSE token is sent. It is the most noticeable latency for
students because the interface appears frozen until streaming starts.

Measure it in `streamAgent`:

```js
const requestStart = Date.now();
let firstTokenSent = false;
let timeToFirstToken = null;

python.stdout.on('data', (chunk) => {
  if (!firstTokenSent) {
    timeToFirstToken = Date.now() - requestStart;
    firstTokenSent = true;
  }
  // ... existing streaming logic
});

python.stdout.on('end', () => {
  const totalLatency = Date.now() - requestStart;

  console.log(JSON.stringify({
    event: 'turn_complete',
    agent_id: agentId,
    user_id: user.id,
    input_tokens: usageData?.input_tokens || 0,
    output_tokens: usageData?.output_tokens || 0,
    time_to_first_token_ms: timeToFirstToken,
    total_latency_ms: totalLatency,
    timestamp: new Date().toISOString(),
  }));

  // ... existing appendTurn and done event logic
});
```

---

## In-Process Error Rate Tracking

An in-process counter tracks the number of requests and errors in the last
N minutes. When the error rate exceeds the threshold, a WARNING is logged.

Create `server/src/lib/errorTracker.js`:

```js
const WINDOW_MS = 5 * 60 * 1000; // 5 minutes
const ALERT_THRESHOLD = 0.05;     // 5% error rate

const events = []; // { timestamp, isError }

export function recordRequest(isError) {
  const now = Date.now();
  events.push({ timestamp: now, isError });

  // Trim events older than the window
  while (events.length > 0 && events[0].timestamp < now - WINDOW_MS) {
    events.shift();
  }

  const total = events.length;
  const errors = events.filter(e => e.isError).length;
  const rate = total > 0 ? errors / total : 0;

  if (total >= 10 && rate >= ALERT_THRESHOLD) {
    console.warn(JSON.stringify({
      event: 'error_rate_alert',
      error_rate: rate.toFixed(3),
      errors_in_window: errors,
      total_in_window: total,
      window_minutes: WINDOW_MS / 60000,
      timestamp: new Date().toISOString(),
    }));
  }
}
```

Call `recordRequest(false)` at the end of every successful agent turn.
Call `recordRequest(true)` whenever the Python agent exits with non-zero
or an unhandled error reaches the orchestrator's catch block.

---

## The Extended Health Endpoint

Update GET /api/health to include last-5-minute error stats:

```js
import { getErrorStats } from '../lib/errorTracker.js';

router.get('/health', (req, res) => {
  try {
    const db = getDb();
    db.prepare('SELECT 1').get();
    const stats = getErrorStats();
    res.json({
      status: 'ok',
      db: 'ok',
      version: process.env.npm_package_version || '0.6.0',
      node_env: process.env.NODE_ENV || 'development',
      last_5min: stats,
    });
  } catch (err) {
    console.error('[health] db check failed:', err.message);
    res.status(503).json({ status: 'error', db: 'unavailable' });
  }
});
```

Add `getErrorStats()` to `errorTracker.js`:

```js
export function getErrorStats() {
  const now = Date.now();
  const recent = events.filter(e => e.timestamp >= now - WINDOW_MS);
  const total = recent.length;
  const errors = recent.filter(e => e.isError).length;
  return {
    requests: total,
    errors,
    error_rate: total > 0 ? (errors / total).toFixed(3) : '0.000',
  };
}
```

---

## Using Claude Code Desktop App

Open your project folder in the Claude Code desktop app. Claude Code already
knows the streamAgent pattern and the TurnTrace structure from CLAUDE.md.

**Prompt to add production monitoring:**

```
Add production monitoring to the SCQ platform.

1. In agent/runner.py, extract the input_tokens and output_tokens from the
   streaming response usage field. After the stream completes, write a single
   line to stdout in this format:
   __USAGE__:{"input_tokens": N, "output_tokens": N}
   This must come after all streaming output so the client receives the full
   response before we append the usage line.

2. In server/src/lib/agentCaller.js (the streamAgent function):
   - Track requestStart = Date.now() at the top
   - Track firstTokenSent boolean and timeToFirstToken
   - In the stdout 'data' handler: on first chunk, set timeToFirstToken
   - Parse the __USAGE__: prefix line and store as usageData
   - Do NOT stream the usage line to the client
   - In the stdout 'end' handler, log a structured turn_complete JSON line
     with agent_id, user_id, input_tokens, output_tokens,
     time_to_first_token_ms, total_latency_ms, and timestamp

3. Create server/src/lib/errorTracker.js with two exports:
   - recordRequest(isError): adds an event to a sliding 5-minute window,
     logs a warning when error rate exceeds 5% and there are at least 10 events
   - getErrorStats(): returns { requests, errors, error_rate } for the window

4. In the orchestrator's error handler, call recordRequest(true).
   In the stdout 'end' handler of streamAgent, call recordRequest(false).

5. In server/src/routes/health.js, import getErrorStats and add last_5min
   to the JSON response body.
```

**What Claude Code will do:**
Update the Python runner to emit token counts, update streamAgent to parse
them and log structured metrics, create the errorTracker module, wire it into
the orchestrator, and extend the health endpoint.

**Tips for this document:**
- Test the token extraction by starting a student session and checking the
  server logs for a turn_complete event with non-zero input_tokens.
- If time_to_first_token_ms is always null, confirm the firstTokenSent flag
  is reset to false before each spawn call. If it is a module-level variable
  instead of a per-call variable, it stays true after the first call and never
  records for subsequent calls.
- Tell Claude Code: "The __USAGE__ line must NOT be sent to the client SSE
  stream. It is an internal signal. Strip it from the output before writing
  any remaining content to res."

---

**Next:** [04-control-costs.md](04-control-costs.md)

---

Copyright Janna AI Research Labs
