# Session 02: The Platform and What You Are Building

> Before you write a single line of code in this session, you need a clear picture
> of what you are building, who it serves, and what each agent is responsible for.
> Every technical decision in Sessions 02 through 06 connects back to this document.

---

## What This Session Covers

Session 02 has two parts. First, the web layer: the Express server, database,
and authentication that make the agents accessible from a browser. Second, the
intelligence layer: task definitions, prompt engineering, few-shot examples,
output format control, evaluation, and iteration.

| Document | What it builds |
|---|---|
| 00-platform-overview.md (this file) | The platform, the agents, the student journey |
| 01-web-integration-layer.md | Express route, SSE streaming, Python agent wiring |
| 02-database-schema-design.md | Sessions table, conversation history storage |
| 03-jwt-and-authentication.md | Login route, JWT signing, role guards |
| 04-task-decomposition.md | Precise job definitions for Matteo, Juli, and Tedd |
| 05-prompt-engineering-principles.md | Five principles applied to Matteo's system prompt |
| 06-few-shot-examples.md | Examples added to Matteo and Tedd's prompts |
| 07-output-format-control.md | Enforced output formats for all three agents |
| 08-evaluation-methods.md | Golden dataset, LLM-as-judge, format validators |
| 09-iteration-workflow.md | Versioned prompts, iteration log, pre-commit gate |

**What you will have at the end of Session 02:**
A working web API with authenticated agent endpoints, a database storing
conversation history, precise task definitions for all three agents, and
a system prompt for Matteo that has been evaluated and iterated at least once.

**Previous session:** [Session 01 - The Frameworks](../Session-01%20(Frameworks)/00-session-overview.md)
**Next session:** Session 03 - Building Matteo, Juli, and Tedd

---

---

## What Is the Business Case Logic Platform?

The Business Case Logic platform is an AI-powered coaching application for MBA
students working on consulting capstone cases. Students use it to develop
structured business thinking through guided conversations with three AI coaching
agents.

The platform does not give students answers. It coaches them through the process
of finding their own answers, in the same way a senior consultant would coach
a junior analyst, with questions, frameworks, and structured feedback.

The product you are building is called the **SCQ Simulation Portal**.

---

## The Student's Journey

A student using the SCQ Simulation Portal works through three coaching stages
in sequence. Each stage is handled by a different AI agent.

```
Stage 1: Issue Analysis
    The student defines the business problem they are solving.
    They work with Matteo to build a rigorous SCQ framework.

    Student enters with: a case scenario and initial thoughts
    Student exits with: a clear Situation, Complication, and Question

         |
         v

Stage 2: Recommendation Structuring
    The student builds a persuasive recommendation for the decision-maker.
    They work with Juli through five structured stages.

    Student enters with: a clear SCQ and a recommendation direction
    Student exits with: a fully structured persuasive argument

         |
         v

Stage 3: Peer Review
    The student's deliverable is evaluated against a quality rubric.
    Tedd scores it on five dimensions and returns specific feedback.

    Student enters with: a completed recommendation document
    Student exits with: a rubric score and one observation per dimension
```

Each stage is a separate agent. Stages are sequential. A student cannot skip
from Stage 1 to Stage 3 without completing Stage 2.

---

## Meet the Three Agents

### Matteo - Issue Analysis Coach

Matteo coaches students through the SCQ framework: Situation, Complication, Question.

**The SCQ framework** is a structured approach to defining a business problem:
- **Situation**: the context that everyone agrees on
- **Complication**: what has changed or what tension has emerged in that situation
- **Question**: the decision the client needs to make as a result of the complication

Most students come to Matteo with a vague sense of "the client has a problem."
Matteo's job is to help them identify precisely what the problem is, why it matters,
and what decision needs to be made. Not by telling them, but by asking the right question.

**Matteo's method is Socratic.** He never states the answer. He never writes any
part of the SCQ for the student. Every response ends with exactly one question that
targets the weakest element of the student's current thinking.

A session with Matteo typically runs 10 to 20 turns. By the end, the student has
a precise, well-reasoned SCQ framework that they built themselves.

**Example exchange:**

> Student: "The situation is that our client is a retail bank losing customers to digital competitors."
>
> Matteo: "You have described what is happening across the industry. What is specific to this client's situation that makes their position different from other retail banks facing the same trend?"

---

### Juli - Monroe's Motivated Sequence Coach

Juli coaches students through structuring a persuasive business recommendation
using Monroe's Motivated Sequence.

**Monroe's Motivated Sequence** is a five-stage framework for persuasive communication,
originally developed for public speaking and now widely used in management consulting:

1. **Attention**: capture the audience's focus with the central issue
2. **Need**: establish why this issue demands a decision now
3. **Satisfaction**: present your recommended solution
4. **Visualisation**: paint a picture of what success (and failure to act) looks like
5. **Action**: define the specific next steps for the decision-maker

Students often write recommendations that jump straight to the solution without
establishing why it matters or what happens if nothing is done. Juli guides them
through each stage in order, ensuring the argument is complete and compelling.

**Juli does not skip stages.** If a student tries to jump ahead, Juli explains
why the current stage must be completed first and continues working on it.

