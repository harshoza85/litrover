"""
AutoGen Orchestrator for LitRover
Multi-agent conversation system for collaborative processing
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

try:
    import autogen
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    print("Warning: AutoGen not installed. Install with: pip install pyautogen")

from ..utils import (
    setup_logger, print_success, print_error, print_info,
    ConfigLoader, ExcelHandler
)
from ..core import SemanticScholarResolver, PDFDownloader, get_extractor


class AutoGenOrchestrator:
    """
    AutoGen-based multi-agent orchestrator
    
    Agents:
    - Coordinator: Manages workflow and assigns tasks
    - Resolver: Handles citation resolution
    - Downloader: Manages PDF downloads  
    - Extractor: Performs metadata extraction
    """
    
    def __init__(self, config_loader: ConfigLoader):
        """
        Initialize AutoGen orchestrator
        
        Args:
            config_loader: Loaded configuration
        """
        if not AUTOGEN_AVAILABLE:
            raise ImportError("AutoGen is required. Install with: pip install pyautogen")
        
        self.config_loader = config_loader
        self.config = config_loader.config
        self.logger = setup_logger('litrover.autogen')
        
        # Initialize components
        self.excel_handler = ExcelHandler(self.config)
        
        api_key = config_loader.get_api_key('semantic_scholar')
        self.resolver = SemanticScholarResolver(self.config, api_key)
        
        self.downloader = PDFDownloader(self.config)
        
        llm_config = self.config.get('llm', {})
        provider = llm_config.get('provider')
        model = llm_config.get('model')
        api_key = config_loader.get_api_key(provider)
        self.extractor = get_extractor(provider, api_key, model, self.config)
        
        # Setup AutoGen
        self._setup_agents()
        
        print_success("AutoGen orchestrator initialized")
    
    def _setup_agents(self):
        """Setup AutoGen agents"""
        # LLM config for agents (using Claude/GPT for coordination)
        llm_provider = self.config.get('llm', {}).get('provider')
        
        # Use appropriate API for agent coordination
        if llm_provider == 'openai':
            api_key = self.config_loader.get_api_key('openai')
            llm_config = {
                "model": "gpt-4o-mini",
                "api_key": api_key,
                "temperature": 0.1
            }
        elif llm_provider == 'claude':
            # AutoGen doesn't natively support Claude, use OpenAI if available
            api_key = self.config_loader.get_api_key('openai')
            if api_key:
                llm_config = {
                    "model": "gpt-4o-mini",
                    "api_key": api_key,
                    "temperature": 0.1
                }
            else:
                print_warning("AutoGen requires OpenAI API. Using manual mode.")
                llm_config = False
        else:
            # Fallback to OpenAI
            api_key = self.config_loader.get_api_key('openai')
            if api_key:
                llm_config = {
                    "model": "gpt-4o-mini",
                    "api_key": api_key,
                    "temperature": 0.1
                }
            else:
                llm_config = False
        
        # Coordinator Agent
        self.coordinator = autogen.AssistantAgent(
            name="Coordinator",
            system_message="""You are the workflow coordinator for a literature processing pipeline.
            Your job is to:
            1. Analyze the current task
            2. Delegate to appropriate specialist agents
            3. Ensure all steps complete successfully
            4. Report final results
            
            Available specialists:
            - Resolver: Resolves citations to DOIs and PDF URLs
            - Downloader: Downloads PDFs from URLs
            - Extractor: Extracts metadata from PDFs
            
            Be concise and directive.""",
            llm_config=llm_config
        )
        
        # User Proxy (represents the system)
        self.user_proxy = autogen.UserProxyAgent(
            name="System",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            code_execution_config={"use_docker": False},
        )
        
        # Register functions for agents to call
        self._register_functions()
    
    def _register_functions(self):
        """Register Python functions that agents can call"""
        
        @self.user_proxy.register_for_execution()
        @self.coordinator.register_for_llm(description="Resolve a citation to metadata and PDF URL")
        def resolve_citation(citation: str) -> Dict[str, Any]:
            """Resolve citation using Semantic Scholar"""
            result = self.resolver.resolve(citation)
            return result if result else {"error": "Resolution failed"}
        
        @self.user_proxy.register_for_execution()
        @self.coordinator.register_for_llm(description="Download PDF from URL")
        def download_pdf(pdf_url: str, identifier: str, index: int = 0) -> str:
            """Download PDF and return path"""
            resolution = {'pdf_url': pdf_url}
            path = self.downloader.download_from_resolution(resolution, identifier, index)
            return str(path) if path else "Download failed"
        
        @self.user_proxy.register_for_execution()
        @self.coordinator.register_for_llm(description="Extract metadata from PDF")
        def extract_metadata(pdf_path: str) -> Dict[str, Any]:
            """Extract metadata from PDF"""
            extraction_prompt = self.config_loader.get_extraction_prompt()
            path = Path(pdf_path)
            
            if not path.exists():
                return {"error": "PDF not found"}
            
            result = self.extractor.extract_with_cache(path, extraction_prompt)
            return result if result else {"error": "Extraction failed"}
    
    def run(self):
        """Execute multi-agent workflow"""
        print_info("Starting AutoGen multi-agent workflow")
        
        # Load data
        df = self.excel_handler.load_excel(self.config['input_file'])
        print_success(f"Loaded {len(df)} rows")
        
        stats = {
            'total_rows': len(df),
            'successful': 0,
            'failed': 0
        }
        
        # Process each row
        for idx, row in df.iterrows():
            identifier = row[self.config['columns']['identifier']]
            papers = self.excel_handler.get_papers_for_row(idx)
            
            if not papers:
                continue
            
            print(f"\n[bold]Row {idx}: {identifier}[/bold]")
            print_info(f"Processing {len(papers)} paper(s) with multi-agent system")
            
            # Create task for coordinator
            task = f"""Process these papers for identifier '{identifier}':

