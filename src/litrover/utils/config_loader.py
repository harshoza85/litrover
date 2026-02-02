"""
Configuration loader for LitRover
Handles YAML config files and environment variables
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import jsonschema
from jsonschema import validate

# Config schema for validation
CONFIG_SCHEMA = {
    "type": "object",
    "required": ["project_name", "input_file", "extraction_schema", "columns", "llm"],
    "properties": {
        "project_name": {"type": "string"},
        "input_file": {"type": "string"},
        "output_dir": {"type": "string"},
        "extraction_schema": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["field", "type", "description"],
                "properties": {
                    "field": {"type": "string"},
                    "type": {"type": "string", "enum": ["text", "number", "boolean", "array"]},
                    "description": {"type": "string"}
                }
            }
        },
        "columns": {
            "type": "object",
            "required": ["identifier", "paper_refs"],
            "properties": {
                "identifier": {"type": "string"},
                "paper_refs": {"type": "array", "items": {"type": "string"}}
            }
        },
        "llm": {
            "type": "object",
            "required": ["provider", "model"],
            "properties": {
                "provider": {"type": "string", "enum": ["gemini", "claude", "openai"]},
                "model": {"type": "string"},
                "temperature": {"type": "number"},
                "max_tokens": {"type": "integer"}
            }
        }
    }
}


class ConfigLoader:
    """Load and validate configuration files"""
    
    def __init__(self, config_path: str = None):
        """
        Initialize config loader
        
        Args:
            config_path: Path to YAML config file
        """
        self.config_path = Path(config_path) if config_path else None
        self.config = {}
        self.env_loaded = False
        
    def load_env(self, env_file: str = ".env"):
        """
        Load environment variables from .env file
        
        Args:
            env_file: Path to .env file
        """
        env_path = Path(env_file)
        if env_path.exists():
            load_dotenv(env_path)
            self.env_loaded = True
        else:
            # Try to find .env in parent directories
            current = Path.cwd()
            for parent in [current] + list(current.parents):
                env_path = parent / ".env"
                if env_path.exists():
                    load_dotenv(env_path)
                    self.env_loaded = True
                    break
    
    def load_config(self, config_path: str = None) -> Dict[str, Any]:
        """
        Load YAML configuration file
        
        Args:
            config_path: Path to config file (overrides constructor path)
            
        Returns:
            Configuration dictionary
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            jsonschema.ValidationError: If config is invalid
        """
        if config_path:
            self.config_path = Path(config_path)
        
        if not self.config_path or not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Validate against schema
        try:
            validate(instance=self.config, schema=CONFIG_SCHEMA)
        except jsonschema.ValidationError as e:
            raise ValueError(f"Invalid configuration: {e.message}")
        
        # Set defaults for optional fields
        self.config.setdefault('output_dir', 'outputs/')
        self.config.setdefault('resolver', {'enabled': True})
        self.config.setdefault('downloader', {'enabled': True})
        self.config.setdefault('logging', {'level': 'INFO'})
        
        return self.config
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            key: Configuration key (supports dot notation, e.g., 'llm.provider')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """
        Get API key for specified provider from environment
        
        Args:
            provider: Provider name ('gemini', 'claude', 'openai')
            
        Returns:
            API key or None if not found
        """
        if not self.env_loaded:
            self.load_env()
        
        key_mapping = {
            'gemini': ['GEMINI_API_KEY', 'GOOGLE_API_KEY'],
            'claude': ['ANTHROPIC_API_KEY', 'CLAUDE_API_KEY'],
            'openai': ['OPENAI_API_KEY'],
            'semantic_scholar': ['SEMANTIC_SCHOLAR_API_KEY'],
        }
        
        for env_var in key_mapping.get(provider, []):
            api_key = os.getenv(env_var)
            if api_key:
                return api_key
        
        return None
    
    def validate_api_keys(self) -> Dict[str, bool]:
        """
        Check which API keys are available
        
        Returns:
            Dictionary of provider -> key_available
        """
        return {
            'gemini': self.get_api_key('gemini') is not None,
            'claude': self.get_api_key('claude') is not None,
            'openai': self.get_api_key('openai') is not None,
            'semantic_scholar': self.get_api_key('semantic_scholar') is not None,
        }
    
    def get_extraction_prompt(self) -> str:
        """
        Generate extraction prompt from schema
        
        Returns:
            Formatted prompt for LLM
        """
        schema = self.config.get('extraction_schema', [])
        request_sources = self.config.get('extraction', {}).get('request_source_refs', False)
        
        if request_sources:
            # Generate prompt with source reference requirements
            prompt = """You are analyzing a scientific paper to extract specific metadata.

