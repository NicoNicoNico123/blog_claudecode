from __future__ import annotations

import re
from typing import Tuple, Dict, Optional, List, Any
import json
import logging
import re
import asyncio

MCPClient = None
# Prefer official package if available
try:  # pragma: no cover
    from langchain_mcp_adapters.client import HttpMCPClient as MCPClient  # type: ignore
except Exception:
    try:
        # Fallback to community MCP client if present
        from langchain_community.tools.mcp import MCPClient  # type: ignore
    except Exception:
        MCPClient = None  # type: ignore

try:  # LangChain model and message classes
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
except Exception:  # pragma: no cover
    ChatOpenAI = None  # type: ignore
    SystemMessage = HumanMessage = ToolMessage = object  # type: ignore

try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
except Exception:  # pragma: no cover
    MultiServerMCPClient = None  # type: ignore


DISCLAIMER = (
    "本內容僅供學習及資訊參考，並不構成任何投資建議。"
)


def normalize_and_quick_qa(html: str) -> str:
    text = html
    # Remove duplicated whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove over-claiming terms
    text = text.replace("必賺", "").replace("保證", "")
    # Normalize zh-TW terms to zh-HK variants (Cantonese style)
    hk_variants = {
        "通膨": "通脹",
        "通膨率": "通脹率",
        "機構投資人": "機構投資者",
        "證券交易所": "證券交易所",  # placeholder, usually same
        "交易量": "成交量",
        "殖利率": "息率",
        "房地產": "地產",
        "公司債": "企業債",
        "股價指數": "股價指數",  # often same; kept for completeness
    }
    for tw, hk in hk_variants.items():
        text = text.replace(tw, hk)
    return text


def append_disclaimer(html: str) -> str:
    if "本內容僅供學習" in html:
        return html
    return html + f"\n\n<p><em>{DISCLAIMER}</em></p>"


def enrich_tickers_with_agent(
    html: str,
    *,
    openai_api_key: Optional[str],
    openai_model: str,
    openai_base_url: Optional[str] = None,
) -> str:
    """Use OpenAI agent to intelligently extract company mentions and add ticker symbols.
    
    This agent-based approach can identify companies in context and apply appropriate
    ticker symbols more accurately than simple pattern matching.
    """
    if not openai_api_key:
        return html
        
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        import openai
        
        # Configure OpenAI client
        client_kwargs = {
            "api_key": openai_api_key,
        }
        if openai_base_url:
            client_kwargs["base_url"] = openai_base_url
            
        client = openai.OpenAI(**client_kwargs)
        
        # System prompt for the agent
        system_prompt = """You are a financial content editor specializing in Chinese markets. Your task is to identify company mentions in HTML content and add appropriate ticker symbols in parentheses after the first occurrence of each company name.

Rules:
1. Only add ticker symbols for companies that are clearly mentioned in the content
2. Use the format: 公司名稱(TICKER.EXCHANGE)
3. For US stocks use .US suffix (e.g., AAPL.US, NVDA.US)
4. For Taiwan stocks use .TW suffix (e.g., 2330.TW, 2317.TW)
5. For Hong Kong stocks use .HK suffix (e.g., 0700.HK, 0005.HK)
6. Only modify the first occurrence of each company name
7. Do not add tickers if the company name is already followed by a ticker in parentheses
8. Return the modified HTML content only

Common mappings:
- 蘋果 → 蘋果(AAPL.US)
- 微軟 → 微軟(MSFT.US)
- 輝達 → 輝達(NVDA.US)
- 超微 → 超微(AMD.US)
- 特斯拉 → 特斯拉(TSLA.US)
- 亞馬遜 → 亞馬遜(AMZN.US)
- 谷歌 → 谷歌(GOOGL.US)
- Meta → Meta(META.US)
- 台積電 → 台積電(2330.TW)
- 鴻海 → 鴻海(2317.TW)
- 聯發科 → 聯發科(2454.TW)
- 廣達 → 廣達(2382.TW)
- 台達電 → 台達電(2308.TW)
- 聯電 → 聯電(2303.TW)
- 華碩 → 華碩(2357.TW)
- 宏碁 → 宏碁(2353.TW)
- 騰訊 → 騰訊(0700.HK)
- 阿里巴巴 → 阿里巴巴(9988.HK)"""

        user_prompt = f"""Please analyze the following HTML content and add appropriate ticker symbols to company mentions:

{html}

Return the modified HTML content with ticker symbols added."""

        # Call OpenAI API
        response = client.chat.completions.create(
            model=openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=4000
        )
        
        enriched_html = response.choices[0].message.content.strip()
        
        # Verify that we got valid HTML back
        if enriched_html and len(enriched_html) > len(html) * 0.8:  # Should be similar length or longer
            logger.debug(f"Agent enrichment successful. Original length: {len(html)}, enriched length: {len(enriched_html)}")
            return enriched_html
        else:
            logger.warning("Agent returned unexpected response, using original HTML")
            return html
            
    except Exception as e:
        logger.error(f"OpenAI agent ticker enrichment failed: {e}")
        return html


