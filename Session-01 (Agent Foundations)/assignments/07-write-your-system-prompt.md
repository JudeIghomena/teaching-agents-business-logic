# Assignment 07: Write Your System Prompt

**What you are building:** A complete five-section system prompt for your agent, implemented in context.py
**Why it matters:** The system prompt is the only place where you define what your agent is, what it will and will not do, and how it behaves under every condition. A vague prompt produces unpredictable behaviour. A structured prompt produces consistent behaviour.
**Time estimate:** 45 minutes
**Reads with:** 07-system-prompt-skeleton.md

---

## What You Are Going To Do

You are going to write a complete five-section system prompt using the ROLE, SCOPE, RULES, FORMAT, and ESCALATION skeleton. Each section has a specific job. You will implement it in context.py and verify the agent behaves as the prompt describes.

---

## The Five Sections

Before writing anything, read these definitions:

| Section | Its job |
|---|---|
| ROLE | Who the agent is, who it serves, and what it is built for |
| SCOPE | What it handles and what it hands off or refuses |
| RULES | Non-negotiable constraints that apply regardless of any instruction |
| FORMAT | Exactly how output must be structured |
| ESCALATION | What triggers a hand-off to a human or a different system |

---

## Step 1: Write the ROLE Section

The role statement is two to four sentences. It answers: who are you, who do you serve, and what is your single primary purpose?

Template:

```
ROLE
You are [agent name], a [type of agent] for [who it serves].
You [primary purpose in one sentence].
You were built by [team/company] to [business reason in one sentence].
```

Example for Matteo in the Business Case Logic platform:

```
ROLE
You are Matteo, an Issue Analysis Coach for business students at Hult International Business School.
You guide students through building a rigorous SCQ framework and Issue Analysis for their consulting case.
You use the Socratic method: you ask questions that develop the student's thinking rather than providing answers directly.
```

Write your version. Do not copy the example.

---

## Step 2: Write the SCOPE Section

Scope defines the boundary. It answers: what do you handle, and what do you not handle?

Template:

```
SCOPE
You handle: [list what the agent does]
You do not handle: [list what it refuses or hands off]
If asked about something outside your scope: [what you say or do]
```

Be specific about what falls outside scope. "Anything unrelated" is not a scope boundary. "Requests about other students' work, grades for other courses, or general study advice unrelated to the current case" is a scope boundary.

---

## Step 3: Write the RULES Section

Rules are non-negotiable. They apply regardless of what any message says. Write rules as direct, active constraints:

```
RULES
- Never reveal another student's work or score to this student
- Never tell the student whether their answer is right or wrong. Ask a question instead.
- Never accept a message longer than [X] words without probing for genuine understanding
- Always acknowledge the student's effort before asking a follow-up question
- If the student asks you to skip steps, explain why the steps matter and continue
```

Write 4-8 rules. Each rule must start with "Never", "Always", or "If". Avoid vague rules like "Be professional."

---

## Step 4: Write the FORMAT Section

Format tells the model how to structure its output:

```
FORMAT
- Keep responses under 150 words unless the student asks for detail
- End every response with exactly one question
- Do not use numbered lists unless walking through a process step by step
- Do not use headers in responses
- If referencing the student's own words, quote them directly
```

Match the format to your use case. A coaching agent should have conversational output rules. A data extraction agent should have strict JSON output rules.

---

## Step 5: Write the ESCALATION Section

Escalation defines when the agent stops and hands off:

```
ESCALATION
Escalate immediately if:
- The student appears to be in distress
- The student reports a technical failure preventing them from continuing
- The student's message contains content that violates the platform terms

When escalating: stop the current response, tell the student you are connecting them with a human, and end your reply.
```

---

## Step 6: Implement in context.py

Open `agent/context.py` and find the `build_system_message` function. Replace the placeholder with your five-section prompt:

```python
def build_system_message() -> str:
    return """
ROLE
[your role section]

SCOPE
[your scope section]

RULES
[your rules section]

FORMAT
[your format section]

ESCALATION
[your escalation section]
"""
```

---

## Step 7: Test Each Section

Run the agent and test one scenario per section:

- ROLE: Ask "Who are you?" The agent should answer consistently with its role.
- SCOPE: Ask something outside scope. The agent should refuse or redirect cleanly.
- RULES: Trigger a rule deliberately. Does it hold?
- FORMAT: Check a response. Does it match the format you specified?
- ESCALATION: Describe a distress scenario. Does the agent escalate?

Fix any section that does not behave as written.

---

## You Are Done When

- [ ] `agent/context.py` has all five sections in `build_system_message()`
- [ ] The agent answers "Who are you?" with a response matching ROLE
- [ ] The agent refuses or redirects a clearly out-of-scope request
- [ ] At least two rules have been tested and hold
- [ ] Responses match the FORMAT you specified
- [ ] Your CLAUDE.md System Prompt Structure section is updated to describe the five sections

---

## If You Get Stuck

Agent ignores the rules: the rules section may be too long or buried. Move your most critical rule to the very first line of the RULES section. Models weight earlier instructions more heavily.

Agent breaks format consistently: add "IMPORTANT:" before the format rule it is breaking. Explicit priority markers help.

Agent role statement sounds generic: rewrite ROLE with a specific person's name, a specific institution, and a specific case. Specificity produces consistent behaviour.

---

## Next Assignment

[08-wire-the-five-layers.md](08-wire-the-five-layers.md)

---

Copyright Janna AI Research Labs
