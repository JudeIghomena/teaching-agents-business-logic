# Build 01: Design the Handoff

**Frameworks applied:** 01 (Agent Mental Model) + 09 (Memory and State)

---

## The Problem This Solves

After Session 03, a student who has finished with Matteo must manually switch
to calling `/api/agent2/chat`. They need to know that Juli exists, that she
handles Monroe's Sequence, and that they should stop calling Matteo and start
calling Juli. None of this should be the student's responsibility.

The handoff design answers one question for each transition: what event
signals that this agent is done, and what data does the next agent need to
start?

Designing this before building the orchestrator is the right sequence. The
orchestrator is just an implementation of the handoff design. If the design
is clear, the code is straightforward. If the design is vague, the code
will be tangled.

---

## The Four-State Journey

A student's journey through the platform has four states:

```
MATTEO -> JULI -> TEDD -> COMPLETE
```

Each state corresponds to the agent that should respond to the student's
next message. The platform is responsible for knowing which state a student
is in. The student never needs to know.

| State | Agent responding | Entry condition | Exit condition |
|---|---|---|---|
| MATTEO | Matteo | New student or SCQ incomplete | All three SCQ elements confirmed |
| JULI | Juli | SCQ confirmed (all 3 elements) | Monroe's Sequence reached Action stage |
| TEDD | Tedd | Monroe's Sequence complete | Evaluation saved (finalised = 1) |
| COMPLETE | None | Tedd evaluation saved | Permanent |

---

## Deriving the Stage from Existing Data

No new database columns are required. The current stage can be derived from
the agent_sessions table, which already exists from Session 02.

The logic uses what you already have:

```js
export async function getCurrentStage(userId) {
  const teddSession = db
    .prepare(
      `SELECT finalised FROM agent_sessions
       WHERE user_id = ? AND agent_id = 'tedd'
       ORDER BY created_at DESC LIMIT 1`
    )
    .get(userId);

  if (teddSession?.finalised === 1) return 'COMPLETE';

  const juliSession = db
    .prepare(
      `SELECT messages FROM agent_sessions
       WHERE user_id = ? AND agent_id = 'juli'
       ORDER BY created_at DESC LIMIT 1`
    )
    .get(userId);

  if (juliSession) {
    const messages = JSON.parse(juliSession.messages || '{}');
    if (messages.current_stage === 'Action' && messages.action_sent) {
      return 'TEDD';
    }
    return 'JULI';
  }

  const matteoSession = db
    .prepare(
      `SELECT messages FROM agent_sessions
       WHERE user_id = ? AND agent_id = 'matteo'
       ORDER BY created_at DESC LIMIT 1`
    )
    .get(userId);

  if (matteoSession) {
    const messages = JSON.parse(matteoSession.messages || '{}');
    const scqComplete =
      messages.situation && messages.complication && messages.question;
    if (scqComplete) return 'JULI';
  }

  return 'MATTEO';
}
```

This function reads only from existing data. It does not write to the database.
The agent_sessions rows are the single source of truth.

---

## What Triggers Each Transition

### MATTEO to JULI

Matteo calls `save_scq_draft` up to three times: once each for situation,
complication, and question. After each call, the messages JSON in the Matteo
session is updated. The transition fires when all three keys are non-null.

The orchestrator checks this after every Matteo response by calling
`isStageComplete(userId, 'MATTEO')`:

```js
export function isStageComplete(userId, stage) {
  if (stage === 'MATTEO') {
    const session = db
      .prepare(
        `SELECT messages FROM agent_sessions
         WHERE user_id = ? AND agent_id = 'matteo'
         ORDER BY created_at DESC LIMIT 1`
      )
      .get(userId);

    if (!session) return false;
    const messages = JSON.parse(session.messages || '{}');
    return !!(messages.situation && messages.complication && messages.question);
  }

  if (stage === 'JULI') {
    const session = db
      .prepare(
        `SELECT messages FROM agent_sessions
         WHERE user_id = ? AND agent_id = 'juli'
         ORDER BY created_at DESC LIMIT 1`
      )
      .get(userId);

    if (!session) return false;
    const messages = JSON.parse(session.messages || '{}');
    return messages.current_stage === 'Action' && !!messages.action_sent;
  }

  if (stage === 'TEDD') {
    const session = db
      .prepare(
        `SELECT finalised FROM agent_sessions
         WHERE user_id = ? AND agent_id = 'tedd'
         ORDER BY created_at DESC LIMIT 1`
      )
      .get(userId);

    return session?.finalised === 1;
  }

  return false;
}
```

### JULI to TEDD

Juli's stage progression already works in Session 03: `parseJuliOutput`
extracts the `[STAGE: Action]` tag and the route updates `current_stage`.
The transition to TEDD fires when `current_stage === 'Action'` and the
Action-stage response has been sent to the student.

