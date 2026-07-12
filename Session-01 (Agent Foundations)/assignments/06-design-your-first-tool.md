# Assignment 06: Design Your First Tool

**What you are building:** One complete tool in tool_registry.py, with a JSON schema, a Python implementation, and a dispatcher entry
**Why it matters:** A tool the model cannot understand will be called incorrectly or not at all. Getting the schema right once establishes the pattern for every tool you add to this agent.
**Time estimate:** 30 minutes
**Reads with:** 06-tool-design.md

---

## What You Are Going To Do

You are going to design one tool your agent actually needs, write its JSON schema, implement the function it calls, register it in the dispatcher, and add it to the Registered Tools table in your CLAUDE.md.

---

## Step 1: Choose Your First Tool

A tool is an action the agent can take in the real world: look something up, make a calculation, write a record, call an API. It is not a task for the agent itself.

Answer this: what is the one thing your agent must be able to do that the model cannot do on its own?

Examples:
- A support agent needs to look up a customer's order status
- A procurement agent needs to check a budget balance
- A coaching agent needs to save the student's current score
- An analysis agent needs to read a document from disk

Write your answer here before moving to Step 2: ______________

---

## Step 2: Write the Tool Schema

Open `agent/tool_registry.py`. Add your tool to the TOOLS list:

```python
# agent/tool_registry.py

TOOLS = [
    {
        "name": "get_order_status",          # snake_case, verb_noun format
        "description": (
            "Look up the current status of a customer order by order ID. "
            "Returns the status (pending, shipped, delivered, cancelled) "
            "and the estimated delivery date if the order is in transit. "
            "Use this when the customer asks about their order."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order ID exactly as the customer provided it"
                }
            },
            "required": ["order_id"]
        }
    }
]
```

Replace this example with your actual tool. Three schema rules to follow:

1. The description must tell the model WHEN to use the tool, not just what it does.
2. Every parameter needs a description that tells the model what format to use.
3. Mark every field the function cannot work without as required.

---

## Step 3: Implement the Tool Function

Below the TOOLS list, write the Python function:

```python
def get_order_status(order_id: str) -> dict:
    """
    Returns order status for a given order ID.
    In a real system this would query your database or call an external API.
    """
    # Placeholder implementation for now
    # Replace with real logic in Session-03
    return {
        "order_id": order_id,
        "status": "shipped",
        "estimated_delivery": "2026-07-15",
        "message": f"Order {order_id} is on its way."
    }
```

The function must:
- Accept the exact same parameter names as the schema defines
- Return a dict (the model receives this as a tool result)
- Never raise an unhandled exception. Catch errors and return them as a dict with an error key.

---

## Step 4: Register the Tool in the Dispatcher

Find the TOOL_DISPATCH dict in tool_registry.py and add your tool:

```python
TOOL_DISPATCH = {
    "get_order_status": get_order_status,
}
```

The key must exactly match the `name` field in the schema. The value is the
function. The dispatcher is the security allowlist: if a tool is not in this
dict, the agent cannot call it even if it tries.

---

## Step 5: Add the Tool to Your CLAUDE.md

Open your CLAUDE.md and fill in the Registered Tools table:

```
## Registered Tools

| Tool name | What it does | When to use it |
|---|---|---|
| get_order_status | Looks up order status by order ID | When the customer asks about a specific order |
```

Add your tool. The "When to use it" column is the most important: it mirrors
the WHEN instruction in your schema description and tells your coding agent
the correct context for each tool.

---

## Step 6: Test the Tool in Isolation

Before testing through the full agent, call your tool function directly:

```python
# Run in a Python shell
from agent.tool_registry import get_order_status

result = get_order_status(order_id="ORD-12345")
print(result)
```

Confirm the output is a dict with the fields your schema promises.

---

## Step 7: Test Through the Agent

Run the full agent and ask it to use the tool:

```bash
python main.py
```

Type a message that should trigger your tool. For example, if your tool looks
up order status: "What is the status of order ORD-12345?"

The agent should call the tool, receive the result, and use it in its response.
If it does not call the tool, check that the schema description clearly states
when to use it.

---

## You Are Done When

- [ ] `agent/tool_registry.py` has at least one tool in TOOLS with a complete schema
- [ ] The tool function is implemented and returns a dict
- [ ] The tool is registered in TOOL_DISPATCH
- [ ] Calling the function directly returns the expected output
- [ ] The agent calls the tool when given an appropriate message
- [ ] Your CLAUDE.md Registered Tools table has a row for the new tool

---

## If You Get Stuck

Agent never calls the tool: the schema description may not be clear enough. Add "Use this tool when..." explicitly to the description and retest.

Tool result is not used in the response: the model received the result but the context window budget may be too small to fit it. Increase MAX_TOKENS temporarily to debug.

"Tool not found" error: the name in TOOL_DISPATCH does not exactly match the name in TOOLS. They must be identical strings.

---

## Next Assignment

[07-write-your-system-prompt.md](07-write-your-system-prompt.md)

---

Copyright Janna AI Research Labs
