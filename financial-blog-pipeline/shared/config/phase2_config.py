"""
Phase 2-3 Configuration - Indexing and Filtering Systems
Updated configuration settings for Chinese financial education blog pipeline
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from pathlib import Path
import logging

@dataclass
class DatabaseConfig:
    """Database configuration"""
    url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "postgresql://username:password@localhost:5432/financial_blog"))
    pool_size: int = 20
    max_overflow: int = 30
    pool_pre_ping: bool = True
    pool_recycle: int = 3600
    echo: bool = False

@dataclass
class IndexingConfig:
    """TF-IDF keyword indexing configuration"""
    max_keywords_per_script: int = 25
    min_tfidf_score: float = 0.03
    max_ngram_size: int = 3
    use_jieba_tokenizer: bool = True
    traditional_chinese_normalization: bool = True
    
    # Financial keyword filtering
    financial_keyword_boost: float = 1.8
    financial_keywords_path: str = str(Path(__file__).parent.parent / "phase2_indexing" / "financial_keywords.txt")
    
    # Stop words
    custom_stopwords_path: str = str(Path(__file__).parent.parent / "phase2_indexing" / "stopwords_zh.txt")
    include_default_stopwords: bool = True
    
    # Processing
    min_transcript_length: int = 50
    max_keywords_per_topic: int = 15

@dataclass
class SearchIndexConfig:
    """PostgreSQL search indexes configuration"""
    enable_gin_index: bool = True
    enable_trigram_index: bool = True
    gin_index_name: str = "idx_video_scripts_fulltext"
    trigram_index_name: str = "idx_video_scripts_trigram"
    
    # Search configuration
    search_language: str = "chinese_zh"
    similarity_threshold: float = 0.3
    full_text_config: str = "chinese_zh"
    
    # Performance
    index_concurrently: bool = True
    maintenance_work_mem: str = "512MB"
    
    # Additional indexes
    enable_composite_indexes: bool = True
    enable_partial_indexes: bool = True

@dataclass
class FilteringConfig:
    """ML-based financial relevance classifier configuration"""
    
    # Model configuration
    model_name: str = "bert-base-chinese"
    model_cache_dir: str = str(Path(__file__).parent.parent / "models")
    max_sequence_length: int = 512
    batch_size: int = 8
    device: str = "auto"  # auto, cpu, cuda
    
    # Classification thresholds
    relevance_threshold: float = 0.75
    confidence_threshold: float = 0.8
    
    # Feature weights
    bert_score_weight: float = 0.6
    keyword_weight: float = 0.2
    entity_weight: float = 0.1
    channel_weight: float = 0.1
    
    # Training configuration
    training_data_path: str = str(Path(__file__).parent.parent / "training_data")
    training_split_ratio: float = 0.8
    positive_samples_ratio: float = 0.7
    
    # Cache settings
    enable_model_cache: bool = True
    cache_ttl_hours: int = 24

@dataclass
class ClusteringConfig:
    """BERTopic clustering configuration"""
    
    # Embedding model
    embedding_model: str = "shibing624/text2vec-base-chinese"
    embedding_device: str = "auto"
    embedding_batch_size: int = 32
    
    # UMAP parameters
    umap_n_neighbors: int = 15
    umap_n_components: int = 5
    umap_min_dist: float = 0.1
    umap_metric: str = "cosine"
    umap_random_state: int = 42
    
    # HDBSCAN parameters
    hdbscan_min_cluster_size: int = 5
    hdbscan_min_samples: int = 3
    hdbscan_cluster_selection_epsilon: float = 0.5
    hdbscan_metric: str = "euclidean"
    hdbscan_cluster_selection_method: str = "eom"
    
    # Topic modeling
    ctfidf_reduce_frequent_words: bool = True
    max_topics: int = 50
    min_topic_size: int = 3
    top_n_words: int = 10
    
    # Output settings
    save_model: bool = True
    model_output_path: str = str(Path(__file__).parent.parent / "models" / "bertopic_model")
    save_visualizations: bool = True
    
    # Processing
    max_documents_per_cluster: int = 1000
    enable_outlier_detection: bool = True
    outlier_threshold: float = 0.1

@dataclass
class ProcessingConfig:
    """Processing pipeline configuration"""
    max_concurrent_scripts: int = 5
    retry_failed_scripts: bool = True
    max_retries: int = 3
    retry_delay_seconds: int = 30
    
    # Batch processing
    batch_size: int = 25
    processing_timeout_seconds: int = 1800
    
    # Validation
    min_transcript_length: int = 100
    min_keywords_required: int = 3
    max_processing_time_per_script: int = 300
    
    # Memory management
    max_memory_usage_mb: int = 2048
    enable_garbage_collection: bool = True

@dataclass
class StorageConfig:
    """File storage configuration"""
    base_path: str = str(Path(__file__).parent.parent / "phase2_indexing" / "outputs")
    
    # Output files
    indexing_results_filename: str = "indexing_results.json"
    filtered_scripts_filename: str = "filtered_scripts.json"
    theme_clusters_filename: str = "theme_clusters.json"
    keyword_index_filename: str = "keyword_index.json"
    processing_log_filename: str = "processing_log.json"
    
    # Temporary files
    temp_path: str = "temp"
    max_file_size_mb: int = 100
    
    # Cleanup settings
    retention_days: int = 30
    cleanup_enabled: bool = True
    backup_enabled: bool = True
    max_backups: int = 5

@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: str = str(Path(__file__).parent.parent / "logs" / "phase2_indexing.log")
    max_file_size_mb: int = 10
    backup_count: int = 3
    enable_console: bool = True

@dataclass
class MonitoringConfig:
    """Monitoring and alerting configuration"""
    enable_metrics: bool = True
    metrics_output_path: str = "metrics"
    
    # Health checks
    health_check_interval: int = 300
    max_processing_time: int = 3600
    
    # Performance monitoring
    enable_performance_tracking: bool = True
    slow_query_threshold_ms: int = 1000
    
    # Alerting
    slack_webhook: str = field(default_factory=lambda: os.getenv("SLACK_WEBHOOK_URL", ""))
    email_alerts: bool = False
    alert_email: str = field(default_factory=lambda: os.getenv("ALERT_EMAIL", ""))
    
    # Error handling
    max_errors_before_alert: int = 5
    error_cooldown_minutes: int = 15

@dataclass
class APIConfig:
    """API configuration for external services"""
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    huggingface_token: str = field(default_factory=lambda: os.getenv("HUGGINGFACE_TOKEN", ""))
    
    # Rate limiting
    max_requests_per_minute: int = 60
    request_timeout_seconds: int = 30
    
    # Cache settings
    enable_cache: bool = True
    cache_ttl_seconds: int = 3600

@dataclass
class Phase2Config:
    """Main configuration class for Phase 2-3"""
    
    def __init__(self):
        self.database = DatabaseConfig()
        self.indexing = IndexingConfig()
        self.search = SearchIndexConfig()
        self.filtering = FilteringConfig()
        self.clustering = ClusteringConfig()
        self.processing = ProcessingConfig()
        self.storage = StorageConfig()
        self.logging = LoggingConfig()
        self.monitoring = MonitoringConfig()
        self.api = APIConfig()
        
        # Environment validation
        self._validate_environment()
        self._setup_logging()
    
    def _validate_environment(self):
        """Validate required environment variables"""
        required_vars = [
            "DATABASE_URL",
            "OPENAI_API_KEY"
        ]
        
        missing_vars = [var for var in required_vars if not getattr(self.api, var.lower(), None)]
        if missing_vars:
            logging.warning(f"Missing environment variables: {', '.join(missing_vars)}")
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_dir = Path(self.logging.file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure root logger
        logging.basicConfig(
            level=getattr(logging, self.logging.level.upper()),
            format=self.logging.format,
            handlers=[
                logging.FileHandler(self.logging.file_path),
                logging.StreamHandler() if self.logging.enable_console else logging.NullHandler()
            ]
        )
    
    def get_storage_paths(self) -> Dict[str, str]:
        """Get configured storage paths"""
        base = Path(self.storage.base_path)
        return {
            "indexing_results": str(base / self.storage.indexing_results_filename),
            "filtered_scripts": str(Path(__file__).parent.parent / "phase3_filtering" / "outputs" / self.storage.filtered_scripts_filename),
            "theme_clusters": str(base / self.storage.theme_clusters_filename),
            "keyword_index": str(base / self.storage.keyword_index_filename),
            "processing_log": str(base / self.storage.processing_log_filename),
            "temp": str(base / self.storage.temp_path),
            "models": str(Path(__file__).parent.parent / "models"),
            "logs": str(Path(__file__).parent.parent / "logs"),
            "metrics": str(base / self.storage.metrics_output_path)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "database": self.database.__dict__,
            "indexing": self.indexing.__dict__,
            "search": self.search.__dict__,
            "filtering": self.filtering.__dict__,
            "clustering": self.clustering.__dict__,
            "processing": self.processing.__dict__,
            "storage": self.storage.__dict__,
            "logging": self.logging.__dict__,
            "monitoring": self.monitoring.__dict__,
            "api": self.api.__dict__
        }
    
    def create_directories(self):
        """Create necessary directories"""
        paths = self.get_storage_paths()
        
        for path_name, path_str in paths.items():
            path = Path(path_str)
            if path_name != "processing_log":  # Skip file paths
                path.mkdir(parents=True, exist_ok=True)
        
        # Create additional directories
        Path(self.logging.file_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.clustering.model_output_path).parent.mkdir(parents=True, exist_ok=True)

# Global configuration instance
config = Phase2Config()

# Create directories on import
config.create_directories()