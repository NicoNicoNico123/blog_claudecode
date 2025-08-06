-- Chinese Financial Education Blog Pipeline - Database Schema
-- PostgreSQL with full-text search and indexing

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- VideoScript: Stores extracted video scripts with metadata
CREATE TABLE IF NOT EXISTS video_scripts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    video_id VARCHAR(50) UNIQUE NOT NULL,
    channel_handle VARCHAR(100) NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    publish_date TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_seconds INTEGER,
    transcript_text TEXT NOT NULL,
    transcript_language VARCHAR(10) DEFAULT 'zh-TW',
    entities_json JSONB, -- Extracted financial entities (tickers, companies, terms)
    confidence_score DECIMAL(3,2), -- Transcription confidence
    processing_status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ScriptKeyword: Extracted keywords with TF-IDF weights
CREATE TABLE IF NOT EXISTS script_keywords (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    script_id UUID REFERENCES video_scripts(id) ON DELETE CASCADE,
    keyword VARCHAR(255) NOT NULL,
    tfidf_score DECIMAL(5,4) NOT NULL,
    frequency INTEGER NOT NULL,
    is_financial BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(script_id, keyword)
);

-- ContentFilter: Filtered scripts for blog generation
CREATE TABLE IF NOT EXISTS filtered_scripts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    script_id UUID REFERENCES video_scripts(id) ON DELETE CASCADE,
    relevance_score DECIMAL(3,2), -- ML-based financial relevance
    cluster_id INTEGER, -- Topic cluster from BERTopic
    cluster_theme VARCHAR(255), -- Theme name from clustering
    filter_reason TEXT, -- Reason for inclusion/exclusion
    is_selected BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- BlogPost: Generated blog posts
CREATE TABLE IF NOT EXISTS blog_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filtered_script_id UUID REFERENCES filtered_scripts(id) ON DELETE CASCADE,
    ghost_post_id VARCHAR(50), -- Ghost CMS post ID
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE,
    content_markdown TEXT NOT NULL,
    content_mobiledoc JSONB, -- Ghost's Mobiledoc format
    featured_image_url TEXT,
    tags VARCHAR(255)[], -- Array of tags
    published_at TIMESTAMP WITH TIME ZONE,
    scheduled_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'draft', -- draft, published, scheduled
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- PostMetrics: Performance tracking for published posts
CREATE TABLE IF NOT EXISTS post_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    blog_post_id UUID REFERENCES blog_posts(id) ON DELETE CASCADE,
    views_count INTEGER DEFAULT 0,
    read_time_minutes INTEGER,
    engagement_score DECIMAL(3,2), -- Combined engagement metric
    social_shares JSONB, -- Platform-specific share counts
    seo_keywords_ranking JSONB, -- Keyword rankings
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ProcessingLog: Detailed processing logs for debugging
CREATE TABLE IF NOT EXISTS processing_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phase VARCHAR(50) NOT NULL, -- extraction, indexing, filtering, generation, publishing
    script_id UUID REFERENCES video_scripts(id) ON DELETE CASCADE,
    log_level VARCHAR(10) NOT NULL, -- INFO, WARN, ERROR
    message TEXT NOT NULL,
    context JSONB, -- Additional context data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_video_scripts_publish_date ON video_scripts(publish_date DESC);
CREATE INDEX IF NOT EXISTS idx_video_scripts_processing_status ON video_scripts(processing_status);
CREATE INDEX IF NOT EXISTS idx_video_scripts_channel_handle ON video_scripts(channel_handle);

-- Full-text search indexes
CREATE INDEX IF NOT EXISTS idx_video_scripts_transcript_fts ON video_scripts USING GIN(to_tsvector('chinese_zh', transcript_text));
CREATE INDEX IF NOT EXISTS idx_video_scripts_title_fts ON video_scripts USING GIN(to_tsvector('chinese_zh', title));

-- Trigram indexes for fuzzy matching
CREATE INDEX IF NOT EXISTS idx_script_keywords_keyword_trgm ON script_keywords USING gin(keyword gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_video_scripts_title_trgm ON video_scripts USING gin(title gin_trgm_ops);

-- JSONB indexes for entity queries
CREATE INDEX IF NOT EXISTS idx_video_scripts_entities ON video_scripts USING GIN(entities_json);
CREATE INDEX IF NOT EXISTS idx_post_metrics_social ON post_metrics USING GIN(social_shares);

-- Foreign key performance indexes
CREATE INDEX IF NOT EXISTS idx_script_keywords_script_id ON script_keywords(script_id);
CREATE INDEX IF NOT EXISTS idx_filtered_scripts_script_id ON filtered_scripts(script_id);
CREATE INDEX IF NOT EXISTS idx_blog_posts_filtered_script_id ON blog_posts(filtered_script_id);
CREATE INDEX IF NOT EXISTS idx_post_metrics_blog_post_id ON post_metrics(blog_post_id);
CREATE INDEX IF NOT EXISTS idx_processing_logs_script_id ON processing_logs(script_id);
CREATE INDEX IF NOT EXISTS idx_processing_logs_phase ON processing_logs(phase);

-- Views for common queries
CREATE OR REPLACE VIEW ready_for_generation AS
SELECT 
    fs.id as filtered_script_id,
    vs.video_id,
    vs.title,
    vs.transcript_text,
    fs.cluster_theme,
    fs.relevance_score,
    array_agg(sk.keyword) as keywords
FROM filtered_scripts fs
JOIN video_scripts vs ON fs.script_id = vs.id
LEFT JOIN script_keywords sk ON sk.script_id = vs.id
WHERE fs.is_selected = TRUE 
    AND NOT EXISTS (
        SELECT 1 FROM blog_posts bp 
        WHERE bp.filtered_script_id = fs.id
    )
GROUP BY fs.id, vs.video_id, vs.title, vs.transcript_text, fs.cluster_theme, fs.relevance_score;

-- Trigger for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_video_scripts_updated_at BEFORE UPDATE ON video_scripts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_filtered_scripts_updated_at BEFORE UPDATE ON filtered_scripts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_blog_posts_updated_at BEFORE UPDATE ON blog_posts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data for testing
INSERT INTO video_scripts (video_id, channel_handle, title, description, publish_date, duration_seconds, transcript_text, entities_json, confidence_score, processing_status)
VALUES 
('test_video_001', '@yutinghaofinance', '台積電Q3財報分析', '深入分析台積電2024年第三季財報表現', '2024-10-15 10:00:00+00', 1800, '台積電今天公布第三季財報...', '{"tickers": ["TSM", "2330"], "companies": ["台積電", "台灣積體電路"], "terms": ["財報", "營收", "毛利率"]}', 0.95, 'completed'),
('test_video_002', '@yutinghaofinance', '美聯儲降息影響', '分析美聯儲最新利率決策對市場的影響', '2024-10-16 14:30:00+00', 2400, '美聯儲宣布降息一碼...', '{"tickers": ["SPY", "QQQ"], "companies": ["美聯儲"], "terms": ["降息", "利率", "通膨"]}', 0.92, 'completed');