import logging
import json
import os
from datetime import datetime
from pathlib import Path
import sys

class PipelineLogger:
    def __init__(self, name: str, phase: str = None):
        self.name = name
        self.phase = phase or name
        self.setup_logging()
    
    def setup_logging(self):
        """Configure logging for the pipeline"""
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        
        # Create logs directory
        log_dir = Path(__file__).parent.parent / 'handoffs' / 'error_logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure logger
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(getattr(logging, log_level))
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # File handler for errors
        error_handler = logging.FileHandler(
            log_dir / f"{self.phase}_errors.log"
        )
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        error_handler.setFormatter(error_formatter)
        
        # JSON handler for structured logs
        json_handler = logging.FileHandler(
            log_dir / f"{self.phase}_structured.log"
        )
        json_handler.setLevel(logging.INFO)
        json_handler.setFormatter(JSONFormatter())
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(json_handler)
    
    def info(self, message: str, **kwargs):
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, exception=None, **kwargs):
        if exception:
            kwargs['exception'] = str(exception)
        self.logger.error(message, extra=kwargs)
    
    def critical(self, message: str, exception=None, **kwargs):
        if exception:
            kwargs['exception'] = str(exception)
        self.logger.critical(message, extra=kwargs)
    
    def debug(self, message: str, **kwargs):
        self.logger.debug(message, extra=kwargs)
    
    def log_processing_step(self, step: str, status: str, details: dict = None):
        """Log a processing step with structured data"""
        self.logger.info(
            f"Processing step: {step}",
            extra={
                'phase': self.phase,
                'step': step,
                'status': status,
                'details': details or {}
            }
        )
    
    def log_validation_error(self, field: str, value: any, error: str):
        """Log validation errors"""
        self.logger.warning(
            f"Validation error in {field}: {error}",
            extra={
                'phase': self.phase,
                'field': field,
                'value': str(value),
                'error': error
            }
        )
    
    def log_api_call(self, service: str, endpoint: str, status_code: int, duration: float):
        """Log API calls for performance monitoring"""
        self.logger.info(
            f"API call to {service}: {endpoint}",
            extra={
                'phase': self.phase,
                'service': service,
                'endpoint': endpoint,
                'status_code': status_code,
                'duration_ms': round(duration * 1000, 2)
            }
        )
    
    def log_database_operation(self, operation: str, table: str, rows_affected: int = None):
        """Log database operations"""
        self.logger.info(
            f"Database operation: {operation} on {table}",
            extra={
                'phase': self.phase,
                'operation': operation,
                'table': table,
                'rows_affected': rows_affected
            }
        )

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'phase': getattr(record, 'phase', None),
            'file': record.filename,
            'line': record.lineno
        }
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created', 'msecs',
                          'relativeCreated', 'thread', 'threadName', 'processName',
                          'process', 'getMessage', 'phase']:
                log_entry[key] = value
        
        return json.dumps(log_entry, ensure_ascii=False)

class PhaseLogger:
    """Context manager for phase-specific logging"""
    
    def __init__(self, phase_name: str):
        self.phase_name = phase_name
        self.logger = PipelineLogger(f"pipeline.{phase_name}", phase_name)
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.utcnow()
        self.logger.info(f"Starting phase: {self.phase_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = datetime.utcnow() - self.start_time
        if exc_type:
            self.logger.error(
                f"Phase {self.phase_name} failed",
                exception=exc_val,
                duration_seconds=duration.total_seconds()
            )
        else:
            self.logger.info(
                f"Phase {self.phase_name} completed successfully",
                duration_seconds=duration.total_seconds()
            )

class PerformanceTracker:
    """Track performance metrics across the pipeline"""
    
    def __init__(self):
        self.metrics = {
            'processing_times': {},
            'success_rates': {},
            'error_counts': {}
        }
        self.logger = PipelineLogger('performance_tracker')
    
    def record_processing_time(self, phase: str, duration: float, item_count: int = 1):
        """Record processing time for a phase"""
        if phase not in self.metrics['processing_times']:
            self.metrics['processing_times'][phase] = []
        
        self.metrics['processing_times'][phase].append({
            'duration': duration,
            'item_count': item_count,
            'items_per_second': item_count / duration,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    def record_success(self, phase: str):
        """Record successful completion"""
        if phase not in self.metrics['success_rates']:
            self.metrics['success_rates'][phase] = {'success': 0, 'total': 0}
        
        self.metrics['success_rates'][phase]['success'] += 1
        self.metrics['success_rates'][phase]['total'] += 1
    
    def record_error(self, phase: str, error_type: str):
        """Record an error"""
        if phase not in self.metrics['error_counts']:
            self.metrics['error_counts'][phase] = {}
        
        if error_type not in self.metrics['error_counts'][phase]:
            self.metrics['error_counts'][phase][error_type] = 0
        
        self.metrics['error_counts'][phase][error_type] += 1
        
        if phase in self.metrics['success_rates']:
            self.metrics['success_rates'][phase]['total'] += 1
    
    def get_performance_summary(self):
        """Get summary of all performance metrics"""
        summary = {
            'timestamp': datetime.utcnow().isoformat(),
            'phases': {}
        }
        
        for phase in set(list(self.metrics['processing_times'].keys()) + 
                        list(self.metrics['success_rates'].keys())):
            phase_data = {
                'avg_processing_time': None,
                'success_rate': None,
                'error_breakdown': {}
            }
            
            # Processing time
            if phase in self.metrics['processing_times']:
                times = [t['duration'] for t in self.metrics['processing_times'][phase]]
                phase_data['avg_processing_time'] = sum(times) / len(times)
            
            # Success rate
            if phase in self.metrics['success_rates']:
                data = self.metrics['success_rates'][phase]
                phase_data['success_rate'] = data['success'] / data['total'] if data['total'] > 0 else 0
            
            # Error breakdown
            if phase in self.metrics['error_counts']:
                phase_data['error_breakdown'] = self.metrics['error_counts'][phase]
            
            summary['phases'][phase] = phase_data
        
        return summary
    
    def save_metrics(self, filepath: str):
        """Save metrics to file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.get_performance_summary(), f, ensure_ascii=False, indent=2)

# Global performance tracker
performance_tracker = PerformanceTracker()

# Convenience functions
def get_logger(name: str, phase: str = None) -> PipelineLogger:
    """Get a configured logger instance"""
    return PipelineLogger(name, phase)

def log_phase_start(phase_name: str):
    """Log phase start with context manager"""
    return PhaseLogger(phase_name)

def setup_global_logging():
    """Setup global logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )