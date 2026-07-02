# Framework 03: Project Structure

> The way you organise files before writing code determines how easy the agent
> is to extend, debug, and hand to another developer. Structure is a decision,
> not a default.

---

## Why Structure Matters Before Code

Most agent tutorials give you one file: `agent.py`. Everything, client setup,
tool definitions, prompt, loop, lives in one place. That works for a demo.
It collapses the moment you add a second tool, a second prompt variant, or a
second developer.

Structure answers three questions before code is written:
1. Where does each type of concern live?
2. What can I change without touching anything else?
3. Where do I look when something breaks?

---

## The Standard Agent Project Layout

```
your-agent/
│
├── agent/                      # Core agent package, imported everywhere
│   ├── __init__.py
│   ├── infrastructure.py       # API client, logger, retry config
│   ├── model_config.py         # Model ID, token budget, temperature
│   ├── tool_registry.py        # Tool schemas + dispatcher + implementations
│   ├── context.py              # Context dataclass, system message builder, history
│   └── runner.py               # Agentic loop, the only place that calls the API
│
├── tools/                      # Complex tool implementations (if tool_registry grows large)
│   ├── __init__.py
│   ├── customer.py             # get_customer_record, update_customer_record
│   ├── billing.py              # apply_discount, process_refund
│   └── inventory.py            # check_stock, reserve_item
│
├── prompts/                    # System message templates, one file per agent role
│   ├── customer_support.py
│   ├── sales_assistant.py
│   └── operations_monitor.py
│
├── tests/                      # One test file per module
│   ├── test_tool_registry.py
│   ├── test_context.py
│   └── test_runner.py
│
├── .env                        # Secrets, never committed to git
├── .env.example                # Template showing required var names (no values)
├── .gitignore                  # Must include .env
├── requirements.txt            # Pinned dependencies
└── main.py                     # Entry point, wires all modules together
```

---

## The Rules Behind the Layout

### Rule 1: One file, one concern

`infrastructure.py` knows about the API client. It does not know about tools.
`tool_registry.py` knows about tools. It does not know about the API client.
`runner.py` is the only file that imports both, it is the wiring layer.

If you find yourself importing `tool_registry` inside `infrastructure.py`,
something has gone wrong. You are mixing concerns.

### Rule 2: The agent/ package has no business logic

`agent/` is reusable infrastructure. It should be possible to lift the entire
`agent/` folder into a different project and have it work with new prompts and
new tools. Business logic belongs in `tools/` and `prompts/`.

### Rule 3: Prompts are not strings, they are modules

A system message for a customer support agent is different from one for a
sales assistant. Each lives in its own file in `prompts/`. This means:
- You can version-control prompt changes separately from code changes
- You can run A/B tests by swapping prompt modules
- You can read the prompt without reading the runner

### Rule 4: tests/ mirrors agent/

`tests/test_tool_registry.py` tests `agent/tool_registry.py`.
`tests/test_context.py` tests `agent/context.py`.
The test file structure tells you immediately what is covered and what is not.

### Rule 5: main.py is thin

`main.py` should read like a summary of what the agent does, not an
implementation of it. It imports, wires, and calls. No logic lives here.

---

## When to Split tools/ Out of tool_registry.py

Start with all tools in `tool_registry.py`. Split into `tools/` when:
- You have more than 6 tools
- Two tools share helper functions
- A tool implementation is more than ~30 lines

The split is mechanical: move the implementation functions into `tools/`,
leave the schemas and dispatcher in `tool_registry.py`, import from `tools/`.

---

## What the Starter Code Already Shows You

The `starter-code/` folder in this session demonstrates the `agent/` package.
It intentionally omits `tools/` and `prompts/` because the project is small.

When you customise the starter code for a real project, your first structural
decision is: does this agent need more than 4 tools? If yes, create `tools/`
from the start.

---

## Sample: Customisable Project Skeleton

