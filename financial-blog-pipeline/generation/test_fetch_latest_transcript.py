#!/usr/bin/env python3
"""
Test: Fetch the latest transcript from PostgreSQL.

This script auto-detects whether your database uses the `video_transcripts`
table (newer schema) or the `blog` table (older/demo schema) and picks the
appropriate column names dynamically.

Usage:
  python financial-blog-pipeline/generation/test_fetch_latest_transcript.py

This writes a JSON file to `financial-blog-pipeline/generation/outputs/latest_transcript.json`.

Requires environment variables (typically via .env):
  POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DATABASE, POSTGRES_PASSWORD, [POSTGRES_USERNAME or POSTGRES_USER]
"""

import os
import sys
from typing import Optional, Tuple, Dict, Set
import json
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor

try:
    # Load .env if available (optional)
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
    # dotenv is optional; continue if not installed
    pass


def build_connection_string() -> str:
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT")
    database = os.getenv("POSTGRES_DATABASE")
    user = os.getenv("POSTGRES_USERNAME", os.getenv("POSTGRES_USER", "root"))
    password = os.getenv("POSTGRES_PASSWORD")

    missing = [name for name, val in [
        ("POSTGRES_HOST", host),
        ("POSTGRES_PORT", port),
        ("POSTGRES_DATABASE", database),
        ("POSTGRES_PASSWORD", password),
    ] if not val]

    if missing:
        raise RuntimeError(
            "Missing required environment variables: " + ", ".join(missing)
        )

    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


def detect_table_and_columns(conn) -> Tuple[str, Set[str]]:
    with conn.cursor() as cur:
        # Detect table preference: video_transcripts -> blog
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        tables = {name for (name,) in cur.fetchall()}
        table = "video_transcripts" if "video_transcripts" in tables else ("blog" if "blog" in tables else "")
        if not table:
            raise RuntimeError("Neither 'video_transcripts' nor 'blog' table exists in schema 'public'.")

        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = %s", (table,))
        cols = {name for (name,) in cur.fetchall()}
        return table, cols


def pick(columns: Set[str], *candidates: str) -> Optional[str]:
    for c in candidates:
        if c in columns:
            return c
    return None


def fetch_latest_transcript(connection_string: str) -> Optional[Dict]:
    with psycopg2.connect(connection_string) as conn:
        table, cols = detect_table_and_columns(conn)

        # Column guesses
        video_col = pick(cols, "video_id", "videoid", "videoId")
        title_col = pick(cols, "title")
        channel_col = pick(cols, "channel_name", "channelname", "channel")
        publish_col = pick(cols, "publish_date", "published_at", "publishedat")
        created_col = pick(cols, "created_at", "createdat")
        duration_col = pick(cols, "duration_seconds", "durationseconds", "duration")
        transcript_col = pick(cols, "transcript_text", "transcripttext", "transcript")

        # Build SELECT list with safe fallbacks
        select_items = []
        for alias, col in {
            "video_id": video_col,
            "title": title_col,
            "channel_name": channel_col,
            "publish_date": publish_col,
            "duration_seconds": duration_col,
            "transcript_text": transcript_col,
            "created_at": created_col,
        }.items():
            if col:
                select_items.append(f"{col} AS {alias}")

        if not select_items:
            raise RuntimeError(f"No readable columns detected on table '{table}'.")

        select_clause = ", ".join(select_items)

        # WHERE clause to ensure we have transcript text if possible
        where_clause = ""
        if transcript_col:
            where_clause = f"WHERE {transcript_col} IS NOT NULL AND LENGTH({transcript_col}) > 0"

        # ORDER BY preference: publish -> created -> first selected
        order_cols = []
        if publish_col:
            order_cols.append(f"{publish_col} DESC NULLS LAST")
        if created_col:
            order_cols.append(f"{created_col} DESC NULLS LAST")
        if not order_cols:
            # pick any available column for deterministic order
            fallback_any = (video_col or title_col or channel_col or transcript_col)
            if fallback_any:
                order_cols.append(f"{fallback_any} DESC")
        order_clause = "ORDER BY " + ", ".join(order_cols) if order_cols else ""

        sql = f"SELECT {select_clause} FROM {table} {where_clause} {order_clause} LIMIT 1"

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql)
            return cur.fetchone()


def ensure_output_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def isoformat_or_none(value) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    # psycopg2 may return str for timestamptz if not parsed; attempt best effort
    try:
        return str(value)
    except Exception:
        return None


def main() -> int:
    try:
        conn_str = build_connection_string()
    except Exception as exc:
        print(f"❌ {exc}")
        print("Ensure you have a .env with POSTGRES_* variables or export them in your shell.")
        return 1

    try:
        row = fetch_latest_transcript(conn_str)
    except Exception as exc:
        print(f"❌ Database query failed: {exc}")
        return 2

    outputs_dir = os.path.join(os.path.dirname(__file__), "outputs")
    ensure_output_dir(outputs_dir)

    output_path = os.path.join(outputs_dir, "latest_transcript.json")

    if not row:
        payload = {
            "success": True,
            "message": "No transcripts found.",
            "data": None,
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"Wrote: {output_path}")
        return 0

    transcript_text = row.get("transcript_text") or ""
    payload = {
        "success": True,
        "message": "Latest transcript fetched.",
        "data": {
            "video_id": row.get("video_id"),
            "title": row.get("title"),
            "channel_name": row.get("channel_name"),
            "publish_date": isoformat_or_none(row.get("publish_date")),
            "created_at": isoformat_or_none(row.get("created_at")),
            "duration_seconds": row.get("duration_seconds"),
            "transcript_text": transcript_text,
            "transcript_length": len(transcript_text),
        },
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"✅ Wrote latest transcript JSON: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
