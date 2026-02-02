# Contributing to LitRover

Thank you for your interest in contributing to LitRover! This document provides guidelines for contributing to the project.

## 🤝 How to Contribute

### Reporting Bugs

If you find a bug, please create an issue on GitHub with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Python version, LLM provider)
- Relevant logs or error messages

### Suggesting Features

Feature requests are welcome! Please:
- Check existing issues to avoid duplicates
- Clearly describe the use case
- Explain how it benefits users
- Consider implementation complexity

### Pull Requests

1. **Fork the repository**
   ```bash
   git clone https://github.com/harshoza/litrover.git
   cd litrover
   git checkout -b feature/your-feature-name
   ```

2. **Set up development environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -e .
   ```

3. **Make your changes**
   - Follow existing code style
   - Add tests if applicable
   - Update documentation
   - Keep commits focused and atomic

4. **Test your changes**
   ```bash
   # Run the pipeline with example config
   python orchestrate.py run --config config/example.yaml
   
   # Test with different LLM providers if possible
   ```

5. **Submit pull request**
   - Write clear PR description
   - Reference related issues
   - Explain what changed and why

## 📝 Code Style

- **Python**: Follow PEP 8
- **Formatting**: Use `black` for code formatting
- **Imports**: Group stdlib, third-party, and local imports
- **Docstrings**: Use Google-style docstrings
- **Type hints**: Add type hints where helpful

Example:
```python
def extract_metadata(
    pdf_path: Path,
    schema: List[Dict[str, Any]],
    llm_provider: str = "gemini"
) -> Dict[str, Any]:
    """
    Extract metadata from PDF using LLM.
    
    Args:
        pdf_path: Path to PDF file
        schema: Extraction schema definition
        llm_provider: LLM provider to use
        
    Returns:
        Dictionary of extracted metadata
        
    Raises:
        FileNotFoundError: If PDF doesn't exist
        ExtractionError: If extraction fails
    """
    pass
```

## 🏗️ Project Structure

```
litrover/
├── src/litrover/          # Main package
│   ├── core/              # Core functionality
│   │   ├── extractors/    # LLM extractors
│   │   ├── annotators/    # PDF annotation
│   │   └── downloaders/   # PDF download
│   ├── orchestrators/     # Pipeline orchestration
│   └── utils/             # Utilities
├── config/                # Configuration files
├── examples/              # Example projects
├── docs/                  # Documentation
└── tests/                 # Test suite
```

## 🧪 Adding New Features

### Adding a New LLM Provider

1. Create new extractor in `src/litrover/core/extractors/`
2. Inherit from `BaseExtractor`
3. Implement required methods
4. Add provider to config schema
5. Update documentation

### Adding a New Orchestrator

1. Create new orchestrator in `src/litrover/orchestrators/`
2. Inherit from base orchestrator if applicable
3. Implement workflow logic
4. Add CLI option in `orchestrate.py`
5. Document usage

### Adding New Extraction Fields

1. Update schema in config file
2. Test with various papers
3. Document field purpose and examples
4. Add to example configs

## 📚 Documentation

- Update README.md for user-facing changes
- Add docstrings to new functions/classes
- Create examples for new features
- Update relevant docs/ files

## 🐛 Testing

While we don't have formal unit tests yet, please:
- Test with multiple papers
- Try different LLM providers
- Verify edge cases
- Check error handling

## 🔒 Security

- Never commit API keys or credentials
- Use `.env` for sensitive data
- Review `.gitignore` before committing
- Report security issues privately to harshoza85@gmail.com

## 📋 Checklist

Before submitting a PR:
- [ ] Code follows project style
- [ ] Documentation updated
- [ ] Tested with example config
- [ ] No API keys or sensitive data
- [ ] Commits are clear and focused
- [ ] PR description is complete

## 💡 Ideas for Contributions

Looking for ideas? Here are some areas that need work:

### High Priority
- Add unit tests and test suite
- Improve error handling and recovery
- Add support for more LLM providers
- Optimize token usage and costs
- Better handling of large multi-record papers

### Medium Priority
- Web UI for configuration
- Batch processing improvements
- Export to more formats (JSON, CSV)
- Integration with reference managers
- Docker containerization

### Documentation
- Video tutorials
- More domain-specific examples
- API documentation
- Troubleshooting guide

## 🙏 Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help others learn and grow

## 📧 Questions?

- Open a GitHub Discussion
- Email: harshoza85@gmail.com
- Check existing issues and docs

Thank you for contributing to LitRover! 🚀
