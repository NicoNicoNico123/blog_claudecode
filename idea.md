## Market‑Impact‑Focused Chinese Financial Education Pipeline 

### Overview

**Content Focus:** Beginner‑friendly investment education for Chinese‑speaking readers, driven by video content that actually moves global markets.

**Stack**

* **Ingestion / AI Agents:** MCP + custom Python micro‑services
* **Database:** PostgreSQL (Zeabur)
* **CMS:** Ghost (Zeabur deploy)
* **Runtime:** Zeabur serverless + CRON (all jobs scheduled in **UTC**)

**Core Promise:** **「教你看懂動市場的新聞」** — turn high‑impact events into simple, actionable lessons.

**Publishing Cadence:** 3 posts / day (flagship impact analysis · live reaction · educational explainer)

---

# Five‑Phase Agent‑Driven Pipeline (HKT)

| Phase                                 | HKT Window                     | Goal                                                                                    | Key Agents                                                                                           |
| ------------------------------------- | ------------------------------ | --------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| **1 · Script Fetch & Store**          | Polling on 10:00 am HKT Mon to Fri | Pull latest transcripts from @yutinghaofinance/streams and write directly to PostgreSQL | `Script_Extraction_Agent`                                                                            |
| **2 · Indexing & Keyword Extraction** | Triggered per batch            | Build full‑text & trigram indexes, extract keywords                                     | `Keyword_Index_Agent`                                                                                |
| **3 · Script Filtering & Theming**    |              | Select finance‑relevant transcripts & cluster by topic                                  | `Script_Filtering_Agent`, `Topic_Clustering_Agent`                                                   |
| **4 · Draft + Image Generation**      |                | Generate Traditional‑Chinese draft + search / generate supporting images; QA            | `Blog_Generation_Agent`, `Image_Research_Agent`, `Image_Generation_Agent`, `Quality_Assurance_Agent` |
| **5 · Refine & Publish**              |                | Apply style guide, convert to Ghost format, publish, track performance                  | `Refinement_Agent`, `Ghost_Publisher_Agent`, `Performance_Tracker`                                   |

> **Time reference:** 21:15 UTC = 05:15 HKT (next calendar day in Hong Kong).

---

## Phase 1 · Script Fetch & Store

| Agent                         | Responsibilities                                                                                                                                                                                                                                                                                       |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Script\_Extraction\_Agent** | • Use MCP to subscribe to **@yutinghaofinance/streams** <br>• Detect newly started or uploaded live‑stream videos <br>• Retrieve video metadata & audio, transcribe to timestamped text <br>• Tag market‑sensitive terms (NER) <br>• **Insert payload directly into PostgreSQL `video_scripts` table** |

**Database schema (created once):**


**Output →** New rows in `video_scripts` ready for indexing.

---

## Phase 2 · Indexing & Keyword Extraction

| Agent                     | Responsibilities                                                                                                                                                                          |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Keyword\_Index\_Agent** | • Fetch unindexed rows from `video_scripts` <br>• Extract key terms & their weights <br>• Populate `script_keywords` table <br>• Build / refresh full‑text search (GIN) & trigram indexes |


**Output →** Indexed scripts + searchable keyword map.

---

## Phase 3 · Script Filtering & Theming (21:15‑22:15 UTC)

| Agent                        | Responsibilities                                                                                                                            |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| **Script\_Filtering\_Agent** | • Query last‑24 h scripts <br>• Drop non‑financial or low‑signal segments <br>• Normalise to Traditional Chinese where needed               |
| **Topic\_Clustering\_Agent** | • Group remaining scripts by ticker / macro theme using BERTopic (or K‑means on embeddings) <br>• Rank clusters by mention volume & recency |

**Output →** `filtered_scripts` view + `theme_clusters.json` (top N clusters with sample segments).

---

## Phase 4 · Draft + Image Generation (23:00‑00:30 UTC)

| Agent                         | Responsibilities                                                                                                         |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| **Blog\_Generation\_Agent**   | • For each top cluster, create draft in **Traditional Chinese**: Hook → Market Impact → Beginner Explanation → Takeaways |
| **Image\_Research\_Agent**    | • Query finance‑related stock‑photo APIs (Unsplash, Pexels) using tickers / topics                                       |
| **Image\_Generation\_Agent**  | • If no suitable image found, call internal image‑gen API to create infographic/chart                                    |
| **Quality\_Assurance\_Agent** | • Validate facts, tone, SEO keywords <br>• Check that images exist & alt‑text added                                      |

**Output →** `blog_draft.md` with embedded image URLs / uploads.

---

## Phase 5 · Refine & Publish (02:00‑03:00 UTC)

| Agent                       | Responsibilities                                                                                                                                                                             |
| --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Refinement\_Agent**       | • Apply house style (簡明、有條理、港式用詞) <br>• Add footnotes, CTAs, tags <br>• Convert Markdown → Ghost Mobiledoc JSON                                                                              |
| **Ghost\_Publisher\_Agent** | • Push post & images to Ghost via Admin API <br>• Schedule publish = immediate (within UTC window)                                                                                           |
| **Performance\_Tracker**    | • Collect metrics (views, scroll, shares) via Ghost Content API <br>• Store in `post_metrics` table <br>• Nightly job feeds engagement data back to Phase 2 for keyword‑weight recalibration |

---

### KPI Targets

| Metric                         | Goal                     |
| ------------------------------ | ------------------------ |
| **Market Direction Accuracy**  | ≥ 75 % on flagged events |
| **Average Read‑through Depth** | ≥ 60 %                   |
| **Free→Paid Conversion**       | ≥ 5 % monthly uplift     |

---

### Closing Note

With a single trusted video source, UTC‑aligned CRONs, and direct PostgreSQL writes, this streamlined pipeline delivers timely, image‑enhanced posts that help Chinese‑speaking beginners grasp the news that truly drives global markets.
