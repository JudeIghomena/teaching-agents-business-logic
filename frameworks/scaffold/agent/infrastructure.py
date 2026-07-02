import os
import logging
import anthropic
from dotenv import load_dotenv

load_dotenv()


def build_logger(name: str) -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    return logging.getLogger(name)


def build_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY is not set.")
    return anthropic.Anthropic(
        api_key=api_key,
        max_retries=3,
        timeout=60.0,
    )


logger = build_logger("agent")
client = build_client()
