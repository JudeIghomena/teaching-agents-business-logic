# Assignment 07: Control Output Format

**What you are building:** Format validators for all three agents wired into the Express routes, and Tedd's structured JSON output format
**Why it matters:** Format failures are invisible without validators. An agent that sometimes returns two questions instead of one, or occasionally wraps its JSON in markdown fences, will cause silent bugs in your UI. Validators catch these failures before they reach the student.
**Time estimate:** 45 minutes
**Reads with:** 07-output-format-control.md

---

## What You Are Going To Do

You are going to implement three validators, one per agent, and add them to the Express routes to log failures in development. You will also add Tedd's JSON format requirement to his system prompt.

---

## What Format Control Must Do

```
1. Log failures, do not block    Students always get a response; failures are recorded
2. Server-side only              Raw format errors never reach the browser
3. Specific checks               Word count, question count, JSON validity - all measurable
```

---

## Step 1: Implement validateMatteoOutput

Add this function to `server/src/routes/agent1.js`:

```js
function validateMatteoOutput(text) {
    const wordCount = text.split(/\s+/).filter(Boolean).length;
    const questionCount = (text.match(/\?/g) || []).length;
    const hasBullets = /^[-*•]/m.test(text);
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

Call it after the stream ends:

```js
python.stdout.on('end', () => {
    const check = validateMatteoOutput(fullResponse);
    if (!check.pass) {
        console.warn('[matteo] format failure:', check);
    }
    appendTurn(session.id, message, fullResponse);
    sendDone(res);
});
```

---

## Step 2: Implement parseJuliOutput

Add this function to `server/src/routes/agent2.js`:

```js
function parseJuliOutput(text) {
    const stageMatch = text.match(/\[STAGE:\s*(\w+)\]/);
    const stage = stageMatch ? stageMatch[1] : null;
    const content = text.replace(/\[STAGE:[^\]]+\]/, '').trim();
    return { content, stage };
}
```

Call it after the stream ends:

```js
python.stdout.on('end', () => {
    const { content, stage } = parseJuliOutput(fullResponse);
    if (!stage) {
        console.warn('[juli] no stage tag in response');
    }
    appendTurn(session.id, message, fullResponse);
    sendDone(res);
});
```

The student sees `content`. The stage tag is extracted and used by the platform to track progress. The tag never appears in the UI.

---

## Step 3: Implement parseTeddOutput

Add this function to `server/src/routes/agent3.js`:

```js
function parseTeddOutput(text) {
    try {
        const cleaned = text.trim()
            .replace(/^```json\n?/, '')
            .replace(/\n?```$/, '');

        const parsed = JSON.parse(cleaned);

        if (!parsed.evaluation) throw new Error('Missing evaluation key');

        const required = ['clear', 'concise', 'compelling', 'credible', 'consistent'];
        for (const key of required) {
            if (typeof parsed.evaluation[key]?.score !== 'number') {
                throw new Error(`Missing score for ${key}`);
            }
            if (!parsed.evaluation[key]?.observation) {
                throw new Error(`Missing observation for ${key}`);
            }
        }

        return { valid: true, data: parsed };
    } catch (err) {
        console.error('[tedd] parse failed:', err.message, '\nRaw:', text);
        return {
            valid: false,
            error: 'Evaluation format error. Please try submitting again.'
        };
    }
}
```

Call it after the stream ends:

```js
python.stdout.on('end', () => {
    const result = parseTeddOutput(fullResponse);
    if (!result.valid) {
        sendDone(res);
        return;
    }
    appendTurn(session.id, message, fullResponse);
    sendDone(res);
});
```

---

## Step 4: Update Tedd's Format Rules

Open agent/prompts/tedd_v1.txt. If the FORMAT section does not already say raw JSON only, update it:

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

Do not wrap in code fences. Do not include triple backticks. Start with { and end with }.
```

---

## Step 5: Write a Local Format Test

Create `server/src/format-test.js` to test each validator with sample inputs:

```js
const { validateMatteoOutput } = require('./routes/agent1');

// Should pass
const goodMatteo = "You have described the situation well. What makes this specific to your client rather than the entire industry?";
console.log('Matteo good:', validateMatteoOutput(goodMatteo));

// Should fail (two questions)
const badMatteo = "What is the situation? What makes it a problem?";
console.log('Matteo bad:', validateMatteoOutput(badMatteo));
```

Run it: `node server/src/format-test.js`

---

## You Are Done When

- [ ] validateMatteoOutput logs a warning when response has 0 or 2+ questions
- [ ] parseJuliOutput logs a warning when no [STAGE: ...] tag is found
- [ ] parseTeddOutput returns { valid: false, error: "..." } when JSON is malformed
- [ ] parseTeddOutput strips markdown fences before parsing
- [ ] Tedd's FORMAT section explicitly says no code fences
- [ ] format-test.js runs without errors and shows pass/fail for both test cases

---

## If You Get Stuck

parseTeddOutput throws instead of returning { valid: false }: the try/catch is not wrapping the right code. Confirm the JSON.parse call and the field validation loop are both inside the try block.

validateMatteoOutput always reports hasBullets: true: the regex `/^[-*•]/m` matches lines starting with a dash, asterisk, or bullet. If your test string has a line starting with a dash for another reason, wrap the check: only flag it if more than one line starts with a bullet character.

Juli's stage tag is not being extracted: confirm the response ends with [STAGE: Attention] (capital A, no extra spaces). The regex is `\[STAGE:\s*(\w+)\]`. Test it in a Node.js shell: `"test [STAGE: Attention]".match(/\[STAGE:\s*(\w+)\]/)`.

---

## Next Assignment

[08-evaluate-your-agent.md](08-evaluate-your-agent.md)

---

Copyright Janna AI Research Labs
