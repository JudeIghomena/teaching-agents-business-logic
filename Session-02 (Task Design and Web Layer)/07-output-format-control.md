# Build 07: Output Format Control

> Framework 07 (System Prompt Skeleton) owns the FORMAT section.
> Framework 03 (Model Selection) determines how reliably that format is followed.
> This document shows how to enforce what each SCQ agent returns and which model
> to choose based on the format complexity.

**Applies:** Framework 07 (System Prompt Skeleton) + Framework 03 (Model Selection)
**Builds:** Enforced output formats for Matteo (plain text), Juli (plain text with stage tags), and Tedd (JSON)

---

## Three Agents, Three Output Types

The three SCQ agents produce fundamentally different output types. The format
for each is determined by what the web layer needs to do with it.

| Agent | Output type | Why |
|---|---|---|
| Matteo | Plain conversational text | Streamed directly to the student. No parsing needed. |
| Juli | Plain text with a stage tag | Web layer reads the tag to track which Monroe's stage is active. |
| Tedd | JSON object | Web layer parses it to render a rubric card with individual scores. |

The format decision is made at the web layer, not by the agent. The agent
follows the FORMAT section of its system prompt. The web layer parses the result.

---

## Matteo: Plain Text

Matteo's format is the simplest. The web layer streams it directly to the student's
browser without parsing.

System prompt FORMAT section:

```
FORMAT
- Maximum 120 words
- One question per response, at the end
- No headers, no bullet points, no numbered lists
- No markdown formatting of any kind
- No phrases that evaluate the student: "Good", "Correct", "Well done", "Exactly"
- No preamble before the question: start with content, not with "I see that..."
```

Verification in the web layer (run after each response in development):

```js
function validateMatteoOutput(text) {
    const wordCount = text.split(/\s+/).length;
    const questionCount = (text.match(/\?/g) || []).length;
    const hasBullets = /^[-*]/m.test(text);
    const hasMarkdown = /\*\*|__|##/.test(text);

    return {
        pass: wordCount <= 120 && questionCount === 1 && !hasBullets && !hasMarkdown,
        wordCount,
        questionCount,
        hasBullets,
        hasMarkdown
    };
}
```

Run this in development on every response. Log failures. Do not block the response
to the student but record when the format breaks so you can fix the prompt.

---

## Juli: Plain Text with Stage Tag

Juli's output is conversational text, like Matteo's, but the web layer needs to
know which Monroe's stage Juli is currently addressing. A stage tag at the end
of each response solves this without changing the streaming behaviour.

System prompt FORMAT section for Juli:

```
FORMAT
- Maximum 150 words
- One guiding prompt or question per response
- No markdown formatting
- End every response with a stage tag on a new line in this exact format:
  [STAGE: Attention]
  [STAGE: Need]
  [STAGE: Satisfaction]
  [STAGE: Visualisation]
  [STAGE: Action]
  Use exactly one of the five stage names above.
```

Web layer parsing:

```js
function parseJuliOutput(text) {
    const stageMatch = text.match(/\[STAGE:\s*(\w+)\]/);
    const stage = stageMatch ? stageMatch[1] : null;
    const content = text.replace(/\[STAGE:[^\]]+\]/, '').trim();

    return { content, stage };
}
```

The stage is extracted and saved to the session record. The content is what
the student sees. The tag never appears in the student's UI.

---

## Tedd: Structured JSON

Tedd's output must be parseable by the web layer to render a rubric card.
This is the most format-sensitive of the three agents.

System prompt FORMAT section for Tedd:

```
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
```

Web layer parsing with a fallback:

```js
function parseTeddOutput(text) {
    try {
        const cleaned = text.trim();
        const parsed = JSON.parse(cleaned);

        if (!parsed.evaluation) {
            throw new Error('Missing evaluation key');
        }

        const required = ['clear', 'concise', 'compelling', 'credible', 'consistent'];
        for (const key of required) {
            if (!parsed.evaluation[key]?.score || !parsed.evaluation[key]?.observation) {
                throw new Error(`Missing or incomplete ${key} field`);
            }
        }

        return { valid: true, data: parsed };
    } catch (err) {
        // Do not show the raw JSON error to the student
        // Log it and return a fallback
        console.error('[tedd] JSON parse failed:', err.message, '\nRaw:', text);
        return {
            valid: false,
            error: 'Evaluation format error. Please try submitting again.'
        };
    }
}
```

The fallback matters. If Tedd returns malformed JSON (which happens when the
model inserts markdown fences around the JSON), the student gets a clean error
message, not a page crash.

---

## Model Selection and Format Reliability

