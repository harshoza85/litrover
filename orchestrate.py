#!/usr/bin/env python3
"""
LitRover Main Orchestrator
Entry point for running the literature processing pipeline
"""

import click
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from litrover.utils import (
    load_config, print_banner, print_success, print_error,
    print_warning, print_info, console
)
from litrover.utils.logger import setup_logger
from litrover.orchestrators import (
    CLIOrchestrator, InteractiveOrchestrator,
    LangGraphOrchestrator, SimpleAutoGenOrchestrator
)


@click.group()
def cli():
    """LitRover: Agentic AI Literature Processing System"""
    pass


@cli.command()
@click.option('--config', '-c', required=True, type=click.Path(exists=True),
              help='Path to configuration file')
@click.option('--mode', '-m', 
              type=click.Choice(['auto', 'interactive'], case_sensitive=False),
              default='auto',
              help='Execution mode: auto (automated) or interactive (step-by-step)')
@click.option('--orchestrator', '-o',
              type=click.Choice(['cli', 'interactive', 'langgraph', 'autogen'], case_sensitive=False),
              default='cli',
              help='Orchestrator type')
def run(config, mode, orchestrator):
    """Run the literature processing pipeline"""
    
    print_banner()
    
    try:
        # Load configuration
        print_info(f"Loading configuration: {config}")
        config_loader = load_config(config)
        
        # Validate API keys
        api_keys = config_loader.validate_api_keys()
        provider = config_loader.get('llm.provider')
        
        if not api_keys.get(provider):
            print_error(f"API key for {provider} not found!")
            print_info("Please set API keys in .env file")
            print_info("Copy config/.env.example to .env and fill in your keys")
            sys.exit(1)
        
        print_success("Configuration loaded")
        print_info(f"Provider: {provider}")
        print_info(f"Model: {config_loader.get('llm.model')}")
        
        # Select orchestrator
        if mode == 'interactive' or orchestrator == 'interactive':
            orch = InteractiveOrchestrator(config_loader)
        
        elif orchestrator == 'langgraph':
            if LangGraphOrchestrator is None:
                print_error("LangGraph not installed. Install with: pip install langgraph")
                sys.exit(1)
            orch = LangGraphOrchestrator(config_loader)
        
        elif orchestrator == 'autogen':
            if SimpleAutoGenOrchestrator is None:
                print_error("AutoGen not installed. Install with: pip install pyautogen")
                sys.exit(1)
            print_info("Using simplified AutoGen (direct execution)")
            orch = SimpleAutoGenOrchestrator(config_loader)
        
        else:  # cli / auto
            orch = CLIOrchestrator(config_loader)
        
        # Run orchestrator
        print_info(f"Starting {orchestrator} orchestrator...")
        stats = orch.run()
        
        if stats:
            print_success("\n🎉 Pipeline completed successfully!")
        
    except KeyboardInterrupt:
        print_warning("\nPipeline cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\nPipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.argument('project_name')
def setup(project_name):
    """Create a new project (wrapper for setup_project.py)"""
    print_info(f"Setting up project: {project_name}")
    print_info("Please run: python setup_project.py")


@cli.command()
@click.option('--config', '-c', required=True, type=click.Path(exists=True))
def validate(config):
    """Validate configuration file"""
    try:
        config_loader = load_config(config)
        print_success("✓ Configuration is valid")
        
        # Check API keys
        api_keys = config_loader.validate_api_keys()
        console.print("\n[bold]API Key Status:[/bold]")
        for provider, available in api_keys.items():
            status = "✓" if available else "✗"
            color = "green" if available else "red"
            console.print(f"  {status} [{color}]{provider}[/{color}]")
        
        # Check input file
        input_file = Path(config_loader.get('input_file'))
        if input_file.exists():
            print_success(f"✓ Input file exists: {input_file}")
        else:
            print_warning(f"✗ Input file not found: {input_file}")
        
        # Show extraction schema
        schema = config_loader.get('extraction_schema', [])
        console.print(f"\n[bold]Extraction Schema ({len(schema)} fields):[/bold]")
        for field in schema:
            console.print(f"  • {field['field']} ({field['type']}): {field['description']}")
        
    except Exception as e:
        print_error(f"Validation failed: {e}")
        sys.exit(1)


@cli.command()
@click.option('--config', '-c', required=True, type=click.Path(exists=True))
def info(config):
    """Show project information"""
    try:
        config_loader = load_config(config)
        
        console.print(f"\n[bold cyan]Project Information[/bold cyan]\n")
        console.print(f"[bold]Name:[/bold] {config_loader.get('project_name')}")
        console.print(f"[bold]Input File:[/bold] {config_loader.get('input_file')}")
        console.print(f"[bold]Output Dir:[/bold] {config_loader.get('output_dir')}")
        console.print(f"[bold]LLM Provider:[/bold] {config_loader.get('llm.provider')}")
        console.print(f"[bold]Model:[/bold] {config_loader.get('llm.model')}")
        
        # Show column mapping
        console.print(f"\n[bold]Column Mapping:[/bold]")
        console.print(f"  Identifier: {config_loader.get('columns.identifier')}")
        console.print(f"  Paper References: {', '.join(config_loader.get('columns.paper_refs'))}")
        
        # Show schema
        schema = config_loader.get('extraction_schema', [])
        console.print(f"\n[bold]Extraction Schema ({len(schema)} fields):[/bold]")
        for field in schema:
            console.print(f"  • {field['field']} ({field['type']})")
        
    except Exception as e:
        print_error(f"Failed to load project info: {e}")
        sys.exit(1)


@cli.command()
def version():
    """Show version information"""
    from litrover import __version__
    console.print(f"\n[bold cyan]LitRover[/bold cyan] version [bold]{__version__}[/bold]")
    console.print("\nAgentic AI System for Literature Processing")
    console.print("https://github.com/yourusername/litrover\n")


if __name__ == '__main__':
    cli()
