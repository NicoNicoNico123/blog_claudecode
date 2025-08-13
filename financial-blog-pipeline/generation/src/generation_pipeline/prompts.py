from __future__ import annotations

from typing import Dict, List


def build_prompts_for_topics(topics: List[Dict]) -> List[Dict]:
    prompts: List[Dict] = []
    for t in topics:
        topic_key = t["topic_key"]
        base = f"主題：{topic_key}。構圖：16:9，清晰，無品牌商標。內容需安全合規。"
        alt = f"與 {topic_key} 相關的說明性圖片"
        prompts.append({"topic_key": topic_key, "prompt": base, "alt_text": alt})
    return prompts
