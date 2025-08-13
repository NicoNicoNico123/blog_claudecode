-- Minimal schema for blog generation persistence

CREATE TABLE IF NOT EXISTS visual_topics (
  id SERIAL PRIMARY KEY,
  video_id TEXT NOT NULL,
  language TEXT NOT NULL,
  topic_key TEXT NOT NULL,
  keywords TEXT[] NOT NULL DEFAULT '{}',
  source_section TEXT,
  score_visual DOUBLE PRECISION NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'pending',
  topic_hash TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_visual_topics_unique
  ON visual_topics (video_id, language, topic_key);

CREATE TABLE IF NOT EXISTS blog_posts_v2 (
  id SERIAL PRIMARY KEY,
  video_id TEXT NOT NULL,
  lang TEXT NOT NULL,
  title TEXT NOT NULL,
  html TEXT NOT NULL,
  meta_description TEXT,
  tags TEXT[] NOT NULL DEFAULT '{}',
  images JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_blog_posts_v2_unique
  ON blog_posts_v2 (video_id, lang);

-- Optional job table if using async workers (not required for basic pipeline)
CREATE TABLE IF NOT EXISTS media_jobs (
  id SERIAL PRIMARY KEY,
  job_type TEXT NOT NULL,
  payload JSONB NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  attempts INT NOT NULL DEFAULT 0,
  run_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
