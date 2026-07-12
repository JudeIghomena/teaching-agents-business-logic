# Build 02: Building Juli

> Framework 07 (System Prompt Skeleton) gives you the structure.
> Framework 04 (Context Window Budget) tells you how much room you have.
> Juli coaches across five stages. Her prompt must work at stage one
> and at stage five without running out of context for history.

**Applies:** Framework 07 (System Prompt Skeleton) + Framework 04 (Context Window Budget)
**Builds:** Juli's full five-stage coaching system with stage progression logic and Matteo context injection

---

## What Makes Juli Different from Matteo

Matteo works on one thing: the SCQ framework. His sessions have no predefined
end. A student might spend five turns or twenty turns before all three elements
are confirmed.

Juli works through a defined sequence: Attention, Need, Satisfaction,
Visualisation, Action. There is a start and a finish. The web layer tracks
where the student is in that sequence and tells Juli via the system prompt.
When stage five is complete, Juli's work is done.

This is a different kind of agent design. Matteo is reactive: he targets
whatever the student's weakest SCQ element is. Juli is progressive: she moves
the student through a fixed sequence in order.

Both designs use the same five-section skeleton from Framework 07. The
difference is what goes in the SCOPE and RULES sections.

---

## Monroe's Motivated Sequence: Stage Reference

Before writing Juli's prompt, it is important to understand what she is coaching.

| Stage | What the student does | What a weak entry looks like |
|---|---|---|
| Attention | Opens with something that makes the audience care | A generic statement of the problem with no hook |
| Need | Shows why this problem matters now, to this audience | A list of facts without urgency or consequence |
| Satisfaction | Proposes a clear solution with three supporting pillars | A vague recommendation without evidence or structure |
| Visualisation | Paints a concrete picture of success if the solution is adopted | Abstract future-state language with no measurable outcome |
| Action | Ends with a specific, accountable next step | A call to action with no named actor, date, or metric |

Juli targets the weakest element of whatever stage the student is currently on.
She does not move the student to the next stage. The web layer moves the student
forward when the student signals they are ready.

---

## Stage Injection for Juli

Unlike Matteo, who needs to know which SCQ element to focus on, Juli needs to
know which Monroe's stage is active. The web layer injects this information the
same way it injects Matteo's SCQ context.

In routes/agent2.js, after loading the system prompt:

```js
const session = await db.getJuliSession(req.user.id);
const stage = session?.current_stage ?? 'Attention';

const stageContext = [
    `\nCURRENT SESSION CONTEXT`,
    `Active stage: ${stage}`,
    `Focus your coaching on the student's work at the ${stage} stage.`,
    `Do not advance to the next stage. The student signals when they are ready.`
].join('\n');

const systemPrompt = baseSystemPrompt + stageContext;
```

When Juli's response arrives at the Express layer, parseJuliOutput extracts
the [STAGE: Name] tag. If the tag matches the next stage in the sequence,
the web layer updates the current_stage in the database. This is how stage
progression works without Juli knowing she is advancing it.

Stage sequence in order: Attention, Need, Satisfaction, Visualisation, Action.

---

## Context Injection: Pulling in Matteo's Work

Juli receives the student's SCQ as starting context. Without this, she would
be coaching a recommendation without knowing what the recommendation is about.

In routes/agent2.js, after loading stage context:

```js
const scqProgress = await db.getStudentProgress(req.user.id);
const scqBlock = scqProgress.question
    ? [
        `\nSTUDENT'S CONFIRMED SCQ`,
        `Situation: ${scqProgress.situation}`,
        `Complication: ${scqProgress.complication}`,
        `Question: ${scqProgress.question}`
      ].join('\n')
    : `\nNote: Student has not yet completed Matteo's SCQ coaching.`;

const systemPrompt = baseSystemPrompt + stageContext + scqBlock;
```

The SCQ block is injected between stage context and the first user turn. It
adds roughly 100-150 tokens. Track this against your context budget.

---

## Context Budget for Juli

Juli's coaching sessions can run longer than Matteo's because recommendation
structuring requires more back-and-forth per stage.

| Consumer | Budget allocation |
|---|---|
| Base system prompt | max 3,000 tokens |
| Stage injection | ~80 tokens |
| SCQ context block | ~150 tokens |
| Conversation history | max 13,000 tokens (32 turns x 400 avg) |
| Buffer | 3,770 tokens |
| Total | 20,000 tokens |

The critical difference from Matteo: Juli's history turns are longer on average.
A student's Satisfaction draft might be 300-400 words. Set MAX_HISTORY_TURNS for
Juli to 32, not 35, to leave more buffer for longer turns.

If the session exceeds the history budget, trim the same way as Matteo:
oldest tool results first, then oldest assistant messages, then oldest user messages.

---

## Juli's Complete System Prompt

```
ROLE
You are Juli, a Persuasive Communication Coach for MBA students at Hult
International Business School. Your students are developing consulting
recommendations using Monroe's Motivated Sequence.

You guide students through five stages in order: Attention, Need,
Satisfaction, Visualisation, and Action. You work on one stage at a time.
You do not advance to the next stage. You never write any part of the
recommendation for the student.

SCOPE
You coach on: developing each Monroe's stage with the depth and specificity
needed to move a consulting audience.

You do not handle: SCQ framework analysis, 5 Cs evaluation, slide design,
or anything outside the Monroe's Motivated Sequence.

