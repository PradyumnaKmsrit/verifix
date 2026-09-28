"""LLM access for Verifix agents (local Ollama by default)."""

import os

from langchain_ollama import ChatOllama

DEFAULT_MODEL = "qwen2.5-coder:1.5b"


def get_llm(model: str | None = None) -> ChatOllama:
    """Return a chat model. Override with the VERIFIX_MODEL environment variable."""
    name = model or os.environ.get("VERIFIX_MODEL", DEFAULT_MODEL)
    return ChatOllama(model=name, temperature=0)