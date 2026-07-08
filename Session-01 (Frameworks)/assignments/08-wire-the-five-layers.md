# Assignment 08: Wire the Five Layers

**What you are building:** A fully wired, running agent where all five layers connect and work together end to end
**Why it matters:** Each of the previous seven assignments built one piece in isolation. This assignment connects them. An agent where the layers do not communicate correctly will fail in ways that are hard to debug. Getting the wiring right once means all future changes build on a solid foundation.
**Time estimate:** 45 minutes
**Reads with:** 08-internal-setup.md

---

## What You Are Going To Do

You are going to trace the path of a single message through all five layers, confirm each layer hands off correctly to the next, and verify the complete loop runs without errors.

---

## The Five-Layer Flow

Every message follows this path:

```
User message
    │
    ▼
Layer 2: context.py
    build_system_message()     assembles the system prompt
    trim_history()             cuts history to fit the budget
    │
    ▼
Layer 4: model_config.py
    MODEL, MAX_TOKENS          sets the model parameters
    TEMPERATURE
    │
    ▼
Layer 5: infrastructure.py
    get_client()               returns the Anthropic API client
    │
    ▼
Layer 3: tool_registry.py
    TOOLS                      passed to the API call as tools parameter
    TOOL_DISPATCH              used to route tool_use results
    │
    ▼
Layer 1: runner.py
    run_agent_loop()           the agentic loop:
                               1. call the API
                               2. if tool_use: dispatch, get result, loop
                               3. if end_turn: return the response
```

---

## Step 1: Confirm Each Layer Imports Correctly

Run this in a Python shell from your project root:

```python
from agent.infrastructure import get_client
from agent.model_config import MODEL, MAX_TOKENS, TEMPERATURE
from agent.tool_registry import TOOLS, TOOL_DISPATCH
from agent.context import build_system_message, trim_history
from agent.runner import run_agent_loop

print("infrastructure:", get_client().__class__.__name__)
print("model:", MODEL)
print("tools:", [t["name"] for t in TOOLS])
print("system prompt length:", len(build_system_message()), "chars")
print("All layers imported successfully")
```

All five lines should print without errors. If any import fails, fix the import before continuing.

---

## Step 2: Trace a Message Through the Loop

Open `agent/runner.py` and add a temporary trace to see each step:

```python
# Temporarily add to run_agent_loop() for debugging
# Remove these print statements after this assignment

def run_agent_loop(user_message: str, history: list = None) -> str:
    history = history or []

    system = build_system_message()
    history = trim_history(history)

    print(f"[TRACE] System prompt: {len(system)} chars")
    print(f"[TRACE] History: {len(history)} messages")
    print(f"[TRACE] Model: {MODEL}")

    messages = history + [{"role": "user", "content": user_message}]
    client = get_client()

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=system,
        tools=TOOLS,
        messages=messages
    )

    print(f"[TRACE] Stop reason: {response.stop_reason}")

    # Handle tool use
    while response.stop_reason == "tool_use":
        tool_calls = [b for b in response.content if b.type == "tool_use"]
        tool_results = []

        for call in tool_calls:
            print(f"[TRACE] Tool called: {call.name} with {call.input}")
            fn = TOOL_DISPATCH.get(call.name)
            if fn:
                result = fn(**call.input)
            else:
                result = {"error": f"Tool {call.name} not found"}
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": call.id,
                "content": str(result)
            })

        messages = messages + [
            {"role": "assistant", "content": response.content},
            {"role": "user", "content": tool_results}
        ]
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system,
            tools=TOOLS,
            messages=messages
        )
        print(f"[TRACE] Stop reason after tool: {response.stop_reason}")

    return response.content[0].text
```

Run `python main.py` and send a message. You should see the TRACE lines printing the state at each layer.

---

## Step 3: Verify Tool Dispatch Works

Send a message that should trigger your tool from Assignment 06. Confirm the TRACE output shows:

```
[TRACE] Tool called: your_tool_name with {'param': 'value'}
[TRACE] Stop reason after tool: end_turn
```

If the tool is not called, the schema description may not be specific enough. Refer to Assignment 06 for debugging.

---

## Step 4: Remove Trace Lines

Once you have confirmed all five layers connect and the tool dispatch works, remove the `print(f"[TRACE]...")` lines from runner.py. The structured logger in infrastructure.py handles production logging. Do not leave debug prints in the code.

---

## Step 5: Run a Clean End-to-End Test

Run `python main.py` and have a three-turn conversation with your agent:

Turn 1: A message that does not trigger any tool. Confirm the agent responds according to its system prompt.
Turn 2: A message that should trigger your tool. Confirm the tool is called and the result is used.
Turn 3: A follow-up that references something from Turn 1. Confirm history is working (the agent remembers Turn 1).

---

## You Are Done When

- [ ] All five layers import without errors
- [ ] The TRACE output shows the correct model, system prompt length, and history count
- [ ] Tool dispatch works: the tool is called and the result appears in the response
- [ ] A three-turn conversation shows history working correctly
- [ ] No TRACE print statements remain in the code
- [ ] `python main.py` runs cleanly with no warnings or errors in the terminal

---

## If You Get Stuck

Import fails with "No module named agent": confirm you are running from the project root, not from inside the agent/ folder.

Tool dispatch returns "Tool not found": the name in TOOL_DISPATCH does not match the name in TOOLS exactly. Both must be identical strings.

History not persisting between turns: main.py must pass history into run_agent_loop and update it after each response. Check that main.py is accumulating history correctly.

Response is empty: the model returned an empty content block. This usually means MAX_TOKENS is too low. Increase it temporarily to 4096 to debug.

---

## Next Assignment

[09-add-memory-to-your-agent.md](09-add-memory-to-your-agent.md)

---

Copyright Janna AI Research Labs