The `action_sent` flag is set by the orchestrator when it sends a Juli
response at the Action stage. This prevents the student from being moved
to TEDD before they have seen the final Action response from Juli.

### TEDD to COMPLETE

The transition fires when `finalised = 1` on the Tedd session row.
This is already set by `save_evaluation` in Session 03. No new code needed.

---

## What Data Passes at Each Handoff

### Matteo to Juli (the SCQ context)

Juli needs the confirmed SCQ so she can anchor her Monroe coaching to the
student's specific issue:

```js
export function getMatteoHandoff(userId) {
  const session = db
    .prepare(
      `SELECT messages FROM agent_sessions
       WHERE user_id = ? AND agent_id = 'matteo'
       ORDER BY created_at DESC LIMIT 1`
    )
    .get(userId);

  if (!session) return null;
  const messages = JSON.parse(session.messages || '{}');

  return {
    situation: messages.situation || null,
    complication: messages.complication || null,
    question: messages.question || null,
  };
}
```

This is injected into Juli's system prompt as the STUDENT'S CONFIRMED SCQ
block. Juli already has a placeholder for this in the stage injection pattern
from Session 03. The orchestrator fills it automatically instead of requiring
the student to paste it in.

### Juli to Tedd

Nothing explicit passes. Tedd evaluates the deliverable the student submits
directly. The student writes their final Monroe's Motivated Sequence
recommendation and sends it in the message body. Tedd receives it as the
user turn. No handoff data needed.

---

## The stageManager Module

Create `server/src/lib/stageManager.js` with three exports:
- `getCurrentStage(userId)` - returns one of: MATTEO, JULI, TEDD, COMPLETE
- `isStageComplete(userId, stage)` - returns boolean
- `getMatteoHandoff(userId)` - returns the confirmed SCQ object or null

This module is the only place in the codebase that contains stage logic.
Individual agent routes do not call these functions. Only the orchestrator does.

---

## What the CLAUDE.md Now Records

After completing this document, your CLAUDE.md records:

```
Stage State Machine:
  MATTEO -> JULI  when all 3 SCQ elements confirmed (non-null in messages JSON)
  JULI -> TEDD    when current_stage = 'Action' AND action_sent = true
  TEDD -> COMPLETE when finalised = 1 on Tedd session row

Stage source: derived from agent_sessions table, no new schema required
Module: server/src/lib/stageManager.js
  getCurrentStage(userId) -> 'MATTEO' | 'JULI' | 'TEDD' | 'COMPLETE'
  isStageComplete(userId, stage) -> boolean
  getMatteoHandoff(userId) -> { situation, complication, question } | null
```

---

## Using Claude Code Desktop App

Open your project folder in the Claude Code desktop app. Claude Code already
knows from your CLAUDE.md that agent_sessions holds the stage data and that
the messages column stores the JSON with situation, complication, question,
and current_stage fields.

**Prompt to build the stageManager:**

```
Create server/src/lib/stageManager.js with three exports for the SCQ platform.

This module derives the student's current stage from the existing agent_sessions
table. It does not write to the database and does not require schema changes.

getCurrentStage(userId):
  1. Check agent_sessions for a tedd row with finalised = 1 -> return 'COMPLETE'
  2. Check agent_sessions for a juli row. If current_stage = 'Action' and
     action_sent is true in messages JSON -> return 'TEDD'. If a juli row
     exists at all -> return 'JULI'
  3. Check agent_sessions for a matteo row. If messages has all three keys
     (situation, complication, question) as non-null strings -> return 'JULI'
  4. Default -> return 'MATTEO'

isStageComplete(userId, stage):
  MATTEO: true if matteo session messages has all 3 non-null SCQ fields
  JULI: true if juli session messages.current_stage = 'Action' and action_sent = true
  TEDD: true if tedd session finalised = 1
  Any other stage: false

getMatteoHandoff(userId):
  Returns { situation, complication, question } from the most recent matteo
  session messages column. Returns null if no matteo session exists.

All queries must scope by user_id. Use parameterised statements only.
No string concatenation in SQL.
```

**What Claude Code will do:**
Create `server/src/lib/stageManager.js` reading the existing db.js singleton,
implementing all three functions with correct scoped queries, and exporting them
as named exports.

**Tips for this document:**
- Ask Claude Code: "Show me the current shape of the messages JSON in a Matteo
  session and a Juli session." This confirms it is reading the right fields
  before building the orchestrator in the next document.
- If `getCurrentStage` always returns MATTEO even after SCQ is complete, ask
  Claude Code: "Is the messages JSON being parsed before checking the SCQ
  fields? Show me the JSON.parse call."
- Tell Claude Code: "Do not add a stage column to any table. The stage is
  derived from existing data only."

---

**Next:** [02-build-the-orchestrator.md](02-build-the-orchestrator.md)

---

Copyright Janna AI Research Labs