IMPORTANT: If the paper describes MULTIPLE cores, sites, or samples, extract information for EACH ONE separately.
Return an ARRAY of records, one for each core/site/sample.

Extract the following information AND provide the exact source text from the paper for each value.

For each field, extract:

"""
            for i, field in enumerate(schema, 1):
                field_name = field['field']
                field_type = field['type']
                description = field['description']
                
                prompt += f"{i}. **{field_name}** ({field_type}): {description}\n"
            
            prompt += """

CRITICAL: For EACH extracted value, also provide:
- "source_text": The EXACT quote (5-30 words) from the paper where you found this info
- "page": The page number (1-indexed) where the quote appears

MULTI-CORE EXTRACTION:
- If the paper has MULTIPLE cores/sites/samples, return an ARRAY: [{core1}, {core2}, ...]
- If the paper has only ONE core/site, return an ARRAY with one element: [{core1}]
- Each core should have ALL fields filled in with its specific data

Respond ONLY with valid JSON. Example format for MULTIPLE cores:
```json
[
  {
"""
            
            for field in schema:
                field_name = field['field']
                field_type = field['type']
                
                if field_type == "text":
                    example = '{"value": "Core A sediment", "source_text": "quoted from paper", "page": 3}'
                elif field_type == "number":
                    example = '{"value": 45.2, "source_text": "Core A at 45.2°N", "page": 5}'
                elif field_type == "boolean":
                    example = '{"value": true, "source_text": "marine environment", "page": 2}'
                else:
                    example = '{"value": [], "source_text": "list items", "page": 4}'
                
                prompt += f'    "{field_name}": {example},\n'
            
            prompt = prompt.rstrip(',\n') + '\n  },\n  {\n'
            
            # Add second core example
            for field in schema:
                field_name = field['field']
                field_type = field['type']
                
                if field_type == "text":
                    example = '{"value": "Core B sediment", "source_text": "quoted from paper", "page": 8}'
                elif field_type == "number":
                    example = '{"value": 46.8, "source_text": "Core B at 46.8°N", "page": 8}'
                elif field_type == "boolean":
                    example = '{"value": true, "source_text": "marine environment", "page": 2}'
                else:
                    example = '{"value": [], "source_text": "list items", "page": 4}'
                
                prompt += f'    "{field_name}": {example},\n'
            
            prompt = prompt.rstrip(',\n') + '\n  }\n]\n```\n\nIf a value is not found, use: {"value": null, "source_text": null, "page": null}\nIf the paper doesn\'t contain relevant information, return an empty array: []'
        
        else:
            # Original prompt without source references
            prompt = """You are analyzing a scientific paper to extract specific metadata.
Extract the following information from this paper. Only extract information that is explicitly stated.
If information is not found, use null.

For each field, extract:

"""
            
            for i, field in enumerate(schema, 1):
                field_name = field['field']
                field_type = field['type']
                description = field['description']
                
                prompt += f"{i}. **{field_name}** ({field_type}): {description}\n"
            
            prompt += """

Respond ONLY with valid JSON. Example format:
```json
{
"""
            
            for field in schema:
                field_name = field['field']
                field_type = field['type']
                
                if field_type == "text":
                    example = '"example text"'
                elif field_type == "number":
                    example = '123'
                elif field_type == "boolean":
                    example = 'true'
                else:
                    example = '[]'
                
                prompt += f'  "{field_name}": {example},\n'
            
            prompt = prompt.rstrip(',\n') + '\n}\n```\n\nIf the paper doesn\'t contain relevant information, return an empty object: {}'
        
        return prompt
    
    def save_config(self, output_path: str = None):
        """
        Save configuration to YAML file
        
        Args:
            output_path: Output file path (defaults to original config_path)
        """
        output_path = Path(output_path) if output_path else self.config_path
        
        if not output_path:
            raise ValueError("No output path specified")
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)


def load_config(config_path: str) -> ConfigLoader:
    """
    Convenience function to load configuration
    
    Args:
        config_path: Path to config file
        
    Returns:
        ConfigLoader instance
    """
    loader = ConfigLoader(config_path)
    loader.load_env()
    loader.load_config()
    return loader
