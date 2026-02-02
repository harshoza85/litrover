"""
LangGraph Orchestrator for LitRover
Graph-based workflow with decision nodes and conditional execution
"""

from typing import TypedDict, Annotated, Sequence
from pathlib import Path
from datetime import datetime
import operator

try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("Warning: LangGraph not installed. Install with: pip install langgraph")

from ..utils import (
    setup_logger, print_success, print_error, print_warning,
    print_info, ConfigLoader, ExcelHandler
)
from ..core import SemanticScholarResolver, PDFDownloader, get_extractor


class WorkflowState(TypedDict):
    """State passed through the workflow graph"""
    row_idx: int
    identifier: str
    papers: list
    resolutions: dict
    pdf_paths: dict
    extracted_data: dict
    errors: Annotated[list, operator.add]
    completed_steps: Annotated[list, operator.add]


class LangGraphOrchestrator:
    """
    LangGraph-based orchestrator with conditional workflow
    
    Features:
    - Graph-based execution flow
    - Decision nodes based on data availability
    - Parallel processing capabilities
    - Error recovery and retry logic
    """
    
    def __init__(self, config_loader: ConfigLoader):
        """
        Initialize LangGraph orchestrator
        
        Args:
            config_loader: Loaded configuration
        """
        if not LANGGRAPH_AVAILABLE:
            raise ImportError("LangGraph is required. Install with: pip install langgraph")
        
        self.config_loader = config_loader
        self.config = config_loader.config
        self.logger = setup_logger('litrover.langgraph')
        
        # Initialize components
        self.excel_handler = ExcelHandler(self.config)
        
        # Initialize resolver
        api_key = config_loader.get_api_key('semantic_scholar')
        self.resolver = SemanticScholarResolver(self.config, api_key)
        
        # Initialize downloader
        self.downloader = PDFDownloader(self.config)
        
        # Initialize extractor
        llm_config = self.config.get('llm', {})
        provider = llm_config.get('provider')
        model = llm_config.get('model')
        api_key = config_loader.get_api_key(provider)
        self.extractor = get_extractor(provider, api_key, model, self.config)
        
        # Build workflow graph
        self.workflow = self._build_workflow()
        
        print_success("LangGraph orchestrator initialized")
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(WorkflowState)
        
        # Add nodes
        workflow.add_node("get_papers", self._get_papers_node)
        workflow.add_node("resolve_citations", self._resolve_citations_node)
        workflow.add_node("download_pdfs", self._download_pdfs_node)
        workflow.add_node("extract_metadata", self._extract_metadata_node)
        workflow.add_node("save_results", self._save_results_node)
        
        # Define edges
        workflow.set_entry_point("get_papers")
        
        # Conditional routing based on papers found
        workflow.add_conditional_edges(
            "get_papers",
            self._should_resolve_citations,
            {
                "resolve": "resolve_citations",
                "end": END
            }
        )
        
        # Conditional routing based on resolutions
        workflow.add_conditional_edges(
            "resolve_citations",
            self._should_download_pdfs,
            {
                "download": "download_pdfs",
                "end": END
            }
        )
        
        # Conditional routing based on PDFs
        workflow.add_conditional_edges(
            "download_pdfs",
            self._should_extract_metadata,
            {
                "extract": "extract_metadata",
                "end": END
            }
        )
        
        workflow.add_edge("extract_metadata", "save_results")
        workflow.add_edge("save_results", END)
        
        return workflow.compile()
    
    def _get_papers_node(self, state: WorkflowState) -> WorkflowState:
        """Node: Get paper references from row"""
        print_info(f"Getting papers for row {state['row_idx']}")
        
        papers = self.excel_handler.get_papers_for_row(state['row_idx'])
        state['papers'] = papers
        state['completed_steps'].append('get_papers')
        
        print_success(f"Found {len(papers)} paper(s)")
        return state
    
    def _resolve_citations_node(self, state: WorkflowState) -> WorkflowState:
        """Node: Resolve citations"""
        print_info(f"Resolving {len(state['papers'])} citation(s)")
        
        resolutions = {}
        for paper in state['papers']:
            try:
                resolution = self.resolver.resolve(paper['value'])
                if resolution:
                    resolutions[paper['value']] = resolution
            except Exception as e:
                state['errors'].append(f"Resolution error: {e}")
                print_error(f"Failed to resolve: {e}")
        
        state['resolutions'] = resolutions
        state['completed_steps'].append('resolve_citations')
        
        print_success(f"Resolved {len(resolutions)} citation(s)")
        return state
    
    def _download_pdfs_node(self, state: WorkflowState) -> WorkflowState:
        """Node: Download PDFs"""
        print_info(f"Downloading {len(state['resolutions'])} PDF(s)")
        
        pdf_paths = {}
        for idx, (ref, resolution) in enumerate(state['resolutions'].items()):
            try:
                pdf_path = self.downloader.download_from_resolution(
                    resolution, state['identifier'], idx
                )
                if pdf_path:
                    pdf_paths[ref] = pdf_path
            except Exception as e:
                state['errors'].append(f"Download error: {e}")
                print_error(f"Failed to download: {e}")
        
        state['pdf_paths'] = pdf_paths
        state['completed_steps'].append('download_pdfs')
        
        print_success(f"Downloaded {len(pdf_paths)} PDF(s)")
        return state
    
    def _extract_metadata_node(self, state: WorkflowState) -> WorkflowState:
        """Node: Extract metadata from PDFs"""
        print_info(f"Extracting metadata from {len(state['pdf_paths'])} PDF(s)")
        
        extraction_prompt = self.config_loader.get_extraction_prompt()
        extracted_data = {}
        
        for ref, pdf_path in state['pdf_paths'].items():
            try:
                data = self.extractor.extract_with_cache(pdf_path, extraction_prompt)
                if data:
                    # Merge extracted data (take first non-null value for each field)
                    for key, value in data.items():
                        if key not in extracted_data or extracted_data[key] is None:
                            extracted_data[key] = value
            except Exception as e:
                state['errors'].append(f"Extraction error: {e}")
                print_error(f"Failed to extract: {e}")
        
        state['extracted_data'] = extracted_data
        state['completed_steps'].append('extract_metadata')
        
        print_success(f"Extracted {len(extracted_data)} field(s)")
        return state
    
    def _save_results_node(self, state: WorkflowState) -> WorkflowState:
        """Node: Save extracted data to Excel"""
        if state['extracted_data']:
            print_info("Saving extracted data")
            
            metadata = {
                'extraction_timestamp': datetime.now().isoformat(),
                'extraction_source': self.extractor.get_provider_name(),
                'confidence': self.extractor.estimate_confidence(state['extracted_data'])
            }
            
            self.excel_handler.update_row(
                state['row_idx'],
                state['extracted_data'],
                metadata
            )
            
            state['completed_steps'].append('save_results')
            print_success("Data saved")
        
        return state
    
    def _should_resolve_citations(self, state: WorkflowState) -> str:
        """Decision: Should we resolve citations?"""
        if state['papers']:
            return "resolve"
        return "end"
    
    def _should_download_pdfs(self, state: WorkflowState) -> str:
        """Decision: Should we download PDFs?"""
        if state['resolutions']:
            return "download"
        return "end"
    
    def _should_extract_metadata(self, state: WorkflowState) -> str:
        """Decision: Should we extract metadata?"""
        if state['pdf_paths']:
            return "extract"
        return "end"
    
    def run(self):
        """Execute workflow for all rows"""
        print_info("Starting LangGraph workflow")
        
        # Load data
        df = self.excel_handler.load_excel(self.config['input_file'])
        print_success(f"Loaded {len(df)} rows")
        
        stats = {
            'total_rows': len(df),
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        # Process each row through workflow
        for idx, row in df.iterrows():
            identifier = row[self.config['columns']['identifier']]
            
            print(f"\n[bold]Processing row {idx}: {identifier}[/bold]")
            
            # Initialize state
            initial_state = WorkflowState(
                row_idx=idx,
                identifier=str(identifier),
                papers=[],
                resolutions={},
                pdf_paths={},
                extracted_data={},
                errors=[],
                completed_steps=[]
            )
            
            try:
                # Execute workflow
                final_state = self.workflow.invoke(initial_state)
                
                if final_state['extracted_data']:
                    stats['successful'] += 1
                else:
                    stats['failed'] += 1
                
                if final_state['errors']:
                    stats['errors'].extend(final_state['errors'])
            
            except Exception as e:
                stats['failed'] += 1
                stats['errors'].append(f"Row {idx}: {e}")
                print_error(f"Workflow failed: {e}")
        
        # Save final Excel
        output_dir = Path(self.config.get('output_dir', 'outputs'))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f"results_langgraph_{timestamp}.xlsx"
        
        self.excel_handler.save_excel(output_file)
        print_success(f"\nResults saved to: {output_file}")
        
        # Print summary
        print(f"\n[bold]LangGraph Workflow Summary:[/bold]")
        print(f"  Total: {stats['total_rows']}")
        print(f"  Successful: {stats['successful']}")
        print(f"  Failed: {stats['failed']}")
        print(f"  Errors: {len(stats['errors'])}")
        
        return stats
