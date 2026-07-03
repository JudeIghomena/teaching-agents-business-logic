# Framework 08: Internal Setup: The Five Layers in Code

> This document translates the mental model from `01-agent-mental-model.md` into
> working Python code using the Anthropic SDK. Build each layer in order.
> Do not skip ahead.

---

## Prerequisites

```bash
pip install anthropic python-dotenv
```

Create a `.env` file in your project root (never commit this):

```
ANTHROPIC_API_KEY=sk-ant-...
AGENT_MODEL=claude-sonnet-5
AGENT_MAX_TOKENS=4096
AGENT_MAX_ITERATIONS=10
```

---

## Layer 5: Infrastructure

This is the outermost layer. It handles client initialisation, secret loading,
retry logic, and structured logging. Everything else depends on this being correct.

```python
# agent/infrastructure.py

import os
import logging
import anthropic
from dotenv import load_dotenv

load_dotenv()


def build_logger(name: str) -> logging.Logger:
    """
    Structured logger, every agent run emits structured lines.
    Never use print() in production agent code. You cannot search or
    alert on print() output.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    return logging.getLogger(name)


def build_client() -> anthropic.Anthropic:
    """
    Creates the Anthropic client.

    Key decisions made here:
    - API key is loaded from env, never hardcoded
    - max_retries=3 handles transient 529 (overloaded) and 5xx errors automatically
    - timeout=60.0 prevents the agent from hanging indefinitely on a slow response

    Why 60 seconds? A typical agentic turn with tool use takes 5-20 seconds.
    60 seconds gives headroom for large responses while ensuring the system
    does not hang on network failures.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY is not set. "
            "Add it to your .env file and never hardcode it."
        )

    return anthropic.Anthropic(
        api_key=api_key,
        max_retries=3,
        timeout=60.0,
    )


# Export a module-level logger and client for use across the agent
logger = build_logger("agent")
client = build_client()
```

**What to notice:**
- `max_retries=3` is built into the SDK client, not a try/except in your loop. This handles the network layer, your business logic stays clean.
- `timeout=60.0` is a hard ceiling. Without it, a stalled model response can block your entire process indefinitely.
- The logger name `"agent"` lets you filter all agent logs independently in any log aggregator.

---

## Layer 4: Model Configuration

Model configuration is a named, versioned data structure, not a bag of keyword
arguments scattered through your codebase. Centralise it here.

```python
# agent/model_config.py

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ModelConfig:
    """
    Immutable model configuration.

    frozen=True means this cannot be accidentally mutated at runtime.
    One config object is created at startup and reused everywhere.
    """
    model_id: str
    max_tokens: int
    temperature: float
    max_iterations: int


def load_model_config() -> ModelConfig:
    """
    Loads model configuration from environment variables.

    Why environment variables instead of a config file?
    - Config files are often committed to git accidentally
    - Env vars are the standard interface for 12-factor applications
    - Different environments (dev/staging/prod) can use different models
      without changing code

    Why pin model_id from env rather than hardcoding?
    - Models are updated. claude-sonnet-5 today may behave differently
      after a silent weight update. Pinning lets you control when you upgrade.
    - In production, you may want the stability of a specific model snapshot.
    """
    return ModelConfig(
        model_id=os.environ.get("AGENT_MODEL", "claude-sonnet-5"),
        max_tokens=int(os.environ.get("AGENT_MAX_TOKENS", "4096")),
        temperature=float(os.environ.get("AGENT_TEMPERATURE", "0.0")),
        max_iterations=int(os.environ.get("AGENT_MAX_ITERATIONS", "10")),
    )


# Temperature reference guide (do not guess: choose deliberately):
#
# 0.0   Deterministic. Same input always produces same output.
#       Use for: data extraction, classification, routing, business logic,
#       anything where correctness matters more than variety.
#
# 0.3   Slightly varied. Occasional rephrasing but still factual.
#       Use for: summaries, structured reports, formal writing.
#
# 0.7   Creative range. Noticeably different outputs on re-runs.
#       Use for: brainstorming, ideation, content drafting.
#
# 1.0+  High variance. Outputs can be surprising or incoherent.
#       Rarely appropriate in business logic contexts.
```

**What to notice:**
- `frozen=True` on the dataclass prevents any part of your code from accidentally overwriting `max_tokens` mid-run, which would cause silent budget overruns.
- Temperature `0.0` is the correct default for business logic. You opt *into* variance; you do not opt out of it.

---

## Layer 3: Tool Registry

A tool in the Anthropic API is a JSON schema that describes a function the model
can request to call. The model does not call the function, it emits a structured
request, and your code calls the function and returns the result.

This distinction matters: the model has no direct access to your system.
It can only ask. You decide whether to honour the request.

