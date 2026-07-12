# Assignment 01: Map Your Agent Layers

**What you are building:** A layer ownership map for your agent that goes into your CLAUDE.md
**Why it matters:** Every decision you make in the next ten assignments depends on knowing which layer owns which responsibility. Mapping this first prevents you from putting the wrong logic in the wrong place.
**Time estimate:** 20 minutes
**Reads with:** 01-agent-mental-model.md

---

## What You Are Going To Do

You are going to draw the five layers of your specific agent and write one sentence per layer describing what it does. Then you are going to paste that map into your CLAUDE.md so your coding agent always knows the architecture.

The five layers are:

```
Layer 5: Infrastructure      API client, logger, retry logic
Layer 4: Model Config        Model ID, token limits, temperature
Layer 3: Tool Registry       Tool schemas, implementations, dispatcher
Layer 2: Context Architecture System message builder, history management
Layer 1: The Prompt          The instructions the model reads at runtime
```

---

## Step 1: Open Your CLAUDE.md

If you have not already copied the CLAUDE.md template from Session-01 starter code, do that now:

```bash
cp "Session-01 (Frameworks)/starter-code/CLAUDE.md" ./CLAUDE.md
```

Open CLAUDE.md in your editor. Find the section called "Layer Ownership".

---

## Step 2: Fill In the Layer Ownership Table

Replace every placeholder with a description specific to your agent.

Here is an example for a customer support agent:

```
| Layer | Name | Handled by |
|---|---|---|
| Layer 5 | Infrastructure | infrastructure.py: Anthropic client, retry on 529, structured logger |
| Layer 4 | Model Config | model_config.py: claude-haiku-4-5, 8k max tokens, temperature 0.0 |
| Layer 3 | Tool Registry | tool_registry.py: get_order_status, escalate_to_human, check_refund_policy |
| Layer 2 | Context Architecture | context.py: system message builder, last-10-turns history trimming |
| Layer 1 | The Prompt | Defined in 07-system-prompt-skeleton.md, implemented in context.py |
```

Fill in your own version. Do not copy the example exactly. Use your agent's actual tool names and files.

If you do not know your tool names yet, write "TBD" for Layer 3 and come back after Assignment 06.

---

## Step 3: Copy the Starter Code

Copy the Session-01 starter code into your project folder:

```bash
cp -r "Session-01 (Frameworks)/starter-code/" ~/my-agent-project/
cd ~/my-agent-project
pip install -r requirements.txt
```

Open `agent/infrastructure.py`, `agent/model_config.py`, `agent/tool_registry.py`,
`agent/context.py`, and `agent/runner.py` in your editor.

Match what you see in each file to the layer in your table. Every file maps to
one layer. This confirms your table is correct.

---

## Step 4: Run the Agent

Verify the starter code runs before you customise anything:

```bash
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
python main.py
```

Type a message. You should get a response from Claude. If you do, the five
layers are wired correctly and you are ready to build on them.

---

## You Are Done When

- [ ] Your CLAUDE.md Layer Ownership table has all five rows filled in with your agent's specifics
- [ ] You can match each row in your table to a file in the starter-code/agent/ folder
- [ ] `python main.py` runs and returns a response
- [ ] You have not changed any agent/ file yet (those come in later assignments)

---

## If You Get Stuck

`python main.py` shows "ModuleNotFoundError": run `pip install -r requirements.txt` first.

`python main.py` shows "AuthenticationError": check that ANTHROPIC_API_KEY is set in your .env file and that there are no quotes around the value.

The agent responds but ignores your message: this is expected at this stage. The starter code has a placeholder system prompt. You will write the real one in Assignment 07.

---

## Next Assignment

[02-create-your-project-structure.md](02-create-your-project-structure.md)

---

Copyright Janna AI Research Labs