If the student asks about SCQ or their rubric scores, redirect them to Matteo
or Tedd respectively.

RULES
- Before writing your response, identify: which Monroe's stage is active,
  what is the weakest element of the student's current draft at that stage,
  and what one question or prompt would sharpen it.
- Your visible response contains only that question or prompt. No preamble.
- Never write any part of the student's recommendation.
- Never evaluate whether the student's draft is good or bad. Coach instead.
- Never advance to the next stage. The student signals when they are ready.
- If the student signals they are ready to advance, confirm the current stage
  is solid before acknowledging the request.

FORMAT
- Maximum 150 words per response
- End every response with one question or actionable prompt
- End every response with a stage tag on its own line: [STAGE: StageName]
  Use exactly one of: Attention, Need, Satisfaction, Visualisation, Action
- No bullet points, lists, or headers
- No evaluative phrases: "Good", "Excellent", "You are on the right track"

ESCALATION
Escalate if: the student describes a personal crisis, reports a platform
technical failure, or sends content that violates academic integrity.
When escalating: tell the student you are connecting them with support and end your reply.
```

---

## Applying the Same Principles to Juli's Prompt

The five principles from Session 02, document 05, apply to Juli the same way
they applied to Matteo:

- Instructions over descriptions: "You guide students through five stages in order"
  is an instruction. "You are a helpful and encouraging communication coach" is
  a description. Use instructions.
- Constraints over explanations: "Never advance to the next stage. The student
  signals when they are ready." is a constraint. It is more reliable than two
  paragraphs explaining Socratic progression.
- Specific format instructions: [STAGE: StageName] is a machine-readable format.
  Vague instructions like "mention the stage somewhere" are not.
- Chain-of-thought in the rules: the three-step reasoning block in RULES tells
  Juli to identify stage, weakness, and question before writing. The reasoning
  happens internally; only the question appears in the output.
- Budget awareness: at 3,000 tokens max for the system prompt plus injected
  context, Juli's total base load is roughly 3,230 tokens per turn.

---

## Using Claude Code Desktop App

Open your project folder in the Claude Code desktop app. Claude Code can read
the existing routes/agent2.js stub from Session 02 and build Juli's full
system prompt and stage progression logic.

**Prompt to build Juli:**

```
Build Juli's full coaching system.

1. Save Juli's system prompt as agent/prompts/juli_v1.txt.
   The prompt must follow the five-section skeleton from Framework 07:
   ROLE, SCOPE, RULES, FORMAT, ESCALATION.
   
   Key constraints for Juli:
   - One turn: student draft in, one stage-specific prompt out
   - FORMAT must include the [STAGE: StageName] tag requirement
   - RULES must include the three-step reasoning block before responding
   - RULES must explicitly say: never advance stages, never write for the student

2. Add stage injection to server/src/routes/agent2.js:
   - Read current_stage from the database for this user
   - Append CURRENT SESSION CONTEXT block to the system prompt
   - Default to 'Attention' if no record exists

3. Add SCQ context injection to server/src/routes/agent2.js:
   - Read the student's confirmed SCQ from the agent_sessions table
   - Append STUDENT'S CONFIRMED SCQ block if question is not null

4. Add db.getJuliSession(user_id) to server/src/db.js that reads the
   current_stage from the agent_sessions table for agent_id = 'juli'.

5. Add stage advance logic in routes/agent2.js:
   - After parseJuliOutput extracts the stage tag from each response
   - If the stage in the tag is different from current_stage, update
     the database with the new stage
   - Update uses parameterised SQL: WHERE user_id = ? AND agent_id = 'juli'

After implementing, count Juli's prompt tokens:
  python -c "import anthropic; c=anthropic.Anthropic(); r=c.messages.count_tokens(model='claude-haiku-4-5-20251001', system=open('agent/prompts/juli_v1.txt').read(), messages=[{'role':'user','content':'test'}]); print(r.input_tokens, 'tokens')"
```

**What Claude Code will do:**
Write juli_v1.txt, add stage and SCQ injection to the route, add the DB helper
function, and wire the stage advance logic.

**Tips for this document:**
- Test stage advance by sending Juli a message where she clearly tags [STAGE: Need].
  Then query the database: SELECT current_stage FROM agent_sessions WHERE agent_id = 'juli'.
  It should show 'Need'. If it still shows 'Attention', the stage advance logic is not running.
- Ask Claude Code: "What happens if Juli tags [STAGE: Action] when the student is
  at the Attention stage? Should the web layer accept this jump?" The answer should be
  no. Add a validation rule: stages must advance one step at a time.
- Check the token count for Juli's prompt. If it is above 2,500 tokens, trim the
  stage definitions in the ROLE section and reference the SESSION CONTEXT injection
  instead: that context is already injected per request.

---

## Starter Code

Juli's prompt file and stage logic are generated by Claude Code from the prompt
above. The stage sequence (Attention through Action) and the parsing logic are
specific to the Monroe's Motivated Sequence structure.

```
starter-code/
|-- CLAUDE.md           Stage Progression section added with the five stage
|                       names, advance conditions, and which route manages it
|-- .env.example        Environment variable reference
|-- package.json        Node dependencies
`-- requirements.txt    Python dependencies
```

---

## Assignment

[02-build-juli.md](assignments/02-build-juli.md)

---

Copyright Janna AI Research Labs
