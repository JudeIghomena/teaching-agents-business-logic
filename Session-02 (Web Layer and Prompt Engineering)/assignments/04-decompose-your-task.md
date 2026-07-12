# Assignment 04: Decompose Your Task

**What you are building:** Precise job definitions for Matteo, Juli, and Tedd that go into your CLAUDE.md and drive every prompt decision from this point forward
**Why it matters:** Vague task definitions produce vague agents. A prompt written without a clear job statement will be rewritten repeatedly as the agent fails in ways you did not anticipate. This assignment forces clarity before you write a single prompt.
**Time estimate:** 30 minutes
**Reads with:** 04-task-decomposition.md

---

## What You Are Going To Do

You are going to write a precise task definition for each of the three SCQ agents using the four-field format from the document. These definitions will be added to your CLAUDE.md as the Task Definitions section. Every prompt you write in Assignments 05 and 06 must align to these definitions.

---

## What a Task Definition Must Do

A task definition answers four questions:

```
1. Job statement    What does this agent do in one sentence?
2. Input            What does it receive, exactly?
3. Output           What does it return, exactly?
4. Boundary         What is explicitly out of scope?
```

The boundary is the most important field. Without it, agents drift into topics they were not designed for and produce inconsistent results.

---

## Step 1: Read the Platform Overview Again

Before writing your task definitions, re-read the agent descriptions in `00-platform-overview.md`. Focus on how Matteo, Juli, and Tedd work together as a sequence, not as independent tools.

The key constraint: a student cannot skip from Matteo to Tedd. The platform enforces the sequence. Your task definitions should reflect this.

---

## Step 2: Write Matteo's Task Definition

Use this template. Fill in the bracketed sections based on your understanding of Matteo's role:

```
Matteo:
  Job: Guide students through the SCQ framework using Socratic questioning.
       The student does all the thinking. Matteo does not provide answers.
  Input: One student message per turn. May contain a draft Situation,
         Complication, or Question, or a question about the framework.
  Output: Plain text, maximum 120 words, ending with exactly one question.
          No evaluation phrases. No markdown.
  Boundary: Does NOT handle Monroe's Sequence, 5 Cs evaluation, slide design,
            or any recommendation-stage work. If asked, redirect to Juli or Tedd.
```

Copy this into the Task Definitions section of your CLAUDE.md.

---

## Step 3: Write Juli's Task Definition

```
Juli:
  Job: Guide students through Monroe's Motivated Sequence for recommendations.
       Five stages in order: Attention, Need, Satisfaction, Visualisation, Action.
  Input: One student draft per turn. The web layer injects which stage is active.
         Juli receives the student's confirmed SCQ from Matteo as context.
  Output: Plain text, maximum 150 words, ending with one coaching prompt.
          Must end with a stage tag: [STAGE: StageName].
  Boundary: Does NOT review SCQ framework, score deliverables, or coach on
            a stage the student has not yet reached.
```

Copy this into CLAUDE.md under Matteo's definition.

---

## Step 4: Write Tedd's Task Definition

```
Tedd:
  Job: Evaluate completed deliverables against the 5 Cs rubric:
       Clear, Concise, Compelling, Credible, Consistent.
  Input: A complete student deliverable (recommendation text).
         Tedd evaluates once per submission. Second submissions are rejected.
  Output: Raw JSON only. No preamble. Schema:
          { "evaluation": { "clear": { "score": 1-5, "observation": "sentence" }, ... } }
  Boundary: Does NOT coach, suggest revisions, or explain how to improve.
            Tedd observes and scores. Coaching is Matteo and Juli's job.
```

Copy this into CLAUDE.md under Juli's definition.

---

## Step 5: Check Your Definitions for Gaps

After writing all three, read them as a set and answer these questions:

1. Is there any student action that falls outside all three definitions?
   (For example: "What if a student asks Matteo to evaluate their final recommendation?")
   Write the answer and add it to the relevant agent's Boundary field.

2. Does each agent's Output field give enough information to write a format validator?
   If you cannot write a regex or function that checks the output format from the definition alone, make it more specific.

3. Do the three agents form a complete sequence?
   Matteo confirms SCQ. Juli builds the recommendation. Tedd evaluates it.
   Is there a gap between any two agents?

---

## Step 6: Update CLAUDE.md

Open your CLAUDE.md. Add a new section called Task Definitions. Paste in all three definitions. The section should look like this:

```
## Task Definitions

Matteo:
  Job: ...
  Input: ...
  Output: ...
  Boundary: ...

Juli:
  Job: ...
  Input: ...
  Output: ...
  Boundary: ...

Tedd:
  Job: ...
  Input: ...
  Output: ...
  Boundary: ...
```

Every prompt you write from this point must align to the relevant task definition. If the prompt says something that contradicts the definition, fix the definition first, then write the prompt.

---

## You Are Done When

- [ ] CLAUDE.md has a Task Definitions section with all three agents
- [ ] Each definition has all four fields: Job, Input, Output, Boundary
- [ ] Matteo's Output field specifies maximum word count and question requirement
- [ ] Tedd's Output field specifies the exact JSON schema
- [ ] Each Boundary field has at least two explicit exclusions

---

## If You Get Stuck

The definitions feel too abstract: read the platform overview again and write the definition as if you were explaining the agent to a new team member in one minute. Specificity comes from imagining what that person would get wrong if the definition was vaguer.

The Boundary fields are empty: think about the most natural thing a user might ask that the agent should refuse. For Matteo: "Can you write the SCQ for me?" For Tedd: "How should I improve my concise score?" Those refusal cases belong in the Boundary.

---

## Next Assignment

[05-apply-prompt-engineering.md](05-apply-prompt-engineering.md)

---

Copyright Janna AI Research Labs
