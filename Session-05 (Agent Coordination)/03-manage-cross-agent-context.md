# Build 03: Manage Cross-Agent Context

**Frameworks applied:** 09 (Memory and State) + 04 (Context Window Budget)

---

## The Context Problem

In Session 03, each agent route handled its own context injection. Matteo's
route read the confirmed SCQ from the database and appended CURRENT SESSION
CONTEXT to the system prompt. Juli's route read the SCQ from Matteo's session
and the current Monroe stage and appended both.

This worked when routes were independent. Now that the orchestrator calls
agents, there is a single place responsible for all context loading. This
document defines exactly what context each agent receives, where it comes
from, and how it is formatted.

Getting this right matters for two reasons:

First, correctness: Juli cannot coach the student on Monroe's Sequence without
knowing their confirmed business issue. If the SCQ context is missing or
incorrectly formatted, Juli will coach in a vacuum.

Second, budget: every token added to the system prompt is a token not available
for conversation history. The context window budget from Session 01 (Framework 04)
applies here: you must account for the orchestrator's added overhead and confirm
the total still fits within the per-agent budget.

---

## The Cross-Agent Context Schema

Define the context each agent receives as a typed contract. The orchestrator
builds this object and passes it to the appropriate agent caller function.

```js
// Context passed to Matteo
// null - Matteo does not need any cross-agent context
// (Matteo reads its own confirmed elements directly from the DB)

// Context passed to Juli
{
  scq: {
    situation: string | null,    // from getMatteoHandoff(userId)
    complication: string | null,
    question: string | null,
  },
  currentStage: string,          // from Juli's own session messages
}

// Context passed to Tedd
// null - Tedd evaluates the message directly, no prior agent context needed
```

This schema makes the dependencies explicit. Juli depends on Matteo's output.
Tedd depends on nothing. Matteo depends on nothing outside its own session.

---

## How Context Is Retrieved

All cross-agent context comes from the existing agent_sessions table.
No new tables are needed.

The retrieval logic lives in `stageManager.js` (from Build 01) and is
called by `agentCaller.js`:

```js
// In agentCaller.js, callJuli:
export async function callJuli(message, scqContext, user, res) {
  // scqContext was passed in from orchestrator.js:
  // const context = stage === 'JULI' ? getMatteoHandoff(user.id) : null;

  const session = getOrCreateSession(user.id, 'juli', user.cohortId);
  const messages = JSON.parse(session.messages || '{}');
  const currentStage = messages.current_stage || 'Attention';

  // Build the combined context block
  const injectedContext = buildJuliContext(currentStage, scqContext);

  await streamAgent('agent2', message, messages.turns || [], injectedContext, user, session, res);
}
```

The `buildJuliContext` function formats both pieces into the block Juli's
system prompt expects:

