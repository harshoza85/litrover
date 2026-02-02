"""
Citation resolver using Semantic Scholar API
Resolves text citations and DOIs to structured metadata
"""

import requests
import re
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from difflib import SequenceMatcher
import json


class SemanticScholarResolver:
    """
    Resolve citations using Semantic Scholar API

    Handles:
    - DOI resolution
    - Text citation matching
    - Fuzzy author/year matching
    - PDF URL retrieval (prioritizes true open access via Unpaywall)
    """

    # Publisher domains that typically require authentication
    PAYWALLED_DOMAINS = [
        'onlinelibrary.wiley.com',
        'agupubs.onlinelibrary.wiley.com',
        'sciencedirect.com',
        'tandfonline.com',
        'springerlink.com',
        'link.springer.com',
        'journals.sagepub.com',
        'academic.oup.com',
    ]

    def __init__(self, config: Dict[str, Any], api_key: Optional[str] = None):
        """
        Initialize resolver
        
        Args:
            config: Configuration dictionary
            api_key: Optional Semantic Scholar API key (increases rate limits)
        """
        self.config = config
        self.api_key = api_key
        
        # Configuration
        resolver_config = config.get('resolver', {})
        self.timeout = resolver_config.get('semantic_scholar', {}).get('timeout', 15)
        self.max_results = resolver_config.get('semantic_scholar', {}).get('max_results', 10)
        self.rate_limit_delay = resolver_config.get('rate_limit_delay', 1.0)
        
        # Cache
        self.cache_enabled = resolver_config.get('cache_results', True)
        self.cache = {}
        self.cache_file = Path('resolution_cache.json')
        self._load_cache()
        
        # Headers
        self.headers = {
            'User-Agent': 'LitRover/1.0 (Research Tool)'
        }
        if self.api_key:
            self.headers['x-api-key'] = self.api_key
    
    def _load_cache(self):
        """Load cache from disk"""
        if self.cache_enabled and self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
                print(f"Loaded {len(self.cache)} cached resolutions")
            except json.JSONDecodeError:
                self.cache = {}
    
    def _save_cache(self):
        """Save cache to disk"""
        if self.cache_enabled:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
    
    def _string_similarity(self, a: str, b: str) -> float:
        """Calculate string similarity (0-1)"""
        return SequenceMatcher(None, str(a).lower(), str(b).lower()).ratio()
    
    def clean_doi(self, doi_or_url: str) -> Optional[str]:
        """
        Extract clean DOI from URL or text
        
        Args:
            doi_or_url: DOI URL or DOI string
            
        Returns:
            Clean DOI or None
        """
        if not isinstance(doi_or_url, str):
            return None
        
        match = re.search(r'(10\.\d{4,9}/[-._;()/:A-Z0-9]+)', doi_or_url, re.IGNORECASE)
        return match.group(1) if match else None
    
    def is_url(self, text: str) -> bool:
        """Check if text is a URL"""
        if not isinstance(text, str):
            return False
        return text.strip().startswith('http')
    
    def resolve_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        """
        Resolve DOI to metadata
        
        Args:
            doi: DOI string
            
        Returns:
            Resolution dictionary with DOI, title, PDF URL
        """
        # Check cache
        cache_key = f"doi:{doi}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}"
            params = {"fields": "externalIds,openAccessPdf,title,year,authors"}
            
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()

                # Get initial PDF URL from Semantic Scholar
                ss_pdf_url = data.get('openAccessPdf', {}).get('url') if data.get('openAccessPdf') else None

                # Determine final PDF URL with priority:
                # 1. Semantic Scholar OA if not paywalled
                # 2. Unpaywall (finds preprints, author copies, etc.)
                # 3. Publisher patterns as last resort
                pdf_url = None

                if ss_pdf_url and not self._is_paywalled_url(ss_pdf_url):
                    pdf_url = ss_pdf_url
                    print(f"    ✓ Found open access PDF via Semantic Scholar")
                else:
                    # Try Unpaywall for truly open access version
                    pdf_url = self._get_unpaywall_pdf(doi)

                    if not pdf_url:
                        # Fall back to publisher patterns (may require auth)
                        pdf_url = self._get_pdf_from_doi(doi)
                        if pdf_url:
                            print(f"    ⚠ Using publisher URL (may require authentication)")

                result = {
                    'doi': doi,
                    'title': data.get('title'),
                    'year': data.get('year'),
                    'pdf_url': pdf_url,
                    'source': 'semantic_scholar'
                }

                self.cache[cache_key] = result
                self._save_cache()

                return result
            
            elif response.status_code == 429:
                print("  ⚠ Rate limited, waiting 45s...")
                time.sleep(45)
                return self.resolve_doi(doi)  # Retry
        
        except Exception as e:
            print(f"  ✗ DOI resolution error: {e}")
        
        self.cache[cache_key] = None
        self._save_cache()
        return None
    
    def _is_paywalled_url(self, url: str) -> bool:
        """Check if URL is from a typically paywalled domain"""
        if not url:
            return False
        for domain in self.PAYWALLED_DOMAINS:
            if domain in url:
                return True
        return False

    def _get_unpaywall_pdf(self, doi: str) -> Optional[str]:
        """
        Get open access PDF URL from Unpaywall API

        Unpaywall provides alternative OA sources like preprints,
        author copies, and repository versions.

        Args:
            doi: DOI string

        Returns:
            Open access PDF URL or None
        """
        try:
            # Unpaywall requires an email for API access
            email = self.config.get('resolver', {}).get('unpaywall_email', 'litrover.user@gmail.com')
            url = f"https://api.unpaywall.org/v2/{doi}?email={email}"

            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()

                # Try best_oa_location first (highest quality OA version)
                best_oa = data.get('best_oa_location')
                if best_oa:
                    pdf_url = best_oa.get('url_for_pdf') or best_oa.get('url')
                    if pdf_url and not self._is_paywalled_url(pdf_url):
                        print(f"    ✓ Found open access via Unpaywall: {best_oa.get('host_type', 'unknown')}")
                        return pdf_url

                # Check all OA locations for a non-paywalled PDF
                for loc in data.get('oa_locations', []):
                    pdf_url = loc.get('url_for_pdf') or loc.get('url')
                    if pdf_url and not self._is_paywalled_url(pdf_url):
                        print(f"    ✓ Found open access via Unpaywall: {loc.get('host_type', 'unknown')}")
                        return pdf_url

        except Exception as e:
            pass  # Silently fail, will fall back to other methods

        return None

    def _get_pdf_from_doi(self, doi: str) -> Optional[str]:
        """
        Construct PDF URL from DOI using publisher patterns
        (fallback when no open access found)

        Args:
            doi: DOI string

        Returns:
            PDF URL or None
        """
        patterns = {
            '10.1029': f"https://agupubs.onlinelibrary.wiley.com/doi/pdfdirect/{doi}",
            '10.1002': f"https://onlinelibrary.wiley.com/doi/pdfdirect/{doi}",
            '10.1111': f"https://onlinelibrary.wiley.com/doi/pdfdirect/{doi}",
            '10.1038': f"https://www.nature.com/articles/{doi.split('/')[-1]}.pdf",
            '10.1007': f"https://link.springer.com/content/pdf/{doi}.pdf",
            '10.3390': f"https://www.mdpi.com/{doi}/pdf",
        }
        
        for prefix, url in patterns.items():
            if doi.startswith(prefix):
                return url
        
        # Copernicus special handling
        if '10.5194/' in doi:
            match = re.search(r'10\.5194/(cp|cpd|sd|se|bg)-(\d+)-(\d+)-(\d+)', doi)
            if match:
                journal, vol, page, year = match.groups()
                return f"https://{journal}.copernicus.org/articles/{vol}/{page}/{year}/{journal}-{vol}-{page}-{year}.pdf"
        
        return None
    
    def search_citation(self, citation_text: str) -> Optional[Dict[str, Any]]:
        """
        Search for a text citation
        
        Args:
            citation_text: Text citation like "Smith et al., 2020"
            
        Returns:
            Resolution dictionary or None
        """
        # Check cache
        cache_key = f"citation:{citation_text}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Extract year and first author
        year_match = re.search(r'\b(19|20)\d{2}\b', citation_text)
        target_year = int(year_match.group(0)) if year_match else None
        
        # Extract first author (first word before comma or "et al")
        first_author = None
        match = re.match(r'([A-Za-z]+)', citation_text)
        if match:
            first_author = match.group(1)
        
        try:
            url = "https://api.semanticscholar.org/graph/v1/paper/search"
            params = {
                "query": citation_text,
                "limit": self.max_results,
                "fields": "title,year,externalIds,openAccessPdf,authors"
            }
            
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                candidates = data.get('data', [])
                
                best_candidate = None
                best_score = -1
                
                for cand in candidates:
                    score = 0
                    
                    # Author matching
                    if first_author:
                        authors = [a.get('name', '').split()[-1] for a in cand.get('authors', [])]
                        if any(self._string_similarity(first_author, a) > 0.8 for a in authors):
                            score += 60
                        else:
                            continue  # Skip if author doesn't match
                    
                    # Year matching
                    if target_year and cand.get('year'):
                        if cand['year'] == target_year:
                            score += 40
                        elif abs(cand['year'] - target_year) <= 1:
                            score += 15
                    
                    # PDF availability bonus
                    if cand.get('openAccessPdf') and cand['openAccessPdf'].get('url'):
                        score += 50
                    
                    if score > best_score:
                        best_score = score
                        best_candidate = cand
                
                if best_candidate and best_score > 50:
                    doi = best_candidate.get('externalIds', {}).get('DOI')

                    # Get initial PDF URL from Semantic Scholar
                    ss_pdf_url = None
                    if best_candidate.get('openAccessPdf'):
                        ss_pdf_url = best_candidate['openAccessPdf'].get('url')

                    # Prioritize truly open access URLs
                    pdf_url = None
                    if ss_pdf_url and not self._is_paywalled_url(ss_pdf_url):
                        pdf_url = ss_pdf_url
                    elif doi:
                        # Try Unpaywall first
                        pdf_url = self._get_unpaywall_pdf(doi)
                        if not pdf_url:
                            pdf_url = self._get_pdf_from_doi(doi)

                    result = {
                        'doi': doi,
                        'title': best_candidate.get('title'),
                        'year': best_candidate.get('year'),
                        'pdf_url': pdf_url,
                        'source': 'semantic_scholar',
                        'confidence': best_score / 150  # Normalize to 0-1
                    }

                    self.cache[cache_key] = result
                    self._save_cache()

                    return result
            
            elif response.status_code == 429:
                print("  ⚠ Rate limited, waiting 45s...")
                time.sleep(45)
                return self.search_citation(citation_text)
        
        except Exception as e:
            print(f"  ✗ Citation search error: {e}")
        
        self.cache[cache_key] = None
        self._save_cache()
        return None
    
    def resolve(self, reference: str) -> Optional[Dict[str, Any]]:
        """
        Resolve any type of reference (URL, DOI, or text citation)
        
        Args:
            reference: Reference string
            
        Returns:
            Resolution dictionary or None
        """
        if not isinstance(reference, str) or not reference.strip():
            return None
        
        reference = reference.strip()
        
        # Remove "(no access)" prefix if present
        if reference.startswith('(no access)'):
            reference = reference.replace('(no access)', '').strip()
        
        # Check if it's a URL with DOI
        doi = self.clean_doi(reference)
        if doi:
            print(f"    Resolving DOI: {doi}")
            result = self.resolve_doi(doi)
            time.sleep(self.rate_limit_delay)
            return result
        
        # Check if it's a direct PDF URL
        if self.is_url(reference) and reference.endswith('.pdf'):
            return {
                'doi': None,
                'pdf_url': reference,
                'source': 'direct_url'
            }
        
        # Try as text citation
        print(f"    Searching citation: '{reference[:50]}...'")
        result = self.search_citation(reference)
        time.sleep(self.rate_limit_delay)
        return result
    
    def batch_resolve(self, references: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Resolve multiple references
        
        Args:
            references: List of reference strings
            
        Returns:
            Dictionary mapping reference -> resolution
        """
        results = {}
        
        for ref in references:
            if ref:
                result = self.resolve(ref)
                if result:
                    results[ref] = result
        
        return results
