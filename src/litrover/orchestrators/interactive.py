"""
Interactive Orchestrator for LitRover
Step-by-step execution with user confirmations
"""

import questionary
from pathlib import Path
from .cli_orchestrator import CLIOrchestrator
from ..utils import print_info, print_success, print_warning, console


class InteractiveOrchestrator(CLIOrchestrator):
    """
    Interactive orchestrator with step-by-step confirmations
    
    Extends CLIOrchestrator with interactive prompts at each stage
    """
    
    def run(self):
        """Execute pipeline with interactive prompts"""
        console.print("\n[bold cyan]Interactive Mode[/bold cyan]")
        console.print("You'll be prompted at each step.\n")
        
        # Load data
        if not questionary.confirm("Load Excel data?", default=True).ask():
            console.print("[yellow]Cancelled[/yellow]")
            return None
        
        print_info(f"Loading: {self.config['input_file']}")
        df = self.excel_handler.load_excel(self.config['input_file'])
        print_success(f"Loaded {len(df)} rows")
        
        # Initialize components
        if not questionary.confirm("\nInitialize components?", default=True).ask():
            console.print("[yellow]Cancelled[/yellow]")
            return None
        
        self.initialize_components()
        
        # Ask which steps to run
        steps = questionary.checkbox(
            "\nWhich steps do you want to run?",
            choices=[
                "Resolve citations",
                "Download PDFs",
                "Extract metadata"
            ],
            default=["Resolve citations", "Download PDFs", "Extract metadata"]
        ).ask()
        
        run_resolve = "Resolve citations" in steps
        run_download = "Download PDFs" in steps
        run_extract = "Extract metadata" in steps
        
        # Ask about row range
        process_all = questionary.confirm(
            f"\nProcess all {len(df)} rows?",
            default=True
        ).ask()
        
        if not process_all:
            start_row = int(questionary.text(
                "Start row (0-indexed):",
                default="0"
            ).ask())
            
            end_row = int(questionary.text(
                f"End row (max {len(df)-1}):",
                default=str(min(9, len(df)-1))
            ).ask())
            
            df = df.iloc[start_row:end_row+1]
            console.print(f"[cyan]Processing rows {start_row} to {end_row}[/cyan]")
        
        # Process rows
        console.print(f"\n[bold]Processing {len(df)} rows...[/bold]\n")
        
        for idx, row in df.iterrows():
            identifier = row[self.config['columns']['identifier']]
            
            console.print(f"\n[bold cyan]Row {idx}: {identifier}[/bold cyan]")
            
            # Get papers
            papers = self.excel_handler.get_papers_for_row(idx)
            if not papers:
                print_warning("No papers found")
                continue
            
            console.print(f"Found {len(papers)} paper(s):")
            for i, paper in enumerate(papers, 1):
                console.print(f"  {i}. {paper['value'][:70]}...")
            
            # Resolve
            resolutions = {}
            if run_resolve:
                if questionary.confirm("  Resolve citations?", default=True).ask():
                    for paper in papers:
                        resolution = self.resolver.resolve(paper['value'])
                        if resolution:
                            resolutions[paper['value']] = resolution
                            console.print(f"    ✓ Resolved: {resolution.get('title', 'Unknown')[:50]}")
            
            # Download
            pdf_paths = {}
            if run_download and resolutions:
                if questionary.confirm("  Download PDFs?", default=True).ask():
                    for ref, resolution in resolutions.items():
                        pdf_path = self.downloader.download_from_resolution(
                            resolution, str(identifier), list(resolutions.keys()).index(ref)
                        )
                        if pdf_path:
                            pdf_paths[ref] = pdf_path
            
            # Extract
            if run_extract and pdf_paths:
                if questionary.confirm("  Extract metadata?", default=True).ask():
                    extraction_prompt = self.config_loader.get_extraction_prompt()
                    
                    for ref, pdf_path in pdf_paths.items():
                        extracted_data = self.extractor.extract_with_cache(pdf_path, extraction_prompt)
                        
                        if extracted_data:
                            # Show extracted data
                            console.print("\n  [green]Extracted data:[/green]")
                            for key, value in extracted_data.items():
                                if value is not None:
                                    console.print(f"    • {key}: {value}")
                            
                            # Ask to save
                            if questionary.confirm("    Save this data?", default=True).ask():
                                from datetime import datetime
                                metadata = {
                                    'extraction_timestamp': datetime.now().isoformat(),
                                    'extraction_source': self.extractor.get_provider_name(),
                                    'confidence': self.extractor.estimate_confidence(extracted_data)
                                }
                                self.excel_handler.update_row(idx, extracted_data, metadata)
                                self.stats['extractions_completed'] += 1
        
        # Save results
        if questionary.confirm("\nSave results?", default=True).ask():
            self._save_results()
            print_success("Results saved!")
        
        console.print("\n[bold green]Interactive session complete![/bold green]\n")
        return self.stats
