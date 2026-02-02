"""
Gemini-based PDF extraction
Uses Google's Gemini API for document understanding
"""

from pathlib import Path
from typing import Dict, Any, Optional
import time
import google.generativeai as genai
from .base import BaseLLMExtractor


class GeminiExtractor(BaseLLMExtractor):
    """
    PDF extraction using Google Gemini
    
    Supports Gemini 2.0 Flash and Gemini 1.5 Pro models
    """
    
    def __init__(self, api_key: str, model: str, config: Dict[str, Any]):
        """
        Initialize Gemini extractor
        
        Args:
            api_key: Google API key
            model: Model name (e.g., 'gemini-2.0-flash-exp')
            config: Configuration dictionary
        """
        super().__init__(api_key, model, config)
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Initialize model
        self.client = genai.GenerativeModel(self.model)
    
    def extract_from_pdf(self, pdf_path: Path, extraction_prompt: str, 
                        request_sources: bool = False) -> Optional[Dict[str, Any]]:
        """
        Extract metadata from PDF using Gemini
        
        Args:
            pdf_path: Path to PDF file
            extraction_prompt: Prompt describing what to extract
            request_sources: If True, request source text and page numbers for verification
            
        Returns:
            Extracted data as dictionary, or None if failed
        """
        # Enhance prompt if source citations requested
        if request_sources:
            extraction_prompt = self._add_source_request(extraction_prompt)
        if not pdf_path.exists():
            print(f"PDF not found: {pdf_path}")
            return None
        
        try:
            # Upload PDF to Gemini
            print(f"    Uploading {pdf_path.name} to Gemini...")
            uploaded_file = genai.upload_file(str(pdf_path))
            
            # Wait for file processing
            while uploaded_file.state.name == "PROCESSING":
                time.sleep(2)
                uploaded_file = genai.get_file(uploaded_file.name)
            
            if uploaded_file.state.name == "FAILED":
                print(f"    ✗ File upload failed for {pdf_path.name}")
                return None
            
            print(f"    Extracting metadata...")
            
            # Generate extraction with retry
            response = self._retry_with_backoff(
                self.client.generate_content,
                [uploaded_file, extraction_prompt],
                generation_config=genai.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                    response_mime_type="application/json",
                ),
            )
            
            # Parse response
            response_text = response.text.strip()
            result = self._parse_json_response(response_text)
            
            # Clean up uploaded file
            try:
                genai.delete_file(uploaded_file.name)
            except:
                pass
            
            if result:
                print(f"    ✓ Extraction successful")
                return result
            else:
                print(f"    ✗ Failed to parse extraction")
                return None
        
        except Exception as e:
            print(f"    ✗ Extraction error: {str(e)[:100]}")
            return None
    
    def batch_extract(self, pdf_paths: list[Path], extraction_prompt: str) -> Dict[str, Dict[str, Any]]:
        """
        Extract from multiple PDFs with rate limiting
        
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
            
            # Rate limiting - be nice to API
            time.sleep(1)
        
        return results
    
    @staticmethod
    def get_available_models() -> list[str]:
        """Get list of available Gemini models"""
        return [
            "gemini-2.0-flash-exp",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
        ]
    
    def _add_source_request(self, prompt: str) -> str:
        """
        Enhance prompt to request source citations
        
        Args:
            prompt: Original extraction prompt
            
        Returns:
            Enhanced prompt requesting source text and page numbers
        """
        source_instruction = """

CRITICAL: For EACH extracted value, also provide:
- "source_text": The EXACT quote (5-30 words) from the paper where you found this information
- "page": The page number (1-indexed) where the quote appears

Format each field as:
{
  "field_name": {
    "value": <extracted_value>,
    "source_text": "<exact quote from paper>",
    "page": <page_number>
  }
}

If a value is not found, use:
{
  "field_name": {
    "value": null,
    "source_text": null,
    "page": null
  }
}

Example:
{
  "latitude": {
    "value": 39.49,
    "source_text": "Site U1425 (39.49°N, 134.44°E)",
    "page": 3
  },
  "sample_size": {
    "value": 150,
    "source_text": "recruited 150 participants",
    "page": 5
  }
}
"""
        return prompt + source_instruction
    
    @staticmethod
    def estimate_cost(num_pages: int, model: str = "gemini-2.0-flash-exp") -> float:
        """
        Estimate API cost for extraction
        
        Args:
            num_pages: Number of PDF pages
            model: Model name
            
        Returns:
            Estimated cost in USD
        """
        # Rough estimates (as of 2025)
        cost_per_page = {
            "gemini-2.0-flash-exp": 0.005,  # ~0.5 cents per page
            "gemini-1.5-pro": 0.02,          # ~2 cents per page
            "gemini-1.5-flash": 0.005,
        }
        
        return num_pages * cost_per_page.get(model, 0.01)
