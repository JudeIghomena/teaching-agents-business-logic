# Assignment 02: Build Juli's Five-Stage Coaching System

**Covers:** Build 02 (02-build-juli.md)
**Time estimate:** 45-60 minutes
**Done when:** Juli responds to a student message with a stage-tagged coaching prompt AND stage advance logic updates the database

---

## What You Are Building

Juli's route exists from Session 02 but she has no system prompt and no stage
logic. This assignment gives her a complete five-section system prompt, wires
in the SCQ context from Matteo, and adds stage progression tracking.

By the end of this assignment, Juli can:
- Coach a student through Monroe's Motivated Sequence one stage at a time
- Return a [STAGE: StageName] tag that the web layer uses to advance the student
- Receive the student's completed Matteo SCQ as context every turn

---

## Before You Start

Confirm these are true:
- [ ] Assignment 01 is complete (Matteo tools working, stage injection in place)
- [ ] A student user exists in the database (created during Session 02)
- [ ] routes/agent2.js stub exists from Session 02

---

## Steps

### Step 1: Write juli_v1.txt

Use the system prompt template from Build 02. Save it as agent/prompts/juli_v1.txt.

Key things to confirm are in the prompt:
- ROLE specifies Monroe's Motivated Sequence by name
- RULES include the three-step reasoning block
- FORMAT specifies the [STAGE: StageName] tag requirement exactly
- ESCALATION section matches Matteo's

Count tokens after saving:
```bash
python -c "import anthropic; c=anthropic.Anthropic(); r=c.messages.count_tokens(model='claude-haiku-4-5-20251001', system=open('agent/prompts/juli_v1.txt').read(), messages=[{'role':'user','content':'test'}]); print(r.input_tokens, 'tokens')"
```
Must be under 3,000. Trim description paragraphs if needed.

### Step 2: Add stage injection to routes/agent2.js

In routes/agent2.js, after loading the base system prompt:

```js
const session = await db.getJuliSession(req.user.id);
const stage = session?.current_stage ?? 'Attention';

const stageContext = `\nCURRENT SESSION CONTEXT\nActive stage: ${stage}\nFocus your coaching on the student's work at the ${stage} stage.\nDo not advance to the next stage. The student signals when they are ready.`;
```

### Step 3: Add SCQ context injection

After stage injection, add the SCQ block:

```js
const scqProgress = await db.getStudentProgress(req.user.id);
const scqBlock = scqProgress?.question
    ? `\nSTUDENT'S CONFIRMED SCQ\nSituation: ${scqProgress.situation}\nComplication: ${scqProgress.complication}\nQuestion: ${scqProgress.question}`
    : `\nNote: Student has not yet completed Matteo's SCQ coaching.`;

const systemPrompt = baseSystemPrompt + stageContext + scqBlock;
```

### Step 4: Add db.getJuliSession to db.js

```js
function getJuliSession(userId) {
    return db.prepare(
        "SELECT * FROM agent_sessions WHERE user_id = ? AND agent_id = 'juli' ORDER BY created_at DESC LIMIT 1"
    ).get(userId);
}
```

### Step 5: Add stage advance logic

After parseJuliOutput runs on the complete response, check if the stage tag
signals an advance:

```js
const STAGE_ORDER = ['Attention', 'Need', 'Satisfaction', 'Visualisation', 'Action'];

const { content, stage } = parseJuliOutput(fullResponse);
if (stage) {
    const currentIndex = STAGE_ORDER.indexOf(currentStage);
    const nextIndex = STAGE_ORDER.indexOf(stage);
    if (nextIndex === currentIndex + 1) {
        db.prepare(
            "UPDATE agent_sessions SET messages = json_set(COALESCE(messages, '{}'), '$.current_stage', ?) WHERE user_id = ? AND agent_id = 'juli'"
        ).run(stage, req.user.id);
    }
}
```

Stages must advance one step at a time. A jump from Attention to Satisfaction
is rejected (nextIndex !== currentIndex + 1).

### Step 6: Test it

```bash
curl -X POST http://localhost:3001/api/agent2/chat \
  -H "Authorization: Bearer YOUR_STUDENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to start my Attention stage with a story about a branch closure."}' \
  --no-buffer
```

The response must end with [STAGE: Attention] (or another valid stage name).

---

## Done Checklist

- [ ] agent/prompts/juli_v1.txt exists and is under 3,000 tokens
- [ ] routes/agent2.js injects CURRENT SESSION CONTEXT and STUDENT'S CONFIRMED SCQ
- [ ] Every Juli response ends with a [STAGE: StageName] tag
- [ ] Stage advance updates the database one step at a time
- [ ] Stage cannot jump more than one step (Attention to Satisfaction rejected)

---

## Troubleshooting

**Juli's response does not include a [STAGE: ...] tag:**
The FORMAT section of juli_v1.txt may not be specific enough. Open the prompt
and confirm the exact tag format is shown: [STAGE: StageName] on its own line.
Add the word "exactly" before "on its own line" to reinforce it.

**Stage advance writes to DB but getJuliSession returns old stage:**
Check that you are reading the most recent session, not all sessions.
The query must have ORDER BY created_at DESC LIMIT 1.

**SCQ block shows "Not yet confirmed" even though Matteo session exists:**
Confirm that db.getStudentProgress uses the same user_id format.
Print req.user.id and the user_id stored in agent_sessions to compare.

---

**Next:** [03-build-tedd.md](03-build-tedd.md)

---

Copyright Janna AI Research Labs
