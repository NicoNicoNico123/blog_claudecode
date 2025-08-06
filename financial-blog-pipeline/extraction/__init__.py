"""
Phase 1: Script Extraction System
Chinese Financial Education Blog Pipeline

This module provides video processing capabilities for Chinese financial education content,
including MCP subscription, audio transcription, and named entity recognition.
"""

__version__ = "1.0.0"
__author__ = "Financial Blog Pipeline Team"

from .config import Phase1Config, config
from .mcp_subscriber import MCPSubscriber, MockMCPSubscriber
from .script_extractor import ScriptExtractor, AudioProcessor, NERTagger

__all__ = [
    "Phase1Config",
    "config", 
    "MCPSubscriber",
    "MockMCPSubscriber",
    "ScriptExtractor",
    "AudioProcessor",
    "NERTagger"
]