# Assignment 03: Manage Cross-Agent Context

**Reads with:** [03-manage-cross-agent-context.md](../03-manage-cross-agent-context.md)
**Time estimate:** 30-40 minutes
**Frameworks applied:** 09 (Memory and State) + 04 (Context Window Budget)

---

## What You Are Building

The context injection path from Matteo's confirmed SCQ to Juli's system
prompt. The orchestrator reads the SCQ from Matteo's session and passes it
to `callJuli`. Juli formats it into the context block she needs.

---

## Steps

### Step 1: Update callJuli in agentCaller.js

The `callJuli` function already accepts `scqContext` as its second argument.
Confirm that it:

- Reads `current_stage` from the Juli session messages
- Calls `buildJuliContext(currentStage, scqContext)` to format the context
- Passes the result as `injected_context` in the agent input JSON

The `buildJuliContext` function must omit the STUDENT'S CONFIRMED SCQ block
if `scqContext` is null or all fields are null. Juli's system prompt handles
missing SCQ gracefully by asking the student to describe their issue.

### Step 2: Confirm the orchestrator passes getMatteoHandoff

In `orchestrator.js`, the context is built as:

```js
const context = stage === 'JULI' ? getMatteoHandoff(user.id) : null;
```

Confirm this line is present and that `getMatteoHandoff` is imported from
`stageManager.js`.

### Step 3: Add MAX_SCQ_FIELD_LENGTH protection

In `.env`, add:

```
MAX_SCQ_FIELD_LENGTH=500
```

In `agentCaller.js`, before building the SCQ block, truncate each field:

```js
const maxLen = parseInt(process.env.MAX_SCQ_FIELD_LENGTH || '500');
const situation = (scq?.situation || '').slice(0, maxLen);
```

### Step 4: Verify the context injection with a live test

1. Complete Matteo with a student account: confirm all three SCQ fields
2. Send a message to POST /api/chat
3. The stage should now be JULI
4. Read the server logs: look for the injected_context field in the agent
   input JSON log. Confirm it contains the student's actual situation text.

If Juli responds generically without referencing the student's issue, the
context is not being injected. Add a `console.log(injectedContext)` in
`callJuli` before the spawn call to confirm the value.

### Step 5: Check the context budget

Open the build document's context budget table. Juli's system prompt is
max 3,000 tokens. With a full SCQ injected, the context block adds up to
~350 tokens. The history budget drops to 13,650.

Confirm the `MAX_HISTORY_TOKENS` constant in Juli's route (or the equivalent)
is not set higher than 13,650. If there is no such constant and the history
is sent in full, you may exceed the budget on long conversations.

---

## Done Checklist

- [ ] `buildJuliContext` is present in agentCaller.js
- [ ] Context block is omitted when scqContext has no non-null fields
- [ ] The orchestrator calls `getMatteoHandoff(user.id)` for JULI stage
- [ ] `MAX_SCQ_FIELD_LENGTH` is in `.env` and `.env.example`
- [ ] Truncation is applied to each SCQ field before injection
- [ ] Live test confirms Juli references the student's specific situation
- [ ] Context budget documented: Juli budget accounts for ~350 injected tokens

---

## Troubleshooting

Juli coaches in generic terms and ignores the student's SCQ: The context
injection is not reaching the Python agent. Log `injectedContext` in
`callJuli` and confirm it has content. Then check that `injected_context`
is included in the JSON written to `python.stdin`.

buildJuliContext returns an empty string: Check that `scqContext` is not
null when `callJuli` is invoked for the JULI stage. In the orchestrator,
add `console.log('context passed to Juli:', context)` before the agent call.

getMatteoHandoff returns null even after Matteo confirms the SCQ: Matteo's
`save_scq_draft` tool updates the messages JSON in the agent_sessions row.
Open the database and check the messages column directly:
`SELECT messages FROM agent_sessions WHERE agent_id = 'matteo' AND user_id = 'your-id';`
If the fields are not there, the tool call is not persisting to the database.

---

**Next assignment:** [04-test-agent-coordination.md](04-test-agent-coordination.md)
