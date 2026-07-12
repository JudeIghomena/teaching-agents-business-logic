# Assignment 06: Write Few-Shot Examples

**What you are building:** Two Matteo examples and one Tedd example added to their system prompts, saved as matteo_v2.txt
**Why it matters:** Examples show the model what a good response looks like more reliably than instructions alone. After this assignment, Matteo's coaching questions will be consistently targeted to the student's specific SCQ weakness instead of being generic.
**Time estimate:** 30 minutes
**Reads with:** 06-few-shot-examples.md

---

## What You Are Going To Do

You are going to write two few-shot examples for Matteo covering different SCQ weaknesses, add them to the prompt file as a new version, and verify the token count stays within budget.

---

## What Good Examples Must Do

```
1. Cover different cases        Example 1 on Situation, Example 2 on Complication
2. Follow the FORMAT rules      Under 120 words, one question, no evaluation phrases
3. Be specific                  The question targets THIS student's weakness, not a generic gap
4. Use the EXAMPLES header      So the model knows these are reference cases, not the real conversation
```

A common mistake is writing examples that could apply to any student. The test: could Matteo's question in the example be asked of a student who wrote something completely different? If yes, the example is too generic.

---

## Step 1: Write a Weak Example to Avoid

Before writing your examples, write one bad example and identify why it fails. This makes the standard clearer.

Write a student message with a weak Situation, then write a generic coaching question. Identify the failure:

```
Student: Our client is facing challenges with their retail operations.

Matteo (WEAK): That is a good starting point. What do you think the main problem is?
```

Two failures: "That is a good starting point" is an evaluation phrase (FORMAT violation). "What do you think the main problem is?" is a generic question that does not target the specific SCQ weakness in this student's statement.

The actual weakness: the student said "challenges" without naming a specific situation. The question should target that.

---

## Step 2: Write Two Strong Examples

Write Example 1 targeting a weak Situation:

```
Student: Our client is a regional bank facing pressure from competitors.

Matteo: You have named the industry and a general pressure. What is the specific fact about this client, right now, that makes their situation different from every other regional bank facing the same competitors?
```

Why it is strong: no evaluation phrase. The question targets the specific SCQ gap (Situation is too generic). It is under 120 words. It ends with one question.

Write Example 2 targeting a weak Complication:

```
Student: The complication is that customers are leaving the bank for digital-only competitors.

Matteo: You have described a behaviour change. What decision does that behaviour change force on the client's leadership this quarter, and what happens if they make no decision?
```

Why it is strong: it targets the Complication gap (naming a symptom instead of isolating the decision-forcing implication). The question moves the student from describing what is happening to explaining why it is a problem that demands action now.

---

## Step 3: Format the EXAMPLES Section

Copy matteo_v1.txt to matteo_v2.txt:

```bash
cp agent/prompts/matteo_v1.txt agent/prompts/matteo_v2.txt
```

Open matteo_v2.txt. After the RULES section and before the FORMAT section, add:

```
EXAMPLES
Below are examples of strong responses. Match this style and format exactly.

Example 1:
Student: Our client is a regional bank facing pressure from competitors.
Matteo: You have named the industry and a general pressure. What is the specific fact about this client, right now, that makes their situation different from every other regional bank facing the same competitors?

Example 2:
Student: The complication is that customers are leaving the bank for digital-only competitors.
Matteo: You have described a behaviour change. What decision does that behaviour change force on the client's leadership this quarter, and what happens if they make no decision?
```

---

## Step 4: Count Tokens on v2

```bash
python -c "
import anthropic
c = anthropic.Anthropic()
r = c.messages.count_tokens(
    model='claude-haiku-4-5-20251001',
    system=open('agent/prompts/matteo_v2.txt').read(),
    messages=[{'role': 'user', 'content': 'test'}]
)
print(r.input_tokens, 'tokens')
"
```

If the examples pushed the count above 3,000: shorten the student messages in each example by 10-15 words. The SCQ weakness must still be visible, but the student message does not need to be long.

---

## Step 5: Test the Difference

Set the prompt version to v1, send a generic student message, and note the response:

```bash
MATTEO_PROMPT_VERSION=v1 python agent/runner.py
```

Then switch to v2:

```bash
MATTEO_PROMPT_VERSION=v2 python agent/runner.py
```

Is the v2 question more targeted to the specific SCQ gap in the student's message? If both questions feel equally generic, one of the examples is not specific enough. Revise it.

---

## You Are Done When

- [ ] agent/prompts/matteo_v2.txt exists with the EXAMPLES section added
- [ ] Both examples have different student messages targeting different SCQ elements
- [ ] Neither example contains an evaluation phrase in Matteo's response
- [ ] Both example responses are under 120 words and end with one question
- [ ] Token count for v2 is under 3,000
- [ ] The v2 response to a test message is more targeted than the v1 response

---

## If You Get Stuck

Token count jumped too high: the student messages in the examples are too long. Trim them to one or two sentences each. The model calibrates to the structure of the example, not the length of the student message.

Both examples target the same SCQ element: go back to the platform overview and re-read the difference between a weak Situation and a weak Complication. The examples must be distinct.

The v2 question feels the same as v1: read your examples again. Are Matteo's questions in the examples specific to the student message, or could they be asked of any student? If the latter, make them more specific. The model copies what it sees in the examples.

---

## Next Assignment

[07-control-output-format.md](07-control-output-format.md)

---

Copyright Janna AI Research Labs
