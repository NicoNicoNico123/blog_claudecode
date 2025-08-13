# Enhanced Blog Generation

Transform YouTube transcripts (stored in PostgreSQL) into rich, SEO‑ready **Cantonese** blog posts with visual assets hosted on **Cloudinary**.

---

## Quick Start (Data Source)

Fetch the latest data from PostgreSQL table **`financial_blog`**, retrieving the fields:

* `video_id` *(for DB keys & Cloudinary naming)*
* `title`
* `channel_name`
* `transThis ensures generation always uses the most current transcript and can persist results reliably.

---

## CLI Usage

The generation pipeline provides a command-line interface with two main commands: `run` and `doctor`.

### Installation & Setup

```bash
cd financial-blog-pipeline/generation
pip install -e .
```

### Environment Variables

Create a `.env` file with required configuration:

```bash
# Database (Required)
DATABASE_URL=postgresql://user:password@host:port/database

# OpenAI API (Required for LLM)
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4o-mini  # or gpt-4
OPENAI_BASE_URL=https://api.openai.com/v1  # optional

# Cloudinary (Required for image hosting)
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
CLOUDINARY_FOLDER=blog  # optional, defaults to 'blog'

# Unsplash (Optional for stock images)
UNSPLASH_ACCESS_KEY=your_unsplash_key

# MCP Ticker Enrichment (Optional)
# Use Financial Modeling Prep MCP server (Streamable HTTP)
MCP_TICKER_SERVER_URL=https://<your-fmp-mcp-host>/mcp
MCP_TICKER_TOOL=searchSymbol
# Optional: headers / session config for MCP
# MCP_TICKER_HEADERS_JSON='{"X-Api-Key":"<your_fmp_token>"}'
# MCP_SESSION_CONFIG_JSON='{"FMP_TOOL_SETS":"search,quotes"}'

# Pipeline Configuration
USE_LANGCHAIN=true  # Use LangChain agents vs direct OpenAI calls
DEFAULT_LANGUAGE=cantonese
OUTPUT_DIR=./outputs  # Where to save generated bundles
```

### Command: `run` - Main Generation Pipeline

**Basic Usage**
```bash
# Generate blog from latest transcript in database
python -m generation_pipeline.cli run

# With database persistence
python -m generation_pipeline.cli run --write-db

# Force regeneration even if output exists
python -m generation_pipeline.cli run --force

# Generate for specific video ID
python -m generation_pipeline.cli run --video-id p08_Rkh36bA
```

**Advanced Options**
```bash
# Text-only generation (skip image processing)
python -m generation_pipeline.cli run --text-only

# Preview HTML output in terminal
python -m generation_pipeline.cli run --print-html

# Override LangChain setting for this run
python -m generation_pipeline.cli run --use-langchain
python -m generation_pipeline.cli run --no-use-langchain

# Set logging level
python -m generation_pipeline.cli run --log-level DEBUG
python -m generation_pipeline.cli run --log-level WARNING
```

**Complete Example**
```bash
# Full pipeline with all features enabled
python -m generation_pipeline.cli run \
  --write-db \
  --print-html \
  --log-level INFO \
  --force
```

#### Options Reference

| Option | Description | Default |
|--------|-------------|---------|
| `--video-id` | Process specific video ID instead of latest | Latest from DB |
| `--write-db/--no-write-db` | Persist results to PostgreSQL after generation | `false` |
| `--force` | Force generation even if output exists | `false` |
| `--use-langchain/--no-use-langchain` | Override USE_LANGCHAIN env variable | From env |
| `--log-level` | Set logging level (DEBUG/INFO/WARNING/ERROR/CRITICAL) | `INFO` |
| `--text-only` | Skip image retrieval/upload; generate text only | `false` |
| `--print-html` | Print generated HTML to stdout and save to file | `false` |

### Command: `doctor` - Environment Check

Check your environment configuration:

```bash
python -m generation_pipeline.cli doctor
```

**Sample Output**
```
DB: OK | LLM(OpenAI): OK | LangChain: ON | Cloudinary: OK | Unsplash: OK
```

**Status Indicators**
- **DB**: Database connection status
- **LLM(OpenAI)**: OpenAI API configuration
- **LangChain**: Whether LangChain agents are enabled
- **Cloudinary**: Image hosting service status
- **Unsplash**: Stock photo service status

### Typical Workflows

#### 1. Daily Blog Generation
```bash
# Check environment first
python -m generation_pipeline.cli doctor

