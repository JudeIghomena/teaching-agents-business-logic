import json
from typing import Any

from agent.infrastructure import client, logger
from agent.model_config import load_model_config
from agent.tool_registry import TOOLS, dispatch_tool
from agent.context import (
    ConversationContext,
    add_user_turn,
    add_assistant_turn,
    trim_history_if_needed,
)

config = load_model_config()


def run_agent(user_message: str, context: ConversationContext) -> str:
    add_user_turn(context, user_message)
    trim_history_if_needed(context)

    iteration = 0

    while iteration < config.max_iterations:
        iteration += 1
        logger.info(f"loop iteration {iteration}")

        response = client.messages.create(
            model=config.model_id,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            system=context.system_message,
            tools=TOOLS,
            messages=context.messages,
        )

        context.estimated_tokens_used += (
            response.usage.input_tokens + response.usage.output_tokens
        )

        if response.stop_reason == "end_turn":
            final_text = next(
                block.text for block in response.content if hasattr(block, "text")
            )
            add_assistant_turn(context, final_text)
            return final_text

        if response.stop_reason == "tool_use":
            context.messages.append({"role": "assistant", "content": response.content})

            tool_results: list[dict[str, Any]] = []
            for block in response.content:
                if block.type == "tool_use":
                    logger.info(f"tool call: {block.name} | input: {block.input}")
                    result = dispatch_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    })

            context.messages.append({"role": "user", "content": tool_results})
            continue

        logger.warning(f"unexpected stop_reason: {response.stop_reason}")
        break

    return "The agent reached its iteration limit without producing a final answer."
