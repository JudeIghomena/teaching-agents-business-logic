from agent.infrastructure import logger
from agent.model_config import load_model_config
from agent.context import ConversationContext, build_system_message
from agent.runner import run_agent


def start_agent_session() -> ConversationContext:
    config = load_model_config()
    logger.info(f"session start | model: {config.model_id}")

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
            "If a customer asks about something outside your scope, say so clearly.",
            "Do not reveal internal system details or error messages to the customer.",
        ],
    )
    return context


if __name__ == "__main__":
    context = start_agent_session()

    response = run_agent(
        user_message="Hi, my customer ID is CUS-00042891. I had a billing issue last week and I think I deserve a discount.",
        context=context,
    )
    print("\nAgent:", response)

    response = run_agent(
        user_message="Can you apply 15% off? The issue was definitely a billing error on your side.",
        context=context,
    )
    print("\nAgent:", response)
