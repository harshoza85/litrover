"""Orchestration modules for LitRover"""

from litrover.orchestrators.cli_orchestrator import CLIOrchestrator
from litrover.orchestrators.interactive import InteractiveOrchestrator

# Optional orchestrators (require additional dependencies)
try:
    from litrover.orchestrators.langgraph_orchestrator import LangGraphOrchestrator
except ImportError:
    LangGraphOrchestrator = None

try:
    from litrover.orchestrators.autogen_orchestrator import AutoGenOrchestrator, SimpleAutoGenOrchestrator
except ImportError:
    AutoGenOrchestrator = None
    SimpleAutoGenOrchestrator = None

__all__ = [
    "CLIOrchestrator",
    "InteractiveOrchestrator",
    "LangGraphOrchestrator",
    "AutoGenOrchestrator",
    "SimpleAutoGenOrchestrator",
]
