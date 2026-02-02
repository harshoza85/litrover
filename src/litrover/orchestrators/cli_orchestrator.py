"""
CLI Orchestrator for LitRover
Automated workflow execution with progress tracking
"""

from pathlib import Path
from typing import Dict, Any
import time
from datetime import datetime

from ..utils import (
    setup_logger, print_banner, print_step, print_success, 
    print_error, print_warning, print_info, create_progress_bar,
    print_summary_table, ConfigLoader, ExcelHandler
)
from ..core import SemanticScholarResolver, PDFDownloader, get_extractor, PDFAnnotator


class CLIOrchestrator:
    """
    Simple CLI orchestrator for automated pipeline execution
    
    Workflow:
    1. Load configuration and Excel
    2. Resolve citations
    3. Download PDFs
    4. Extract metadata
    5. Save results
    """
    
    def __init__(self, config_loader: ConfigLoader):
        """
        Initialize orchestrator
        
        Args:
            config_loader: Loaded configuration
        """
        self.config_loader = config_loader
        self.config = config_loader.config
        self.logger = setup_logger('litrover', 
                                   level=self.config.get('logging', {}).get('level', 'INFO'),
                                   log_file=self.config.get('logging', {}).get('file'))
        
        # Initialize components
        self.excel_handler = ExcelHandler(self.config)
        self.resolver = None
        self.downloader = None
        self.extractor = None
        self.annotator = None  # PDF annotator
        
        # Statistics
        self.stats = {
            'start_time': None,
            'end_time': None,
            'total_rows': 0,
            'citations_resolved': 0,
            'pdfs_downloaded': 0,
            'extractions_completed': 0,
            'pdfs_annotated': 0,
            'errors': 0,
        }
    
    def initialize_components(self):
        """Initialize resolver, downloader, and extractor"""
        print_info("Initializing components...")
        
        # Resolver
        if self.config.get('resolver', {}).get('enabled', True):
            api_key = self.config_loader.get_api_key('semantic_scholar')
            self.resolver = SemanticScholarResolver(self.config, api_key)
            print_success("Citation resolver initialized")
        
        # Downloader
        if self.config.get('downloader', {}).get('enabled', True):
            self.downloader = PDFDownloader(self.config)
            print_success("PDF downloader initialized")
        
        # Extractor
        llm_config = self.config.get('llm', {})
        provider = llm_config.get('provider')
        model = llm_config.get('model')
        api_key = self.config_loader.get_api_key(provider)
        
        if not api_key:
            raise ValueError(f"No API key found for {provider}. Please set in .env file.")
        
        self.extractor = get_extractor(provider, api_key, model, self.config)
        print_success(f"LLM extractor initialized: {provider}/{model}")
        
        # Annotator (if enabled)
        if self.config.get('extraction', {}).get('annotate_pdfs', False):
            self.annotator = PDFAnnotator()
            print_success("PDF annotator initialized")
    
    def run(self) -> Dict[str, Any]:
        """
        Execute the complete pipeline
        
        Returns:
            Statistics dictionary
        """
        self.stats['start_time'] = datetime.now()
        
        print_banner()
        print(f"\n[bold cyan]Project:[/bold cyan] {self.config['project_name']}\n")
        
        try:
            # Step 1: Load data
            print_step(1, 4, "Loading Excel data")
            df = self.excel_handler.load_excel(self.config['input_file'])
            self.stats['total_rows'] = len(df)
            print_success(f"Loaded {len(df)} rows from {self.config['input_file']}")
            
            # Step 2: Initialize components
            print_step(2, 4, "Initializing components")
            self.initialize_components()
            
            # Step 3: Process rows
            print_step(3, 4, "Processing papers")
            self._process_all_rows(df)
            
            # Step 4: Save results
            print_step(4, 4, "Saving results")
            self.stats['end_time'] = datetime.now()
            self._save_results()
            duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
            
            # Print summary
            print("\n" + "=" * 60)
            summary_data = {
                'Total Rows': self.stats['total_rows'],
                'Citations Resolved': self.stats['citations_resolved'],
                'PDFs Downloaded': self.stats['pdfs_downloaded'],
                'Extractions Completed': self.stats['extractions_completed'],
                'Errors': self.stats['errors'],
                'Duration': f"{duration:.1f}s",
            }
            
            if self.stats['pdfs_annotated'] > 0:
                summary_data['PDFs Annotated'] = self.stats['pdfs_annotated']
            
            print_summary_table(summary_data, title="Pipeline Summary")
            
            print_success(f"\nPipeline completed successfully!")
            
            return self.stats
        
        except Exception as e:
            print_error(f"Pipeline failed: {e}")
            self.logger.exception("Pipeline error")
            raise
    
    def _process_all_rows(self, df):
        """Process all rows in the DataFrame"""
        with create_progress_bar() as progress:
            task = progress.add_task(
                "[cyan]Processing rows...",
                total=len(df)
            )
            
            for idx, row in df.iterrows():
                try:
                    self._process_row(idx, row)
                    progress.update(task, advance=1)
                except Exception as e:
                    self.stats['errors'] += 1
                    print_error(f"Row {idx} error: {e}")
                    self.logger.error(f"Row {idx} error: {e}")
    
    def _process_row(self, idx: int, row):
        """
        Process a single row
        
        Args:
            idx: Row index
            row: Row data
        """
        identifier = row[self.config['columns']['identifier']]
        
        print(f"\n[bold]Row {idx}: {identifier}[/bold]")
        
        # Get paper references
        papers = self.excel_handler.get_papers_for_row(idx)
        
        if not papers:
            print_warning("No paper references found")
            return
        
        print_info(f"Found {len(papers)} paper reference(s)")
        
        # Step 1: Resolve citations
        resolutions = {}
        if self.resolver:
            for paper in papers:
                resolution = self.resolver.resolve(paper['value'])
                if resolution:
                    resolutions[paper['value']] = resolution
                    self.stats['citations_resolved'] += 1
        
        if resolutions:
            print_success(f"Resolved {len(resolutions)} citation(s)")
        
        # Step 2: Download PDFs
        pdf_paths = {}
        if self.downloader and resolutions:
            for ref, resolution in resolutions.items():
                pdf_path = self.downloader.download_from_resolution(
                    resolution, str(identifier), list(resolutions.keys()).index(ref)
                )
                if pdf_path:
                    pdf_paths[ref] = pdf_path
                    self.stats['pdfs_downloaded'] += 1
        
        if pdf_paths:
            print_success(f"Downloaded {len(pdf_paths)} PDF(s)")
        
        # Step 3: Extract metadata
        if self.extractor and pdf_paths:
            extraction_prompt = self.config_loader.get_extraction_prompt()
            request_sources = self.config.get('extraction', {}).get('request_source_refs', False)
            
            for ref, pdf_path in pdf_paths.items():
                extracted_data = self.extractor.extract_with_cache(
                    pdf_path, 
                    extraction_prompt,
                    request_sources=request_sources
                )
                
                if extracted_data:
                    # Check if extracted_data is an array (multi-core) or single object
                    cores_data = extracted_data if isinstance(extracted_data, list) else [extracted_data]
                    
                    if len(cores_data) == 0:
                        print_warning(f"No data extracted from {pdf_path.name}")
                        continue
                    
                    print_info(f"Extracted {len(cores_data)} core(s) from {pdf_path.name}")
                    
                    # Process each core
                    all_clean_data = []
                    all_source_refs = []
                    
                    for core_idx, core_data in enumerate(cores_data):
                        # Separate values from source references if present
                        clean_data = {}
                        source_refs = []
                        
                        for key, value in core_data.items():
                            if isinstance(value, dict) and 'value' in value:
                                # Format with source references
                                clean_data[key] = value['value']
                                source_refs.append({
                                    'field': key,
                                    'value': value.get('value'),
                                    'source_text': value.get('source_text'),
                                    'page': value.get('page')
                                })
                            else:
                                # Simple value format
                                clean_data[key] = value
                        
                        all_clean_data.append(clean_data)
                        all_source_refs.extend(source_refs)
                    
                    # Update Excel with extracted data
                    metadata = {
                        'extraction_timestamp': datetime.now().isoformat(),
                        'extraction_source': self.extractor.get_provider_name(),
                    }
                    
                    if len(all_clean_data) == 1:
                        # Single core - update existing row
                        metadata['confidence'] = self.extractor.estimate_confidence(all_clean_data[0])
                        self.excel_handler.update_row(idx, all_clean_data[0], metadata)
                        self.stats['extractions_completed'] += 1
                        print_success(f"Updated row {idx} with extracted data")
                    else:
                        # Multiple cores - insert new rows
                        # First, update the original row with first core
                        metadata['confidence'] = self.extractor.estimate_confidence(all_clean_data[0])
                        self.excel_handler.update_row(idx, all_clean_data[0], metadata)
                        
                        # Then insert additional rows for remaining cores
                        remaining_cores = []
                        for core_data in all_clean_data[1:]:
                            core_metadata = metadata.copy()
                            core_metadata['confidence'] = self.extractor.estimate_confidence(core_data)
                            remaining_cores.append({**core_data, **core_metadata})
                        
                        self.excel_handler.insert_rows_after(idx, remaining_cores)
                        self.stats['extractions_completed'] += len(all_clean_data)
                        print_success(f"Inserted {len(all_clean_data)} rows for multiple cores")
                    
                    # Step 4: Annotate PDF (if enabled and sources were provided)
                    if self.annotator and all_source_refs:
                        annotation_dir = Path(self.config.get('extraction', {}).get(
                            'annotation_dir', 'annotated_papers'
                        ))
                        annotation_dir.mkdir(parents=True, exist_ok=True)
                        
                        # Prepare data for annotation (combine all cores for same PDF)
                        annotation_data = [{
                            'identifier': str(identifier),
                            **{sr['field']: {'value': sr['value'], 'source_text': sr['source_text'], 'page': sr['page']} 
                               for sr in all_source_refs}
                        }]
                        
                        output_path = annotation_dir / f"annotated_{pdf_path.name}"
                        add_legend = self.config.get('extraction', {}).get('include_legend', False)  # Disable legend due to font issues
                        
                        if self.annotator.annotate_pdf(pdf_path, annotation_data, output_path, add_legend):
                            self.stats['pdfs_annotated'] += 1
    
    def _save_results(self):
        """Save results to output file"""
        output_dir = Path(self.config.get('output_dir', 'outputs'))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create output filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f"results_{timestamp}.xlsx"
        
        # Save Excel
        self.excel_handler.save_excel(
            output_file,
            create_backup=self.config.get('output', {}).get('create_backup', True)
        )
        
        print_success(f"Results saved to: {output_file}")
        
        # Save statistics
        stats_file = output_dir / f"stats_{timestamp}.json"
        import json
        with open(stats_file, 'w') as f:
            # Convert datetime to string
            stats_copy = self.stats.copy()
            stats_copy['start_time'] = stats_copy['start_time'].isoformat()
            stats_copy['end_time'] = stats_copy['end_time'].isoformat()
            json.dump(stats_copy, f, indent=2)
        
        print_info(f"Statistics saved to: {stats_file}")
