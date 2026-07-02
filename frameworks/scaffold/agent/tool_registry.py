from typing import Any


TOOLS: list[dict[str, Any]] = [
    {
        "name": "get_customer_record",
        "description": (
            "Retrieves a customer record by their unique customer ID. "
            "Use this to verify customer details and eligibility before making a decision."
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
            "Applies a discount to a customer's account. "
            "Only call after confirming eligibility via get_customer_record."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "discount_percent": {
                    "type": "number",
                    "minimum": 1,
                    "maximum": 50,
                },
                "reason": {
                    "type": "string",
                    "enum": ["loyalty", "complaint_resolution", "promotional", "error_correction"],
                },
            },
            "required": ["customer_id", "discount_percent", "reason"],
        },
    },
]


def get_customer_record(customer_id: str) -> dict[str, Any]:
    # Replace with a real parameterised DB query in production
    return {
        "customer_id": customer_id,
        "name": "Amara Osei",
        "account_status": "active",
        "loyalty_tier": "gold",
        "purchases_this_year": 14,
    }


def apply_discount(customer_id: str, discount_percent: float, reason: str) -> dict[str, Any]:
    confirmation_code = f"DISC-{customer_id}-{int(discount_percent)}"
    return {
        "success": True,
        "confirmation_code": confirmation_code,
        "message": f"{discount_percent}% discount applied for reason: {reason}",
    }


TOOL_DISPATCH: dict[str, Any] = {
    "get_customer_record": get_customer_record,
    "apply_discount": apply_discount,
}


def dispatch_tool(tool_name: str, tool_input: dict[str, Any]) -> Any:
    if tool_name not in TOOL_DISPATCH:
        raise ValueError(
            f"Tool '{tool_name}' is not registered. "
            f"Available: {list(TOOL_DISPATCH.keys())}"
        )
    return TOOL_DISPATCH[tool_name](**tool_input)
