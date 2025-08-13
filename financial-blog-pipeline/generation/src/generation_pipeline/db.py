from __future__ import annotations

import json
from typing import Iterable, List, Optional, Tuple

import psycopg2
from psycopg2.extras import RealDictCursor

from .models import FinancialBlogRow


class Database:
    def __init__(self, database_url: str):
        if not database_url:
            raise ValueError("Database connection URL is required (derive from POSTGRES_* or set DATABASE_URL)")
        self.database_url = database_url

    def _connect(self):
        return psycopg2.connect(self.database_url)

    def ensure_schema(self, schema_sql_path: str) -> None:
        with open(schema_sql_path, "r", encoding="utf-8") as f:
            sql = f.read()
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                conn.commit()

    def fetch_latest_financial_blog(self) -> Optional[FinancialBlogRow]:
        # Support both schemas by probing table existence at runtime
        detect_sql = """
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = current_schema() AND table_name = %s
        """
        select_sql_template = """
            SELECT {cols}
            FROM {table}
            WHERE {transcript_col} IS NOT NULL AND LENGTH({transcript_col}) > 0
            ORDER BY {order_col_1} DESC NULLS LAST, {order_col_2} DESC NULLS LAST
            LIMIT 1
        """
        with self._connect() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Detect table: prefer financial_blog, fallback to blog
            cur.execute(detect_sql, ("financial_blog",))
            use_table = "financial_blog" if cur.fetchone() else "blog"

            if use_table == "financial_blog":
                cols = (
                    "id, video_id, channel_name, title, transcript_text, "
                    "published_at, created_at, lang"
                )
                transcript_col = "transcript_text"
                order_col_1 = "published_at"
                order_col_2 = "created_at"
            else:
                # blog schema may not have all columns; select safe subset
                # Determine available columns
                cur.execute(
                    "SELECT column_name FROM information_schema.columns WHERE table_name=%s AND table_schema=current_schema()",
                    ("blog",),
                )
                present = {r["column_name"] for r in cur.fetchall()}
                def has(name: str) -> bool:
                    return name in present

                select_parts = []
                # Core columns with fallbacks and aliasing
                if has("video_id"):
                    select_parts.append("video_id AS video_id")
                elif has("videoid"):
                    select_parts.append("videoid AS video_id")
                if has("title"):
                    select_parts.append("title AS title")
                if has("channel_name"):
                    select_parts.append("channel_name AS channel_name")
                elif has("channel"):
                    select_parts.append("channel AS channel_name")
                elif has("channelid"):
                    select_parts.append("channelid AS channel_name")
                if has("transcript_text"):
                    select_parts.append("transcript_text AS transcript_text")
                elif has("transcript"):
                    select_parts.append("transcript AS transcript_text")
                if has("published_at"):
                    select_parts.append("published_at AS published_at")
                elif has("publish_date"):
                    select_parts.append("publish_date AS published_at")
                elif has("date"):
                    select_parts.append("date AS published_at")
                if has("created_at"):
                    select_parts.append("created_at AS created_at")
                # blog might not have id/lang
                cols = ", ".join(select_parts) if select_parts else "video_id, title, transcript_text"
                transcript_col = "transcript_text" if has("transcript_text") else ("transcript" if has("transcript") else "transcript")
                if has("published_at"):
                    order_col_1 = "published_at"
                elif has("publish_date"):
                    order_col_1 = "publish_date"
                elif has("date"):
                    order_col_1 = "date"
                elif has("id"):
                    order_col_1 = "id"
                elif has("videoid"):
                    order_col_1 = "videoid"
                else:
                    order_col_1 = "title"
                if has("created_at"):
                    order_col_2 = "created_at"
                elif has("id"):
                    order_col_2 = "id"
                elif has("date"):
                    order_col_2 = "date"
                else:
                    order_col_2 = order_col_1

            query = select_sql_template.format(
                cols=cols,
                table=use_table,
                transcript_col=transcript_col,
                order_col_1=order_col_1,
                order_col_2=order_col_2,
            )
            cur.execute(query)
            row = cur.fetchone()
            if not row:
                return None
            # Map into FinancialBlogRow with safe fallbacks
            return FinancialBlogRow(
                id=row.get("id") or 0,
                video_id=row.get("video_id"),
                channel_name=row.get("channel_name") or "",
                title=row.get("title") or "",
                transcript_text=row.get("transcript_text") or "",
                published_at=row.get("published_at"),
                created_at=row.get("created_at"),
                lang=row.get("lang"),
            )

    def upsert_visual_topics(self, topics: List[dict]) -> None:
        if not topics:
            return
        sql = (
            """
            INSERT INTO visual_topics (video_id, language, topic_key, keywords, source_section, score_visual, status, topic_hash)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (video_id, language, topic_key)
            DO UPDATE SET keywords = EXCLUDED.keywords,
                          source_section = EXCLUDED.source_section,
                          score_visual = EXCLUDED.score_visual,
                          status = EXCLUDED.status,
                          updated_at = NOW()
            """
        )
        with self._connect() as conn, conn.cursor() as cur:
            for t in topics:
                cur.execute(
                    sql,
                    (
                        t["video_id"],
                        t["language"],
                        t["topic_key"],
                        t.get("keywords", []),
                        t.get("source_section"),
                        float(t.get("score_visual", 0.0)),
                        t.get("status", "pending"),
                        t.get("topic_hash", f"{t['video_id']}::{t['language']}::{t['topic_key']}")
                    ),
                )
            conn.commit()

    def upsert_blog_post_v2(
        self,
        video_id: str,
        lang: str,
        title: str,
        html: str,
        tags: Iterable[str],
        meta_description: Optional[str],
        images: List[dict],
    ) -> None:
        sql = (
            """
            INSERT INTO blog_posts_v2 (video_id, lang, title, html, meta_description, tags, images)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (video_id, lang)
            DO UPDATE SET title = EXCLUDED.title,
                          html = EXCLUDED.html,
                          meta_description = EXCLUDED.meta_description,
                          tags = EXCLUDED.tags,
                          images = EXCLUDED.images,
                          updated_at = NOW()
            """
        )
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                sql,
                (
                    video_id,
                    lang,
                    title,
                    html,
                    meta_description,
                    list(tags),
                    json.dumps(images),
                ),
            )
            conn.commit()

    def mark_source_processed(self, video_id: str) -> None:
        sql = "UPDATE financial_blog SET processed_generation = TRUE WHERE video_id = %s"
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(sql, (video_id,))
            conn.commit()