def enrich_tickers_simple(html: str) -> str:
    """Simple pattern-based ticker insertion for common companies.
    
    This is a fallback when MCP is not configured.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.debug(f"enrich_tickers_simple called with HTML length: {len(html)}")
    
    # Common Chinese company name to ticker mappings
    ticker_map = {
        "蘋果": "AAPL.US",
        "微軟": "MSFT.US", 
        "輝達": "NVDA.US",
        "超微": "AMD.US",
        "特斯拉": "TSLA.US",
        "亞馬遜": "AMZN.US",
        "谷歌": "GOOGL.US",
        "Meta": "META.US",
        "台積電": "2330.TW",
        "鴻海": "2317.TW",
        "聯發科": "2454.TW",
        "廣達": "2382.TW",
        "台達電": "2308.TW",
        "日月光": "2311.TW",
        "南亞科": "2408.TW",
        "華碩": "2357.TW",
        "宏碁": "2353.TW",
        "聯電": "2303.TW",
    }
    
    replaced = html
    replacements_made = 0
    
    for company, ticker in ticker_map.items():
        if company in html:
            logger.debug(f"Found company '{company}' in HTML")
            # Only replace if not already annotated
            pattern = re.escape(company) + r"(?!\s*\()"
            matches = re.findall(pattern, replaced)
            if matches:
                logger.debug(f"Pattern matches for '{company}': {len(matches)}")
                old_replaced = replaced
                replaced = re.sub(pattern, f"{company}({ticker})", replaced)
                if old_replaced != replaced:
                    replacements_made += 1
                    logger.debug(f"Replaced '{company}' with '{company}({ticker})'")
    
    logger.debug(f"Total replacements made: {replacements_made}")
    return replaced


def enrich_tickers_with_mcp(
    html: str,
    mcp_server_url: Optional[str],
    tool_name: str = "searchSymbol",
    *,
    headers: Optional[Dict[str, str]] = None,
    session_config: Optional[Dict[str, Any]] = None,
) -> str:
    """Detect company mentions and append ticker in parentheses via MCP tool.

    Expects MCP server to accept an input like {"query": "蘋果"} and return
    {"ticker": "AAPL.US"} or similar.
    """
    if not mcp_server_url:
        logging.getLogger(__name__).info("MCP enrichment: MCP_TICKER_SERVER_URL not set; skipping")
        return html
    if MCPClient is None and MultiServerMCPClient is None:
        logging.getLogger(__name__).warning("MCP enrichment: no MCP client available; please install langchain-mcp-adapters >= 0.0.16")
        return html

    logger = logging.getLogger(__name__)
    def _normalize_streamable_url(url: str) -> str:
        u = url.strip()
        # Ensure path ends with /mcp/
        if "/mcp" in u and not u.rstrip().endswith("/mcp/"):
            # Add trailing slash after /mcp
            if u.endswith("/mcp"):
                u = u + "/"
            # If URL already has /mcp?query, insert a slash before query if missing
            elif "/mcp?" in u and not "/mcp/?" in u:
                u = u.replace("/mcp?", "/mcp/?")
        # Append session config if provided and not present
        if session_config and "config=" not in u:
            try:
                import base64, json as _json
                cfg_b64 = base64.b64encode(_json.dumps(session_config).encode("utf-8")).decode("utf-8")
                sep = '&' if '?' in u else '?'
                u = f"{u}{sep}config={cfg_b64}"
            except Exception:
                pass
        return u
    mcp_server_url = _normalize_streamable_url(mcp_server_url)
    logger.debug(f"MCP enrichment start | url={mcp_server_url} | tool={tool_name}")
    # Candidate extraction: restrict to known company terms and obvious tickers to improve precision
    chinese_chunks = set(re.findall(r"[\u4e00-\u9fa5]{2,6}", html))
    # Minimal bilingual alias map to help MCP find the right instrument
    name_to_symbol_query: Dict[str, str] = {
        # US
        "蘋果": "AAPL",
        "微軟": "MSFT",
        "輝達": "NVDA",
        "超微": "AMD",
        "特斯拉": "TSLA",
        "亞馬遜": "AMZN",
        "谷歌": "GOOGL",
        "Google": "GOOGL",
        "Meta": "META",
        "英偉達": "NVDA",
        "高通": "QCOM",
        "博通": "AVGO",
        "美光": "MU",
        # TW
        "台積電": "2330.TW",
        "臺積電": "2330.TW",
        "台達電": "2308.TW",
        "聯發科": "2454.TW",
        "鴻海": "2317.TW",
        "廣達": "2382.TW",
        "聯電": "2303.TW",
        # KR
        "三星": "005930.KS",
        # HK
        "騰訊": "0700.HK",
        "阿里巴巴": "9988.HK",
        "小米": "1810.HK",
    }
    # English tokens found directly
    english_tokens = set(re.findall(r"\b([A-Z]{2,6})(?:\.[A-Z]{2})?\b", html))
    # Numeric Taiwan tickers like 0050, 2330 in text (exclude years 1900-2099)
    numeric_tw_all = set(re.findall(r"\b(\d{4})\b", html))
    numeric_tw = {n for n in numeric_tw_all if not (1900 <= int(n) <= 2099)}

    # Build candidate names from alias keys present + obvious patterns
    alias_keys_present = {k for k in name_to_symbol_query.keys() if k in html}
    candidates = set(alias_keys_present)
    # Also include uppercase tokens which might already be symbols
    for tok in english_tokens:
        candidates.add(tok)
        # ensure symbol formatting if later annotated directly
        name_to_symbol_query.setdefault(tok, tok)
    # Numeric Taiwanese tickers -> .TW
    for tw in numeric_tw:
        name_to_symbol_query.setdefault(tw, f"{tw}.TW")
        candidates.add(tw)

    if not candidates:
        logger.info("MCP enrichment: no candidate company names detected in HTML")
        return html
    logger.info(f"MCP enrichment: {len(candidates)} candidate terms: {sorted(list(candidates))[:10]}{'...' if len(candidates)>10 else ''}")

    client = None
    tools_map: Dict[str, object] = {}
    http_only = False
    # Prefer MultiServerMCPClient to properly load declared tools
    try:
        if MultiServerMCPClient is not None:
            cfg: Dict[str, Dict[str, str]] = {
                "ticker": {"transport": "streamable_http", "url": mcp_server_url}
            }
            if headers:
                # type: ignore[assignment]
                cfg["ticker"]["headers"] = headers  # type: ignore[index]
            ms_client = MultiServerMCPClient(cfg)
            tools = asyncio.run(ms_client.get_tools())  # type: ignore[arg-type]
            tools_map = {getattr(t, "name", ""): t for t in tools}
            logger.info(f"MCP enrichment: discovered tools: {list(tools_map.keys())}")
    except Exception as e:
        logger.debug(f"MultiServerMCPClient init failed: {e}")
        tools_map = {}
    
    # Try MCP Python SDK streamable HTTP client directly if adapters didn't load tools
    if not tools_map:
        try:
            from mcp import ClientSession  # type: ignore
            from mcp.client.streamable_http import streamablehttp_client  # type: ignore
            from langchain_mcp_adapters.tools import load_mcp_tools  # type: ignore

            async def _load_tools_streamable(url: str):
                params: Dict[str, Any] = {"url": url}
                if headers:
                    params["headers"] = headers
                async with streamablehttp_client(**params) as (read, write, _):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        return await load_mcp_tools(session)

            tools = asyncio.run(_load_tools_streamable(mcp_server_url))
            tools_map = {getattr(t, "name", ""): t for t in tools}
            logger.info(f"MCP enrichment (SDK): discovered tools: {list(tools_map.keys())}")
        except Exception as e:
            logger.debug(f"MCP SDK streamable client init failed: {e}")
    
    # Fallback to simple HTTP client if available
    if not tools_map and MCPClient is not None:
        try:
            client = MCPClient(base_url=mcp_server_url)  # type: ignore[call-arg]
        except Exception as e:
            logger.debug(f"HttpMCPClient init failed: {e}")
            client = None
    
    # Final fallback: direct HTTP calls against streamable_http MCP server
    if not tools_map and client is None:
        http_only = True
        logger.info("MCP enrichment: falling back to direct HTTP mode for streamable_http server")
    
    if not tools_map and client is None and not http_only:
        return html

    def _extract_symbol_from_response(resp_obj: object) -> Optional[str]:
        # Try common placements first
        if isinstance(resp_obj, dict):
            # direct fields
            for key in ("ticker", "symbol", "fullSymbol"):
                val = resp_obj.get(key)
                if isinstance(val, str) and len(val) <= 16:
                    return val
            # nested known containers
            for key in ("price", "info", "meta", "data"):
                sub = resp_obj.get(key)
                if isinstance(sub, dict):
                    sym = _extract_symbol_from_response(sub)
                    if sym:
                        return sym
            # list under result/results/items
            for key in ("result", "results", "items"):
                arr = resp_obj.get(key)
                if isinstance(arr, list):
                    for item in arr:
                        sym = _extract_symbol_from_response(item)
                        if sym:
                            return sym
        elif isinstance(resp_obj, list):
            for item in resp_obj:
                sym = _extract_symbol_from_response(item)
                if sym:
                    return sym
        return None

    def _extract_exchange_from_response(resp_obj: object) -> Optional[str]:
        if isinstance(resp_obj, dict):
            for key in ("exchange", "market", "fullExchangeName", "exchangeName", "primaryExchange", "quoteType"):
                val = resp_obj.get(key)
                if isinstance(val, str) and len(val) <= 32:
                    return val
            for key in ("price", "info", "meta", "data", "summaryProfile"):
                sub = resp_obj.get(key)
                if isinstance(sub, dict):
                    ex = _extract_exchange_from_response(sub)
                    if ex:
                        return ex
            for key in ("result", "results", "items"):
                arr = resp_obj.get(key)
                if isinstance(arr, list):
                    for item in arr:
                        ex = _extract_exchange_from_response(item)
                        if ex:
                            return ex
        elif isinstance(resp_obj, list):
            for item in resp_obj:
                ex = _extract_exchange_from_response(item)
                if ex:
                    return ex
        return None

    def _format_with_suffix(symbol: str, exchange: Optional[str]) -> str:
        if not exchange:
            return symbol
        ex = exchange.lower()
        if any(k in ex for k in ["nasdaq", "nyse", "nyq", "nms", "us"]):
            return f"{symbol}.US"
        if any(k in ex for k in ["hk", "hong kong", "hkse"]):
            # Ensure leading zeros for numeric tickers common in HK
            return f"{symbol}.HK"
        if any(k in ex for k in ["taiwan", "tpe", "twse", "tw"]):
            return f"{symbol}.TW"
        if any(k in ex for k in ["tse", "tsx"]):
            return f"{symbol}.CA"
        if any(k in ex for k in ["lse", "lon"]):
            return f"{symbol}.GB"
        return symbol

    def lookup(name: str) -> Optional[str]:
        try:
            # Official adapter: prefer a generic call signature
            resp = None
            # Try multiple common argument names for Yahoo Finance tools
            query_values = [name]
            alias = name_to_symbol_query.get(name)
            if alias and alias not in query_values:
                query_values.append(alias)
            arg_attempts = []
            for qv in query_values:
                arg_attempts.extend([
                    {"query": qv},
                    {"q": qv},
                    {"symbol": qv},
                    {"ticker": qv},
                    {"name": qv},
                ])
            # Try multiple tool names within this MCP server, staying MCP-only
            # Prefer lightweight lookups first
            preferred = [tool_name, "searchName", "getQuote", "get_stock_info"]
            # De-duplicate while preserving order
            seen = set()
            tool_names = [t for t in preferred if not (t in seen or seen.add(t))]
            server_unavailable = False
            for tn in tool_names:
                for args in arg_attempts:
                    if server_unavailable:
                        break
                    try:
                        if tools_map:
                            tool_obj = tools_map.get(tn)
                            if tool_obj is None:
                                continue
                            inv = getattr(tool_obj, "invoke", None)
                            ainv = getattr(tool_obj, "ainvoke", None)
                            callm = getattr(tool_obj, "call", None)
                            arun = getattr(tool_obj, "arun", None)
                            if callable(ainv):
                                resp = asyncio.run(ainv(args))
                            elif callable(arun):
                                resp = asyncio.run(arun(args))
                            elif callable(inv):
                                # Some tools may support sync invoke
                                resp = inv(args)
                            elif callable(callm):
                                resp = callm(args)
                            else:
                                resp = None
                        elif client is not None:
                            if hasattr(client, "invoke"):
                                resp = client.invoke(tn, args)
                            elif hasattr(client, "call"):
                                resp = client.call(tn, args)
                            else:
                                resp = None
                        elif http_only:
                            import requests
                            from urllib.parse import urlsplit, urlunsplit
                            parts = urlsplit(mcp_server_url)
                            # Ensure path ends with /mcp/
                            base_path = parts.path
                            if not base_path.endswith("/mcp/"):
                                if base_path.endswith("/mcp"):
                                    base_path = base_path + "/"
                                elif base_path.endswith("/mcp?"):
                                    base_path = base_path.replace("/mcp?", "/mcp/?")
                            invoke_path = base_path.rstrip("/") + f"/tools/{tn}/invoke"
                            url = urlunsplit((parts.scheme, parts.netloc, invoke_path, parts.query, parts.fragment))
                            try:
                                req_headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
                                if headers:
                                    req_headers.update(headers)
                                r = requests.post(url, json=args, headers=req_headers, timeout=10)
                                if r.status_code == 200:
                                    resp = r.json()
                                else:
                                    logger.debug(f"HTTP MCP invoke failed {r.status_code}: {r.text[:200]} | url={url}")
                                    # If server is unavailable, stop further attempts for this run
                                    if r.status_code in (502, 503, 504):
                                        server_unavailable = True
                                    resp = None
                            except Exception as http_e:
                                logger.debug(f"HTTP MCP error: {http_e} | url={url}")
                                resp = None
                        else:
                            resp = None
                        if isinstance(resp, str):
                            try:
                                resp = json.loads(resp)
                            except Exception:
                                pass
                        if resp is not None:
                            ticker = _extract_symbol_from_response(resp)
                            exchange = _extract_exchange_from_response(resp)
                            logger.debug(f"MCP resp for '{name}' with tool='{tn}' args={args}: {str(resp)[:200]}")
                            if ticker and isinstance(ticker, str):
                                return _format_with_suffix(ticker, exchange)
                    except Exception as inner_e:
                        logger.debug(f"MCP call failed for '{name}' tool='{tn}' args={args}: {inner_e}")
        except Exception:
            return None
        return None

    replaced = html
    applied = 0
    for name in sorted(candidates, key=len, reverse=True):
        ticker = lookup(name)
        if not ticker:
            logger.debug(f"No ticker found for '{name}' via MCP")
            continue
        # Normalize common outputs: if no market suffix, keep as-is (do not guess)
        formatted = ticker.strip()
        # Avoid double-adding if already present
        pattern = re.escape(name) + r"(?!\s*\()"
        replaced = re.sub(pattern, f"{name}({formatted})", replaced)
        applied += 1
        logger.info(f"Annotated '{name}' -> {name}({formatted})")
    if applied == 0:
        logger.info("MCP enrichment: 0 annotations applied")
    else:
        logger.info(f"MCP enrichment: applied {applied} annotations")
    return replaced


def enrich_tickers_with_mcp_agent(
    html: str,
    *,
    mcp_url: Optional[str],  # single-server convenience
    mcp_servers: Optional[Dict[str, Dict[str, str]]] = None,  # multi-server config
    openai_api_key: Optional[str],
    openai_model: str,
    openai_base_url: Optional[str] = None,
) -> str:
    """Use official MCP adapters to load tools and let an agent decide tickers.

    This follows the README pattern by loading MCP tools and binding them to a model.
    """
    if not (MultiServerMCPClient and ChatOpenAI and openai_api_key):
        return html

    async def _get_tools(url: Optional[str], servers: Optional[Dict[str, Dict[str, str]]]):
        config: Dict[str, Dict[str, str]] = {}
        # Prefer explicit multi-server config
        if servers:
            config.update(servers)
        # Also include single URL if provided
        if url:
            config.setdefault("ticker", {"transport": "streamable_http", "url": url})
        if not config:
            return []
        client = MultiServerMCPClient(config)
        tools = await client.get_tools()
        return tools

    try:
        tools = asyncio.run(_get_tools(mcp_url, mcp_servers))  # type: ignore[arg-type]
    except Exception:
        return html

    # Initialize model and bind tools
    kwargs: Dict[str, object] = {
        "model": openai_model,
        "api_key": openai_api_key,
        "temperature": 0.0,
    }
    if openai_base_url:
        kwargs["base_url"] = openai_base_url
    try:
        model = ChatOpenAI(**kwargs)  # type: ignore
    except Exception:
        return html

    try:
        bound = model.bind_tools(tools)  # type: ignore[attr-defined]
        system = (
            "You are a financial editing assistant. If the content mentions a company/brand, "
            "use available tools to resolve the proper ticker symbol (e.g., AAPL.US) and insert it in parentheses "
            "after the first occurrence of that company name. Keep original wording; only add ticker annotations. "
            "Return updated HTML only."
        )
        user = (
            "HTML content to annotate with tickers:\n\n" + html +
            "\n\nRules:\n- Do not fabricate tickers.\n- If no ticker is found, leave the term unchanged.\n- Output valid HTML only."
        )
        messages = [SystemMessage(content=system), HumanMessage(content=user)]  # type: ignore
        tool_map = {getattr(t, "name", None): t for t in tools}
        # Simple tool-call loop
        for _ in range(5):
            ai = bound.invoke(messages)
            messages.append(ai)
            tool_calls = getattr(ai, "tool_calls", None)
            if not tool_calls:
                content = getattr(ai, "content", None)
                if isinstance(content, str) and content.strip():
                    return content
                break
            # Execute tool calls and feed results back
            for tc in tool_calls:
                name = getattr(tc, "name", None) or (tc.get("name") if isinstance(tc, dict) else None)
                args = getattr(tc, "args", None) or (tc.get("args") if isinstance(tc, dict) else {})
                tc_id = getattr(tc, "id", None) or (tc.get("id") if isinstance(tc, dict) else None)
                tool = tool_map.get(name)
                if tool is None:
                    continue
                try:
                    result = tool.invoke(args)
                except Exception as e:
                    result = {"error": str(e)}
                messages.append(ToolMessage(content=json.dumps(result, ensure_ascii=False), tool_call_id=tc_id))  # type: ignore
        # If loop ended without clear content, return original
        return html
    except Exception:
        return html