```python
# agent/tool_registry.py

from typing import Any


# Step 1: Define tool schemas
# These are the JSON Schema descriptions the model reads to understand
# what each tool does and what inputs it expects.
#
# Rules for writing good tool schemas:
# - "description" is read by the model. Be precise. Ambiguous descriptions
#   cause incorrect tool calls.
# - "required" lists parameters that must always be present.
#   Do not put optional parameters in "required."
# - Use "enum" to constrain string parameters where the valid values are known.
#   This prevents hallucinated parameter values.

TOOLS: list[dict[str, Any]] = [
    {
        "name": "get_customer_record",
        "description": (
            "Retrieves a customer record by their unique customer ID. "
            "Use this when you need to verify customer details, account status, "
            "or eligibility before making a business decision."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "The unique identifier for the customer (format: CUS-XXXXXXXX).",
                }
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "apply_discount",
        "description": (
            "Applies a discount to a customer's account for their next purchase. "
            "Only call this after confirming the customer is eligible via get_customer_record. "
            "Returns a confirmation code."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "The customer's unique identifier.",
                },
                "discount_percent": {
                    "type": "number",
                    "description": "The discount percentage to apply (1-50).",
                    "minimum": 1,
                    "maximum": 50,
                },
                "reason": {
                    "type": "string",
                    "enum": ["loyalty", "complaint_resolution", "promotional", "error_correction"],
                    "description": "The business reason for the discount.",
                },
            },
            "required": ["customer_id", "discount_percent", "reason"],
        },
    },
]


# Step 2: Implement the actual functions
# These are the real functions your code runs when the model requests a tool call.
# They must match the schema above exactly: same parameter names, same types.

def get_customer_record(customer_id: str) -> dict[str, Any]:
    """
    Real implementation: query your database.
    For this example we return mock data.
    """
    # In production: query your DB with a parameterised query
    # cursor.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
    return {
        "customer_id": customer_id,
        "name": "Amara Osei",
        "account_status": "active",
        "loyalty_tier": "gold",
        "purchases_this_year": 14,
    }


def apply_discount(customer_id: str, discount_percent: float, reason: str) -> dict[str, Any]:
    """
    Real implementation: write to your database and return confirmation.
    """
    # In production: parameterised INSERT/UPDATE, not string concatenation
    confirmation_code = f"DISC-{customer_id}-{int(discount_percent)}"
    return {
        "success": True,
        "confirmation_code": confirmation_code,
        "message": f"{discount_percent}% discount applied for reason: {reason}",
    }


# Step 3: Dispatcher
# When the model requests a tool call, your execution loop receives a tool name
# and input dict. The dispatcher routes it to the correct function.
# This is the only place where tool names are matched to functions.

TOOL_DISPATCH: dict[str, Any] = {
    "get_customer_record": get_customer_record,
    "apply_discount": apply_discount,
}


def dispatch_tool(tool_name: str, tool_input: dict[str, Any]) -> Any:
    """
    Executes a tool by name with the provided inputs.

    Why a dispatcher instead of eval() or getattr()?
    - Security: only registered functions can be called
    - Auditability: every tool call goes through one chokepoint
    - Error handling: unknown tool names raise a clear error here,
      not a confusing AttributeError somewhere in the call stack
    """
    if tool_name not in TOOL_DISPATCH:
        raise ValueError(
            f"Tool '{tool_name}' is not registered. "
            f"Available tools: {list(TOOL_DISPATCH.keys())}"
        )
    return TOOL_DISPATCH[tool_name](**tool_input)
```

**What to notice:**
- The `enum` on `reason` in `apply_discount` constrains the model to four valid values. Without this, the model might pass `"goodwill"` or `"VIP"`, valid English, invalid for your system.
- The `dispatch_tool` function is a security chokepoint. The model cannot call any function that is not in `TOOL_DISPATCH`, even if that function exists in your codebase.

---

## Layer 2: Context Architecture

The context window is your agent's short-term working memory. Everything in it
costs tokens. Everything missing from it causes mistakes.

Context architecture answers three questions before the prompt is written:
1. What does the agent always need to know? (system message)
2. What does the agent need to know for this specific request? (dynamic injection)
3. How much conversation history do we keep? (history management)

