# Build 03: Building Tedd

> Framework 07 (System Prompt Skeleton) structures the prompt.
> Framework 09 (Memory Architecture and Tiers) shows where to store the result.
> Tedd's output is not a conversation. It is a record. This document
> builds Tedd's rubric evaluator and makes sure every evaluation is persisted.

**Applies:** Framework 07 (System Prompt Skeleton) + Framework 09 (Memory Architecture and Tiers)
**Builds:** Tedd's complete 5 Cs evaluation system with a rubric tool, JSON output, and persistent evaluation storage

---

## Tedd Is Not a Coach

This is the most important design constraint to build into Tedd's system prompt.

Matteo coaches. He asks questions and builds understanding through dialogue.
Juli coaches. She guides students through a progression with prompts and questions.
Tedd evaluates. He receives a completed deliverable, applies the 5 Cs rubric,
and returns a scored JSON object. He does not ask questions. He does not suggest
revisions. He does not explain how to improve. He observes, scores, and reports.

This constraint matters because a model will naturally want to be helpful by adding
coaching commentary alongside scores. The system prompt must explicitly prohibit this.

The distinction is also architectural. Matteo and Juli have multi-turn conversations.
Tedd is a one-turn evaluator. Each call to Tedd produces one JSON object per
submitted deliverable.

---

## Tool: get_rubric_config

Tedd's rubric definitions are not hardcoded in the system prompt. They are
loaded from a config file. This allows rubric criteria to be updated without
changing the prompt file.

Tool schema:

```python
GET_RUBRIC_CONFIG = {
    "name": "get_rubric_config",
    "description": (
        "Load the current 5 Cs rubric configuration including scoring criteria "
        "for each dimension. Call this at the start of every evaluation turn."
    ),
    "input_schema": {
        "type": "object",
        "properties": {},
        "required": []
    }
}
```

Implementation:

```python
import json
from pathlib import Path

RUBRIC_FILE = Path(__file__).parent / "config" / "rubric.json"

def get_rubric_config() -> dict:
    with open(RUBRIC_FILE) as f:
        return json.load(f)
```

The rubric.json file:

```json
{
  "dimensions": {
    "clear": {
      "description": "The recommendation is stated explicitly and the reader knows what is proposed within the first two sentences.",
      "score_1": "The central recommendation is not stated anywhere.",
      "score_5": "The recommendation is explicit, specific, and repeated at both the opening and closing."
    },
    "concise": {
      "description": "Every section serves the argument. No section is longer than it needs to be.",
      "score_1": "More than 40% of the word count does not contribute to the argument.",
      "score_5": "Every sentence advances the recommendation or the evidence."
    },
    "compelling": {
      "description": "The argument builds urgency. The reader understands why this matters to this audience now.",
      "score_1": "The argument could apply to any company at any time.",
      "score_5": "The urgency is specific to this client, this market, and this moment."
    },
    "credible": {
      "description": "Claims are supported by evidence. Sources are cited or named.",
      "score_1": "No claims are supported. All assertions are opinions.",
      "score_5": "Every key claim has a source, a named framework, or a cited data point."
    },
    "consistent": {
      "description": "Numbers, timelines, and framing are the same across all sections.",
      "score_1": "Numbers or timelines contradict between sections.",
      "score_5": "Every reference to timelines, figures, and scope is identical across sections."
    }
  }
}
```

---

## Tool: save_evaluation

Tedd's scored rubric must be written to the database after every evaluation.
This is the Tier 3 memory application from Framework 09: data that must survive
across sessions is stored in SQLite, not in the Python session store.

Tool schema:

```python
SAVE_EVALUATION = {
    "name": "save_evaluation",
    "description": (
        "Save the completed 5 Cs evaluation to the database. "
        "Call this after producing the evaluation JSON, before ending the turn."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "The student's user ID"
            },
            "session_id": {
                "type": "integer",
                "description": "The Tedd agent session ID"
            },
            "evaluation": {
                "type": "object",
                "description": "The full evaluation object matching the 5 Cs schema"
            }
        },
        "required": ["user_id", "session_id", "evaluation"]
    }
}
```

Implementation:

```python
import json

def save_evaluation(user_id: str, session_id: int, evaluation: dict) -> dict:
    db = get_db()
    score = sum(
        evaluation["evaluation"][c]["score"]
        for c in ["clear", "concise", "compelling", "credible", "consistent"]
    ) / 5.0
    db.execute(
        "UPDATE agent_sessions SET quality_score = ?, finalised = 1 "
        "WHERE id = ? AND user_id = ?",
        (score, session_id, user_id)
    )
    return {"saved": True, "average_score": score}
```

The quality_score column was added to the schema in Session 02. This is its
first use in production. The finalised flag prevents a student from submitting
the same deliverable twice.

---

## Tedd's System Prompt

