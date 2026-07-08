# Build 05: Prompt Engineering Principles

> Framework 07 (System Prompt Skeleton) gave you the five sections.
> Framework 04 (Context Window Budget) showed you the constraint.
> This document shows you how to fill the skeleton with prompts that produce
> consistent, correct output without consuming the budget you need for history.

**Applies:** Framework 07 (System Prompt Skeleton) + Framework 04 (Context Window Budget)
**Builds:** Production-ready system prompts for Matteo, with patterns transferable to Juli and Tedd

---

## The Gap Between a Skeleton and a Working Prompt

In Session One you filled in the five sections with placeholder content.
A skeleton with rough content is enough to verify the agent loop works.
It is not enough to produce consistent coaching behaviour at scale.

The difference between a working prompt and a placeholder prompt is precision.

Placeholder ROLE:
```
You are Matteo, a coaching agent for business students.
```

Working ROLE:
```
You are Matteo, an Issue Analysis Coach for MBA students at Hult International
Business School working on their consulting capstone cases. You use the Socratic
method exclusively: you ask questions that build the student's own understanding.
You never state the answer. You never write any part of the SCQ framework for them.
```

The working version gives the model three things the placeholder does not:
a specific institution, a specific method, and two explicit constraints.
Specificity is not padding. It directly determines how the model behaves.

---

## Principle 1: Instructions Over Descriptions

A description tells the model what it is. An instruction tells the model what to do.
Instructions produce more consistent behaviour than descriptions.

**Description (weak):**
```
You are a helpful and patient coach who guides students.
```

**Instruction (strong):**
```
When a student submits any text about their case, your first action is to
identify the weakest element of their SCQ structure. Your response is one
question that targets that weakness. Nothing else.
```

The instruction specifies a trigger (student submits text), an internal action
(identify the weakest element), and an output constraint (one question, nothing else).
The model has no room to interpret.

---

## Principle 2: Constraints Are Cheaper Than Explanations

Every constraint you add to RULES makes the model more predictable.
A constraint is a short, active statement. An explanation is a paragraph.
Explanations consume context budget. Constraints do not.

**Explanation (expensive):**
```
It is important to remember that in a Socratic coaching environment, the role
of the coach is to help the student discover answers through guided questioning
rather than through direct instruction, because students who arrive at their
own answers retain the understanding more deeply than those who receive answers
directly...
```

**Constraints (cheap):**
```
RULES
- Never state the answer to an SCQ question. Ask a question instead.
- Never evaluate whether the student's answer is correct. Ask another question.
- Never write any part of the SCQ framework for the student.
```

Three constraints replace two paragraphs of explanation and produce more
reliable behaviour. The model does not need to understand the reasoning
to follow the rule.

---

## Principle 3: Format Instructions Must Be Specific

Vague format instructions produce inconsistent output. Specific ones do not.

**Vague:**
```
Keep your responses conversational and concise.
```

**Specific:**
```
FORMAT
- Maximum 120 words per response
- End every response with exactly one question
- Do not use bullet points, numbered lists, or headers
- Do not quote the student's words back to them in the same turn
```

The specific version gives the model four measurable constraints it can check
against before generating output. You can also check these programmatically
in your evaluation layer (document 08).

---

## Principle 4: Chain-of-Thought in the Prompt, Not in the Output

Chain-of-thought prompting makes the model reason through a problem before
responding. You can trigger it without making the reasoning visible to the student.

For Matteo:

```
RULES
- Before writing your response, identify: (1) which part of the SCQ framework
  the student is working on, (2) what is missing or unclear in their thinking,
  and (3) what one question would expose that gap.
- Your visible response contains only the question.
```

The first three bullet points describe internal reasoning steps. The model
performs them before writing the response but does not include them in the output.
This produces more thoughtful questions without adding tokens to the reply.

---

## Principle 5: Budget Your Prompt Against the History Window

From Framework 04: the context window has four consumers. The system prompt
is one of them. Every token it uses is unavailable for conversation history.

For Matteo, coaching sessions can run 20-30 turns. If each turn averages 200
tokens, the history alone can reach 6,000 tokens. With a 20,000-token context
limit for claude-haiku-4-5, the system prompt budget is roughly 2,000-3,000
tokens before history trimming kicks in.

Check your prompt length before deploying:

```python
import anthropic

client = anthropic.Anthropic()
prompt = build_system_message()

# Count tokens without making a full API call
response = client.messages.count_tokens(
    model="claude-haiku-4-5-20251001",
    system=prompt,
    messages=[{"role": "user", "content": "test"}]
)
print(f"System prompt: {response.input_tokens} tokens")
```

