# Build 06: Few-Shot Examples

> Framework 07 (System Prompt Skeleton) defines five sections.
> Few-shot examples live inside the RULES or FORMAT section, not as a sixth section.
> They are the most powerful token you can add to a prompt and the easiest to get wrong.

**Applies:** Framework 07 (System Prompt Skeleton)
**Builds:** Example sets for Matteo and Tedd that enforce consistent coaching style and output format

---

## When Examples Beat Instructions

Instructions tell the model what to do. Examples show it.

For most straightforward tasks, instructions are enough. For tasks where the
quality of the output depends on a specific voice, style, or judgment call,
examples are more reliable.

Matteo is a Socratic coach. "Ask one question" is an instruction. But what
makes one Socratic question better than another is harder to describe in words
than it is to show. The model will calibrate to the examples you provide more
accurately than to a description of the ideal question.

Tedd returns structured JSON. "Return a JSON object with scores" is an instruction.
But the exact field names, the score range, and the observation format are easier
to enforce with one real example than with three sentences describing the schema.

**Use examples when:**
- The output quality depends on tone, voice, or judgment that is hard to describe
- The output format is complex or has fields that are easy to confuse
- The model keeps misinterpreting an instruction despite multiple rewrites

**Do not use examples when:**
- The task is simple and a clear instruction covers it completely
- You are running against a tight context budget and instructions will suffice
- The example you have is mediocre, because mediocre examples pull the model down

---

## How Many Examples

Two to three examples is almost always the right number for a coaching agent.

One example defines the pattern. Two examples show the pattern is consistent across
different inputs. Three examples cover edge cases (short student input, detailed
student input, confused student input). Beyond three, the additional examples
consume context budget that the conversation history needs.

For Tedd's structured JSON output, one example is usually enough because the
format is the constraint, not the judgment.

---

## Format: Where Examples Go in the Prompt

Examples belong at the end of the RULES section, introduced with a clear header
so the model knows they are examples, not more rules.

```
RULES
[your rules]

EXAMPLES
Below are examples of strong responses. Match this style and format.

Example 1:
Student: [student message]
Matteo: [ideal coaching question]

Example 2:
Student: [student message]
Matteo: [ideal coaching question]
```

The `EXAMPLES` header is important. Without it, the model may interpret the
example messages as part of the actual conversation history. The header makes
it unambiguous that these are reference examples, not turns to respond to.

---

## Matteo's Examples

A weak example and a strong example for the same student input:

**Weak example (do not use):**
```
Student: The situation is that our client, a retail chain, is facing declining
sales in their brick-and-mortar stores over the past two years.

Matteo: That's a good observation. What do you think is causing the decline?
```

Why it is weak: "That's a good observation" evaluates the student (Rule violation).
"What do you think is causing the decline?" is a generic question that does not
target a specific SCQ weakness.

**Strong example (use this):**
```
Student: The situation is that our client, a retail chain, is facing declining
sales in their brick-and-mortar stores over the past two years.

Matteo: You have described what is happening. What makes this decline a problem
specifically for this client, as opposed to an industry trend affecting everyone?
```

Why it is strong: No evaluation. The question targets a specific SCQ gap (the
Situation describes a fact but does not yet isolate the Complication). It is
under 120 words. It ends with one question.

**Second example (showing a different SCQ gap):**
```
Student: The complication is that customers are buying online instead of in-store,
and the client needs to decide what to do about it.

Matteo: You have named the behaviour change. What decision does the client actually
need to make, and who in their organisation needs to make it?
```

This example shows Matteo working on the Question element of SCQ, not the
Complication, demonstrating that the coaching moves to the weakest element
regardless of which stage the student thinks they are on.

---

## Tedd's Example

Tedd returns structured JSON. One example pins the schema exactly:

