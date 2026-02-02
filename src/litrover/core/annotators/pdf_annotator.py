"""
PDF Annotator for LitRover
Highlights source text in PDFs with color-coded annotations
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import fitz  # PyMuPDF
import re
import unicodedata


class PDFAnnotator:
    """
    Annotate PDFs by highlighting source text for extracted data
    
    Features:
    - Color-coded highlights by field type
    - Tooltips with field names
    - Legend on first page
    - Source traceability
    """
    
    # Color scheme for different field types (RGB 0-1 range)
    DEFAULT_COLORS = {
        "location": (0.0, 0.4, 1.0),       # Blue - coordinates, addresses
        "environment": (0.0, 0.7, 0.3),    # Green - flags, categories
        "measurement": (1.0, 0.5, 0.0),    # Orange - quantities, sizes
        "method": (0.6, 0.0, 0.8),         # Purple - techniques, procedures
        "instrument": (1.0, 0.0, 0.0),     # Red - equipment, tools
        "statistical": (0.8, 0.7, 0.0),    # Yellow - data amounts, statistics
        "other": (0.5, 0.5, 0.5),          # Gray - miscellaneous
    }
    
    def __init__(self, color_map: Optional[Dict[str, Tuple[float, float, float]]] = None, debug: bool = False):
        """
        Initialize PDF annotator
        
        Args:
            color_map: Optional custom color mapping {field_name: (r, g, b)}
            debug: Enable debug logging for failed matches
        """
        self.color_map = color_map or {}
        self.annotations_count = 0
        self.debug = debug
        self.failed_matches = []  # Track failed matches for debugging
    
    def annotate_pdf(
        self,
        pdf_path: Path,
        extraction_results: List[Dict[str, Any]],
        output_path: Path,
        add_legend: bool = True
    ) -> bool:
        """
        Annotate PDF with highlights for extracted data
        
        Args:
            pdf_path: Path to original PDF
            extraction_results: List of extracted data with source references
            output_path: Path to save annotated PDF
            add_legend: Whether to add color legend on first page
            
        Returns:
            True if annotations were added successfully
        """
        if not extraction_results:
            return False
        
        try:
            doc = fitz.open(str(pdf_path))
        except Exception as e:
            print(f"    ✗ Cannot open PDF: {e}")
            return False
        
        self.annotations_count = 0
        
        # Process each extraction result
        for result in extraction_results:
            self._annotate_result(doc, result)
        
        if self.annotations_count > 0:
            # Add legend if requested
            if add_legend and len(doc) > 0:
                self._add_legend(doc[0])
            
            # Save annotated PDF
            output_path.parent.mkdir(parents=True, exist_ok=True)
            doc.save(str(output_path))
            doc.close()
            
            print(f"    ✓ Added {self.annotations_count} highlights → {output_path.name}")
            return True
        else:
            doc.close()
            print(f"    ○ No text matches found for highlighting")
            return False
    
    def _annotate_result(self, doc: fitz.Document, result: Dict[str, Any]):
        """Annotate a single extraction result"""
        # Get identifier for tooltips
        identifier = result.get("identifier", "Unknown")
        
        for field_name, field_data in result.items():
            if field_name == "identifier":
                continue
            
            # Handle both formats: {value, source_text, page} or plain value
            if not isinstance(field_data, dict):
                continue
            
            source_text = field_data.get("source_text")
            page_num = field_data.get("page")
            value = field_data.get("value")
            
            if not source_text or value is None:
                continue
            
            # Get color for this field
            color = self._get_color_for_field(field_name)
            
            # Search and highlight
            found = self._highlight_text(
                doc, source_text, page_num, color, field_name, identifier
            )
            
            if found:
                self.annotations_count += 1
    
    def _highlight_text(
        self,
        doc: fitz.Document,
        search_text: str,
        page_num: Optional[int],
        color: Tuple[float, float, float],
        field_name: str,
        identifier: str
    ) -> bool:
        """
        Search for and highlight text in the document
        
        Args:
            doc: PDF document
            search_text: Text to search for
            page_num: Preferred page number (1-indexed)
            color: RGB color tuple
            field_name: Name of the field
            identifier: Identifier for tooltip
            
        Returns:
            True if text was found and highlighted
        """
        # Try specific page first
        if page_num and isinstance(page_num, int) and 1 <= page_num <= len(doc):
            page = doc[page_num - 1]
            if self._highlight_on_page(page, search_text, color, field_name, identifier):
                return True
        
        # Search all pages if not found on specific page
        for page in doc:
            if self._highlight_on_page(page, search_text, color, field_name, identifier):
                return True
        
        # Try shorter snippet if full text not found
        if len(search_text) > 20:
            short_text = search_text[:20]
            for page in doc:
                if self._highlight_on_page(page, short_text, color, field_name, identifier):
                    return True
        
        # Log failed match if debug enabled
        if self.debug:
            self.failed_matches.append({
                'field': field_name,
                'text': search_text,
                'page_hint': page_num
            })
        
        return False
    
    @staticmethod
    def _normalize_text(text: str) -> str:
        """
        Normalize text for better matching
        
        Args:
            text: Text to normalize
            
        Returns:
            Normalized text
        """
        if not text:
            return ""
        
        # Normalize unicode characters (e.g., different dash types)
        text = unicodedata.normalize('NFKD', text)
        
        # Replace special degree symbols and similar characters
        replacements = {
            '°': ' ',
            '±': '+/-',
            '−': '-',
            '–': '-',
            '—': '-',
            '"': '"',
            '"': '"',
            ''': "'",
            ''': "'",
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text
    
    @staticmethod
    def _extract_numbers(text: str) -> List[float]:
        """
        Extract numeric values from text (useful for coordinates)
        
        Args:
            text: Text containing numbers
            
        Returns:
            List of extracted numbers
        """
        # Match decimal numbers (including negative)
        pattern = r'-?\d+\.?\d*'
        matches = re.findall(pattern, text)
        return [float(m) for m in matches if m]
    
    def _highlight_on_page(
        self,
        page: fitz.Page,
        search_text: str,
        color: Tuple[float, float, float],
        field_name: str,
        identifier: str
    ) -> bool:
        """
        Highlight text on a specific page with multiple fallback strategies
        
        Returns:
            True if text was found and highlighted
        """
        if not search_text:
            return False
        
        # Strategy 1: Exact match (case insensitive)
        text_instances = page.search_for(search_text, quads=True)
        
        # Strategy 2: Normalized whitespace
        if not text_instances:
            normalized = ' '.join(search_text.split())
            text_instances = page.search_for(normalized, quads=True)
        
        # Strategy 3: Normalized special characters
        if not text_instances:
            normalized_text = self._normalize_text(search_text)
            text_instances = page.search_for(normalized_text, quads=True)
        
        # Strategy 4: For numeric fields (lat/lon), search for the numbers
        if not text_instances and any(kw in field_name.lower() for kw in ['lat', 'lon', 'coord', 'depth', 'length', 'temperature']):
            numbers = self._extract_numbers(search_text)
            if numbers:
                # Try searching for the first significant number
                for num in numbers:
                    num_str = str(num)
                    text_instances = page.search_for(num_str, quads=True)
                    if text_instances:
                        break
        
        # Strategy 5: Try first 30 characters if text is long
        if not text_instances and len(search_text) > 30:
            short_text = search_text[:30]
            text_instances = page.search_for(short_text, quads=True)
        
        # Strategy 6: Try last 30 characters
        if not text_instances and len(search_text) > 30:
            short_text = search_text[-30:]
            text_instances = page.search_for(short_text, quads=True)
        
        if not text_instances:
            return False
        
        # Add highlights for all instances (limit to first 5 to avoid clutter)
        for quad in text_instances[:5]:
            highlight = page.add_highlight_annot(quad)
            highlight.set_colors(stroke=color)
            highlight.set_opacity(0.35)
            
            # Add tooltip
            tooltip = f"[{field_name}] {identifier}"
            highlight.set_info(content=tooltip, title=field_name)
            highlight.update()
        
        return True
    
    def _get_color_for_field(self, field_name: str) -> Tuple[float, float, float]:
        """
        Get color for a field
        
        Args:
            field_name: Name of the field
            
        Returns:
            RGB color tuple
        """
        # Check custom color map first
        if field_name in self.color_map:
            return self.color_map[field_name]
        
        # Categorize by field name patterns
        field_lower = field_name.lower()
        
        if any(kw in field_lower for kw in ['lat', 'lon', 'coord', 'location', 'address']):
            return self.DEFAULT_COLORS["location"]
        
        elif any(kw in field_lower for kw in ['marine', 'terrestrial', 'environment', 'climate', 'sediment', 'rock']):
            return self.DEFAULT_COLORS["environment"]
        
        elif any(kw in field_lower for kw in ['depth', 'length', 'size', 'temperature', 'weight', 'volume']):
            return self.DEFAULT_COLORS["measurement"]
        
        elif any(kw in field_lower for kw in ['method', 'technique', 'procedure', 'analysis', 'application']):
            return self.DEFAULT_COLORS["method"]
        
        elif any(kw in field_lower for kw in ['machine', 'instrument', 'equipment', 'device', 'tool']):
            return self.DEFAULT_COLORS["instrument"]
        
        elif any(kw in field_lower for kw in ['count', 'amount', 'number', 'sample', 'data', 'p_value', 'statistical']):
            return self.DEFAULT_COLORS["statistical"]
        
        else:
            return self.DEFAULT_COLORS["other"]
    
    def _add_legend(self, page: fitz.Page):
        """Add color-coded legend to the first page"""
        legend_items = [
            ("Location (lat/lon, coordinates)", self.DEFAULT_COLORS["location"]),
            ("Environment (marine, terrestrial, etc.)", self.DEFAULT_COLORS["environment"]),
            ("Measurements (depth, length, size)", self.DEFAULT_COLORS["measurement"]),
            ("Methods (analysis, techniques)", self.DEFAULT_COLORS["method"]),
            ("Instruments (machines, equipment)", self.DEFAULT_COLORS["instrument"]),
            ("Statistical (counts, p-values)", self.DEFAULT_COLORS["statistical"]),
            ("Other information", self.DEFAULT_COLORS["other"]),
        ]
        
        # Calculate legend box dimensions
        page_width = page.rect.width
        box_x = page_width - 230
        box_y = 10
        box_w = 220
        box_h = len(legend_items) * 15 + 25
        
        # Draw white background with border
        rect = fitz.Rect(box_x, box_y, box_x + box_w, box_y + box_h)
        page.draw_rect(rect, color=(0, 0, 0), fill=(1, 1, 1), width=0.5)
        
        # Add title
        page.insert_text(
            fitz.Point(box_x + 5, box_y + 14),
            "LitRover Extraction Legend",
            fontsize=9,
            fontname="helv-bold",
            color=(0, 0, 0),
        )
        
        # Add legend entries
        for i, (label, color) in enumerate(legend_items):
            y = box_y + 28 + i * 15
            
            # Color swatch
            swatch = fitz.Rect(box_x + 5, y - 6, box_x + 15, y + 2)
            page.draw_rect(swatch, fill=color)
            
            # Label text
            page.insert_text(
                fitz.Point(box_x + 20, y),
                label,
                fontsize=7,
                fontname="helv",
                color=(0, 0, 0),
            )
    
    def get_failed_matches(self) -> List[Dict[str, Any]]:
        """
        Get list of failed text matches (for debugging)
        
        Returns:
            List of failed match information
        """
        return self.failed_matches
    
    @staticmethod
    def create_color_map_for_schema(schema: List[Dict[str, Any]]) -> Dict[str, Tuple[float, float, float]]:
        """
        Create a custom color map based on extraction schema
        
        Args:
            schema: Extraction schema with field definitions
            
        Returns:
            Dictionary mapping field names to colors
        """
        annotator = PDFAnnotator()
        color_map = {}
        
        for field in schema:
            field_name = field.get('field')
            if field_name:
                color_map[field_name] = annotator._get_color_for_field(field_name)
        
        return color_map
