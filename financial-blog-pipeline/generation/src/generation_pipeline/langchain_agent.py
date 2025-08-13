from __future__ import annotations

import json
from typing import Dict, List, Tuple
import os
import yaml

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from .config import AppConfig
from .models import Outline


def _chunk_text(text: str, chunk_size: int = 2000, overlap: int = 200) -> List[str]:
    if not text:
        return []
    chunks: List[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + chunk_size, n)
        chunks.append(text[start:end])
        if end >= n:
            break
        start = end - overlap
        if start < 0:
            start = 0
    return chunks


def _ensure_llm(config: AppConfig) -> ChatOpenAI:
    if not config.llm_enabled:
        raise RuntimeError("OPENAI_API_KEY required for LangChain LLM")
    kwargs = {
        "model": config.openai_model,
        "api_key": config.openai_api_key,
        "temperature": 0.3,
    }
    # Allow overriding the OpenAI base URL (for proxies/compatible providers)
    if getattr(config, "openai_base_url", None):
        kwargs["base_url"] = config.openai_base_url
    return ChatOpenAI(**kwargs)


def _load_prompts(config: AppConfig) -> Dict[str, str]:
    # Determine prompt path precedence: explicit env path -> default in generation dir
    default_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "prompt.yaml"))
    path = config.prompt_yaml_path or default_path
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            if isinstance(data, dict):
                # Expect keys: outline_system, outline_user, post_system, post_user
                return {str(k): v if isinstance(v, str) else str(v) for k, v in data.items()}
    except Exception:
        pass
    return {}


def generate_outline_entities_langchain(
    config: AppConfig, title: str, channel_name: str, transcript_text: str
) -> Outline:
    llm = _ensure_llm(config)
    prompts = _load_prompts(config)
    chunks = _chunk_text(transcript_text, chunk_size=2500, overlap=200)
    # Limit to first few chunks to avoid context overflow
    max_chunks = 4
    used_chunks = chunks[:max_chunks]
    context = "\n\n---\n\n".join(used_chunks)

    system = prompts.get("outline_system") or (
        "You are a meticulous Cantonese financial content analyst. "
        "Use ONLY the provided transcript context. Do not invent examples (e.g., HK stocks) unless explicitly present. "
        "Output valid JSON with keys: sections (4-6 short Cantonese headings), entities (array), entity_map (entity->array)."
    )
    user = prompts.get("outline_user") or (
        f"標題: {title}\n頻道: {channel_name}\n\n逐字稿片段（只可根據以下內容推斷）：\n{context}\n\n請用 JSON 回答，格式如下：\n{{\n  \"sections\": [\"...\"],\n  \"entities\": [\"...\"],\n  \"entity_map\": {{ \"實體\": [\"關聯\"] }}\n}}"
    )
    try:
        user = user.format(title=title, channel_name=channel_name, context=context)
    except Exception:
        pass

    prompt = ChatPromptTemplate.from_messages([("system", system), ("user", "{input}")])
    chain = prompt | llm
    res = chain.invoke({"input": user})
    content = res.content or ""

    sections: List[str] = []
    entities: List[str] = []
    entity_map: Dict[str, List[str]] = {}
    try:
        # Extract last JSON object in the string, if any
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            data = json.loads(content[start:end+1])
            sections = list(data.get("sections", []))
            entities = list(data.get("entities", []))
            raw_map = data.get("entity_map", {})
            if isinstance(raw_map, dict):
                entity_map = {str(k): list(v) for k, v in raw_map.items() if isinstance(v, list)}
    except Exception:
        pass

    if not sections:
        sections = ["開場白", "市場分析", "投資貼士", "風險與免責", "結語"]

    return Outline(sections=sections, entities=entities, entity_map=entity_map)


def generate_post_cantonese_langchain(
    config: AppConfig,
    title: str,
    channel_name: str,
    transcript_text: str,
    outline: Outline,
) -> Tuple[str, str, List[str]]:
    llm = _ensure_llm(config)
    prompts = _load_prompts(config)
    chunks = _chunk_text(transcript_text, chunk_size=2500, overlap=200)
    max_chunks = 4
    context = "\n\n---\n\n".join(chunks[:max_chunks])

    system = prompts.get("post_system") or (
        "You write authentic Cantonese financial posts for a Hong Kong audience. "
        "Base strictly on transcript facts; do not insert local HK-specific examples unless stated. "
        "Use an approachable KOL tone, avoid investment advice phrasing. Output HTML (<h2>, <p>, <ul><li>)."
    )
    user = prompts.get("post_user") or (
        f"標題: {title}\n頻道: {channel_name}\n\n逐字稿依據：\n{context}\n\n大綱：{outline.sections}\n實體：{outline.entities}\n\n請用 HTML 產出段落結構（引子→分析→重點→免責→結語），維持自然廣東話。"
    )
    try:
        user = user.format(title=title, channel_name=channel_name, context=context, sections=outline.sections, entities=outline.entities)
    except Exception:
        pass

    prompt = ChatPromptTemplate.from_messages([("system", system), ("user", "{input}")])
    chain = prompt | llm
    res = chain.invoke({"input": user})
    html = (res.content or "").strip()

    if not html:
        html = (
            f"<h2>{title}</h2>\n"
            "<p>大家好，我係今日嘅主持。下面同大家快講重點。</p>\n"
            "<h3>市場分析</h3><p>根據影片逐字稿，我哋整理咗幾個重點供參考。</p>\n"
            "<h3>投資貼士</h3><ul><li>重點一</li><li>重點二</li></ul>\n"
            "<h3>風險與免責聲明</h3><p>本內容不構成任何投資建議。</p>\n"
            "<h3>結語</h3><p>多謝收睇。</p>"
        )

    tags = ["財經", "港股", "學習"]
    meta = f"{title}｜{channel_name} 精華整理"
    return html, meta, tags