```
EXAMPLES
Return your evaluation in exactly this format:

{
  "evaluation": {
    "clear": {
      "score": 4,
      "observation": "The central recommendation is stated in the opening paragraph and reinforced in the conclusion. The reader knows what is being proposed within the first two sentences."
    },
    "concise": {
      "score": 2,
      "observation": "The Need section runs 340 words. The core argument could be made in 150. The detail does not add evidence; it adds length."
    },
    "compelling": {
      "score": 3,
      "observation": "The Visualisation stage opens with a financial projection but does not anchor it to the client's stated target. The impact feels abstract rather than concrete."
    },
    "credible": {
      "score": 4,
      "observation": "Three cited sources support the market sizing claim. The BCG framework reference is appropriate and correctly applied."
    },
    "consistent": {
      "score": 3,
      "observation": "The Action section calls for a 12-month rollout but the Satisfaction section described a 6-month timeline. These need to align."
    }
  }
}
```

This example does three things instructions alone cannot reliably do:
- Pins the exact field names (`clear`, `concise`, `compelling`, `credible`, `consistent`)
- Shows that `score` is a number between 1 and 5
- Shows that `observation` is one specific, actionable sentence about this deliverable, not a general comment

---

## Adding Examples Without Consuming the Budget

From Framework 04: examples cost tokens. Two Matteo examples at 100 tokens each
and one Tedd example at 200 tokens adds 400 tokens to the system prompt. That
is acceptable for the coaching quality it buys.

Check the impact:

```python
# Before examples
base_prompt = build_matteo_system_prompt()

# After examples
full_prompt = build_matteo_system_prompt_with_examples()

response = client.messages.count_tokens(
    model="claude-haiku-4-5-20251001",
    system=full_prompt,
    messages=[{"role": "user", "content": "test"}]
)

print(f"Token cost of examples: {response.input_tokens - base_tokens}")
```

If examples push the system prompt above 3,000 tokens, trim history more
aggressively (reduce `MAX_HISTORY_TURNS` by 2) to compensate.

---

## Using Claude Code Desktop App

Open your project folder in the Claude Code desktop app. Claude Code has
access to `agent/prompts/matteo_v1.txt` from document 05. The examples
you add here will become `matteo_v2.txt`.

**Prompt to write few-shot examples for Matteo:**

```
Add two few-shot examples to Matteo's system prompt and save as agent/prompts/matteo_v2.txt.

The examples must go at the end of the RULES section, introduced with an EXAMPLES header.
Each example is:
  Student: [student message about their SCQ case]
  Matteo: [ideal Socratic coaching question]

Requirements for each example:
  - The student message should be realistic: a draft Situation, Complication, or Question
  - Matteo's response must follow all FORMAT rules: under 120 words, one question, no markdown
  - No evaluation phrases in Matteo's response ("Good", "Interesting", etc.)
  - Each example should target a DIFFERENT SCQ element (one on Situation, one on Complication)
  - Matteo's question must be specific to that student message, not generic

After adding examples, count tokens and confirm the prompt is still under 3,000:
  python -c "import anthropic; c=anthropic.Anthropic(); r=c.messages.count_tokens(model='claude-haiku-4-5-20251001', system=open('agent/prompts/matteo_v2.txt').read(), messages=[{'role':'user','content':'test'}]); print(r.input_tokens, 'tokens')"
```

**What Claude Code will do:**
Read the existing v1 prompt, add the EXAMPLES section with two well-formed
examples, save as v2, and run the token count.

**Tips for this document:**
- Before accepting the examples, test them against the quality criteria from
  document 06: is each question specific to THAT student message, or could it
  be asked of any student? Generic questions are the most common failure.
- Ask Claude Code: "For example 1, what SCQ weakness does Matteo's question target?
  Explain it to me." If it cannot explain it, the example is too vague.
- If token count grows too much, ask: "Shorten each student message by 30 words
  without losing the SCQ weakness that Matteo is targeting."

---

## Starter Code

The output of this document is `agent/prompts/matteo_v2.txt` - an updated
version of your system prompt with examples added. Claude Code generates it
from the prompt above using your specific SCQ case context.

```
starter-code/
├── CLAUDE.md           Claude Code reads this to understand Matteo's task
│                       and FORMAT rules before writing the examples
├── package.json        Node dependencies
├── requirements.txt    Python dependencies
└── .env.example        Environment variable reference
```

The examples Claude Code writes will be specific to your case context, which
is why they cannot be pre-written. Generic examples produce generic coaching.

---

## Assignment

[06-write-few-shot-examples.md](assignments/06-write-few-shot-examples.md)

---

Copyright Janna AI Research Labs
