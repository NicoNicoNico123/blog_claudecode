from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional


@dataclass
class FinancialBlogRow:
    id: int
    video_id: str
    channel_name: str
    title: str
    transcript_text: str
    published_at: Optional[str] = None
    created_at: Optional[str] = None
    lang: Optional[str] = None


@dataclass
class Outline:
    sections: List[str]
    entities: List[str]
    entity_map: Dict[str, List[str]]


@dataclass
class GeneratedPost:
    language: str
    title: str
    html: str
    tags: List[str] = field(default_factory=list)
    meta_description: Optional[str] = None


@dataclass
class ImageCloudinary:
    public_id: str
    secure_url: str
    width: int
    height: int
    format: str


@dataclass
class ImageMetadata:
    topic_key: str
    image_name: str
    provider: str
    source_url: Optional[str]
    attribution: Optional[str]
    cloudinary: Optional[ImageCloudinary]


@dataclass
class ContentBundle:
    original_video: Dict[str, Any]
    generated_posts: List[Dict[str, Any]]
    images: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