From Framework 03: model selection is a decision with consequences, not a preference.

For format compliance, the relationship is straightforward:

| Model | Plain text format | JSON format |
|---|---|---|
| claude-haiku-4-5 | Highly reliable | Reliable with clear schema example |
| claude-sonnet-5 | Highly reliable | Very reliable, handles edge cases better |

For Matteo and Juli, `claude-haiku-4-5` is the right choice. The format is simple,
the coaching task does not require deep reasoning, and speed matters for streaming.

For Tedd, start with `claude-haiku-4-5`. If JSON parsing errors appear more than
once per 20 evaluations in testing, switch to `claude-sonnet-5` for the evaluation
step. The cost difference is acceptable for a one-shot rubric evaluation.

This is the routing rule from Framework 03 applied: use the smallest model that
reliably meets the format requirement.

```python
# agent/model_config.py

MATTEO_MODEL = "claude-haiku-4-5-20251001"
JULI_MODEL = "claude-haiku-4-5-20251001"
TEDD_MODEL = "claude-haiku-4-5-20251001"  # Upgrade to sonnet-5 if JSON error rate > 5%
```

Record the model per agent in CLAUDE.md so any coding agent session knows
which model each agent uses and why.

---

## Adding Format to CLAUDE.md

Update your CLAUDE.md Output Format section:

```
## Output Format

Matteo: plain text, max 120 words, exactly one question at the end, no markdown.
  Validated by: validateMatteoOutput() in routes/agent1.js

Juli: plain text, max 150 words, one question or prompt, ends with [STAGE: Name].
  Parsed by: parseJuliOutput() in routes/agent2.js

Tedd: raw JSON matching { evaluation: { clear, concise, compelling, credible, consistent } }.
  Each field: { score: 1-5, observation: "one sentence" }.
  Parsed by: parseTeddOutput() in routes/agent3.js
  Fallback: clean error message if JSON is malformed.

Model routing:
  Matteo: claude-haiku-4-5-20251001
  Juli:   claude-haiku-4-5-20251001
  Tedd:   claude-haiku-4-5-20251001 (switch to claude-sonnet-5 if JSON errors > 5%)
```

---

## Using Claude Code Desktop App

Open your project folder in the Claude Code desktop app. Claude Code reads
the Output Formats section of your CLAUDE.md which already lists the three
format specifications. It will implement validators that match those specs exactly.

**Prompt to implement output format validators:**

```
Implement output format validators for all three SCQ agents.

1. server/src/routes/agent1.js - add validateMatteoOutput(text) that checks:
   - word count <= 120
   - exactly one question mark
   - no bullet points (lines starting with - or *)
   - no markdown bold (**) or headers (##)
   - returns { pass: bool, wordCount, questionCount, hasBullets, hasMarkdown }
   Wire it to log a warning in development when the check fails.
   Do not block the student response on failure.

2. server/src/routes/agent2.js - add parseJuliOutput(text) that:
   - extracts the [STAGE: Name] tag using a regex
   - removes the tag from the text the student sees
   - returns { content, stage } where stage is null if no valid tag found

3. server/src/routes/agent3.js - add parseTeddOutput(text) that:
   - parses raw JSON (no markdown fences)
   - validates all five C keys exist with score (1-5) and observation fields
   - on any parse or validation failure: logs the raw text server-side,
     returns { valid: false, error: 'Evaluation format error. Please try submitting again.' }
   - on success: returns { valid: true, data: parsed }

Reference the Output Formats section of CLAUDE.md for the exact field names.
```

**What Claude Code will do:**
Implement all three parsers/validators wired into the correct route files,
with clean client-facing error messages that never expose raw JSON or parse errors.

**Tips for this document:**
- After implementing, test Tedd's parser by deliberately sending malformed JSON:
  `parseTeddOutput("not json at all")` - it should return the clean error, not throw.
- Ask Claude Code to write a `format_test.js` file that calls each validator
  with sample inputs so you can run `node format_test.js` to verify them locally.
- If Tedd keeps returning JSON wrapped in markdown fences (```json), add this
  to Tedd's system prompt RULES: "Return raw JSON only. Do not wrap in code fences."

---

## Starter Code

Format validators and parsers in `starter-code/07-output-format/`:

```
07-output-format/
├── matteo_validator.js     validateMatteoOutput()
├── juli_parser.js          parseJuliOutput()
├── tedd_parser.js          parseTeddOutput() with fallback
└── format_test.js          Run all three validators against sample outputs
```

---

## Assignment

[07-control-output-format.md](assignments/07-control-output-format.md)

---

Copyright Janna AI Research Labs
