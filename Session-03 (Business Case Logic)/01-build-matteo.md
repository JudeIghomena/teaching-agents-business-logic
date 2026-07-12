# Build 01: Building Matteo

> Framework 06 (Tool Design and Schema) taught you how to give an agent tools
> it can call during a turn. Framework 07 (System Prompt Skeleton) gave you
> the five-section structure. This document applies both to finish Matteo:
> a fully-tooled SCQ coach with a complete, tested system prompt.

**Applies:** Framework 06 (Tool Design and Schema) + Framework 07 (System Prompt Skeleton)
**Builds:** Matteo with two platform tools, a stage-aware system prompt, and full integration with the web layer

---

## What Matteo Is Missing After Session 02

After Session 02, Matteo can:
- Receive a student message via the Express route
- Call run_agent_loop with the message and history
- Return a streamed SSE response
- Pass format validation (word count, single question)

What Matteo cannot yet do:
- Know which SCQ element the student is currently working on
- Save a student's confirmed SCQ draft to the database
- Read back a student's prior SCQ progress in a new session

These three capabilities require two tools and one context injection.
Without them, Matteo treats every session as a blank slate and cannot
guide students through the SCQ framework progressively.

---

## Tool 1: save_scq_draft

This tool saves the current SCQ elements a student has confirmed.
Matteo calls it when the student explicitly agrees their Situation,
Complication, or Question is ready to move on.

Tool schema:

```python
SAVE_SCQ_DRAFT = {
    "name": "save_scq_draft",
    "description": (
        "Save the student's confirmed SCQ element to the database. "
        "Call this only when the student explicitly confirms a Situation, "
        "Complication, or Question is finalised, not when they are still refining it."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "session_id": {
                "type": "integer",
                "description": "The agent session ID from the database"
            },
            "element": {
                "type": "string",
                "enum": ["situation", "complication", "question"],
                "description": "Which SCQ element is being saved"
            },
            "content": {
                "type": "string",
                "description": "The student's exact text for this SCQ element"
            }
        },
        "required": ["session_id", "element", "content"]
    }
}
```

Implementation in tool_registry.py:

```python
def save_scq_draft(session_id: int, element: str, content: str) -> dict:
    db = get_db()
    db.execute(
        "UPDATE agent_sessions SET "
        "messages = json_set(COALESCE(messages, '[]'), '$.' || ?, ?) "
        "WHERE id = ? AND agent_id = 'matteo'",
        (element, content, session_id)
    )
    return {"saved": True, "element": element}
```

Register in TOOL_DISPATCH:

```python
TOOL_DISPATCH = {
    "save_scq_draft": lambda args: save_scq_draft(**args),
}
```

---

## Tool 2: get_student_progress

This tool reads back which SCQ elements a student has already confirmed
across previous sessions. Matteo calls it at the start of every session.

Tool schema:

```python
GET_STUDENT_PROGRESS = {
    "name": "get_student_progress",
    "description": (
        "Read the student's previously confirmed SCQ elements. "
        "Call this at the start of a new session to avoid asking the student "
        "to repeat work they have already confirmed."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "The authenticated student's user ID"
            }
        },
        "required": ["user_id"]
    }
}
```

Implementation:

```python
def get_student_progress(user_id: str) -> dict:
    db = get_db()
    row = db.execute(
        "SELECT messages FROM agent_sessions "
        "WHERE user_id = ? AND agent_id = 'matteo' "
        "ORDER BY created_at DESC LIMIT 1",
        (user_id,)
    ).fetchone()
    if not row:
        return {"situation": None, "complication": None, "question": None}
    import json
    data = json.loads(row["messages"])
    return {
        "situation": data.get("situation"),
        "complication": data.get("complication"),
        "question": data.get("question")
    }
```

---

## Stage Injection: Telling Matteo Where the Student Is

Matteo cannot know which SCQ element to focus on unless the web layer tells it.
This is the stage injection pattern: the Express route adds a context line to
the system prompt before calling run_agent_loop.

In routes/agent1.js, after loading the system prompt:

```js
const progress = await db.getStudentProgress(req.user.id);

const scqContext = [
    `\nCURRENT SESSION CONTEXT`,
    `Situation: ${progress.situation ?? 'Not yet confirmed'}`,
    `Complication: ${progress.complication ?? 'Not yet confirmed'}`,
    `Question: ${progress.question ?? 'Not yet confirmed'}`,
    `Focus on the first element that is not yet confirmed.`
].join('\n');

const systemPrompt = baseSystemPrompt + scqContext;
```

This context is appended after the ESCALATION section. It is not part of the
versioned prompt file in agent/prompts/. It is dynamically constructed per request.

The benefit from Framework 04: this approach adds roughly 60-80 tokens per
request, not per turn. It does not grow with conversation history.

