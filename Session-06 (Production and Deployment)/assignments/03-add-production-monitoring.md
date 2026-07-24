# Assignment 03: Add Production Monitoring

**Reads with:** [03-add-production-monitoring.md](../03-add-production-monitoring.md)
**Time estimate:** 40-50 minutes
**Frameworks applied:** 10 (Observability) + 01 (Agent Mental Model)

---

## What You Are Building

Extended TurnTrace logging with token counts and time-to-first-token. An
in-process error tracker that alerts when the error rate in the last five
minutes exceeds 5%. An extended health endpoint that surfaces these stats.

---

## Steps

### Step 1: Emit token counts from the Python agent

Update `agent/runner.py` to write a usage line after the stream completes:

```python
sys.stdout.write(f'\n__USAGE__:{json.dumps({"input_tokens": input_tokens, "output_tokens": output_tokens})}\n')
sys.stdout.flush()
```

The `__USAGE__:` prefix marks the line as metadata, not agent output.
It must come after all streaming content so the client receives the full
response before the metadata appears.

### Step 2: Parse the usage line in agentCaller.js

In the `streamAgent` function, update the stdout handler to:
- Track `firstTokenSent` and `timeToFirstToken`
- Detect the `__USAGE__:` prefix line and store the parsed JSON as `usageData`
- Not stream the usage line to the client (strip it before writing to res)

In the stdout `end` handler, log the structured turn_complete event as shown
in the build document.

### Step 3: Create errorTracker.js

Create `server/src/lib/errorTracker.js` with `recordRequest` and `getErrorStats`.

The sliding window must be 5 minutes. The alert threshold must be 5%.
The alert must fire only when there are at least 10 events in the window
(to avoid spurious alerts on startup with one request and one error).

### Step 4: Wire the error tracker

In `orchestrator.js`, call `recordRequest(true)` in the catch block.
In `streamAgent`, call `recordRequest(false)` in the stdout `end` handler.

### Step 5: Extend the health endpoint

Import `getErrorStats` and add `last_5min` to the health response. Test it:

```bash
curl http://localhost:3001/api/health
```

Expected addition to the response:

```json
"last_5min": { "requests": 3, "errors": 0, "error_rate": "0.000" }
```

### Step 6: Verify monitoring with a live student session

Start a session as a student. Send three messages to POST /api/chat.
In the server logs, confirm you see:
- A `turn_complete` JSON log line for each message
- Non-zero `input_tokens` and `output_tokens` on each line
- A non-null `time_to_first_token_ms` on each line

---

## Done Checklist

- [ ] Python agent emits `__USAGE__:` line at end of each response
- [ ] agentCaller.js strips the usage line from the SSE stream
- [ ] `turn_complete` log event includes input_tokens, output_tokens, time_to_first_token_ms, total_latency_ms
- [ ] `server/src/lib/errorTracker.js` with recordRequest and getErrorStats
- [ ] recordRequest(true) called in orchestrator catch block
- [ ] recordRequest(false) called in stdout 'end' handler
- [ ] Health endpoint returns last_5min stats
- [ ] Live test confirms turn_complete logs appear with non-zero token counts

---

## Troubleshooting

Token counts are always 0: The Python stream ends before the usage field is
populated. Check that `for event in response` iterates all events including
the final `message_delta` type which carries the usage. Add a print to
stderr in Python to see what event types are arriving.

__USAGE__ line appears in the student's SSE stream: The split logic is not
stripping the prefix line before writing to res. Confirm the 'data' handler
splits on `__USAGE__:` and only streams the content before that marker.

errorTracker always shows error_rate 0.000 even after a failure: Confirm
`recordRequest(true)` is being called. Add a temporary `console.log` inside
`recordRequest` to confirm it receives `isError = true` after an agent
process exits with non-zero code.

time_to_first_token_ms is always null: The `firstTokenSent` variable may
be declared outside the function scope and carry state across calls. Move
the declaration inside the `streamAgent` function body so each call gets
a fresh variable.

---

**Next assignment:** [04-control-costs.md](04-control-costs.md)
