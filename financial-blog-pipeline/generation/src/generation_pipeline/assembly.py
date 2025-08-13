from __future__ import annotations

import json
import os
import time
from typing import Dict, List

from .models import ContentBundle


def build_content_bundle(
    video_id: str,
    title: str,
    transcript_text: str,
    language: str,
    generated_post: Dict,
    images: List[Dict],
) -> ContentBundle:
    bundle = ContentBundle(
        original_video={
            "video_id": video_id,
            "title": title,
            "transcript_text": transcript_text,
        },
        generated_posts=[{"language": language, "post": generated_post}],
        images=images,
    )
    return bundle


def save_bundle_to_outputs(bundle: ContentBundle, output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    video_id = bundle.original_video["video_id"]
    timestamp = int(time.time())
    filename = f"{video_id}_blogs_{timestamp}.json"
    path = os.path.join(output_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(bundle.to_dict(), f, ensure_ascii=False, indent=2)
    return path