A session with Juli typically runs 8 to 15 turns, five to three turns per stage.
Each of Juli's responses identifies which stage the student is working on and
guides them forward within that stage.

**Example exchange:**

> Student: "My recommendation is that the bank should invest in a mobile-first digital platform and close 30% of branches over three years."
>
> Juli: "You have described your solution clearly. Before your audience can evaluate it, they need to understand the specific consequences of not acting. What happens to the bank's competitive position if this investment is delayed by 18 months?" [STAGE: Need]

---

### Tedd - 5 Cs Peer Review Evaluator

Tedd evaluates a student's completed business case deliverable against the 5 Cs rubric
and returns a structured score with specific feedback.

**The 5 Cs rubric** evaluates professional business communication:

| Dimension | What it measures |
|---|---|
| **Clear** | The reader understands what is being proposed and why within the first paragraph |
| **Concise** | The argument makes its point without unnecessary length or repetition |
| **Compelling** | The argument motivates the reader to act, not just to understand |
| **Credible** | Claims are supported with evidence, data, or sound reasoning |
| **Consistent** | The recommendation, timeline, and supporting analysis do not contradict each other |

Tedd scores each dimension from 1 to 5 and provides one specific, actionable
observation per dimension. Not general advice. An observation specific to
what was written in this student's deliverable.

Unlike Matteo and Juli, Tedd does not coach. He evaluates. His responses are
structured JSON that the web layer renders as a rubric card. The student sees
their scores and one sentence of feedback per dimension.

**Example output:**

```json
{
  "evaluation": {
    "clear": {
      "score": 4,
      "observation": "The central recommendation is in the opening paragraph and the reader knows what is being proposed within two sentences."
    },
    "concise": {
      "score": 2,
      "observation": "The Need section runs 380 words. The core argument could be made in 140. The additional detail does not add evidence."
    },
    "compelling": {
      "score": 3,
      "observation": "The Visualisation stage describes a financial projection but does not connect it to the client's stated growth target."
    },
    "credible": {
      "score": 4,
      "observation": "Three cited sources support the market sizing. The competitive analysis framework is correctly applied."
    },
    "consistent": {
      "score": 3,
      "observation": "The Action section calls for a 12-month rollout but the Satisfaction section described a 6-month timeline."
    }
  }
}
```

---

## How the Three Agents Work Together

The agents are independent. They do not communicate with each other. The platform
manages the student's progression between them.

Each agent has a single job:
- Matteo knows nothing about Monroe's Sequence or the 5 Cs
- Juli knows nothing about SCQ or peer review rubrics
- Tedd knows nothing about coaching or questioning techniques

This separation is intentional. It makes each agent simpler, more reliable, and
easier to improve. An agent that tries to do everything does everything poorly.

The web layer owns the progression logic: it tracks which stage the student is on,
routes their messages to the correct agent, and decides when a stage is complete.

---

## Why This Platform Is the Build Thread

Every framework from Session 01 exists in this platform. When you build the SCQ
Simulation Portal across Sessions 02 through 06, you are implementing those
frameworks in a real production context:

| Framework | Where it lives in the platform |
|---|---|
| Framework 01 (Agent Mental Model) | The three agents have precisely bounded jobs |
| Framework 02 (Project Structure) | server/ and agent/ layer separation |
| Framework 03 (Model Selection) | haiku for Matteo and Juli, haiku with sonnet fallback for Tedd |
| Framework 04 (Context Window Budget) | Session history managed per agent per student |
| Framework 05 (Environment Config) | JWT_SECRET, ANTHROPIC_API_KEY, database path |
| Framework 06 (Tool Design) | save_scq_draft, get_rubric_config, get_student_history |
| Framework 07 (System Prompt Skeleton) | Five-section prompts for all three agents |
| Framework 08 (Internal Setup) | run_agent_loop() called by Express, not by a CLI |
| Framework 09 (Memory and State) | agent_sessions table in SQLite |
| Framework 10 (Observability) | TurnTrace per agent, LLM-as-judge for quality |
| Framework 11 (Security Baseline) | JWT auth, role guards, parameterised queries |

By the end of Session 06, you will have a working multi-agent coaching platform.
The same architecture scales to any number of agents and any coaching domain.

---

## What You Are Not Building in This Course

To keep the scope manageable across six sessions, the following are out of scope:

- A React or Next.js frontend (the platform runs via API and command-line testing)
- User registration and profile management
- A professor dashboard UI (the database can be queried directly for now)
- Email notifications or reminders
- Payment or subscription handling
- Deployment to a cloud host (covered as an optional extension in Session 06)

You are building the agent layer and the API that powers it. A frontend can be
added on top of the API at any point without changing the agents.

---

## Before You Start Building

Read this document once more and answer these three questions in your own words:

1. What is Matteo's job in exactly one sentence?
2. What is the difference between how Juli and Tedd interact with the student?
3. What does the web layer own that none of the three agents should ever do?

If you can answer all three clearly, you are ready to start Build 01.

---

## Next

[Build 01: The Web Integration Layer](01-web-integration-layer.md)

---

Copyright Janna AI Research Labs