If the system prompt exceeds 2,500 tokens for Matteo, it is too long.
Cut descriptions, keep constraints.

---

## Matteo's Complete System Prompt

```python
def build_matteo_system_prompt() -> str:
    return """
ROLE
You are Matteo, an Issue Analysis Coach for MBA students at Hult International
Business School. Your students are working on consulting capstone cases that
require a rigorous Situation-Complication-Question (SCQ) framework.

You use the Socratic method: you ask questions that build the student's own
understanding. You never state the answer. You never write any part of the
SCQ framework for the student.

SCOPE
You coach on: defining the Situation, identifying the Complication, and
formulating the central Question of the business case.

You do not handle: recommendation structuring, presentation format, peer review
feedback, or anything outside the Issue Analysis stage.

If the student asks about something outside your scope, acknowledge it briefly
and redirect to the SCQ work.

RULES
- Before writing your response, identify: which SCQ element the student is working
  on, what is missing or unclear in their current thinking, and what one question
  would expose that gap.
- Your visible response contains only that question. No preamble, no explanation.
- Never evaluate whether the student's answer is correct.
- Never write any part of the SCQ for the student.
- Never give more than one question per response.
- If the student is stuck and asks for an example, ask them what they have tried
  before offering any guidance.
- If the student shows distress, acknowledge it briefly and ask if they need support.

FORMAT
- Maximum 120 words per response
- End every response with exactly one question ending in a question mark
- No bullet points, lists, or headers
- No phrases like "Great question" or "That's interesting"

ESCALATION
Escalate if: the student describes a personal crisis, reports a platform
technical failure, or sends content that violates academic integrity.
When escalating: tell the student you are connecting them with support and end your reply.
"""
```

---

## Applying the Same Principles to Juli and Tedd

The five principles apply identically to Juli and Tedd. The details change.

For **Juli**, the ROLE specifies Monroe's Motivated Sequence and the five stages.
The RULES include which stage is currently active (injected by the web layer).
The FORMAT specifies that Juli ends every response by naming the stage being worked on.

For **Tedd**, the ROLE specifies the 5 Cs evaluator. The SCOPE is one rubric
evaluation per turn. The FORMAT is JSON with a specific schema (document 07
covers this). The RULES specify that Tedd never coaches, only evaluates.

---

## Using Claude Code Desktop App

Open your project folder in the Claude Code desktop app. Claude Code already
knows Matteo's task definition from the Task Definitions section you added to
CLAUDE.md in document 04. Use that as the starting context for writing the prompt.

**Prompt to write Matteo's system prompt:**

```
Write Matteo's system prompt and save it as agent/prompts/matteo_v1.txt.

Apply these five principles from document 05:
1. Instructions over descriptions - tell the model what to DO, not just what it IS
2. Constraints over explanations - use Never/Always/If rules, not paragraphs
3. Specific format rules - measurable constraints, not "be concise"
4. Chain-of-thought in the rules - three reasoning steps before the visible response
5. Budget awareness - the prompt must be under 3,000 tokens for haiku

Use the five-section skeleton from Framework 07 (ROLE, SCOPE, RULES, FORMAT, ESCALATION).
Reference the Task Definitions section of CLAUDE.md for Matteo's job statement,
scope, and boundary.

After writing the file, count its tokens:
  python -c "import anthropic; c=anthropic.Anthropic(); r=c.messages.count_tokens(model='claude-haiku-4-5-20251001', system=open('agent/prompts/matteo_v1.txt').read(), messages=[{'role':'user','content':'test'}]); print(r.input_tokens, 'tokens')"
```

**What Claude Code will do:**
Write matteo_v1.txt applying all five principles, and run the token counter
to confirm it fits within the context budget.

**Tips for this document:**
- Read the generated prompt out loud before accepting it. If it sounds like
  marketing copy rather than engineering constraints, ask Claude Code to
  replace all descriptive sentences with direct instructions.
- Ask Claude Code: "Which rules in this prompt could the model misinterpret?
  Make them more specific." This usually reveals two or three rules that need tightening.
- If the token count is above 3,000, ask Claude Code: "Trim this prompt to
  under 2,500 tokens. Keep all rules. Cut all explanations."

---

## Starter Code

Working system prompts for all three agents in `starter-code/05-prompt-engineering/`:

```
05-prompt-engineering/
├── matteo_prompt.py    build_matteo_system_prompt()
├── juli_prompt.py      build_juli_system_prompt()
├── tedd_prompt.py      build_tedd_system_prompt()
└── token_counter.py    Script to measure prompt token cost
```

---

## Assignment

[05-apply-prompt-engineering.md](assignments/05-apply-prompt-engineering.md)

---

Copyright Janna AI Research Labs
