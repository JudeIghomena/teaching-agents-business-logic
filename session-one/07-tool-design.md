# Framework 07: Tool Design

> A tool the model cannot understand is a tool that will be called incorrectly.
> Tool design is not code — it is communication between you and the model.

---

## What a Tool Actually Is

A tool in the Anthropic API is a structured contract with three components:

```
┌─────────────────────────────────────────────────────────────────┐
│  name          The unique identifier the model uses to call it  │
│  description   What the model reads to decide WHEN to call it  │
│  input_schema  The JSON Schema the model uses to form the call  │
└─────────────────────────────────────────────────────────────────┘
```

The model never sees your Python function. It only sees the schema.
Your Python function never sees the model. It only sees the inputs the
dispatcher passes it.

This separation is what makes agents safe and testable.

---

## The Most Important Field: description

The `description` field is read by the model every time it reasons about
whether to call a tool. It is not documentation for humans — it is an
instruction to the model.

A bad description produces bad tool calls. A good description produces
precisely correct tool calls.

```python
# Bad — too vague: when should the model call this?
{
    "name": "get_data",
    "description": "Gets data.",
}

# Bad — too literal: tells the model WHAT it does, not WHEN to use it
{
    "name": "get_customer_record",
    "description": "Queries the customers table in the database by customer ID.",
}

# Good — tells the model WHEN to call it, with context about what follows
{
    "name": "get_customer_record",
    "description": (
        "Retrieves a customer's profile including account status, loyalty tier, "
        "and purchase history. Call this before making any decision that depends "
        "on the customer's eligibility, tier, or history. Do not guess customer "
        "details — always retrieve them."
    ),
}
```

**Rules for writing good descriptions:**
- State the WHEN, not just the WHAT
- Name what decisions this tool enables
- Add a negative instruction when misuse is likely ("Do not guess — always retrieve")
- Keep under 100 words — longer descriptions introduce noise

---

## Input Schema Design

### Use enum to constrain known values

When a parameter has a finite set of valid values, always use `enum`.
Without it, the model will invent plausible-sounding but invalid values.

```python
# Bad: the model might pass "goodwill", "VIP", "sorry about that"
"reason": {
    "type": "string",
    "description": "The reason for the discount.",
}

# Good: the model can only pass one of four valid values
"reason": {
    "type": "string",
    "enum": ["loyalty", "complaint_resolution", "promotional", "error_correction"],
    "description": "The business reason for the discount.",
}
```

### Set minimum and maximum on numbers

```python
# Without constraints, the model might request 150% discount
"discount_percent": {
    "type": "number",
    "description": "The discount percentage to apply.",
}

# With constraints, the model cannot exceed your business rules
"discount_percent": {
    "type": "number",
    "minimum": 1,
    "maximum": 50,
    "description": "The discount percentage to apply (1-50).",
}
```

### required vs optional parameters

Only put parameters in `required` if the function cannot run without them.
Optional parameters go in `properties` but not in `required`.

```python
"input_schema": {
    "type": "object",
    "properties": {
        "customer_id": {
            "type": "string",
            "description": "The customer's unique ID (required).",
        },
        "include_history": {
            "type": "boolean",
            "description": "Whether to include purchase history. Defaults to false.",
        },
    },
    "required": ["customer_id"],
    # include_history is optional — model passes it only when needed
}
```

---

## Tool Error Returns

How your tool returns errors shapes how the model recovers.

```python
# Bad: raises an exception — the loop crashes, no recovery possible
def get_customer_record(customer_id: str) -> dict:
    if not customer_id.startswith("CUS-"):
        raise ValueError("Invalid customer ID format")

# Good: returns a structured error — the model reads it and decides what to do
def get_customer_record(customer_id: str) -> dict:
    if not customer_id.startswith("CUS-"):
        return {
            "success": False,
            "error": "invalid_id_format",
            "message": "Customer IDs must start with CUS-. The provided ID does not match this format.",
            "suggestion": "Ask the customer to confirm their ID from their account confirmation email.",
        }
    # ... proceed with lookup
```

