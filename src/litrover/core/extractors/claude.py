"""
Claude-based PDF extraction
Uses Anthropic's Claude API for document understanding
"""

from pathlib import Path
from typing import Dict, Any, Optional
import base64
from anthropic import Anthropic
from .base import BaseLLMExtractor


class ClaudeExtractor(BaseLLMExtractor):
    """
    PDF extraction using Anthropic Claude
    
    Supports Claude Sonnet and Opus models with PDF vision capabilities
    """
    
    def __init__(self, api_key: str, model: str, config: Dict[str, Any]):
        """
        Initialize Claude extractor
        
        Args:
            api_key: Anthropic API key
            model: Model name (e.g., 'claude-sonnet-4-20250514')
            config: Configuration dictionary
        """
        super().__init__(api_key, model, config)
        
        # Initialize Anthropic client
        self.client = Anthropic(api_key=self.api_key)
    
    def extract_from_pdf(self, pdf_path: Path, extraction_prompt: str,
                        request_sources: bool = False) -> Optional[Dict[str, Any]]:
        """
        Extract metadata from PDF using Claude
        
        Args:
            pdf_path: Path to PDF file
            extraction_prompt: Prompt describing what to extract
            request_sources: If True, request source text and page numbers
            
        Returns:
            Extracted data as dictionary, or None if failed
        """
        if request_sources:
            extraction_prompt = self._add_source_request(extraction_prompt)
        if not pdf_path.exists():
            print(f"PDF not found: {pdf_path}")
            return None
        
        try:
            print(f"    Reading {pdf_path.name}...")
            
            # Read PDF as base64
            with open(pdf_path, 'rb') as f:
                pdf_data = base64.standard_b64encode(f.read()).decode('utf-8')
            
            print(f"    Extracting metadata with Claude...")
            
            # Create message with PDF
            response = self._retry_with_backoff(
                self.client.messages.create,
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": "application/pdf",
                                    "data": pdf_data,
                                },
                            },
                            {
                                "type": "text",
                                "text": extraction_prompt,
                            },
                        ],
                    }
                ],
            )
            
            # Parse response
            response_text = response.content[0].text if response.content else ""
            result = self._parse_json_response(response_text)
            
            if result:
                print(f"    ✓ Extraction successful")
                return result
            else:
                print(f"    ✗ Failed to parse extraction")
                # Save raw response for debugging
                debug_file = self.cache_dir / f"{pdf_path.stem}_raw.txt"
                debug_file.write_text(response_text)
                return None
        
        except Exception as e:
            print(f"    ✗ Extraction error: {str(e)[:100]}")
            return None
    
    def batch_extract(self, pdf_paths: list[Path], extraction_prompt: str) -> Dict[str, Dict[str, Any]]:
        """
        Extract from multiple PDFs
        
        Args:
            pdf_paths: List of PDF paths
            extraction_prompt: Extraction prompt
            
        Returns:
            Dictionary mapping PDF path to extracted data
        """
        results = {}
        
        for pdf_path in pdf_paths:
            print(f"\n  Processing: {pdf_path.name}")
            
            # Check cache first
            data = self.extract_with_cache(pdf_path, extraction_prompt)
            
            if data:
                results[str(pdf_path)] = data
            
            # No rate limiting needed for Claude (built into SDK)
        
        return results
    
    @staticmethod
    def get_available_models() -> list[str]:
        """Get list of available Claude models"""
        return [
            "claude-sonnet-4-20250514",
            "claude-opus-4-20250514",
            "claude-3-5-sonnet-20241022",
        ]
    
    @staticmethod
    def estimate_cost(num_pages: int, model: str = "claude-sonnet-4-20250514") -> float:
        """
        Estimate API cost for extraction
        
        Args:
            num_pages: Number of PDF pages
            model: Model name
            
        Returns:
            Estimated cost in USD
        """
        # Claude pricing is based on tokens, not pages
        # Rough estimates: ~1000 tokens per page for PDF
        tokens_per_page = 1000
        
        # Costs per million tokens (as of 2025)
        input_cost_per_mtok = {
            "claude-sonnet-4-20250514": 3.0,
            "claude-opus-4-20250514": 15.0,
            "claude-3-5-sonnet-20241022": 3.0,
        }
        
        output_tokens = 1000  # Typical extraction output
        output_cost_per_mtok = {
            "claude-sonnet-4-20250514": 15.0,
            "claude-opus-4-20250514": 75.0,
            "claude-3-5-sonnet-20241022": 15.0,
        }
        
        input_cost = (num_pages * tokens_per_page / 1_000_000) * input_cost_per_mtok.get(model, 3.0)
        output_cost = (output_tokens / 1_000_000) * output_cost_per_mtok.get(model, 15.0)
        
        return input_cost + output_cost
    
    def _add_source_request(self, prompt: str) -> str:
        """Add source citation request to prompt"""
        source_instruction = """

CRITICAL: For EACH extracted value, also provide:
- "source_text": The EXACT quote (5-30 words) from the paper
- "page": The page number where the quote appears

Format: {"field": {"value": X, "source_text": "...", "page": N}}
If not found: {"field": {"value": null, "source_text": null, "page": null}}
"""
        return prompt + source_instruction
