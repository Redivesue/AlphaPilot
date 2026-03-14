"""
LLM factory for AlphaPilot V3.
"""

from langchain_openai import ChatOpenAI

from core.config import Config


def get_llm(config: Config) -> ChatOpenAI:
    """Create ChatOpenAI instance from config."""
    llm_kwargs = {
        "model": config.llm_model,
        "temperature": config.llm_temperature,
    }
    if config.openai_api_key:
        llm_kwargs["api_key"] = str(config.openai_api_key).strip().strip('"\'')
    if config.openai_api_base:
        llm_kwargs["base_url"] = str(config.openai_api_base).strip().strip('"\'')
    return ChatOpenAI(**llm_kwargs)