A structured error return gives the model:
- What went wrong (`error` field — machine-readable)
- Why it went wrong (`message` field — human-readable)
- What to try next (`suggestion` field — agent-readable)

The model will incorporate this into its next response naturally.

---

## When NOT to Use a Tool

Tools are not always the answer. Some tasks should stay in the prompt.

| Use a tool when | Use the prompt when |
|---|---|
| You need to read from or write to an external system | The information is static and known in advance |
| The data changes between sessions | The rules never change |
| The operation has side effects (write, send, update) | You are just formatting or classifying |
| You need fresh data at query time | The model can reason about it from context |

**Example — wrong use of a tool:**

```python
# This tool retrieves data that never changes and could be in the system message
{
    "name": "get_discount_tiers",
    "description": "Returns the company discount tier structure.",
}
# If discount tiers change quarterly at most, put them in the system message.
# A tool call costs tokens and latency. A system message costs only tokens.
```

**Example — correct use of a tool:**

```python
# This tool retrieves data that is different for every customer
{
    "name": "get_customer_discount_eligibility",
    "description": "Checks whether this specific customer is currently eligible for a discount.",
}
# This must be a tool — you cannot know the answer without querying live data.
```

---

## The Dispatcher Pattern (Security)

Every tool call from the model goes through one chokepoint: the dispatcher.

```python
# agent/tool_registry.py

TOOL_DISPATCH: dict[str, callable] = {
    "get_customer_record": get_customer_record,
    "apply_discount": apply_discount,
    "send_confirmation_email": send_confirmation_email,
}

def dispatch_tool(tool_name: str, tool_input: dict) -> any:
    """
    The only place in the codebase where tool names map to functions.

    If tool_name is not in TOOL_DISPATCH, we raise immediately.
    The model cannot call functions that are not registered here —
    even if those functions exist in the codebase.

    This is an allowlist, not a blocklist.
    """
    if tool_name not in TOOL_DISPATCH:
        raise ValueError(
            f"Unregistered tool: '{tool_name}'. "
            f"Available: {list(TOOL_DISPATCH.keys())}"
        )
    return TOOL_DISPATCH[tool_name](**tool_input)
```

---

## Sample: Full Tool Definition to Customise

Replace the placeholders to define your own tool:

```python
{
    "name": "[action_verb]_[noun]",
    # Examples: get_invoice, create_ticket, update_shipment, check_availability

    "description": (
        "[What it retrieves or does]. "
        "Call this when [situation that requires this tool]. "
        "[What the result enables]. "
        "[One negative instruction if misuse is plausible]."
    ),

    "input_schema": {
        "type": "object",
        "properties": {
            "[required_param]": {
                "type": "string",  # or "number", "boolean", "array"
                "description": "[What this param is, format if relevant].",
                # Add "enum": [...] if values are finite and known
                # Add "minimum"/"maximum" if numeric with valid range
            },
            "[optional_param]": {
                "type": "boolean",
                "description": "[What this param controls. Defaults to X].",
            },
        },
        "required": ["[required_param]"],
        # List only the params your function cannot run without
    },
}
```

---

## Tool Design Checklist

Before registering any tool, verify:

```
[ ] name uses snake_case and starts with an action verb (get_, create_, update_, send_)
[ ] description says WHEN to call it, not just WHAT it does
[ ] description is under 100 words
[ ] all finite-value string params use "enum"
[ ] all numeric params have "minimum" and "maximum" where business rules exist
[ ] "required" contains only params the function cannot run without
[ ] the implementation returns a structured dict on both success AND error
[ ] the function is registered in TOOL_DISPATCH
[ ] there is at least one unit test for the function
```

---

Copyright Janna AI Research Labs
