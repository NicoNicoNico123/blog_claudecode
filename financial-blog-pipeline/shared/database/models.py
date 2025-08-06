from sqlalchemy import create_engine, Column, String, Text, Integer, DateTime, Boolean, DECIMAL, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class VideoScript(Base):
    __tablename__ = 'video_scripts'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(String(50), unique=True, nullable=False)
    channel_handle = Column(String(100), nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text)
    publish_date = Column(DateTime(timezone=True), nullable=False)
    duration_seconds = Column(Integer)
    transcript_text = Column(Text, nullable=False)
    transcript_language = Column(String(10), default='zh-TW')
    entities_json = Column(JSON)
    confidence_score = Column(DECIMAL(3,2))
    processing_status = Column(String(20), default='pending')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    keywords = relationship("ScriptKeyword", back_populates="script", cascade="all, delete-orphan")
    filtered_script = relationship("FilteredScript", back_populates="script", uselist=False)
    processing_logs = relationship("ProcessingLog", back_populates="script", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_video_scripts_publish_date', 'publish_date'),
        Index('idx_video_scripts_processing_status', 'processing_status'),
        Index('idx_video_scripts_channel_handle', 'channel_handle'),
    )

class ScriptKeyword(Base):
    __tablename__ = 'script_keywords'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    script_id = Column(UUID(as_uuid=True), ForeignKey('video_scripts.id', ondelete='CASCADE'), nullable=False)
    keyword = Column(String(255), nullable=False)
    tfidf_score = Column(DECIMAL(5,4), nullable=False)
    frequency = Column(Integer, nullable=False)
    is_financial = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    script = relationship("VideoScript", back_populates="keywords")
    
    __table_args__ = (
        Index('idx_script_keywords_script_id', 'script_id'),
    )

class FilteredScript(Base):
    __tablename__ = 'filtered_scripts'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    script_id = Column(UUID(as_uuid=True), ForeignKey('video_scripts.id', ondelete='CASCADE'), nullable=False)
    relevance_score = Column(DECIMAL(3,2))
    cluster_id = Column(Integer)
    cluster_theme = Column(String(255))
    filter_reason = Column(Text)
    is_selected = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    script = relationship("VideoScript", back_populates="filtered_script")
    blog_post = relationship("BlogPost", back_populates="filtered_script", uselist=False)
    
    __table_args__ = (
        Index('idx_filtered_scripts_script_id', 'script_id'),
    )

class BlogPost(Base):
    __tablename__ = 'blog_posts'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filtered_script_id = Column(UUID(as_uuid=True), ForeignKey('filtered_scripts.id', ondelete='CASCADE'), nullable=False)
    ghost_post_id = Column(String(50))
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True)
    content_markdown = Column(Text, nullable=False)
    content_mobiledoc = Column(JSON)
    featured_image_url = Column(Text)
    tags = Column(ARRAY(String(255)))
    published_at = Column(DateTime(timezone=True))
    scheduled_at = Column(DateTime(timezone=True))
    status = Column(String(20), default='draft')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    filtered_script = relationship("FilteredScript", back_populates="blog_post")
    metrics = relationship("PostMetrics", back_populates="blog_post", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_blog_posts_filtered_script_id', 'filtered_script_id'),
    )

class PostMetrics(Base):
    __tablename__ = 'post_metrics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    blog_post_id = Column(UUID(as_uuid=True), ForeignKey('blog_posts.id', ondelete='CASCADE'), nullable=False)
    views_count = Column(Integer, default=0)
    read_time_minutes = Column(Integer)
    engagement_score = Column(DECIMAL(3,2))
    social_shares = Column(JSON)
    seo_keywords_ranking = Column(JSON)
    collected_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    blog_post = relationship("BlogPost", back_populates="metrics")
    
    __table_args__ = (
        Index('idx_post_metrics_blog_post_id', 'blog_post_id'),
    )

class ProcessingLog(Base):
    __tablename__ = 'processing_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phase = Column(String(50), nullable=False)
    script_id = Column(UUID(as_uuid=True), ForeignKey('video_scripts.id', ondelete='CASCADE'), nullable=False)
    log_level = Column(String(10), nullable=False)
    message = Column(Text, nullable=False)
    context = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    script = relationship("VideoScript", back_populates="processing_logs")
    
    __table_args__ = (
        Index('idx_processing_logs_script_id', 'script_id'),
        Index('idx_processing_logs_phase', 'phase'),
    )

# Database connection utilities
class DatabaseManager:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self):
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        return self.SessionLocal()
    
    def close(self):
        self.engine.dispose()

# Configuration class for database settings
class DatabaseConfig:
    def __init__(self):
        self.database_url = "postgresql://username:password@localhost:5432/financial_blog"
        self.pool_size = 20
        self.max_overflow = 30
        self.pool_pre_ping = True
        self.pool_recycle = 3600