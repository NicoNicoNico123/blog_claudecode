from __future__ import annotations

import hashlib
import re
from typing import Dict, List

from .models import Outline


def _tokenize(text: str) -> List[str]:
    tokens = re.findall(r"[\w\u4e00-\u9fff]+", text.lower())
    return tokens


def extract_candidate_topics(final_html: str, outline: Outline, language: str, video_id: str) -> List[Dict]:
    # Very simple heuristic: use outline sections + entities as topics
    base_topics: List[str] = list(outline.entities)
    base_topics += [s for s in outline.sections if len(s) <= 20]

    # De-duplicate and normalize
    seen = set()
    topics: List[Dict] = []
    for raw in base_topics:
        topic_key = re.sub(r"\s+", "_", raw.strip().lower())
        if topic_key in seen or not topic_key:
            continue
        seen.add(topic_key)
        topic_hash = hashlib.sha256(f"{video_id}:{language}:{topic_key}".encode()).hexdigest()[:16]
        topics.append(
            {
                "video_id": video_id,
                "language": language,
                "topic_key": topic_key,
                "keywords": [raw],
                "source_section": "auto",
                "score_visual": 0.6,  # baseline
                "status": "pending",
                "topic_hash": topic_hash,
            }
        )
    return topics


def choose_modality_for_topic(topic: Dict) -> str:
    # Simple rule: entities likely news, short abstract likely stock
    key = topic["topic_key"]
    if any(ch.isdigit() for ch in key) or len(key) <= 8:
        return "news"
    return "stock"