---

## Matteo's Complete System Prompt (Final)

The matteo_v1.txt from Session 02 had the skeleton. The final version adds
explicit tool-calling instructions for the two new tools:

```
ROLE
You are Matteo, an Issue Analysis Coach for MBA students at Hult International
Business School. Your students are working on consulting capstone cases requiring
a rigorous Situation-Complication-Question (SCQ) framework.

You use the Socratic method: you ask questions that build the student's own
understanding. You never state the answer. You never write any part of the
SCQ framework for the student.

SCOPE
You coach on: defining the Situation, isolating the Complication, and
formulating the central Question of the business case.

You do not handle: recommendation structuring, presentation format, peer
review feedback, Monroe's Sequence, or anything outside the Issue Analysis stage.

If a student asks about anything outside your scope, acknowledge it briefly
and redirect to the SCQ work.

RULES
- Before writing your response, identify: which SCQ element the student is working
  on, what is missing or unclear in their current thinking, and what one question
  would expose that gap.
- Your visible response contains only that question. No preamble, no explanation.
- Never evaluate whether the student's answer is correct.
- Never write any part of the SCQ for the student.
- Never give more than one question per response.
- Call get_student_progress at the start of the first turn of a new session.
- Call save_scq_draft only when the student explicitly says an element is finalised.
  Do not call it speculatively.
- If the student is stuck and asks for an example, ask what they have tried first.
- If the student shows distress, acknowledge it briefly and ask if they need support.

FORMAT
- Maximum 120 words per response
- End every response with exactly one question ending in a question mark
- No bullet points, lists, or headers
- No phrases like "Great question" or "That is interesting"

ESCALATION
Escalate if: the student describes a personal crisis, reports a platform
technical failure, or sends content that violates academic integrity.
When escalating: tell the student you are connecting them with support and end your reply.
```

---

## Using Claude Code Desktop App

Open your project folder in the Claude Code desktop app. Claude Code can
read your existing tool_registry.py and runner.py from Session 02, then add
the two new tools and the stage injection to the correct files.

**Prompt to build Matteo's tools and stage injection:**

```
Add two tools to Matteo and wire the stage injection into the Express route.

1. In agent/tool_registry.py, add two new tool schemas and implementations:

   a. save_scq_draft(session_id, element, content)
      - element must be one of: situation, complication, question
      - Updates the agent_sessions row using parameterised SQL
      - Returns {"saved": True, "element": element}

   b. get_student_progress(user_id)
      - Reads the most recent Matteo session for this user
      - Returns {"situation": text or null, "complication": text or null, "question": text or null}

   Register both in TOOL_DISPATCH. The TOOL_DISPATCH dict is the security allowlist.
   Any tool name NOT in TOOL_DISPATCH must be rejected with an error.

2. In server/src/routes/agent1.js, add stage injection after loading the system prompt:
   - Call db.getStudentProgress(req.user.id) to read current SCQ state
   - Append a CURRENT SESSION CONTEXT block to the system prompt
   - Pass the modified system prompt to run_agent_loop

3. Update agent/prompts/matteo_v1.txt to add tool-calling instructions
   to the RULES section (call get_student_progress at session start,
   call save_scq_draft only on explicit student confirmation).

Reference the Database Schema and Registered Tools sections of CLAUDE.md.
All SQL must use parameterised statements. No string concatenation into SQL.
```

**What Claude Code will do:**
Implement both tool schemas and handlers, add stage injection to the Express route,
and update the prompt file with tool-calling rules.

**Tips for this document:**
- After implementing save_scq_draft, test it with a curl request to the Matteo route.
  Tell Matteo: "My situation is finalised: the client is a regional bank losing 15%
  of retail customers." Check that the row updates in the database.
- Ask Claude Code: "Show me what happens if save_scq_draft is called with an element
  value that is not in the enum. How is it rejected?" The tool schema validation
  should catch this before the implementation runs.
- Check the token count after adding the tool schemas to the system prompt:
  python evaluation/measure_prompt.py matteo v1
  If it exceeds 3,000 tokens, trim the description fields first.

---

## Starter Code

The tools are generated by Claude Code from the prompt above, wired into
your existing tool_registry.py and runner.py files.

```
starter-code/
|-- CLAUDE.md           Registered Tools section now includes save_scq_draft
|                       and get_student_progress with their schemas
|-- .env.example        Environment variable reference
|-- package.json        Node dependencies
`-- requirements.txt    Python dependencies
```

After Claude Code generates the tools, verify that TOOL_DISPATCH contains
exactly the tools you expect and nothing more. The dispatch dict is the
security gate. An unexpected entry means something was added outside the
intended workflow.

---

## Assignment

[01-build-matteo.md](assignments/01-build-matteo.md)

---

Copyright Janna AI Research Labs
