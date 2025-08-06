import json
import os
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
import tempfile

class FileManager:
    """Centralized file management for the pipeline"""
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or os.getcwd())
        self.ensure_directory_structure()
    
    def ensure_directory_structure(self):
        """Ensure all required directories exist"""
        directories = [
            'shared/handoffs',
            'shared/handoffs/agent_outputs',
            'shared/handoffs/error_logs',
            'shared/handoffs/backups',
            'phase1_extraction/outputs',
            'phase2_indexing/outputs',
            'phase3_filtering/outputs',
            'phase4_generation/outputs/blog_drafts',
            'phase4_generation/outputs/generated_images',
            'phase5_publishing/outputs',
            'tests/fixtures',
            'tests/results'
        ]
        
        for directory in directories:
            dir_path = self.base_path / directory
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def save_json(self, data: Any, filepath: str, backup: bool = True) -> bool:
        """Save data as JSON with optional backup"""
        try:
            full_path = self.base_path / filepath
            
            # Create backup if file exists and backup is requested
            if backup and full_path.exists():
                self.create_backup(str(full_path))
            
            # Ensure directory exists
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save new file
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving JSON to {filepath}: {e}")
            return False
    
    def load_json(self, filepath: str, default: Any = None) -> Any:
        """Load JSON data from file"""
        try:
            full_path = self.base_path / filepath
            if not full_path.exists():
                return default
            
            with open(full_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading JSON from {filepath}: {e}")
            return default
    
    def create_backup(self, filepath: str, max_backups: int = 5) -> str:
        """Create a timestamped backup of a file"""
        try:
            source_path = Path(filepath)
            if not source_path.exists():
                return None
            
            # Create backup directory
            backup_dir = self.base_path / 'shared' / 'handoffs' / 'backups'
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{source_path.stem}_{timestamp}{source_path.suffix}"
            backup_path = backup_dir / backup_filename
            
            # Copy file
            shutil.copy2(source_path, backup_path)
            
            # Cleanup old backups
            self.cleanup_old_backups(str(backup_dir), max_backups)
            
            return str(backup_path)
        except Exception as e:
            print(f"Error creating backup for {filepath}: {e}")
            return None
    
    def cleanup_old_backups(self, backup_dir: str, max_backups: int):
        """Remove old backup files"""
        try:
            backup_path = Path(backup_dir)
            backups = sorted(backup_path.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Remove oldest backups
            for backup in backups[max_backups:]:
                backup.unlink()
        except Exception as e:
            print(f"Error cleaning up backups: {e}")
    
    def get_file_hash(self, filepath: str) -> str:
        """Get MD5 hash of file contents"""
        try:
            full_path = self.base_path / filepath
            if not full_path.exists():
                return ""
            
            with open(full_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""
    
    def list_phase_outputs(self, phase: str) -> List[Dict[str, Any]]:
        """List all output files for a phase"""
        phase_dirs = {
            'phase1': 'phase1_extraction/outputs',
            'phase2': 'phase2_indexing/outputs',
            'phase3': 'phase3_filtering/outputs',
            'phase4': 'phase4_generation/outputs',
            'phase5': 'phase5_publishing/outputs'
        }
        
        phase_dir = phase_dirs.get(phase.lower())
        if not phase_dir:
            return []
        
        outputs = []
        try:
            dir_path = self.base_path / phase_dir
            if dir_path.exists():
                for file_path in dir_path.rglob("*"):
                    if file_path.is_file():
                        stat = file_path.stat()
                        outputs.append({
                            'filename': file_path.name,
                            'path': str(file_path.relative_to(self.base_path)),
                            'size': stat.st_size,
                            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            'hash': self.get_file_hash(str(file_path.relative_to(self.base_path)))
                        })
        except Exception as e:
            print(f"Error listing phase outputs: {e}")
        
        return outputs
    
    def copy_between_phases(self, source_phase: str, target_phase: str, filename: str) -> bool:
        """Copy file between phases"""
        try:
            source_path = self.get_phase_path(source_phase, filename)
            target_path = self.get_phase_path(target_phase, filename)
            
            if not source_path.exists():
                return False
            
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target_path)
            return True
        except Exception as e:
            print(f"Error copying file between phases: {e}")
            return False
    
    def get_phase_path(self, phase: str, filename: str = None) -> Path:
        """Get path for a specific phase"""
        phase_dirs = {
            'phase1': 'phase1_extraction/outputs',
            'phase2': 'phase2_indexing/outputs',
            'phase3': 'phase3_filtering/outputs',
            'phase4': 'phase4_generation/outputs',
            'phase5': 'phase5_publishing/outputs'
        }
        
        phase_dir = phase_dirs.get(phase.lower())
        if not phase_dir:
            return self.base_path
        
        path = self.base_path / phase_dir
        if filename:
            path = path / filename
        
        return path
    
    def create_temp_file(self, suffix: str = '.tmp') -> str:
        """Create temporary file"""
        temp_dir = self.base_path / 'temp'
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        with tempfile.NamedTemporaryFile(
            dir=str(temp_dir),
            suffix=suffix,
            delete=False
        ) as tmp:
            return tmp.name
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            temp_dir = self.base_path / 'temp'
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
                temp_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Error cleaning temp files: {e}")
    
    def atomic_write(self, data: Any, filepath: str) -> bool:
        """Write file atomically using temporary file"""
        temp_path = None
        try:
            # Create temporary file
            temp_path = self.create_temp_file(Path(filepath).suffix)
            
            # Write to temp file
            with open(temp_path, 'w', encoding='utf-8') as f:
                if isinstance(data, str):
                    f.write(data)
                else:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Atomic move
            target_path = self.base_path / filepath
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(temp_path, target_path)
            
            return True
        except Exception as e:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
            print(f"Error in atomic write: {e}")
            return False
    
    def get_handoff_status(self) -> Dict[str, Any]:
        """Get current handoff status"""
        status_file = self.base_path / 'shared' / 'handoffs' / 'phase_status.json'
        
        if status_file.exists():
            return self.load_json(str(status_file.relative_to(self.base_path)), {})
        
        return {
            'phase1_extraction': {'status': 'pending', 'last_run': None, 'output_files': []},
            'phase2_indexing': {'status': 'pending', 'last_run': None, 'output_files': []},
            'phase3_filtering': {'status': 'pending', 'last_run': None, 'output_files': []},
            'phase4_generation': {'status': 'pending', 'last_run': None, 'output_files': []},
            'phase5_publishing': {'status': 'pending', 'last_run': None, 'output_files': []},
            'pipeline_status': 'not_started'
        }
    
    def update_handoff_status(self, phase: str, status: str, output_files: List[str] = None):
        """Update handoff status for a phase"""
        status_data = self.get_handoff_status()
        
        status_data[phase] = {
            'status': status,
            'last_run': datetime.now().isoformat(),
            'output_files': output_files or []
        }
        
        # Update overall pipeline status
        all_phases = ['phase1_extraction', 'phase2_indexing', 'phase3_filtering', 
                     'phase4_generation', 'phase5_publishing']
        
        if all(status_data[p]['status'] == 'completed' for p in all_phases):
            status_data['pipeline_status'] = 'completed'
        elif any(status_data[p]['status'] == 'failed' for p in all_phases):
            status_data['pipeline_status'] = 'failed'
        elif any(status_data[p]['status'] == 'in_progress' for p in all_phases):
            status_data['pipeline_status'] = 'in_progress'
        else:
            status_data['pipeline_status'] = 'partial'
        
        self.save_json(
            status_data,
            'shared/handoffs/phase_status.json',
            backup=False
        )
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """Get summary of all processing"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_files': 0,
            'phase_summaries': {}
        }
        
        for phase in ['phase1', 'phase2', 'phase3', 'phase4', 'phase5']:
            phase_files = self.list_phase_outputs(phase)
            summary['phase_summaries'][phase] = {
                'files': len(phase_files),
                'total_size': sum(f['size'] for f in phase_files),
                'latest_file': max(phase_files, key=lambda x: x['modified']) if phase_files else None
            }
            summary['total_files'] += len(phase_files)
        
        return summary
    
    def cleanup_old_files(self, days: int = 7):
        """Clean up files older than specified days"""
        cutoff_date = datetime.now().timestamp() - (days * 24 * 3600)
        
        try:
            for phase in ['phase1', 'phase2', 'phase3', 'phase4', 'phase5']:
                phase_files = self.list_phase_outputs(phase)
                for file_info in phase_files:
                    file_path = self.base_path / file_info['path']
                    if file_path.stat().st_mtime < cutoff_date:
                        file_path.unlink()
        except Exception as e:
            print(f"Error cleaning up old files: {e}")

# Global file manager instance
file_manager = FileManager()