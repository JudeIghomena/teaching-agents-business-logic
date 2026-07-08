# Build 04: Task Decomposition

> Framework 01 (Agent Mental Model) asks: what is this agent's job in one sentence?
> If you cannot answer in one sentence, the agent is doing too much.
> This document applies that principle to Matteo, Juli, and Tedd.

**Applies:** Framework 01 (Agent Mental Model)
**Builds:** Precise task definitions for all three SCQ platform agents

---

## Why Decomposition Comes Before Prompting

You cannot write a good system prompt for a task you have not precisely defined.

The most common mistake in agent development is writing the system prompt first
and discovering the task boundary later, during debugging, when the agent starts
doing things you did not expect.

Task decomposition answers three questions before you write a single prompt line:

1. What is the agent responsible for in a single turn?
2. What does it receive as input and what does it return as output?
3. What is it not responsible for, and who handles that instead?

Until you have clear answers to all three, the prompt will be vague and the
agent will be inconsistent.

---

## The Decomposition Framework

For each agent on the SCQ platform, define:

| Question | What to answer |
|---|---|
| Job statement | One sentence: what does this agent do? |
| Input | What does it receive? (message, history, context injected by web layer) |
| Output | What does it return? (coaching question, structured rubric, narrative) |
| Trigger | What kind of message should cause the agent to act? |
| Boundary | What is explicitly outside its scope? |
| One-turn definition | What does a single successful turn look like? |

---

## Matteo: Issue Analysis Coach

**Job statement:**
Matteo guides students through the SCQ (Situation, Complication, Question)
framework using Socratic questioning, one question per turn.

**Input:**
- The student's message (what they wrote about their case situation)
- History of previous turns in this session
- Web layer injects: user_id, cohort_id (Matteo does not use these directly)

**Output:**
One coaching question that develops the student's thinking about the SCQ
structure. Plain conversational text, under 150 words.

**Trigger:**
Any student message about their business case, consulting scenario, or
SCQ structure.

**Boundary:**
- Matteo does not evaluate, score, or grade the student's work
- Matteo does not provide answers or model SCQ outputs
- Matteo does not handle questions about Juli or Tedd's tasks
- Matteo does not continue past a completed SCQ framework (that is Juli's entry point)

**One-turn definition:**
Student submits a statement about their case. Matteo reads it, identifies the
weakest element of the SCQ structure in the student's thinking, and returns
exactly one question that prompts the student to strengthen it.

---

## Juli: Monroe's Motivated Sequence Coach

**Job statement:**
Juli guides students through structuring a persuasive business recommendation
using Monroe's Motivated Sequence, one stage at a time.

**Input:**
- The student's message (their draft recommendation or argument)
- History of previous turns (which stages have been completed)
- Web layer injects: current stage (Attention, Need, Satisfaction, Visualisation, Action)

**Output:**
One guiding prompt or question that moves the student forward within the
current stage of Monroe's sequence. Under 150 words.

**Trigger:**
Any student message related to their business recommendation or argument structure.

**Boundary:**
- Juli does not review the underlying SCQ analysis (that is Matteo's job)
- Juli does not score or evaluate the final recommendation
- Juli does not skip stages on request, even if the student asks
- Juli does not write the recommendation for the student

**One-turn definition:**
Student submits a draft or partial recommendation. Juli identifies which stage
of Monroe's sequence the student is currently working on and returns a prompt
that helps them develop that stage more fully.

---

## Tedd: Peer Review Coach

**Job statement:**
Tedd evaluates a student's business case deliverable against the 5 Cs rubric
(Clear, Concise, Compelling, Credible, Consistent) and returns structured feedback.

**Input:**
- The student's submitted deliverable (full text)
- The 5 Cs rubric (injected by the web layer from a config file, not from the system prompt)
- Web layer injects: which Cs are being evaluated this turn

**Output:**
A structured assessment with a score per C (1-5) and one specific, actionable
observation per C. JSON format so the web layer can render it as a rubric card.

**Trigger:**
A student submitting a completed or partial deliverable for peer review.

**Boundary:**
- Tedd does not coach the student through revisions (that is Matteo and Juli)
- Tedd does not re-evaluate a deliverable that has already been finalised
- Tedd does not evaluate process or participation, only the written deliverable

**One-turn definition:**
Student submits a deliverable. Tedd scores it on all five Cs and returns one
observation per C in JSON format. One turn is one complete rubric evaluation.

---

## The Handoff Points

The three agents cover sequential stages of the student's work.
Understanding where one ends and the next begins prevents overlap and gaps.

```
Stage 1: Issue Analysis
  Agent: Matteo
  Student work: Developing the SCQ framework for their case
  Matteo is done when: Student has a complete, coherent SCQ
  Trigger for Juli: Student submits their completed SCQ for recommendation work

Stage 2: Recommendation Structuring
  Agent: Juli
  Student work: Building a persuasive recommendation using Monroe's Sequence
  Juli is done when: Student has worked through all five stages
  Trigger for Tedd: Student submits their final deliverable for peer review

Stage 3: Peer Review
  Agent: Tedd
  Student work: Receiving structured feedback on the completed deliverable
  Tedd is done when: All five Cs have been scored and feedback delivered
  Platform records the session as finalised
```

The web layer manages the handoff. It tracks which agent a student is currently
working with and routes their messages accordingly. The agents themselves do not
know about each other.

---

## What Not to Put in the Agent

When you define the task this precisely, it becomes clear what does not belong
in the agent at all:

- **Stage tracking** (which Monroe's stage the student is on): this is state.
  It belongs in the database (Tier 3 from Framework 09), read by the web layer
  and injected into the agent's context.

- **Rubric text** (the 5 Cs definitions): this is configuration. It belongs in
  a config file loaded by the web layer. The agent receives it as part of the
  message context, not hardcoded in the system prompt.

- **Session completion logic** (deciding when a student has finished with Matteo):
  this is a business rule. It belongs in the Express route, not in the agent.

This is Framework 01 applied strictly: the agent reasons and responds.
Everything else is the web layer's job.

---

## Recording Your Task Definitions in CLAUDE.md

Add a Task Definitions section to your CLAUDE.md:

```
## Task Definitions

Matteo:
  Job: Guide students through the SCQ framework using Socratic questioning.
  One turn: student message in, one coaching question out.
  Output format: plain text, under 150 words, ends with one question.
  Out of scope: scoring, model answers, Juli/Tedd topics.

Juli:
  Job: Guide students through Monroe's Motivated Sequence for recommendations.
  One turn: student draft in, one stage-specific prompt out.
  Output format: plain text, under 150 words.
  Out of scope: SCQ review, evaluation, skipping stages.

Tedd:
  Job: Evaluate deliverables against the 5 Cs rubric.
  One turn: deliverable in, scored rubric out (JSON).
  Output format: JSON with score and observation per C.
  Out of scope: revision coaching, process evaluation, finalised submissions.
```

This section is what any future Claude Code session reads to understand exactly
what each agent is supposed to do before touching any agent file.

---

## Starter Code

Working task definition files in `starter-code/04-task-decomposition/`:

```
04-task-decomposition/
├── task-definitions.md     Full definitions for all three agents (reference)
├── matteo-task.json        Structured task definition for Matteo
├── juli-task.json          Structured task definition for Juli
└── tedd-task.json          Structured task definition for Tedd
```

---

## Assignment

[04-decompose-your-task.md](assignments/04-decompose-your-task.md)

---

Copyright Janna AI Research Labs
