"""
Interactive setup wizard for LitRover projects
Helps users create configuration files through guided prompts
"""

import questionary
from pathlib import Path
import yaml
from rich.console import Console
from rich.panel import Panel

console = Console()


def create_project_setup():
    """Run interactive setup wizard"""
    
    console.print("\n")
    console.print(Panel.fit(
        "[bold cyan]🔍 LitRover Project Setup Wizard[/bold cyan]\n"
        "Let's configure your literature survey project!",
        border_style="cyan"
    ))
    
    # Project name
    project_name = questionary.text(
        "What is your project name?",
        default="My Literature Survey"
    ).ask()
    
    # Extraction schema
    console.print("\n[bold]Define Extraction Schema[/bold]")
    console.print("What fields do you want to extract from papers?")
    console.print("[dim]Enter field names separated by commas[/dim]")
    console.print("[dim]Example: author, year, sample_size, methodology, findings[/dim]\n")
    
    fields_input = questionary.text(
        "Fields to extract:",
        default="author, publication_year, sample_size, methodology, key_findings"
    ).ask()
    
    fields = [f.strip() for f in fields_input.split(',')]
    
    # Build schema interactively
    schema = []
    console.print(f"\n[bold]Configure {len(fields)} fields:[/bold]\n")
    
    for field in fields:
        console.print(f"[cyan]Field: {field}[/cyan]")
        
        field_type = questionary.select(
            f"  Type for '{field}':",
            choices=['text', 'number', 'boolean']
        ).ask()
        
        description = questionary.text(
            f"  Description for '{field}':",
            default=f"{field.replace('_', ' ').title()}"
        ).ask()
        
        schema.append({
            'field': field,
            'type': field_type,
            'description': description
        })
        console.print()
    
    # Excel configuration
    console.print("[bold]Excel Configuration[/bold]\n")
    
    has_excel = questionary.confirm(
        "Do you already have an Excel file with paper references?",
        default=False
    ).ask()
    
    if has_excel:
        excel_path = questionary.path(
            "Path to your Excel file:",
            default="data/papers.xlsx"
        ).ask()
        
        identifier_col = questionary.text(
            "What column contains unique identifiers? (e.g., 'Paper_ID', 'Study_Name')",
            default="Paper_ID"
        ).ask()
        
        paper_refs_input = questionary.text(
            "Which columns contain paper references?\n(Enter comma-separated, e.g., 'Reference, Citation_1, Citation_2')",
            default="Primary_Reference, Supporting_Ref_1, Supporting_Ref_2"
        ).ask()
        
        paper_refs = [c.strip() for c in paper_refs_input.split(',')]
        
        create_template = False
    else:
        excel_path = "data/papers.xlsx"
        identifier_col = questionary.text(
            "What should we call the identifier column?",
            default="Paper_ID"
        ).ask()
        
        num_ref_cols = questionary.text(
            "How many reference columns do you need?",
            default="3"
        ).ask()
        
        paper_refs = [f"Reference_{i+1}" for i in range(int(num_ref_cols))]
        create_template = True
    
    # LLM Configuration
    console.print("\n[bold]LLM Provider Configuration[/bold]\n")
    
    provider = questionary.select(
        "Which LLM provider do you want to use?",
        choices=[
            'gemini (Google - Fast & Affordable)',
            'claude (Anthropic - High Quality)',
            'openai (GPT-4 - Versatile)'
        ]
    ).ask().split()[0]
    
    # Model selection based on provider
    model_choices = {
        'gemini': ['gemini-2.0-flash-exp (Recommended)', 'gemini-1.5-pro'],
        'claude': ['claude-sonnet-4-20250514 (Recommended)', 'claude-opus-4-20250514'],
        'openai': ['gpt-4o (Recommended)', 'gpt-4-turbo', 'gpt-4o-mini']
    }
    
    model = questionary.select(
        f"Which {provider} model?",
        choices=model_choices[provider]
    ).ask().split()[0]
    
    # Output directory
    output_dir = questionary.text(
        "Output directory for results:",
        default="outputs/"
    ).ask()
    
    # Build configuration
    config = {
        'project_name': project_name,
        'input_file': excel_path,
        'output_dir': output_dir,
        'extraction_schema': schema,
        'columns': {
            'identifier': identifier_col,
            'paper_refs': paper_refs,
            'preserve_columns': []
        },
        'llm': {
            'provider': provider,
            'model': model,
            'temperature': 0.1,
            'max_tokens': 4000,
            'max_retries': 3,
            'retry_delay': 2
        },
        'resolver': {
            'enabled': True,
            'cache_results': True,
            'semantic_scholar': {
                'enabled': True,
                'timeout': 15,
                'max_results': 10
            },
            'rate_limit_delay': 1.0
        },
        'downloader': {
            'enabled': True,
            'skip_existing': True,
            'timeout': 60,
            'max_retries': 3,
            'pdf_dir': 'papers/',
            'respect_robots_txt': True
        },
        'extraction': {
            'batch_size': 10,
            'cache_enabled': True,
            'cache_dir': 'extracted/',
            'validate_output': True,
            'confidence_threshold': 0.7
        },
        'output': {
            'format': 'xlsx',
            'include_timestamps': True,
            'include_sources': True,
            'create_backup': True,
            'backup_dir': 'backups/'
        },
        'logging': {
            'level': 'INFO',
            'file': 'litrover.log',
            'console': True
        }
    }
    
    # Save configuration
    config_dir = Path('config')
    config_dir.mkdir(exist_ok=True)
    
    # Sanitize project name for filename
    safe_name = project_name.lower().replace(' ', '_').replace('/', '_')
    config_path = config_dir / f"{safe_name}.yaml"
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    console.print(f"\n[green]✓ Configuration saved to: {config_path}[/green]")
    
    # Create Excel template if needed
    if create_template:
        from ..utils.excel_handler import ExcelHandler
        
        data_dir = Path('data')
        data_dir.mkdir(exist_ok=True)
        
        excel_handler = ExcelHandler(config)
        excel_handler.create_template(excel_path, schema)
        
        console.print(f"[green]✓ Excel template created: {excel_path}[/green]")
    
    # Next steps
    console.print("\n")
    console.print(Panel.fit(
        "[bold green]Setup Complete![/bold green]\n\n"
        f"[bold]Next Steps:[/bold]\n"
        f"1. {'Fill in ' + excel_path if create_template else 'Your Excel file is ready'}\n"
        f"2. Set up API keys in .env file (copy from config/.env.example)\n"
        f"3. Run: [cyan]python orchestrate.py --config {config_path}[/cyan]\n\n"
        f"[dim]For help: python orchestrate.py --help[/dim]",
        border_style="green"
    ))
    
    return config_path


def main():
    """Main entry point for setup wizard"""
    try:
        config_path = create_project_setup()
        return str(config_path)
    except KeyboardInterrupt:
        console.print("\n[yellow]Setup cancelled[/yellow]")
        return None


if __name__ == "__main__":
    main()
