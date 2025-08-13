from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional, Dict, Any
from urllib.parse import quote_plus
import json

from dotenv import load_dotenv, find_dotenv


@dataclass
class AppConfig:
    database_url: str

    # LLM
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    openai_image_model: str = "dall-e-3"
    openai_base_url: Optional[str] = None
    use_langchain: bool = False

    # Cloudinary
    cloudinary_cloud_name: Optional[str] = None
    cloudinary_api_key: Optional[str] = None
    cloudinary_api_secret: Optional[str] = None
    cloudinary_root_folder: str = "blog"

    # Providers
    unsplash_access_key: Optional[str] = None

    # Execution
    output_dir: str = "./outputs"
    default_language: str = "cantonese"
    prompt_yaml_path: Optional[str] = None
    # MCP (optional) for ticker symbol resolution
    mcp_ticker_server_url: Optional[str] = None
    mcp_ticker_tool: str = "searchSymbol"
    mcp_servers: Optional[Dict[str, Any]] = None
    mcp_ticker_headers: Optional[Dict[str, str]] = None
    mcp_session_config: Optional[Dict[str, Any]] = None

    @property
    def cloudinary_enabled(self) -> bool:
        return all([
            self.cloudinary_cloud_name,
            self.cloudinary_api_key,
            self.cloudinary_api_secret,
        ])

    @property
    def llm_enabled(self) -> bool:
        return bool(self.openai_api_key)

    @staticmethod
    def load() -> "AppConfig":
        # Load .env from common locations deterministically
        # 1) Standard search from CWD upwards
        env_path = find_dotenv(usecwd=True)
        if env_path:
            load_dotenv(env_path, override=False)
        # 2) generation/.env (relative to this file)
        gen_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        load_dotenv(os.path.join(gen_dir, ".env"), override=False)
        # 3) project root .env (one more level up)
        project_root = os.path.abspath(os.path.join(gen_dir, ".."))
        load_dotenv(os.path.join(project_root, ".env"), override=False)
        # Prefer DATABASE_URL; otherwise, build from POSTGRES_* env vars
        database_url_env = os.getenv("DATABASE_URL", "")
        if not database_url_env:
            host = os.getenv("POSTGRES_HOST")
            port = os.getenv("POSTGRES_PORT")
            database = os.getenv("POSTGRES_DATABASE")
            user = os.getenv("POSTGRES_USERNAME", os.getenv("POSTGRES_USER", ""))
            password = os.getenv("POSTGRES_PASSWORD")
            # Default to "prefer" so non-SSL works if server doesn't support SSL.
            sslmode = os.getenv("DB_SSLMODE", os.getenv("POSTGRES_SSLMODE", "prefer"))

            if all([host, port, database, user, password]):
                # URL-encode password minimally
                safe_password = quote_plus(password)
                database_url_env = f"postgresql://{user}:{safe_password}@{host}:{port}/{database}"
                if sslmode:
                    sep = "&" if "?" in database_url_env else "?"
                    database_url_env = f"{database_url_env}{sep}sslmode={sslmode}"

        # Optional: multiple MCP servers via JSON in env
        mcp_servers_env = os.getenv("MCP_SERVERS_JSON") or os.getenv("MCP_SERVERS")
        mcp_servers = None
        if mcp_servers_env:
            try:
                mcp_servers = json.loads(mcp_servers_env)
            except Exception:
                mcp_servers = None

        # Optional headers for MCP requests (e.g., API keys)
        mcp_headers_env = os.getenv("MCP_TICKER_HEADERS_JSON") or os.getenv("MCP_TICKER_HEADERS")
        mcp_headers: Optional[Dict[str, str]] = None
        if mcp_headers_env:
            try:
                mcp_headers = json.loads(mcp_headers_env)
            except Exception:
                mcp_headers = None

        # Optional per-session config for MCP (Base64 JSON normally; here keep as dict and we will encode later)
        session_config_env = os.getenv("MCP_SESSION_CONFIG_JSON") or os.getenv("MCP_SESSION_CONFIG")
        mcp_session_config: Optional[Dict[str, Any]] = None
        if session_config_env:
            try:
                mcp_session_config = json.loads(session_config_env)
            except Exception:
                mcp_session_config = None

        return AppConfig(
            database_url=database_url_env,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            openai_image_model=os.getenv("OPENAI_IMAGE_MODEL", "dall-e-3"),
            openai_base_url=os.getenv("OPENAI_BASE_URL"),
            use_langchain=os.getenv("USE_LANGCHAIN", "false").lower() in {"1", "true", "yes"},
            cloudinary_cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
            cloudinary_api_key=os.getenv("CLOUDINARY_API_KEY"),
            cloudinary_api_secret=os.getenv("CLOUDINARY_API_SECRET"),
            cloudinary_root_folder=os.getenv("CLOUDINARY_ROOT_FOLDER", "blog"),
            unsplash_access_key=os.getenv("UNSPLASH_ACCESS_KEY"),
            output_dir=os.getenv("OUTPUT_DIR", "./outputs"),
            default_language=os.getenv("DEFAULT_LANGUAGE", "cantonese"),
            prompt_yaml_path=os.getenv("PROMPT_YAML_PATH"),
            mcp_ticker_server_url=os.getenv("MCP_TICKER_SERVER_URL"),
            mcp_ticker_tool=os.getenv("MCP_TICKER_TOOL", "searchSymbol"),
            mcp_servers=mcp_servers,
            mcp_ticker_headers=mcp_headers,
            mcp_session_config=mcp_session_config,
        )
