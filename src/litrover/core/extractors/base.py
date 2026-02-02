"""
Base class for LLM extractors
Defines the interface that all LLM providers must implement
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, List
import json
import time


class BaseLLMExtractor(ABC):
    """
    Abstract base class for LLM-powered PDF extraction
    
    All LLM provider implementations must inherit from this class
    and implement the abstract methods.
    """
    
    def __init__(self, api_key: str, model: str, config: Dict[str, Any]):
        """
        Initialize base extractor
        
        Args:
            api_key: API key for the LLM provider
            model: Model identifier
            config: Configuration dictionary
        """
        self.api_key = api_key
        self.model = model
        self.config = config
        self.cache_dir = Path(config.get('extraction', {}).get('cache_dir', 'extracted'))
        self.cache_enabled = config.get('extraction', {}).get('cache_enabled', True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Extraction parameters
        self.temperature = config.get('llm', {}).get('temperature', 0.1)
        self.max_tokens = config.get('llm', {}).get('max_tokens', 4000)
        self.max_retries = config.get('llm', {}).get('max_retries', 3)
        self.retry_delay = config.get('llm', {}).get('retry_delay', 2)
    
    @abstractmethod
    def extract_from_pdf(self, pdf_path: Path, extraction_prompt: str, 
                        request_sources: bool = False) -> Optional[Dict[str, Any]]:
        """
        Extract metadata from a PDF file
        
        Args:
            pdf_path: Path to PDF file
            extraction_prompt: Prompt describing what to extract
            request_sources: If True, request source text and page numbers
            
        Returns:
            Extracted data as dictionary, or None if extraction failed
        """
        pass
    
    def _get_cache_path(self, pdf_path: Path) -> Path:
        """Get cache file path for a PDF"""
        return self.cache_dir / f"{pdf_path.stem}.json"
    
    def _load_from_cache(self, pdf_path: Path) -> Optional[Dict[str, Any]]:
        """
        Load extraction from cache if available
        
        Args:
            pdf_path: PDF file path
            
        Returns:
            Cached data or None
        """
        if not self.cache_enabled:
            return None
        
        cache_path = self._get_cache_path(pdf_path)
        
        if cache_path.exists():
            try:
                with open(cache_path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return None
        
        return None
    
    def _save_to_cache(self, pdf_path: Path, data: Dict[str, Any]):
        """
        Save extraction to cache
        
        Args:
            pdf_path: PDF file path
            data: Extracted data
        """
        if not self.cache_enabled:
            return
        
        cache_path = self._get_cache_path(pdf_path)
        
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _parse_json_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse JSON from LLM response, handling markdown code blocks
        
        Args:
            response_text: Raw response from LLM
            
        Returns:
            Parsed JSON dictionary or None
        """
        response_text = response_text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            # Remove first line (```json or ```)
            lines = lines[1:]
            # Remove last line if it's ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            response_text = "\n".join(lines)
        
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            print(f"Response text: {response_text[:500]}")
            return None
    
    def _retry_with_backoff(self, func, *args, **kwargs):
        """
        Retry a function with exponential backoff
        
        Args:
            func: Function to retry
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If all retries fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    print(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
        
        raise last_exception
    
    def extract_with_cache(self, pdf_path: Path, extraction_prompt: str,
                          request_sources: bool = False) -> Optional[Dict[str, Any]]:
        """
        Extract from PDF with caching support
        
        Args:
            pdf_path: Path to PDF file
            extraction_prompt: Extraction prompt
            request_sources: If True, request source text and page numbers
            
        Returns:
            Extracted data dictionary or None
        """
        # Check cache first
        cached_data = self._load_from_cache(pdf_path)
        if cached_data is not None:
            return cached_data
        
        # Extract from PDF
        data = self.extract_from_pdf(pdf_path, extraction_prompt, request_sources)
        
        # Save to cache if successful
        if data is not None:
            self._save_to_cache(pdf_path, data)
        
        return data
    
    def get_provider_name(self) -> str:
        """Get the name of this LLM provider"""
        return self.__class__.__name__.replace('Extractor', '').lower()
    
    def validate_extraction(self, data: Dict[str, Any], schema: List[Dict[str, Any]]) -> bool:
        """
        Validate extracted data against schema
        
        Args:
            data: Extracted data
            schema: Expected schema
            
        Returns:
            True if valid, False otherwise
        """
        if not data:
            return False
        
        # Check if all required fields are present
        required_fields = [field['field'] for field in schema]
        
        for field in required_fields:
            if field not in data:
                return False
        
        return True
    
    def estimate_confidence(self, data: Dict[str, Any]) -> float:
        """
        Estimate confidence score for extraction
        
        Args:
            data: Extracted data
            
        Returns:
            Confidence score between 0 and 1
        """
        if not data:
            return 0.0
        
        # Count non-null values
        non_null = sum(1 for v in data.values() if v is not None and str(v).strip())
        total = len(data)
        
        return non_null / total if total > 0 else 0.0