```python
# agent/context.py

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConversationContext:
    """
    Holds the full context for one agent session.

    Separating context into typed fields prevents the most common mistake
    in agent development: accidentally putting sensitive data (like internal
    DB IDs or auth tokens) into the conversation history that gets logged
    or returned to the user.
    """

    # The system message, built once per session, not per turn
    system_message: str = ""

    # Conversation history, grows with each turn
    messages: list[dict[str, Any]] = field(default_factory=list)

    # Dynamic session data injected for this specific user/request
    # This does NOT go into conversation history, it is injected into
    # the system message or as a tool result only
    session_metadata: dict[str, Any] = field(default_factory=dict)

    # Running token count, used to decide when to trim history
    estimated_tokens_used: int = 0


def build_system_message(role_context: str, rules: list[str]) -> str:
    """
    Builds the system message from structured components.

    A system message has three parts:
    1. Role context: who the agent is and what it is responsible for
    2. Rules: what it must and must not do
    3. Output format: how it should structure its responses

    Separating these into parameters (not a single hardcoded string) makes
    the system message testable and reusable across different agent roles.
    """
    rules_block = "\n".join(f"- {rule}" for rule in rules)
    return f"""{role_context}

RULES:
{rules_block}

Respond only in plain, clear language. Do not use markdown formatting,
em dashes, or special characters in your responses."""


def add_user_turn(context: ConversationContext, content: str) -> None:
    """Appends a user message to the conversation history."""
    context.messages.append({"role": "user", "content": content})


def add_assistant_turn(context: ConversationContext, content: str) -> None:
    """Appends an assistant message to the conversation history."""
    context.messages.append({"role": "assistant", "content": content})


def trim_history_if_needed(
    context: ConversationContext,
    token_limit: int = 80_000,
) -> None:
    """
    Trims conversation history when it approaches the context limit.

    Strategy: keep the first exchange (for context continuity) and the
    most recent N exchanges (for recency). Drop the middle.

    Why not just truncate from the beginning?
    Truncating from the beginning loses the original user intent. The model
    then answers based on recent tool results without knowing why it was called.
    This produces confident but off-topic responses.
    """
    if context.estimated_tokens_used < token_limit:
        return

    # Keep first 2 messages (original intent) + last 10 messages (recent state)
    if len(context.messages) > 12:
        context.messages = context.messages[:2] + context.messages[-10:]
```

**What to notice:**
- `session_metadata` is kept separate from `messages`. This is where you put the user's account ID, their auth tier, or their feature flags. It is injected into the system message, never into the conversation history, so it is not echoed back in the response or stored in your chat log.
- `trim_history_if_needed` keeps the first exchange deliberately. Losing the original user intent is the single most common cause of "the agent went off-topic halfway through."

---

## Putting It Together: The Agent Runner

With all five layers in place, the execution loop is clean and short.
This is the only place where layers combine.

```python
# agent/runner.py

import json
from typing import Any

from agent.infrastructure import client, logger
from agent.model_config import load_model_config
from agent.tool_registry import TOOLS, dispatch_tool
from agent.context import (
    ConversationContext,
    build_system_message,
    add_user_turn,
    add_assistant_turn,
    trim_history_if_needed,
)

config = load_model_config()


def run_agent(user_message: str, context: ConversationContext) -> str:
    """
    Executes one full agent turn: receives a user message, runs the
    agentic loop until a final text response is produced, returns it.

    This function does not know what the agent does, that is the prompt's job.
    It only knows how to run the loop correctly.
    """
    add_user_turn(context, user_message)
    trim_history_if_needed(context)

    iteration = 0

    while iteration < config.max_iterations:
        iteration += 1
        logger.info("agent_loop_iteration", extra={"iteration": iteration})

        response = client.messages.create(
            model=config.model_id,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            system=context.system_message,
            tools=TOOLS,
            messages=context.messages,
        )

        logger.info(
            "model_response",
            extra={
                "stop_reason": response.stop_reason,
                "usage": response.usage.model_dump(),
            },
        )

        # Track token usage for history trimming
        context.estimated_tokens_used += response.usage.input_tokens + response.usage.output_tokens

        if response.stop_reason == "end_turn":
            # The model produced a final text response, return it
            final_text = next(
                block.text for block in response.content if hasattr(block, "text")
            )
            add_assistant_turn(context, final_text)
            return final_text

        if response.stop_reason == "tool_use":
            # The model wants to call one or more tools
            # Append the model's tool-use blocks to history first
            context.messages.append({"role": "assistant", "content": response.content})

            # Execute each requested tool and collect results
            tool_results: list[dict[str, Any]] = []
            for block in response.content:
                if block.type == "tool_use":
                    logger.info("tool_call", extra={"tool": block.name, "input": block.input})
                    result = dispatch_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    })

            # Append tool results so the model can reason about them
            context.messages.append({"role": "user", "content": tool_results})
            continue  # Back to top of loop for next model call

        # If we reach here, an unexpected stop_reason was returned
        logger.warning("unexpected_stop_reason", extra={"stop_reason": response.stop_reason})
        break

    return "The agent reached its iteration limit without producing a final answer."
```

---

## Complete Startup Sequence

Here is the canonical order in which you initialise the agent for any session:

