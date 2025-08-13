from __future__ import annotations

from typing import Dict, List

from .db import Database


def validate_bundle(bundle: Dict) -> None:
    ov = bundle.get("original_video", {})
    if not ov.get("video_id"):
        raise ValueError("original_video.video_id is required")
    posts = bundle.get("generated_posts", [])
    if not posts:
        raise ValueError("generated_posts must have at least one entry")
    for img in bundle.get("images", []):
        if not img.get("topic_key"):
            raise ValueError("image.topic_key is required")
        if not img.get("cloudinary", {}).get("public_id"):
            raise ValueError("image.cloudinary.public_id is required")


def persist_bundle_to_db(db: Database, bundle: Dict) -> None:
    ov = bundle["original_video"]
    video_id = ov["video_id"]
    for post_entry in bundle["generated_posts"]:
        lang = post_entry.get("language", "cantonese")
        post = post_entry["post"]
        db.upsert_blog_post_v2(
            video_id=video_id,
            lang=lang,
            title=post.get("title") or ov.get("title") or "",
            html=post.get("html") or "",
            tags=post.get("tags") or [],
            meta_description=post.get("meta_description"),
            images=bundle.get("images", []),
        )
    db.mark_source_processed(video_id)