```js
function buildJuliContext(currentStage, scq) {
  let context = `\n\nCURRENT SESSION CONTEXT\nActive stage: ${currentStage}`;

  if (scq?.situation) {
    context += `\n\nSTUDENT'S CONFIRMED SCQ`;
    context += `\nSituation: ${scq.situation}`;
    if (scq.complication) context += `\nComplication: ${scq.complication}`;
    if (scq.question) context += `\nQuestion: ${scq.question}`;
  }

  return context;
}
```

---

## Context Budget After Orchestrator

The context window budget from Session 01 must be updated to account for the
orchestrator's cross-agent injection. The new numbers:

| Agent | System prompt | Injected context | History budget | Buffer |
|---|---|---|---|---|
| Matteo | max 3,000 | ~80 (SCQ state, same as before) | max 13,920 | 3,000 |
| Juli | max 3,000 | ~350 (stage + full SCQ) | max 13,650 | 3,000 |
| Tedd | max 4,000 | 0 (no cross-agent context) | min (one shot) | 16,000 |

Juli's injected context grew from ~230 tokens (Session 03) to ~350 tokens
because the full confirmed SCQ text (three fields, potentially several
sentences each) is injected alongside the active stage. The history budget
decreases by 120 tokens to compensate. This is acceptable: Juli's
conversations are typically shorter than Matteo's because each stage has
a defined scope.

To verify the actual token count of the injected context:

```bash
python3 evaluation/measure_prompt.py --agent juli --include-context
```

If the injected context exceeds 400 tokens for any student session, review
the SCQ text. Students occasionally write extremely long situation descriptions.
Add a `MAX_SCQ_FIELD_LENGTH` environment variable (default 500 characters) and
truncate fields that exceed it before injection.

---

## What Only the Orchestrator Can Write

Context flows in one direction only: downward from the orchestrator to the
agent. Individual agents never write to each other's sessions.

Matteo writes to the Matteo session (via `save_scq_draft`).
Juli writes to the Juli session (via stage advancement in the route).
Tedd writes to the Tedd session (via `save_evaluation`).

The orchestrator reads from Matteo's session and passes the result to Juli.
It does not write to Juli's session on Matteo's behalf. This keeps the
ownership boundary clean: each agent writes only its own state.

If you find code that writes to one agent's session from another agent's
context, it is a boundary violation and should be removed.

---

## Handling Missing Context Gracefully

Juli can technically be called before Matteo has confirmed all three SCQ
elements. This should not happen if stage logic is working correctly (a student
in the MATTEO stage is never routed to Juli), but defensive code handles it.

If `getMatteoHandoff(userId)` returns null or returns an object with all null
fields, `buildJuliContext` omits the STUDENT'S CONFIRMED SCQ block:

```js
function buildJuliContext(currentStage, scq) {
  let context = `\n\nCURRENT SESSION CONTEXT\nActive stage: ${currentStage}`;

  const hasScq = scq?.situation || scq?.complication || scq?.question;
  if (hasScq) {
    context += `\n\nSTUDENT'S CONFIRMED SCQ`;
    if (scq.situation) context += `\nSituation: ${scq.situation}`;
    if (scq.complication) context += `\nComplication: ${scq.complication}`;
    if (scq.question) context += `\nQuestion: ${scq.question}`;
  }

  return context;
}
```

Juli's system prompt already handles missing SCQ context gracefully: she asks
the student to describe their business issue before beginning the Monroe
coaching. This is the correct fallback.

---

## Using Claude Code Desktop App

Open your project folder in the Claude Code desktop app. Claude Code already
knows the context injection pattern from your CLAUDE.md's Stage Progression
section and the injected context field names.

**Prompt to wire cross-agent context:**

```
Update the SCQ platform to inject cross-agent context through the orchestrator.

1. In server/src/lib/agentCaller.js, update callJuli to accept scqContext as
   its second argument. Build the injected context using both:
   - currentStage from the Juli session messages column
   - scqContext passed in from the orchestrator

   Format the combined context as:
   \n\nCURRENT SESSION CONTEXT\nActive stage: {currentStage}
   \n\nSTUDENT'S CONFIRMED SCQ\nSituation: {sit}\nComplication: {comp}\nQuestion: {q}

   Only include the SCQ block if at least one SCQ field is non-null.

2. In server/src/routes/orchestrator.js, confirm that callJuli is called with
   getMatteoHandoff(user.id) as the second argument when stage is JULI.

3. Add a MAX_SCQ_FIELD_LENGTH env variable (default 500). Before building the
   SCQ block, truncate each field to MAX_SCQ_FIELD_LENGTH characters if it
   exceeds the limit. Log a warning when truncation occurs.

4. Update the context window budget comment in CLAUDE.md to reflect Juli's
   new injected context size: ~350 tokens instead of ~230.

Do not change any agent system prompts. The context is injected by the
orchestrator, not by modifying the prompt files.
```

**What Claude Code will do:**
Update `callJuli` to receive and format the SCQ context, update the
orchestrator to pass `getMatteoHandoff`, add the truncation safety, and
update the CLAUDE.md budget table.

**Tips for this document:**
- After wiring the context, start a conversation as a student. Complete Matteo
  (confirm all three SCQ elements). Then send one message to `/api/chat`.
  Confirm Juli's first response references the student's specific situation.
  If she speaks in generic terms, the SCQ context is not being injected.
- Ask Claude Code: "Log the injected context string to the console before
  passing it to the agent. What does it look like for a student with all
  three SCQ fields confirmed?" Read the log to verify the format.
- Tell Claude Code: "Do not store the SCQ context anywhere inside the Juli
  session. It is read from the Matteo session on every request. This is
  correct and intentional."

---

**Next:** [04-test-agent-coordination.md](04-test-agent-coordination.md)

---

Copyright Janna AI Research Labs
