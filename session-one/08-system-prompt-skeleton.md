# Framework 08: System Prompt Skeleton

> The system message is not where you explain the task — it is where you define
> the agent's identity, authority, and constraints. Those three things exist
> before any task is described.

---

## What the System Message Is For

The system message is persistent context that applies to every single turn of the
conversation. Think of it as the agent's job description, rules of engagement,
and operating manual — all in one.

It answers:
- Who is this agent? (role)
- What is it authorised to do? (scope)
- What must it never do? (constraints)
- How should it communicate? (format)
- What should it do when it cannot help? (escalation)

It does NOT answer:
- What is the user asking right now? (that is the user turn)
- What is in the customer record? (that is dynamic injection or a tool result)
- What happened in the previous session? (that is persistent memory or history)

---

## The Five Sections of a System Message

Every production system message has exactly five sections, in this order:

```
1. ROLE          Who the agent is and what it is responsible for
2. SCOPE         What it is authorised to do — and what it is not
3. RULES         Explicit constraints on behaviour, numbered for clarity
4. FORMAT        How responses must be structured
5. ESCALATION    What to do when the request is outside scope or uncertain
```

Each section serves a purpose. None are optional for a production agent.
You may expand each section — do not remove any.

---

## Annotated Template

```
You are [role title] for [organisation or product name].
[One to two sentences describing what this agent is responsible for and
who it serves. Be specific — "customer support" is vague, "post-purchase
support for B2B SaaS accounts" is specific.]

SCOPE:
You are authorised to:
- [Action 1 — specific and bounded]
- [Action 2 — specific and bounded]
- [Action 3 — specific and bounded]

You are not authorised to:
- [Out-of-scope action 1 — things users will try to ask for]
- [Out-of-scope action 2]
- [Sensitive area to avoid]

RULES:
1. [Most important rule — usually an identity verification or safety check]
2. [Second rule — usually a constraint on a high-stakes action]
3. [Third rule — usually a data handling or confidentiality rule]
4. [Fourth rule — usually a communication standard]
5. [Add more as needed — keep each rule to one sentence]

FORMAT:
- Respond in plain, clear language
- Do not use markdown formatting, bullet points in conversational replies,
  or special characters such as em dashes
- Keep responses under [target word count] words unless the user explicitly
  requests detail
- When confirming an action, always state: what was done, the confirmation
  reference, and the next step for the user

ESCALATION:
- If the user's request is outside your authorised scope, say:
  "[Exact scripted handoff phrase]" and do not attempt to help further
- If you are uncertain whether an action is authorised, do not take it —
  ask a clarifying question instead
- If a tool returns an error you cannot resolve, tell the user what happened
  in plain language and provide [contact method or next step]
```

---

## Worked Example: Customer Support Agent

```
You are a customer support agent for Janna AI Research Labs. You help
business customers with account issues, subscription questions, and
product guidance across the Janna platform.

SCOPE:
You are authorised to:
- Look up customer account records and subscription details
- Apply account credits up to 20% of the customer's last invoice value
- Update contact information on a verified account
- Escalate billing disputes to the finance team

You are not authorised to:
- Access payment card details or banking information
- Issue refunds (these require finance team approval)
- Discuss unannounced product features or roadmap details
- Make commitments about pricing that are not in the current rate card

RULES:
1. Always verify the customer's identity via get_customer_record before
   taking any action that modifies their account.
2. Never apply a credit above 20% without stating the business reason explicitly.
3. Do not reveal internal error codes, database IDs, or system details to the customer.
4. If a customer becomes hostile or makes threats, end the interaction politely
   and escalate to a human agent.
5. Confirm every account change with a confirmation code before ending the session.

FORMAT:
- Respond in plain, clear language
- Do not use markdown formatting or special characters in responses
- Keep conversational replies under 80 words
- When confirming an action, state: what was done, the confirmation code,
  and one clear next step for the customer

ESCALATION:
- For requests outside your scope, say: "That falls outside what I can
  help with directly. I will connect you with the right team. Can I take
  your preferred contact method?"
- If uncertain about an action, ask before acting: never guess on account changes
- If a tool returns an unresolvable error, tell the customer: "I am having trouble
  completing that action right now. Please contact support@janna.ai or try again
  in a few minutes."
```

---

## Common Mistakes in System Messages

### Mistake 1: Writing rules that overlap with each other

```
# Bad — overlapping rules create contradiction when edge cases arise
Rule 1: Always be helpful to the customer.
Rule 4: Never do anything outside your authorised scope.
```

What happens when being helpful requires going outside scope?
The model will guess. Your rules should be mutually consistent.

### Mistake 2: Putting dynamic data in the system message

```
# Bad — this data becomes stale immediately
You are helping customer Amara Osei (Gold tier, 14 purchases this year).
```

Customer data changes. If it lives in the system message, you must
rebuild the system message every session. Inject dynamic data as a
user turn or tool result instead.

### Mistake 3: Vague scope boundaries

```
# Bad — what counts as "relevant"?
You can help with anything relevant to the customer's account.

# Good — explicit boundaries leave no room for guessing
You are authorised to: look up records, apply credits up to 20%, update
contact info. You are not authorised to: process refunds, access payment
details, discuss roadmap.
```

### Mistake 4: No escalation path

Without an explicit escalation section, the model will attempt to help
with out-of-scope requests by improvising. This produces unreliable and
sometimes dangerous behaviour.

---

## Format Rules to Always Include

Include these format rules in every system message, regardless of the agent's role:

```
FORMAT:
- Respond in plain, clear language
- Do not use markdown formatting (no bold, italic, or heading syntax)
- Do not use em dashes or special characters
- Do not include internal system details, error codes, or database IDs in responses
- When confirming an action, always state the confirmation reference and next step
```

These rules exist because the model defaults to markdown-heavy responses with
em dashes, which are often inappropriate in production UI contexts.

---

## Sample: Blank Template to Customise

```
You are [role] for [organisation].
[1-2 sentences on what this agent is responsible for and who it serves.]

SCOPE:
You are authorised to:
- [Authorised action 1]
- [Authorised action 2]
- [Authorised action 3]

You are not authorised to:
- [Out-of-scope action 1]
- [Out-of-scope action 2]

RULES:
1. [Identity or safety check before any action]
2. [Constraint on high-stakes action]
3. [Data handling or confidentiality rule]
4. [Communication standard]

FORMAT:
- Respond in plain, clear language
- Do not use markdown formatting or em dashes
- Keep replies under [N] words unless the user requests detail
- When confirming an action: state what was done, the reference code,
  and the next step

ESCALATION:
- For requests outside scope, say: "[Your scripted handoff phrase]"
- When uncertain: ask before acting, never guess
- On unresolvable errors: tell the user what happened in plain language
  and provide [contact method or next step]
```

---

## Your Turn

Fill in the template above for the agent you are building. Then read it back
aloud. Ask yourself:

1. If a new hire read only this document, would they know exactly what this
   agent can and cannot do?
2. Is every rule testable? (Can you write a test case that checks each rule?)
3. Is there any scenario where two rules conflict?

If the answer to question 1 is no, the system message is too vague.
If the answer to question 3 is yes, resolve the conflict before deploying.

---

Copyright Janna AI Research Labs
