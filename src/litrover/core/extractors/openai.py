"""
OpenAI-based PDF extraction
Uses OpenAI's GPT-4 with vision for document understanding
"""

from pathlib import Path
from typing import Dict, Any, Optional
import base64
from openai import OpenAI
from .base import BaseLLMExtractor


class OpenAIExtractor(BaseLLMExtractor):
    """
    PDF extraction using OpenAI GPT-4
    
    Supports GPT-4o and GPT-4 Turbo with vision capabilities
    """
    
    def __init__(self, api_key: str, model: str, config: Dict[str, Any]):
        """
        Initialize OpenAI extractor
        
        Args:
            api_key: OpenAI API key
            model: Model name (e.g., 'gpt-4o')
            config: Configuration dictionary
        """
        super().__init__(api_key, model, config)
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key)
    
    def _pdf_to_images(self, pdf_path: Path) -> list[str]:
        """
        Convert PDF pages to base64 images
        
        Note: OpenAI doesn't support direct PDF input, so we convert to images
        
        Args:
            pdf_path: Path to PDF
            
        Returns:
            List of base64-encoded images
        """
        try:
            from pdf2image import convert_from_path
            from io import BytesIO
            from PIL import Image
            
            # Convert PDF to images (limit to first 20 pages for cost)
            images = convert_from_path(str(pdf_path), dpi=150, last_page=20)
            
            base64_images = []
            for img in images:
                # Convert to base64
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                base64_images.append(img_str)
            
            return base64_images
        
        except ImportError:
            print("    ✗ pdf2image not installed. Install with: pip install pdf2image")
            print("    ✗ Also requires poppler: brew install poppler (Mac) or apt-get install poppler-utils (Linux)")
            return []
        except Exception as e:
            print(f"    ✗ PDF conversion error: {e}")
            return []
    
    def extract_from_pdf(self, pdf_path: Path, extraction_prompt: str,
                        request_sources: bool = False) -> Optional[Dict[str, Any]]:
        """
        Extract metadata from PDF using OpenAI
        
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
            print(f"    Converting {pdf_path.name} to images...")
            
            # Convert PDF to images
            images = self._pdf_to_images(pdf_path)
            
            if not images:
                return None
            
            print(f"    Extracting metadata from {len(images)} page(s)...")
            
            # Build message with images
            content = [
                {
                    "type": "text",
                    "text": extraction_prompt,
                }
            ]
            
            # Add images (limit to prevent token overflow)
            for img_b64 in images[:10]:  # Max 10 pages
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{img_b64}",
                        "detail": "high",
                    },
                })
            
            # Call OpenAI API
            response = self._retry_with_backoff(
                self.client.chat.completions.create,
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": content,
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"},
            )
            
            # Parse response
            response_text = response.choices[0].message.content
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
        
        return results
    
    @staticmethod
    def get_available_models() -> list[str]:
        """Get list of available OpenAI models"""
        return [
            "gpt-4o",
            "gpt-4-turbo",
            "gpt-4o-mini",
        ]
    
    @staticmethod
    def estimate_cost(num_pages: int, model: str = "gpt-4o") -> float:
        """
        Estimate API cost for extraction
        
        Args:
            num_pages: Number of PDF pages (converted to images)
            model: Model name
            
        Returns:
            Estimated cost in USD
        """
        # OpenAI vision pricing is based on tokens + images
        # Each image (high detail) = ~765 tokens
        tokens_per_page = 765
        
        # Input cost per million tokens
        input_cost_per_mtok = {
            "gpt-4o": 2.5,
            "gpt-4-turbo": 10.0,
            "gpt-4o-mini": 0.15,
        }
        
        output_tokens = 1000
        output_cost_per_mtok = {
            "gpt-4o": 10.0,
            "gpt-4-turbo": 30.0,
            "gpt-4o-mini": 0.6,
        }
        
        # Limit to 10 pages (we only process first 10)
        num_pages = min(num_pages, 10)
        
        input_cost = (num_pages * tokens_per_page / 1_000_000) * input_cost_per_mtok.get(model, 2.5)
        output_cost = (output_tokens / 1_000_000) * output_cost_per_mtok.get(model, 10.0)
        
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