Papers to process:
{chr(10).join([f"{i+1}. {p['value']}" for i, p in enumerate(papers)])}

Steps:
1. Resolve each citation to get DOI and PDF URL
2. Download PDFs
3. Extract metadata from PDFs
4. Return the extracted metadata

Extraction schema:
{self.config_loader.get_extraction_prompt()}

Be concise and focus on results."""
            
            try:
                # Initiate conversation
                self.user_proxy.initiate_chat(
                    self.coordinator,
                    message=task
                )
                
                # Note: In a real implementation, you'd parse the conversation
                # to extract results and save to Excel. This is simplified.
                stats['successful'] += 1
                
            except Exception as e:
                print_error(f"Agent workflow failed: {e}")
                stats['failed'] += 1
        
        # Save results
        output_dir = Path(self.config.get('output_dir', 'outputs'))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f"results_autogen_{timestamp}.xlsx"
        
        self.excel_handler.save_excel(output_file)
        print_success(f"\nResults saved to: {output_file}")
        
        # Print summary
        print(f"\n[bold]AutoGen Workflow Summary:[/bold]")
        print(f"  Total: {stats['total_rows']}")
        print(f"  Successful: {stats['successful']}")
        print(f"  Failed: {stats['failed']}")
        
        return stats


# Alternative: Simplified AutoGen without LLM coordination
class SimpleAutoGenOrchestrator(AutoGenOrchestrator):
    """
    Simplified AutoGen orchestrator that doesn't require LLM for coordination
    Uses direct function calls instead of agent conversation
    """
    
    def run(self):
        """Execute simplified workflow without LLM coordination"""
        print_info("Starting simplified AutoGen workflow (direct execution)")
        
        # Load data
        df = self.excel_handler.load_excel(self.config['input_file'])
        print_success(f"Loaded {len(df)} rows")
        
        stats = {
            'total_rows': len(df),
            'successful': 0,
            'failed': 0
        }
        
        # Process rows directly
        for idx, row in df.iterrows():
            identifier = row[self.config['columns']['identifier']]
            papers = self.excel_handler.get_papers_for_row(idx)
            
            if not papers:
                continue
            
            print(f"\n[bold]Row {idx}: {identifier}[/bold]")
            
            all_extracted_data = {}
            
            for i, paper in enumerate(papers):
                # Resolve
                resolution = self.resolver.resolve(paper['value'])
                if not resolution:
                    continue
                
                # Download
                pdf_path = self.downloader.download_from_resolution(
                    resolution, str(identifier), i
                )
                if not pdf_path:
                    continue
                
                # Extract
                extraction_prompt = self.config_loader.get_extraction_prompt()
                extracted_data = self.extractor.extract_with_cache(
                    pdf_path, extraction_prompt
                )
                
                if extracted_data:
                    # Merge data
                    for key, value in extracted_data.items():
                        if key not in all_extracted_data or all_extracted_data[key] is None:
                            all_extracted_data[key] = value
            
            # Save if we got data
            if all_extracted_data:
                metadata = {
                    'extraction_timestamp': datetime.now().isoformat(),
                    'extraction_source': self.extractor.get_provider_name()
                }
                self.excel_handler.update_row(idx, all_extracted_data, metadata)
                stats['successful'] += 1
            else:
                stats['failed'] += 1
        
        # Save results
        output_dir = Path(self.config.get('output_dir', 'outputs'))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f"results_autogen_simple_{timestamp}.xlsx"
        
        self.excel_handler.save_excel(output_file)
        print_success(f"\nResults saved to: {output_file}")
        
        return stats
