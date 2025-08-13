from __future__ import annotations

from typing import Dict, List, Tuple

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
except Exception:  # pragma: no cover
    ChatOpenAI = None  # type: ignore
    ChatPromptTemplate = None  # type: ignore

from .config import AppConfig


def call_langchain_chat(config: AppConfig, system: str, user: str, temperature: float = 0.7) -> str:
    if not config.llm_enabled or ChatOpenAI is None:
        return ""
    llm = ChatOpenAI(model=config.openai_model, api_key=config.openai_api_key, temperature=temperature)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("user", "{user}")
        ]
    )
    chain = prompt | llm
    res = chain.invoke({"user": user})
    return res.content or ""
