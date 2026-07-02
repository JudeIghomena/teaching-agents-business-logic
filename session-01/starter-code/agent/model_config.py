import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ModelConfig:
    model_id: str
    max_tokens: int
    temperature: float
    max_iterations: int


def load_model_config() -> ModelConfig:
    return ModelConfig(
        model_id=os.environ.get("AGENT_MODEL", "claude-sonnet-5"),
        max_tokens=int(os.environ.get("AGENT_MAX_TOKENS", "4096")),
        temperature=float(os.environ.get("AGENT_TEMPERATURE", "0.0")),
        max_iterations=int(os.environ.get("AGENT_MAX_ITERATIONS", "10")),
    )
