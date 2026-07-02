# Session One: Starter Code

This folder is the hands-on companion to the 11 framework documents in `session-one/`.

The documents explain the *why* and the *what*.
This code is the *how*, a complete, runnable Python agent you copy, customise, and run.

---

## What Is Inside

```
starter-code/
├── agent/
│   ├── infrastructure.py   Layer 5, API client, logger, retry config
│   ├── model_config.py     Layer 4, Model ID, token limits, temperature
│   ├── tool_registry.py    Layer 3, Tool schemas, implementations, dispatcher
│   ├── context.py          Layer 2, System message builder, history, trimming
│   └── runner.py           Layer 1, Agentic loop (the only file that calls the API)
├── main.py                 Entry point, wires all layers together
├── requirements.txt        Python dependencies
└── .env.example            Template for your environment variables
```

Each file maps directly to a framework document:

| File | Document |
|---|---|
| `infrastructure.py` | 02-internal-setup.md (Layer 5) |
| `model_config.py` | 02-internal-setup.md (Layer 4) + 04-model-selection.md |
| `tool_registry.py` | 02-internal-setup.md (Layer 3) + 07-tool-design.md |
| `context.py` | 02-internal-setup.md (Layer 2) + 06-context-window-budget.md |
| `runner.py` | 02-internal-setup.md (Layer 1) |
| `.env.example` | 05-environment-config.md |

---

## How to Use It

### Step 1: Copy the folder to your project

```bash
cp -r session-one/starter-code/ your-project-name/
cd your-project-name/
```

### Step 2: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Set up your environment

```bash
cp .env.example .env
# Open .env and fill in your ANTHROPIC_API_KEY and settings
```

### Step 4: Customise the two files that describe your agent

**`agent/tool_registry.py`**: Replace the example tools with your own.
Follow the tool design rules in `session-one/07-tool-design.md`.

**`main.py`**: Replace the system message with your agent's role.
Use the template in `session-one/08-system-prompt-skeleton.md`.

### Step 5: Run it

```bash
python main.py
```

---

## What You Should NOT Change (Yet)

`infrastructure.py`, `model_config.py`, `context.py`, and `runner.py` are
infrastructure, they work as-is and apply to any agent. Customise them only
when you have a specific reason (different retry logic, custom trimming strategy,
etc.). Change the tools and the prompt first.

---

## The Customisation Points

```
main.py
  └── start_agent_session()
        └── build_system_message(role_context=..., rules=[...])
                                  ↑ CUSTOMISE THIS

agent/tool_registry.py
  ├── TOOLS = [...]               ↑ CUSTOMISE THIS, add your tool schemas
  ├── def your_function(...)      ↑ CUSTOMISE THIS, implement your tools
  └── TOOL_DISPATCH = {...}       ↑ CUSTOMISE THIS, register your tools
```

Everything else is wiring. Leave it alone until you understand why it exists.

---

Copyright Janna AI Research Labs