# Generate and save to database
python -m generation_pipeline.cli run --write-db --log-level INFO
```

#### 2. Development & Testing
```bash
# Generate text-only for quick testing
python -m generation_pipeline.cli run --text-only --print-html

# Test specific video without saving to DB
python -m generation_pipeline.cli run --video-id ABC123 --force
```

#### 3. Debugging & Analysis
```bash
# Verbose logging with HTML preview
python -m generation_pipeline.cli run \
  --log-level DEBUG \
  --print-html \
  --force
```

#### 4. Production Deployment
```bash
# Full pipeline with error handling
python -m generation_pipeline.cli run \
  --write-db \
  --log-level WARNING \
  || echo "Generation failed, check logs"
```

### Output Files

When you run the pipeline, it creates:

**Always Generated**
- `outputs/{video_id}_blogs_{timestamp}.json` - Complete content bundle

**With `--print-html`**
- `outputs/{video_id}_post_{timestamp}.html` - Standalone HTML preview

**With `--write-db`**
- Data persisted to PostgreSQL tables:
  - `blog_posts_v2` - Generated blog posts
  - `visual_topics` - Extracted visual topics
  - `media_jobs` - Image processing jobs (if applicable)

### Error Handling

The CLI provides clear error messages for common issues:

```bash
# Missing database URL
ERROR: DATABASE_URL is required in environment

# No source data
No source transcripts found in financial_blog table