```
ROLE
You are Tedd, a Peer Review Evaluator for MBA students at Hult International
Business School. You evaluate completed business recommendations against the
5 Cs rubric: Clear, Concise, Compelling, Credible, and Consistent.

You evaluate. You do not coach. You do not ask questions. You do not explain
how to improve. You observe what is present in the deliverable and score it.

SCOPE
You evaluate: completed student deliverables submitted for 5 Cs review.

You do not handle: SCQ framework coaching, Monroe's Sequence coaching, slide
design advice, grammar correction, or anything outside the 5 Cs evaluation.

If a student asks for coaching or revision advice, tell them to work with
Matteo or Juli and resubmit when they are ready.

RULES
- Call get_rubric_config at the start of every evaluation turn.
- Read the full deliverable before scoring any dimension.
- Score each dimension 1 to 5 using the rubric definitions from get_rubric_config.
- Write one observation per dimension. The observation must describe what you
  observed in THIS deliverable, not what a student should do differently.
- After producing the evaluation JSON, call save_evaluation with the user_id,
  session_id, and the evaluation object.
- Never write anything outside the JSON object in your response.
- Never ask the student a question.

FORMAT
Return your evaluation as a JSON object only. No preamble, no explanation
outside the JSON, no markdown code fences. Raw JSON starting with { and
ending with }.

Required schema:
{
  "evaluation": {
    "clear":       { "score": 1-5, "observation": "one specific sentence" },
    "concise":     { "score": 1-5, "observation": "one specific sentence" },
    "compelling":  { "score": 1-5, "observation": "one specific sentence" },
    "credible":    { "score": 1-5, "observation": "one specific sentence" },
    "consistent":  { "score": 1-5, "observation": "one specific sentence" }
  }
}

Rules for observations:
- One sentence only
- Specific to this deliverable, not generic advice
- Describes what was observed, not what should be done

ESCALATION
Escalate if: the student describes a personal crisis, reports a platform
technical failure, or sends content that clearly violates academic integrity.
When escalating: tell the student you are connecting them with support and end your reply.
```

---

## Memory Architecture: Where Evaluations Live

From Framework 09, there are three tiers of memory:

- Tier 1 is in-context conversation history. Tedd's conversation history is
  minimal because each evaluation is one turn. The deliverable arrives, the
  evaluation leaves.
- Tier 2 is the Python session store. Tedd does not use it because his sessions
  do not persist between server restarts.
- Tier 3 is the SQLite database. This is where Tedd's output must go. The
  save_evaluation tool writes the quality_score to the agent_sessions row
  and sets finalised = 1.

The professor dashboard (built in document 04) reads these quality_score values
to show how students are performing across the cohort. Without Tier 3 persistence,
the professor sees nothing.

---

## Using Claude Code Desktop App

Open your project folder in the Claude Code desktop app. Claude Code can read
the existing routes/agent3.js stub and the parseTeddOutput validator from
Session 02, then complete Tedd's full implementation.

**Prompt to build Tedd:**

```
Build Tedd's complete evaluation system.

1. Create agent/config/rubric.json with the 5 Cs rubric definitions.
   Each dimension needs a description, a score_1 anchor, and a score_5 anchor.
   Dimensions: clear, concise, compelling, credible, consistent.

2. In agent/tool_registry.py, add two new tools:

   a. get_rubric_config()
      - Reads agent/config/rubric.json
      - Returns the full rubric dict
      - No parameters required

   b. save_evaluation(user_id, session_id, evaluation)
      - Calculates average score across all five dimensions
      - Updates agent_sessions: SET quality_score = ?, finalised = 1
        WHERE id = ? AND user_id = ?
      - Uses parameterised SQL only
      - Returns {"saved": True, "average_score": float}

   Register both in TOOL_DISPATCH.

3. Save Tedd's system prompt as agent/prompts/tedd_v1.txt.
   Use the five-section skeleton from Framework 07.
   The RULES section must include:
   - Call get_rubric_config at the start of every turn
   - Call save_evaluation after producing the JSON
   - Never write anything outside the JSON

4. In server/src/routes/agent3.js, after parseTeddOutput succeeds,
   verify that finalised is not already set to 1 for this user.
   If it is, return a 409 status: {"error": "This deliverable has already been evaluated."}.
   This prevents double-submission.

Reference the Database Schema section of CLAUDE.md for the agent_sessions columns.
```

**What Claude Code will do:**
Create rubric.json, add both tool implementations, save tedd_v1.txt, and add
the double-submission guard to the Express route.

**Tips for this document:**
- After implementing, send Tedd a short test deliverable via curl. Verify two things:
  (1) the JSON comes back with all five dimensions, and (2) the database row
  shows quality_score is set and finalised = 1.
- Then send the same deliverable again. The response should be 409.
- Ask Claude Code: "What happens if get_rubric_config is called but rubric.json
  is missing?" The tool should raise a FileNotFoundError that the runner catches
  and returns as a generic error, not a stack trace, to the client.

---

## Starter Code

Tedd's tools and prompt are generated by Claude Code. The rubric.json file
in particular must be reviewed for clarity: the observation examples should
be specific enough that a student reading their scores understands exactly
what was observed.

```
starter-code/
|-- CLAUDE.md           Registered Tools section includes get_rubric_config
|                       and save_evaluation. Memory Architecture section explains
|                       why evaluations go to Tier 3 and not the session store.
|-- .env.example        Environment variable reference
|-- package.json        Node dependencies
`-- requirements.txt    Python dependencies
```

---

## Assignment

[03-build-tedd.md](assignments/03-build-tedd.md)

---

Copyright Janna AI Research Labs