Copy this tree and replace the placeholders:

```
[your-agent-name]/
│
├── agent/
│   ├── __init__.py
│   ├── infrastructure.py       # No changes needed, reuse as-is from starter-code
│   ├── model_config.py         # No changes needed, configure via .env
│   ├── tool_registry.py        # CUSTOMISE: replace example tools with yours
│   ├── context.py              # CUSTOMISE: adjust trim_history_if_needed threshold
│   └── runner.py               # No changes needed, the loop is universal
│
├── tools/                      # Create this when you have 5+ tools
│   ├── __init__.py
│   └── [your_domain].py        # e.g. hr.py, finance.py, logistics.py
│
├── prompts/
│   └── [your_role].py          # CUSTOMISE: your system message for this agent's role
│
├── tests/
│   └── test_tool_registry.py   # CUSTOMISE: test your tools
│
├── .env                        # Fill in your ANTHROPIC_API_KEY and settings
├── .env.example                # Commit this, shows required vars, no values
├── requirements.txt
└── main.py                     # CUSTOMISE: wire your prompt + start the session
```

---

## Apply to Your Coding Agent

**Task:** Add a project structure map to your CLAUDE.md so your coding agent
always knows where every type of file belongs and never creates files in the
wrong location.

**Why this matters:** A coding agent without a structure map places new files
wherever seems reasonable in the moment. Over several sessions, your project
drifts from the intended layout. Every future Claude session then has to
reverse-engineer where things live. A structure map in CLAUDE.md prevents this
permanently.

**Step 1: Copy this template**

```
## Project Structure

[your-agent-name]/
├── agent/                  # Core package: do not add business logic here
│   ├── infrastructure.py   # API client and logger
│   ├── model_config.py     # Model ID and limits: configure via .env
│   ├── tool_registry.py    # Tool schemas, implementations, dispatcher
│   ├── context.py          # Context dataclass, system message, history
│   └── runner.py           # Agentic loop: the only file that calls the API
├── tools/                  # Extended tool implementations (create when agent/ grows)
│   └── [domain].py         # e.g. hr.py, billing.py, logistics.py
├── prompts/                # System message templates, one file per agent role
│   └── [role].py           # e.g. customer_support.py, sales_agent.py
├── tests/                  # One test file per module
│   └── test_[module].py
├── .env                    # Secrets: never read or modify, never commit
├── .env.example            # Template only: safe to edit and commit
├── requirements.txt        # Pinned dependencies
└── main.py                 # Entry point: thin, wires modules, no logic here

Placement rules (apply every time a new file is created):
- New business logic goes in tools/ not agent/
- New system messages go in prompts/ not inline in main.py
- New tests go in tests/ mirroring the module they test
- Configuration changes go in .env, not hardcoded in any Python file
- main.py stays thin: if it grows past 50 lines, something belongs elsewhere
```

**Step 2: Update with your actual project name and domain**

Replace `[your-agent-name]` with your project folder name. Replace `[domain]`
with your business domain (e.g. `hr`, `finance`, `logistics`). If you do not
yet have a `tools/` folder, keep the entry but note "create when agent has 5+
tools."

**Step 3: Paste into CLAUDE.md**

Open your project CLAUDE.md. Add the completed structure under `## Project
Structure`. This should be the third section, after Architecture and Permissions.

**Step 4: Apply to your coding tool**

For Claude Code: paste into CLAUDE.md. When you ask Claude Code to create a
new file, it will check the structure map first. If you ask it to add a new
business rule, it will place it in `tools/` not in `agent/`.

For Cursor: paste into `.cursorrules`. Cursor will follow the placement rules
when suggesting where to create new files.

For Codex: add to the workspace system prompt so file placement decisions
follow the map.

**What you now have:** Every future coding agent session on this project opens
with a complete picture of where everything belongs. New files go in the right
place the first time, and the project stays navigable as it grows.

---

Copyright Janna AI Research Labs
