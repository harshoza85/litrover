"""LLM extractors for PDF metadata extraction"""

from .base import BaseLLMExtractor
from .gemini import GeminiExtractor
from .claude import ClaudeExtractor
from .openai import OpenAIExtractor

__all__ = [
    "BaseLLMExtractor",
    "GeminiExtractor",
    "ClaudeExtractor",
    "OpenAIExtractor",
]


def get_extractor(provider: str, api_key: str, model: str, config: dict) -> BaseLLMExtractor:
    """
    Factory function to get the appropriate extractor
    
    Args:
        provider: Provider name ('gemini', 'claude', 'openai')
        api_key: API key for the provider
        model: Model identifier
        config: Configuration dictionary
        
    Returns:
        Appropriate extractor instance
        
    Raises:
        ValueError: If provider is not supported
    """
    providers = {
        'gemini': GeminiExtractor,
        'claude': ClaudeExtractor,
        'openai': OpenAIExtractor,
    }
    
    provider_lower = provider.lower()
    
    if provider_lower not in providers:
        raise ValueError(
            f"Unsupported provider: {provider}. "
            f"Supported providers: {list(providers.keys())}"
        )
    
    return providers[provider_lower](api_key, model, config)
