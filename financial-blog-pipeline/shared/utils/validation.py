import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import os

class ValidationError(Exception):
    """Custom validation exception"""
    pass

class DataValidator:
    """Comprehensive data validation for pipeline stages"""
    
    def __init__(self, phase_name: str):
        self.phase_name = phase_name
        self.errors = []
        self.warnings = []
    
    def validate_video_script(self, data: Dict[str, Any]) -> bool:
        """Validate Phase 1 extraction data"""
        required_fields = ['video_id', 'title', 'transcript_text', 'publish_date']
        
        # Check required fields
        for field in required_fields:
            if field not in data or not data[field]:
                self.errors.append(f"Missing required field: {field}")
                return False
        
        # Validate video_id format
        if not re.match(r'^[a-zA-Z0-9_-]+$', data.get('video_id', '')):
            self.errors.append("Invalid video_id format")
        
        # Validate transcript length
        transcript = data.get('transcript_text', '')
        if len(transcript) < 100:
            self.warnings.append("Transcript too short (< 100 chars)")
        
        # Validate confidence score
        confidence = data.get('confidence_score', 0)
        if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
            self.errors.append("Invalid confidence_score (must be 0-1)")
        elif confidence < 0.8:
            self.warnings.append("Low confidence score (< 0.8)")
        
        # Validate publish date
        try:
            publish_date = datetime.fromisoformat(data['publish_date'].replace('Z', '+00:00'))
            if publish_date > datetime.now():
                self.errors.append("Publish date in the future")
            if publish_date < datetime.now() - timedelta(days=7):
                self.warnings.append("Publish date older than 7 days")
        except (ValueError, TypeError):
            self.errors.append("Invalid publish_date format")
        
        # Validate entities JSON
        entities = data.get('entities_json', {})
        if entities and not isinstance(entities, dict):
            self.errors.append("entities_json must be a dict")
        
        return len(self.errors) == 0
    
    def validate_indexing_results(self, data: Dict[str, Any]) -> bool:
        """Validate Phase 2 indexing results"""
        if not isinstance(data, dict):
            self.errors.append("Indexing results must be a dict")
            return False
        
        # Check for required structure
        if 'script_id' not in data:
            self.errors.append("Missing script_id")
        
        keywords = data.get('keywords', [])
        if not isinstance(keywords, list):
            self.errors.append("Keywords must be a list")
        elif len(keywords) > 50:
            self.warnings.append("Too many keywords (> 50)")
        
        # Validate keyword data
        for keyword_data in keywords:
            if not isinstance(keyword_data, dict):
                self.errors.append("Keyword data must be dict")
                continue
            
            if 'keyword' not in keyword_data or 'tfidf_score' not in keyword_data:
                self.errors.append("Keyword missing required fields")
                continue
            
            if not isinstance(keyword_data['tfidf_score'], (int, float)):
                self.errors.append("Invalid tfidf_score type")
            elif keyword_data['tfidf_score'] < 0.05:
                self.warnings.append(f"Low tfidf_score for {keyword_data.get('keyword')}")
        
        return len(self.errors) == 0
    
    def validate_filtering_results(self, data: Dict[str, Any]) -> bool:
        """Validate Phase 3 filtering results"""
        required_fields = ['relevance_score', 'cluster_id', 'is_selected']
        
        for field in required_fields:
            if field not in data:
                self.errors.append(f"Missing required field: {field}")
        
        # Validate relevance score
        relevance = data.get('relevance_score')
        if isinstance(relevance, (int, float)):
            if relevance < 0 or relevance > 1:
                self.errors.append("Relevance score must be 0-1")
            elif relevance < 0.7:
                self.warnings.append("Low relevance score (< 0.7)")
        
        # Validate cluster data
        cluster_id = data.get('cluster_id')
        if cluster_id is not None and (not isinstance(cluster_id, int) or cluster_id < 0):
            self.errors.append("Invalid cluster_id")
        
        return len(self.errors) == 0
    
    def validate_blog_draft(self, content: str, metadata: Dict[str, Any]) -> bool:
        """Validate Phase 4 blog draft"""
        # Check content length
        if len(content) < 1000:
            self.errors.append("Content too short (< 1000 chars)")
        elif len(content) > 3000:
            self.warnings.append("Content too long (> 3000 chars)")
        
        # Check required sections
        required_sections = ['hook', 'market_impact', 'explanation', 'takeaways']
        for section in required_sections:
            if section not in content.lower():
                self.warnings.append(f"Missing section: {section}")
        
        # Validate metadata
        if 'title' not in metadata or not metadata['title']:
            self.errors.append("Missing title")
        
        if 'tags' in metadata:
            tags = metadata['tags']
            if not isinstance(tags, list):
                self.errors.append("Tags must be a list")
            elif len(tags) > 10:
                self.warnings.append("Too many tags (> 10)")
        
        # Check for Traditional Chinese
        traditional_chinese_pattern = re.compile(r'[\u4e00-\u9fff]+')
        if not traditional_chinese_pattern.search(content):
            self.warnings.append("Content may not contain Traditional Chinese")
        
        return len(self.errors) == 0
    
    def validate_publishing_data(self, data: Dict[str, Any]) -> bool:
        """Validate Phase 5 publishing data"""
        required_fields = ['ghost_post_id', 'title', 'status']
        
        for field in required_fields:
            if field not in data or not data[field]:
                self.errors.append(f"Missing required field: {field}")
        
        # Validate Ghost post ID
        ghost_id = data.get('ghost_post_id')
        if ghost_id and not re.match(r'^[a-f0-9]+$', str(ghost_id)):
            self.errors.append("Invalid Ghost post ID format")
        
        # Validate status
        valid_statuses = ['draft', 'published', 'scheduled']
        status = data.get('status', '').lower()
        if status not in valid_statuses:
            self.errors.append(f"Invalid status: {status}")
        
        # Validate scheduled date if provided
        scheduled_at = data.get('scheduled_at')
        if scheduled_at:
            try:
                scheduled_date = datetime.fromisoformat(scheduled_at.replace('Z', '+00:00'))
                if scheduled_date < datetime.now():
                    self.errors.append("Scheduled date in the past")
            except (ValueError, TypeError):
                self.errors.append("Invalid scheduled date format")
        
        return len(self.errors) == 0
    
    def validate_file_structure(self, filepath: str, expected_type: str) -> bool:
        """Validate file structure and permissions"""
        path = Path(filepath)
        
        # Check if file exists
        if not path.exists():
            self.errors.append(f"File does not exist: {filepath}")
            return False
        
        # Check if it's a file
        if not path.is_file():
            self.errors.append(f"Path is not a file: {filepath}")
            return False
        
        # Check file size
        file_size = path.stat().st_size
        if file_size == 0:
            self.errors.append(f"File is empty: {filepath}")
        elif file_size > 10 * 1024 * 1024:  # 10MB limit
            self.warnings.append(f"File very large: {file_size} bytes")
        
        # Check file extension
        if expected_type == 'json' and path.suffix != '.json':
            self.errors.append(f"Expected JSON file: {filepath}")
        
        return len(self.errors) == 0
    
    def validate_json_structure(self, filepath: str, schema: Dict[str, Any]) -> bool:
        """Validate JSON structure against schema"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return self._validate_schema(data, schema)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON: {e}")
            return False
    
    def _validate_schema(self, data: Any, schema: Dict[str, Any]) -> bool:
        """Recursively validate data against schema"""
        if schema.get('type') == 'object':
            if not isinstance(data, dict):
                self.errors.append("Expected object")
                return False
            
            for key, sub_schema in schema.get('properties', {}).items():
                if key in data:
                    self._validate_schema(data[key], sub_schema)
                elif key in schema.get('required', []):
                    self.errors.append(f"Missing required property: {key}")
        
        elif schema.get('type') == 'array':
            if not isinstance(data, list):
                self.errors.append("Expected array")
                return False
            
            item_schema = schema.get('items', {})
            for item in data:
                self._validate_schema(item, item_schema)
        
        elif schema.get('type') == 'string':
            if not isinstance(data, str):
                self.errors.append("Expected string")
        
        elif schema.get('type') == 'number':
            if not isinstance(data, (int, float)):
                self.errors.append("Expected number")
        
        return len(self.errors) == 0
    
    def get_validation_summary(self) -> Dict[str, List[str]]:
        """Get validation summary"""
        return {
            'errors': self.errors,
            'warnings': self.warnings,
            'phase': self.phase_name,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def save_validation_report(self, filepath: str):
        """Save validation report to file"""
        summary = self.get_validation_summary()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
    
    def is_valid(self) -> bool:
        """Check if data is valid (no errors)"""
        return len(self.errors) == 0
    
    def has_warnings(self) -> bool:
        """Check if there are any warnings"""
        return len(self.warnings) > 0

class ConfigValidator:
    """Validate configuration and environment"""
    
    @staticmethod
    def validate_environment_variables() -> List[str]:
        """Validate required environment variables"""
        required_env_vars = [
            'DATABASE_URL',
            'OPENAI_API_KEY',
            'GHOST_ADMIN_API_KEY',
            'GHOST_URL',
            'UNSPLASH_ACCESS_KEY',
            'PEXELS_API_KEY'
        ]
        
        missing_vars = []
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        return missing_vars
    
    @staticmethod
    def validate_directory_structure(base_path: str) -> List[str]:
        """Validate required directory structure"""
        required_dirs = [
            'shared/database',
            'shared/config',
            'shared/utils',
            'shared/handoffs',
            'phase1_extraction/outputs',
            'phase2_indexing/outputs',
            'phase3_filtering/outputs',
            'phase4_generation/outputs/blog_drafts',
            'phase4_generation/outputs/generated_images',
            'phase5_publishing/outputs'
        ]
        
        missing_dirs = []
        for dir_path in required_dirs:
            full_path = os.path.join(base_path, dir_path)
            if not os.path.exists(full_path):
                missing_dirs.append(dir_path)
        
        return missing_dirs
    
    @staticmethod
    def validate_api_connectivity() -> Dict[str, bool]:
        """Validate API connectivity (basic checks)"""
        import requests
        
        api_endpoints = {
            'openai': 'https://api.openai.com/v1/models',
            'unsplash': 'https://api.unsplash.com/photos',
            'pexels': 'https://api.pexels.com/v1/search'
        }
        
        results = {}
        for service, endpoint in api_endpoints.items():
            try:
                # Basic connectivity check
                response = requests.head(endpoint, timeout=5)
                results[service] = response.status_code < 500
            except Exception:
                results[service] = False
        
        return results