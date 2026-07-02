# Session Three: Business Case Logic

> This is where frameworks become features. Session Three implements real
> business logic patterns: approval workflows, pricing engines, routing rules,
> and data validation, all driven by an agent.

**Status: Coming after Session Two**

---

## What This Session Covers

Session Three takes the infrastructure from Session One and the prompt and
evaluation skills from Session Two, and applies them to concrete business cases.
Every document includes a full worked example with runnable code.

By this point you can design, build, and evaluate a working agent. Session Three
gives you the patterns for the most common business logic use cases, written as
agents you can copy and adapt to your own domain.

---

## Planned Documents

```
session-three/
├── 01-approval-workflow.md
│     Building an agent that routes requests through approval chains.
│     Multi-step human-in-the-loop (HITL) pattern.
│     Example: expense approval with tier-based routing.
│
├── 02-pricing-engine.md
│     Agent-driven pricing decisions with business rules.
│     Discount eligibility, tier pricing, dynamic adjustments.
│     Example: B2B SaaS pricing agent.
│
├── 03-data-validation.md
│     Using an agent to validate incoming data against business rules.
│     When rules are complex enough to need reasoning, not just regex.
│     Example: contract data validation before CRM entry.
│
├── 04-routing-and-triage.md
│     Classifying and routing incoming requests to the correct handler.
│     Multi-label classification, confidence thresholds, escalation.
│     Example: support ticket triage agent.
│
├── 05-document-extraction.md
│     Extracting structured fields from unstructured business documents.
│     Invoices, contracts, forms, emails.
│     Example: invoice processing agent.
│
├── 06-decision-audit-trail.md
│     Recording every agent decision for compliance and audit purposes.
│     What to store, how to store it, how to query it.
│
└── starter-code/
      One complete business case implementation per document.
      Each is a standalone, runnable Python agent.
```

---

## Prerequisites

Complete Sessions One and Two before starting Session Three. Session Three
assumes you can design, write, run, and evaluate a basic agent. The business
logic patterns here build directly on those skills.

---

Copyright Janna AI Research Labs
