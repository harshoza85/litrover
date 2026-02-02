"""
Logging utility for LitRover
Provides consistent logging with Rich console output
"""

import logging
import sys
from pathlib import Path
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.table import Table

console = Console()


def setup_logger(name: str, level: str = "INFO", log_file: str = None):
    """
    Set up logger with Rich handler for beautiful console output
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file path for logging
    
    Returns:
        logging.Logger: Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    logger.handlers = []
    
    # Console handler with Rich
    console_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=False,
        markup=True,
        rich_tracebacks=True,
    )
    console_handler.setLevel(getattr(logging, level.upper()))
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def print_banner():
    """Print LitRover banner"""
    banner = """
    ╔═══════════════════════════════════════════════╗
    ║         🔍 LitRover v1.0                      ║
    ║   Agentic AI Literature Processing System     ║
    ╚═══════════════════════════════════════════════╝
    """
    console.print(banner, style="bold blue")


def print_step(step_num: int, total_steps: int, description: str):
    """Print step header"""
    console.print(f"\n[bold cyan]Step {step_num}/{total_steps}:[/bold cyan] {description}")


def print_success(message: str):
    """Print success message"""
    console.print(f"✓ [green]{message}[/green]")


def print_error(message: str):
    """Print error message"""
    console.print(f"✗ [red]{message}[/red]")


def print_warning(message: str):
    """Print warning message"""
    console.print(f"⚠ [yellow]{message}[/yellow]")


def print_info(message: str):
    """Print info message"""
    console.print(f"ℹ [blue]{message}[/blue]")


def create_progress_bar():
    """Create a Rich progress bar"""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    )


def print_summary_table(data: dict, title: str = "Summary"):
    """
    Print a summary table
    
    Args:
        data: Dictionary of key-value pairs
        title: Table title
    """
    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    for key, value in data.items():
        table.add_row(key, str(value))
    
    console.print(table)


def print_config_panel(config: dict, title: str = "Configuration"):
    """
    Print configuration in a panel
    
    Args:
        config: Configuration dictionary
        title: Panel title
    """
    import yaml
    config_str = yaml.dump(config, default_flow_style=False, sort_keys=False)
    panel = Panel(config_str, title=title, border_style="blue")
    console.print(panel)


# Export Rich console for direct use
__all__ = [
    "setup_logger",
    "console",
    "print_banner",
    "print_step",
    "print_success",
    "print_error",
    "print_warning",
    "print_info",
    "create_progress_bar",
    "print_summary_table",
    "print_config_panel",
]