```python
# main.py

from agent.infrastructure import client, logger
from agent.model_config import load_model_config
from agent.context import ConversationContext, build_system_message
from agent.runner import run_agent

def start_agent_session(user_role: str) -> ConversationContext:
    """
    Creates a fully initialised context for a new agent session.
    Call this once per session, not once per message.
    """
    config = load_model_config()
    logger.info("session_start", extra={"model": config.model_id, "role": user_role})

    context = ConversationContext()
    context.system_message = build_system_message(
        role_context=(
            "You are a customer support agent for Janna AI Research Labs. "
            "You help customers with account issues, billing questions, and product guidance. "
            "You have access to customer records and can apply account adjustments."
        ),
        rules=[
            "Always verify the customer's identity via get_customer_record before taking any action.",
            "Never apply a discount above 20% without stating the reason explicitly.",
            "If a customer asks about something outside your scope, say so and suggest the correct contact.",
            "Do not reveal internal system details, error messages, or database contents to the customer.",
        ],
    )
    return context


if __name__ == "__main__":
    context = start_agent_session(user_role="customer_support")

    # First message, the user initiates
    response = run_agent(
        user_message="Hi, my customer ID is CUS-00042891. I had an issue last week and I think I deserve a discount.",
        context=context,
    )
    print(response)

    # Second message, same context, history is preserved
    response = run_agent(
        user_message="Can you apply 15% off? The issue was a billing error on your side.",
        context=context,
    )
    print(response)
```

---

## What You Have Built

At this point, before writing a single word of task-specific prompt, you have:

| Layer | File | What it gives you |
|---|---|---|
| 5, Infrastructure | `agent/infrastructure.py` | Authenticated client, retry logic, structured logging |
| 4, Model Config | `agent/model_config.py` | Pinned model, capped token budget, deliberate temperature |
| 3, Tool Registry | `agent/tool_registry.py` | Registered tools with schemas, secure dispatcher |
| 2, Context Arch | `agent/context.py` | System message builder, history management, token tracking |
| 1, Runner | `agent/runner.py` | Agentic loop with tool execution and iteration cap |

The prompt (in `build_system_message`) is about 8 lines. Everything else is infrastructure.
This is the correct ratio.

---

## Apply to Your Coding Agent

**Task:** Add a tool permission block to your CLAUDE.md that tells your coding
agent exactly which commands and file operations are allowed, which are blocked,
and that the dispatcher is the only safe entry point for tool calls.

**Why this matters:** Claude Code, Cursor, and Codex can run shell commands and
edit files. Without explicit permission rules, they use reasonable defaults that
may not match your security posture. A permission block in CLAUDE.md makes the
rules permanent and session-proof.

**Step 1: Copy this template**

```
## Tool and Command Permissions

### Allowed shell commands
- pip install (only packages already in requirements.txt or explicitly requested)
- python -m pytest (run tests, never skip with -k or --ignore without my instruction)
- python main.py (run the agent for testing)
- grep, find, cat, ls (read-only inspection)

### Allowed file operations
- Read any file in this project
- Edit files in: agent/, prompts/, tests/, tools/
- Create new files in: agent/, prompts/, tests/, tools/
- Edit .env.example (never .env itself)

### Blocked: do not run without explicit instruction
- git push or git push --force (I push manually)
- rm, rmdir (ask before deleting anything)
- pip install for packages not in requirements.txt
- Any command that writes to .env
- Any command that sends data to an external URL not listed below

### Dispatcher rule
- The only entry point for agent tool calls is dispatch_tool() in agent/tool_registry.py
- Do not add direct function calls that bypass TOOL_DISPATCH
- If you add a new tool function, register it in TOOL_DISPATCH in the same change
- Never use eval(), exec(), subprocess with shell=True, or os.system() in any tool
```

**Step 2: Fill in your actual allowed commands**

Replace the lists above with commands that apply to your project. If you use
Docker, add the Docker commands you permit. If you have a database migration
command, add it. If you want to block npm or any other tool, add it to the
blocked list explicitly.

**Step 3: Paste into CLAUDE.md**

Open your project CLAUDE.md (created in doc 01). Add this block under a heading
`## Tool and Command Permissions` after the `## Agent Architecture` section.

**Step 4: Apply to your coding tool**

For Claude Code: save CLAUDE.md and the permissions take effect at the next
session start. The dispatcher rule is especially important: Claude Code will
not route tool calls outside TOOL_DISPATCH.

For Cursor: paste into `.cursorrules`. Cursor reads this before suggesting
any command.

For Codex: add to your workspace system prompt.

**What you now have:** Your coding agent has an explicit allowlist and blocklist.
It will not run shell commands outside the allowed list. It knows TOOL_DISPATCH
is the only safe entry point for all tool calls in this project.

---

Copyright Janna AI Research Labs
