from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConversationContext:
    system_message: str = ""
    messages: list[dict[str, Any]] = field(default_factory=list)
    session_metadata: dict[str, Any] = field(default_factory=dict)
    estimated_tokens_used: int = 0


def build_system_message(role_context: str, rules: list[str]) -> str:
    rules_block = "\n".join(f"- {rule}" for rule in rules)
    return f"""{role_context}

RULES:
{rules_block}

Respond only in plain, clear language. Do not use markdown formatting,
em dashes, or special characters in your responses."""


def add_user_turn(context: ConversationContext, content: str) -> None:
    context.messages.append({"role": "user", "content": content})


def add_assistant_turn(context: ConversationContext, content: str) -> None:
    context.messages.append({"role": "assistant", "content": content})


def trim_history_if_needed(
    context: ConversationContext,
    token_limit: int = 80_000,
) -> None:
    if context.estimated_tokens_used < token_limit:
        return
    if len(context.messages) > 12:
        context.messages = context.messages[:2] + context.messages[-10:]
