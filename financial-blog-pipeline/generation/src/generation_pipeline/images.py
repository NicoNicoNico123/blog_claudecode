from __future__ import annotations

import io
from dataclasses import asdict
from typing import Dict, List, Optional, Tuple

import requests

try:
    import cloudinary
    import cloudinary.uploader
except Exception:  # pragma: no cover
    cloudinary = None  # type: ignore

try:
    import openai  # for DALL·E
except Exception:  # pragma: no cover
    openai = None  # type: ignore

from .config import AppConfig
from .models import ImageCloudinary, ImageMetadata


def _ensure_cloudinary(config: AppConfig) -> None:
    if not config.cloudinary_enabled or cloudinary is None:
        raise RuntimeError("Cloudinary not configured")
    cloudinary.config(
        cloud_name=config.cloudinary_cloud_name,
        api_key=config.cloudinary_api_key,
        api_secret=config.cloudinary_api_secret,
        secure=True,
    )


def _download_bytes(url: str) -> bytes:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.content


def search_unsplash(access_key: str, query: str, per_page: int = 3) -> List[Dict]:
    url = "https://api.unsplash.com/search/photos"
    params = {"query": query, "per_page": per_page, "orientation": "landscape"}
    headers = {"Accept-Version": "v1", "Authorization": f"Client-ID {access_key}"}
    resp = requests.get(url, params=params, headers=headers, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    return data.get("results", [])


def generate_dalle_image(config: AppConfig, prompt: str) -> Optional[bytes]:
    if not config.llm_enabled or openai is None:
        return None
    client = openai.OpenAI(api_key=config.openai_api_key)
    # Using Images API
    img = client.images.generate(model=config.openai_image_model, prompt=prompt, size="1600x900")
    url = img.data[0].url
    return _download_bytes(url)


def upload_to_cloudinary(
    config: AppConfig,
    video_id: str,
    language: str,
    topic_key: str,
    image_slug: str,
    content: bytes,
    file_format: str = "png",
) -> ImageCloudinary:
    _ensure_cloudinary(config)
    folder = f"{config.cloudinary_root_folder}/{video_id}/{language}/{topic_key}"
    public_id = f"{folder}/{image_slug}"
    upload_result = cloudinary.uploader.upload(content, public_id=public_id, resource_type="image", format=file_format)
    return ImageCloudinary(
        public_id=upload_result["public_id"],
        secure_url=upload_result["secure_url"],
        width=int(upload_result["width"]),
        height=int(upload_result["height"]),
        format=str(upload_result["format"]),
    )


def retrieve_and_upload_images(
    config: AppConfig,
    video_id: str,
    language: str,
    topics: List[Dict],
    prompts: List[Dict],
) -> List[Dict]:
    results: List[Dict] = []
    prompt_map = {p["topic_key"]: p for p in prompts}

    for topic in topics:
        topic_key = topic["topic_key"]
        image_name = f"{topic_key}__auto"
        provider = None
        source_url = None
        attribution = None
        cloudinary_info = None

        # Try Unsplash when key present
        if config.unsplash_access_key:
            try:
                q = topic_key.replace("_", " ")
                photos = search_unsplash(config.unsplash_access_key, q, per_page=1)
                if photos:
                    photo = photos[0]
                    source_url = photo.get("urls", {}).get("regular")
                    attribution = f"{photo.get('user',{}).get('name','Unknown')} / Unsplash"
                    img_bytes = _download_bytes(source_url)
                    cloudinary_info = upload_to_cloudinary(config, video_id, language, topic_key, "unsplash", img_bytes, file_format="jpg")
                    provider = "unsplash"
            except Exception:
                pass

        # If still no image, try DALL·E
        if cloudinary_info is None and config.llm_enabled:
            try:
                p = prompt_map.get(topic_key, {}).get("prompt", topic_key)
                img_bytes = generate_dalle_image(config, p)
                if img_bytes:
                    cloudinary_info = upload_to_cloudinary(config, video_id, language, topic_key, "dalle", img_bytes, file_format="png")
                    provider = "dalle"
                    source_url = None
                    attribution = None
            except Exception:
                pass

        if cloudinary_info is None:
            # Skip if no providers are available
            continue

        results.append(
            {
                "topic_key": topic_key,
                "image_name": image_name,
                "provider": provider or "unknown",
                "source_url": source_url,
                "attribution": attribution,
                "cloudinary": asdict(cloudinary_info),
            }
        )

    return results
