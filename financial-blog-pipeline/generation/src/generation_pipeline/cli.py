from __future__ import annotations

import json
import os
import sys
from typing import Optional
import logging
import time

import click

from .assembly import build_content_bundle, save_bundle_to_outputs
from .config import AppConfig
from .db import Database
from .finalize import append_disclaimer, normalize_and_quick_qa, enrich_tickers_with_mcp
from .images import retrieve_and_upload_images
from .langchain_agent import generate_outline_entities_langchain, generate_post_cantonese_langchain
from .models import GeneratedPost
from .persistence import persist_bundle_to_db, validate_bundle
from .prompts import build_prompts_for_topics
from .visual_topics import choose_modality_for_topic, extract_candidate_topics


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option("--video-id", "video_id_opt", help="Specific video_id to process", default=None)
@click.option("--write-db/--no-write-db", default=False, help="Persist results into PostgreSQL after generating bundle")
@click.option("--force", is_flag=True, help="Force generation even if output exists")
@click.option("--use-langchain/--no-use-langchain", default=None, help="Override USE_LANGCHAIN env for this run")
@click.option("--log-level", type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False), default="INFO", show_default=True)
@click.option("--text-only", is_flag=True, default=False, help="Skip image retrieval/upload; generate text only")
@click.option("--print-html", is_flag=True, default=False, help="Print generated HTML to stdout for debugging")
def run(video_id_opt: Optional[str], write_db: bool, force: bool, use_langchain: Optional[bool], log_level: str, text_only: bool, print_html: bool) -> None:
    """End-to-end pipeline: fetch -> generate -> images -> bundle -> (optional) DB."""
    # Configure logging early
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logger = logging.getLogger(__name__)
    config = AppConfig.load()
    # Log resolved key config (mask secrets)
    redacted_db = (config.database_url or "").replace((config.openai_api_key or ""), "***")
    logger.info("Starting generation run | DB=%s | LangChain=%s | Model=%s", "set" if bool(config.database_url) else "missing", getattr(config, 'use_langchain', False), config.openai_model)
    if logging.getLogger().level <= logging.DEBUG:
        logger.debug("Resolved DATABASE_URL: %s", redacted_db)
    if not config.database_url:
        click.echo("DATABASE_URL is required in environment", err=True)
        sys.exit(2)

    if use_langchain is not None:
        # Allow runtime toggle regardless of env
        config.use_langchain = bool(use_langchain)

    db = Database(config.database_url)
    # Ensure schema present (idempotent)
    schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "sql", "schema.sql")
    schema_path = os.path.abspath(schema_path)
    db.ensure_schema(schema_path)

    row = db.fetch_latest_financial_blog()
    if not row:
        click.echo("No source transcripts found in financial_blog table")
        return

    if video_id_opt and row.video_id != video_id_opt:
        click.echo(f"Latest row video_id={row.video_id} does not match requested {video_id_opt}. Proceeding with latest.")

    language = config.default_language

    # 1) Outline + entities
    outline = generate_outline_entities_langchain(config, row.title, row.channel_name, row.transcript_text)

    # 2) Generate post (Cantonese)
    html, meta, tags = generate_post_cantonese_langchain(config, row.title, row.channel_name, row.transcript_text, outline)

    # 3) Finalization & QA
    html = normalize_and_quick_qa(html)
    # 3.1) MCP-only enrichment for tickers (no fallback)
    # Load streamable_http MCP URL strictly from environment (MCP_TICKER_SERVER_URL)
    mcp_server_url = getattr(config, "mcp_ticker_server_url", None)
    if not mcp_server_url:
        logger.warning("MCP_TICKER_SERVER_URL is not set. Skipping ticker enrichment.")
    else:
        logger.info(f"Using MCP ticker server: {mcp_server_url}")

        try:
            html = enrich_tickers_with_mcp(
                html,
                mcp_server_url,
                getattr(config, "mcp_ticker_tool", "searchSymbol"),
                headers=getattr(config, "mcp_ticker_headers", None),
                session_config=getattr(config, "mcp_session_config", None),
            )
        except Exception as e:
            logger.error(f"MCP ticker enrichment failed: {e}")
            # Per requirement: do not fallback; proceed with original HTML
    
    html = append_disclaimer(html)

    post = GeneratedPost(language=language, title=row.title, html=html, tags=tags, meta_description=meta)

    if text_only:
        images = []
    else:
        # 4) Visual topic extraction
        topics = extract_candidate_topics(html, outline, language, row.video_id)

        # 5) Prompt synthesis
        prompts = build_prompts_for_topics(topics)

        # 6) Retrieve images & Cloudinary upload
        images = retrieve_and_upload_images(config, row.video_id, language, topics, prompts)

    # 7) Assembly
    bundle = build_content_bundle(
        video_id=row.video_id,
        title=row.title,
        transcript_text=row.transcript_text,
        language=language,
        generated_post={
            "title": post.title,
            "html": post.html,
            "tags": post.tags,
            "meta_description": post.meta_description,
        },
        images=images,
    )
    out_path = save_bundle_to_outputs(bundle, config.output_dir)
    click.echo(f"Saved bundle to {out_path}")

    if print_html:
        # Emit HTML to stdout and also write a standalone HTML file for convenience
        click.echo("\n===== Generated HTML (preview) =====\n")
        click.echo(html)
        html_filename = f"{row.video_id}_post_{int(time.time())}.html"
        html_path = os.path.join(config.output_dir, html_filename)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        click.echo(f"\nSaved HTML to {html_path}")

    # 9) Upload to PostgreSQL (Storage)
    if write_db:
        validate_bundle(bundle.to_dict())
        persist_bundle_to_db(db, bundle.to_dict())
        click.echo("Persisted bundle to PostgreSQL.")


@cli.command()
def doctor() -> None:
    """Check environment configuration for providers."""
    config = AppConfig.load()
    msgs = []
    msgs.append(f"DB: {'OK' if bool(config.database_url) else 'MISSING'}")
    msgs.append(f"LLM(OpenAI): {'OK' if config.llm_enabled else 'DISABLED'}")
    msgs.append(f"LangChain: {'ON' if getattr(config, 'use_langchain', False) else 'OFF'}")
    msgs.append(f"Cloudinary: {'OK' if config.cloudinary_enabled else 'DISABLED'}")
    msgs.append(f"Unsplash: {'OK' if bool(config.unsplash_access_key) else 'DISABLED'}")
    click.echo(" | ".join(msgs))


if __name__ == "__main__":
    cli()
