"""
LitRover: Agentic AI System for Automated Literature Survey

An intelligent orchestration system for processing research papers:
- Citation resolution
- PDF download
- AI-powered metadata extraction
- Multi-orchestrator support
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__license__ = "MIT"

from .core.extractors.base import BaseLLMExtractor
from .core.extractors.gemini import GeminiExtractor
from .core.extractors.claude import ClaudeExtractor
from .core.extractors.openai import OpenAIExtractor

__all__ = [
    "BaseLLMExtractor",
    "GeminiExtractor",
    "ClaudeExtractor",
    "OpenAIExtractor",
]
