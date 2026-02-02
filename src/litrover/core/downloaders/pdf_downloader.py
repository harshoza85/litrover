"""
PDF downloader with multi-publisher support
Downloads PDFs from various academic publishers
"""

import requests
import time
from pathlib import Path
from typing import Dict, Any, Optional
from urllib.parse import urlparse


class PDFDownloader:
    """
    Download PDFs from academic publishers
    
    Features:
    - Multi-publisher URL patterns
    - Retry logic with exponential backoff
    - File validation
    - Smart naming
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize PDF downloader
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        
        # Configuration
        downloader_config = config.get('downloader', {})
        self.skip_existing = downloader_config.get('skip_existing', True)
        self.timeout = downloader_config.get('timeout', 60)
        self.max_retries = downloader_config.get('max_retries', 3)
        self.pdf_dir = Path(downloader_config.get('pdf_dir', 'papers'))
        
        # Ensure PDF directory exists
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        
        # Headers to mimic browser
        self.headers = {
            'User-Agent': downloader_config.get('user_agent', 
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'),
            'Accept': 'application/pdf,application/octet-stream,*/*',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    
    def download(self, url: str, filename: str) -> Optional[Path]:
        """
        Download PDF from URL
        
        Args:
            url: PDF URL
            filename: Output filename
            
        Returns:
            Path to downloaded file or None if failed
        """
        if not url:
            return None
        
        output_path = self.pdf_dir / filename
        
        # Skip if already exists
        if self.skip_existing and output_path.exists() and output_path.stat().st_size > 1000:
            print(f"    ✓ Already exists: {filename}")
            return output_path
        
        # Try download with retries
        for attempt in range(self.max_retries):
            try:
                print(f"    Downloading: {url[:70]}...")
                
                response = requests.get(
                    url,
                    headers=self.headers,
                    timeout=self.timeout,
                    stream=True,
                    allow_redirects=True
                )
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    
                    # Verify it's a PDF
                    if 'pdf' in content_type.lower() or url.endswith('.pdf') or response.content[:4] == b'%PDF':
                        # Write file
                        with open(output_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        # Verify file size
                        if output_path.stat().st_size > 1000:
                            print(f"    ✓ Downloaded: {filename}")
                            return output_path
                        else:
                            output_path.unlink()
                            print(f"    ✗ File too small, likely not a PDF")
                            return None
                    else:
                        print(f"    ✗ Not a PDF (content-type: {content_type})")
                        return None
                
                elif response.status_code == 403:
                    print(f"    ✗ Access denied (403) - may require authentication")
                    return None
                
                elif response.status_code == 404:
                    print(f"    ✗ Not found (404)")
                    return None
                
                else:
                    print(f"    ✗ HTTP {response.status_code}")
                    if attempt < self.max_retries - 1:
                        wait_time = 2 ** attempt
                        print(f"    Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    return None
            
            except requests.exceptions.Timeout:
                print(f"    ✗ Timeout")
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"    Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                return None
            
            except Exception as e:
                print(f"    ✗ Error: {str(e)[:50]}")
                return None
        
        return None
    
    def download_from_resolution(self, resolution: Dict[str, Any], 
                                 identifier: str, column_idx: int = 0) -> Optional[Path]:
        """
        Download PDF from a resolution result
        
        Args:
            resolution: Resolution dictionary with pdf_url
            identifier: Unique identifier for naming
            column_idx: Column index for naming
            
        Returns:
            Path to downloaded file or None
        """
        pdf_url = resolution.get('pdf_url')
        if not pdf_url:
            return None
        
        # Create filename
        doi = resolution.get('doi', '')
        if doi:
            safe_doi = doi.replace('/', '_').replace('.', '_')
            filename = f"{self._sanitize_filename(identifier)}_{column_idx}_{safe_doi}.pdf"
        else:
            # Use part of URL
            url_part = urlparse(pdf_url).path.split('/')[-1][:30]
            filename = f"{self._sanitize_filename(identifier)}_{column_idx}_{url_part}.pdf"
        
        return self.download(pdf_url, filename)
    
    def batch_download(self, resolutions: Dict[str, Dict[str, Any]], 
                       identifier: str) -> Dict[str, Path]:
        """
        Download multiple PDFs
        
        Args:
            resolutions: Dictionary of reference -> resolution
            identifier: Row identifier
            
        Returns:
            Dictionary of reference -> downloaded path
        """
        results = {}
        
        for idx, (ref, resolution) in enumerate(resolutions.items()):
            if resolution and resolution.get('pdf_url'):
                path = self.download_from_resolution(resolution, identifier, idx)
                if path:
                    results[ref] = path
                
                # Rate limiting
                time.sleep(1)
        
        return results
    
    @staticmethod
    def _sanitize_filename(text: str, max_length: int = 50) -> str:
        """
        Create safe filename from text
        
        Args:
            text: Input text
            max_length: Maximum length
            
        Returns:
            Sanitized filename
        """
        import re
        # Remove invalid characters
        text = re.sub(r'[<>:"/\\|?*]', '_', str(text))
        text = re.sub(r'\s+', '_', text)
        return text[:max_length]
    
    def get_download_stats(self) -> Dict[str, Any]:
        """
        Get download statistics
        
        Returns:
            Dictionary with stats
        """
        pdf_files = list(self.pdf_dir.glob('*.pdf'))
        
        return {
            'total_pdfs': len(pdf_files),
            'total_size_mb': sum(f.stat().st_size for f in pdf_files) / (1024 * 1024),
            'pdf_directory': str(self.pdf_dir)
        }
