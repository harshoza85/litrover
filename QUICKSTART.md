# Quick Start Guide

Get LitRover up and running in 5 minutes!

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- API key for at least one LLM provider (Gemini, Claude, or OpenAI)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/harshoza/litrover.git
cd litrover
```

### 2. Install Dependencies

```bash
# Option A: Using pip
pip install -r requirements.txt

# Option B: Install as package (recommended for development)
pip install -e .
```

### 3. Set Up API Keys

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API key(s)
nano .env  # or use your preferred editor
```

Add at least one API key:
```bash
GEMINI_API_KEY=your_actual_api_key_here
```

**Get API Keys:**
- Gemini: https://ai.google.dev/
- Claude: https://www.anthropic.com/
- OpenAI: https://platform.openai.com/

## First Run

### Option 1: Use Example Configuration

```bash
# Copy the example config
cp config/example.yaml config/my_project.yaml

# Edit to customize for your domain
nano config/my_project.yaml

# Create input Excel file
# See examples/geological_survey/input.xlsx for format

# Run the pipeline
python orchestrate.py run --config config/my_project.yaml
```

### Option 2: Interactive Setup Wizard

```bash
# Run the setup wizard
python setup_project.py

# Follow the prompts to:
# - Name your project
# - Define extraction fields
# - Configure Excel columns
# - Choose LLM provider

# This creates:
# - config/your_project.yaml
# - data/template.xlsx
```

## Input File Format

Your Excel file should have:

| Paper_ID | DOI or Reference | Notes |
|----------|------------------|-------|
| 1 | https://doi.org/10.1234/example | Optional notes |
| 2 | Smith et al., 2023 | Another paper |

**Required columns:**
- Identifier column (e.g., "Paper_ID")
- At least one reference column (DOI, URL, or citation)

## Running the Pipeline

### Basic Usage

```bash
python orchestrate.py run --config config/your_project.yaml
```

### Advanced Options

```bash
# Interactive mode (step-by-step)
python orchestrate.py run --config config/your_project.yaml --mode interactive

# Use different orchestrator
python orchestrate.py run --config config/your_project.yaml --orchestrator langgraph

# Validate configuration
python orchestrate.py validate --config config/your_project.yaml

# View project info
python orchestrate.py info --config config/your_project.yaml
```

## Output

After running, you'll find:

```
outputs/your_project/
├── results_YYYYMMDD_HHMMSS.xlsx    # Extracted data
├── stats_YYYYMMDD_HHMMSS.json      # Pipeline statistics
└── logs/                            # Execution logs

annotated_papers/your_project/
└── annotated_*.pdf                  # PDFs with highlighted sources

papers/your_project/
└── *.pdf                            # Downloaded PDFs
```

## Troubleshooting

### API Key Not Found
```
Error: API key for gemini not found!
```
**Solution**: Check that `.env` file exists and contains valid API key

### PDF Download Failed
```
Error: Failed to download PDF
```
**Solution**: 
- Check if DOI is valid
- Try alternative reference format
- Some publishers require institutional access

### Extraction Failed
```
Error: JSON parse error
```
**Solution**:
- Paper may be too large (>100 pages)
- Try reducing extraction schema
- Check LLM provider quota

### Rate Limit Exceeded
```
Error: 429 Rate limit exceeded
```
**Solution**:
- Wait a few minutes
- Reduce `rate_limits.requests_per_minute` in config
- Upgrade API plan

## Next Steps

1. **Customize extraction schema** for your domain
2. **Test with 2-3 papers** before large runs
3. **Review annotated PDFs** to verify extraction quality
4. **Adjust LLM temperature** if needed (lower = more consistent)
5. **Check API costs** before processing hundreds of papers

## Example Workflows

### Medical Literature Review
```yaml
extraction_schema:
  - field: "patient_count"
    type: "number"
  - field: "intervention"
    type: "text"
  - field: "primary_outcome"
    type: "text"
```

### Market Research
```yaml
extraction_schema:
  - field: "market_size"
    type: "number"
  - field: "growth_rate"
    type: "number"
  - field: "key_players"
    type: "list"
```

### Environmental Science
```yaml
extraction_schema:
  - field: "location_latitude"
    type: "number"
  - field: "location_longitude"
    type: "number"
  - field: "measurement_type"
    type: "text"
```

## Getting Help

- 📖 Read the [full documentation](docs/)
- 💬 Ask in [GitHub Discussions](https://github.com/harshoza/litrover/discussions)
- 🐛 Report bugs in [GitHub Issues](https://github.com/harshoza/litrover/issues)
- 📧 Email: harshoza85@gmail.com

## Tips for Success

1. **Start small**: Test with 5-10 papers first
2. **Be specific**: Clear field descriptions = better extraction
3. **Verify quality**: Always review annotated PDFs
4. **Monitor costs**: Check API usage regularly
5. **Cache results**: Enable caching to avoid re-processing

Happy researching! 🚀
