"""Core modules for LitRover"""

from .extractors import BaseLLMExtractor, GeminiExtractor, ClaudeExtractor, OpenAIExtractor, get_extractor
from .resolvers import SemanticScholarResolver
from .downloaders import PDFDownloader
from .annotators import PDFAnnotator

__all__ = [
    "BaseLLMExtractor",
    "GeminiExtractor",
    "ClaudeExtractor",
    "OpenAIExtractor",
    "get_extractor",
    "SemanticScholarResolver",
    "PDFDownloader",
    "PDFAnnotator",
]