# Video ID mismatch (warning, continues with latest)
Latest row video_id=XYZ789 does not match requested ABC123. Proceeding with latest.
```

---

## End‑to‑End Flow (Pretty Structure)

### 0) Source & Retrieval

**Input**: `title`, `channel_name`, `transcript_text` from `financial_blog` (latest row by `published_at` DESC; fallback `created_at`).
**Output**: Cleaned transcript payload → **LLM Agent**.

---

### 1) LLM Agent — Task Breakdown

**What it does**

* Cluster topics & sub‑questions from the transcript.
* Detect entities (tickers, companies, macro events) and map to markets.
* Draft outline (Cantonese) with section goals.

**Output**: Outline + entity map.

---

### 2) Blog Post Generation (LLM)

**What it does**

* Generate a Cantonese post (authentic Hong Kong KOL tone).
* Enforce structure (hooks → analysis → explanation → conclusions/disclaimer).

**Output**: Cantonese post.

---

### 3) Finalization & QA

**What it does**

* Consistency checks across sections; remove duplication, hallucinations,與財經無關內容。
* Normalize tone/style; insert risk disclaimers and clear takeaways.

**Output**: Finalized Cantonese post.

---

### 4) Visual Topic Extraction (AI‑Decided)

**What it does**

* AI agent decides **which keywords/topics** from finalized text become visuals (by entities, sections, sentiments).
* Score which sections benefit from visuals (event photos, concept art, charts).

**Output**: Candidate visual topics.

**Subtasks (4.x)**

* **4.1 Normalization & Dedup**: normalize case, strip punctuation, merge synonyms (e.g., "CPI" ≈ "通脹指數").
* **4.2 Visualizability Scoring**: rank by newsworthiness, concreteness, chartability, uniqueness, audience value → `score_visual` ∈ \[0,1].
* **4.3 Safety & Brand Compliance**: remove prohibited/sensitive visuals (logos, watermarks, graphic content); enforce neutral, non‑promotional framing.
* **4.4 Persistence (bridge)**: upsert each topic into **`visual_topics`** with fields: `video_id`, `language`, `topic_key`, `keywords[]`, `source_section`, `score_visual`, `status='pending'`, timestamps; compute `topic_hash` for idempotency.
* **4.5 Modality Hinting (choose image source)**

  * **News (Google News Images)** → time‑sensitive (event ≤ 30 days), named entities/tickers, real‑world photos; store source URL, publisher, license.
  * **Stock (Unsplash)** → evergreen/abstract concepts, metaphor‑friendly visuals; store photographer attribution.
  * **Generate (AI)** → no suitable/licensable images or need diagrams/custom charts; avoid logos/trademarks.
  * **Tie‑breakers**: prefer (1) clear license, (2) width ≥ 1200px, (3) relevance ≥ 0.7, (4) safety pass.
  * **Pseudo Flow (selection)**

    1. Compute `timeliness_score`, `entity_specificity`, `search_availability`.
    2. If `timeliness_score` within window AND high `entity_specificity` AND sufficient licensed results → **News**.
    3. Else if evergreen/abstract AND stock results sufficient → **Stock**.
    4. Else → **Generate** (AI) with compliance‑safe prompt.
    5. Persist chosen source + rationale on the topic.
* **4.6 Query Preparation**: build search queries (zh‑HK / en only), add tickers (e.g., 0700, 0388) & date windows (e.g., last 30 days for news).
* **4.7 Optional Queuing**: enqueue image‑fetch jobs in **`media_jobs`** (`job_type='image_fetch'`, payload with topic ids) for parallel workers.

---

### 5) Prompt Synthesis

**What it does**

* Convert selected topics into concise text‑to‑image prompts (avoid brand logos; include scene, subject, context; use 16:9 if feature image).
* Provide alt‑text suggestions.

**Output**: Prompt set per topic.

---

### 6) Image Retrieval & Selection → Cloudinary Upload

**What it does**

* **Google News** for timely visuals; **Unsplash** for stock; **AI gen** (DALL·E) if needed.
* Rank candidates by relevance, freshness, resolution, safety; select top N.
* **Mandatory**: upload selected/generated image(s) to **Cloudinary**; capture:

  * `topic_key` (links back to visual topic)
  * `image_name` (human‑readable; convention: `${topic_key}__${source_basename_or_label}`)
  * `public_id` (pattern: `${CLOUDINARY_FOLDER}/${video_id}/${lang}/${topic_key}/${image_slug}`)
  * `secure_url`, `width`, `height`, `format`
  * `source_url`, `attribution` (for news/stock)
  * `provider` (`google_news` | `unsplash` | `dalle`)
* Persist image metadata to PostgreSQL.

**Output**: Cloudinary URLs + metadata per topic.

---

### 7) Assembly & Persistence

**What it does**

* Build JSON payload with posts, prompts, selected images, attributions.
* Save to `generation/outputs/` only (no DB writes here).

**Output**: Publish‑ready content bundle.

---

### 8) Idempotency & Logging

**What it does**

* Skip generation if `(video_id, language)` already exists; allow force‑rerun when needed.
* Log reasoning hashes (prompt+response) for audit.

**Output**: Stable, deduplicated pipeline.

---

### 9) Upload to PostgreSQL (Storage)

**Input**

* Finalized JSON bundle from step 7 (assembly): posts, prompts, selected images, attributions, Cloudinary metadata.

**What it does**

* **Validate JSON**: ensure required fields exist

  * `original_video.video_id`
  * at least one entry in `generated_posts` (prefer `language = "cantonese"` as primary)
  * each `images[]` item includes `topic_key`, `image_name`, `provider`, `source_url` (if news/stock), `attribution` (if required), and `cloudinary.public_id` (must match naming pattern), `cloudinary.secure_url`, `width`, `height`, `format`.
* **Upsert posts** into **`blog_posts_v2`** (new table; key: `(video_id, lang)`):

  * `title`, `html`, `tags`, `meta_description`, `images` (JSONB array with Cloudinary fields), `created_at`/`updated_at (UTC)`.
  * **On conflict**: update `html`, `tags`, `meta_description`, `images`, `updated_at`.
* **Mark source transcript** (`financial_blog`) as `processed_generation = true` by `video_id`.
* **Return** write confirmations (affected rows, ids).

**Output**

* Persisted blog rows in `blog_posts_v2` and processed flag on source transcript.

---

## Blog Structure（只生成廣東話）

> 本結構僅輸出 **廣東話（真·香港KOL語氣）**；並在每個段落標示需要 **AI Agent** 參與的任務。

**圖例**

* `[AI]` 需要 LLM 生成/改寫
* `[Rule]` 規則化/模板化處理（非生成）

1. **開場白** —「大家好，我係……」自然口語

   * `[AI]` 依據 `channel_name`、主播風格與主題自動寫作，保持真實親切；避免投資建議語氣。

2. **市場分析**

   * `[AI]` 嚴格根據 `transcript_text` 萃取核心事件、影響機制與重點數據。
   * `[Rule]` 只可引用逐字稿中已出現的市場、資產、代號或例子；避免自行補充或假設本地（港股）示例。

3. **投資貼士｜記住呢幾點**

   * `[AI]` 將重點歸納為 3–5 條 bullet，強調風險意識與情境條件。
   * `[Rule]` 用詞審核：移除「必賺」「保證」等不當字眼。

4. **風險與免責聲明**

   * `[Rule]` 套用標準免責模板（非投資建議）。
   * `[AI]` 微調語氣，與整體文風一致。

5. **結語 / Call‑to‑learn**

   * `[AI]` 溫和收束與鼓勵，避免推銷式語氣；可提示讀者進一步學習方向。

6. **視覺位標註（給圖像管線）**

   * `[AI]` 在需要配圖的小節加上 ⚑ 標記並產生 `topic_key`（供 4.x 影像流程使用）。

---

## Output Layout

```
generation/outputs/
└── [video_id]_blogs_[timestamp].json   # Blog + Cloudinary URLs (no local image files)
```

### JSON Schema (excerpt)

```json
{
  "original_video": {
    "video_id": "p08_Rkh36bA",
    "title": "影片標題",
    "transcript_text": "完整逐字稿..."
  },
  "generated_posts": [
    {
      "language": "cantonese",
      "post": { "title": "...", "html": "...", "tags": ["財經"], "meta_description": "..." }
    }
  ],
        "meta_description": "..."
      }
    },
    {
      "language": "cantonese",
      "post": { "title": "...", "html": "...", "tags": ["財經"], "meta_description": "..." }
    }
  ],
  "images": [
    {
      "topic_key": "us_inflation_cpi",
      "image_name": "us_inflation_cpi__cpi-report-2024-headline",
      "provider": "unsplash",
      "source_url": "https://unsplash.com/photos/...",
      "attribution": "Photographer / Unsplash",
      "cloudinary": {
        "public_id": "blog/p08_Rkh36bA/cantonese/us_inflation_cpi/cpi-report-2024-headline",
        "secure_url": "https://res.cloudinary.com/<cloud>/image/upload/v.../blog/p08_Rkh36bA/cantonese/us_inflation_cpi/cpi-report-2024-headline.png",
        "width": 1600,
        "height": 900,
        "format": "png"
      }
    }
  ]
}
```

---

## Integration with PostgreSQL

**Reads**: transcripts produced upstream (table: `financial_blog`).

Expected minimal columns:

* `id`, `video_id`, `channel_name`, `title`, `published_at`, `transcript_text`, `lang`, `processed_generation` (bool)

**Writes**:

* Table **`visual_topics`**: `video_id`, `language`, `topic_key`, `keywords[]`, `source_section`, `score_visual`, `status`, `topic_hash`, timestamps
* Table **`media_jobs`** (optional): `job_type`, `payload jsonb`, `status`, `attempts`, `run_at`, `updated_at`
* Table **`blog_posts_v2`** (new): `video_id`, `lang`, `title`, `html`, `meta_description`, `tags`, `images jsonb` *(each item: **`topic_key`**, **`image_name`**, **`provider`**, **`source_url`**, **`attribution`**, **`cloudinary.{public_id,secure_url,width,height,format}`**)*, `created_at`, `updated_at`

> Tip: Add UNIQUE indexes on `blog_posts_v2(video_id, lang)` and `visual_topics(video_id, language, topic_key)`.

---
