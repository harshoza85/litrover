# Quick Start Guide

Get up and running with LitRover in 5 minutes!

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- API key for at least one LLM provider (Gemini, Claude, or OpenAI)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/litrover.git
cd litrover
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install as a package:

```bash
pip install -e .
```

### 3. Set Up API Keys

Copy the example environment file:

```bash
cp config/.env.example .env
```

Edit `.env` and add your API key(s):

```bash
# Choose at least one:
GEMINI_API_KEY=your_gemini_key_here
ANTHROPIC_API_KEY=your_claude_key_here
OPENAI_API_KEY=your_openai_key_here
```

**Get API Keys:**
- **Gemini**: https://aistudio.google.com/app/apikey (Free tier available)
- **Claude**: https://console.anthropic.com/ (Requires payment)
- **OpenAI**: https://platform.openai.com/api-keys (Requires payment)

## First Project

### Option 1: Interactive Setup (Recommended)

```bash
python setup_project.py
```

Follow the prompts to:
1. Name your project
2. Define fields to extract
3. Configure Excel columns
4. Choose LLM provider

This creates:
- `config/your_project.yaml` - Configuration file
- `data/template.xlsx` - Excel template (if starting fresh)

### Option 2: Use Example Project

```bash
# Copy the geological survey example
cp examples/geological_survey/config.yaml config/my_project.yaml
cp examples/geological_survey/sample_data.xlsx data/my_data.xlsx
```

## Running the Pipeline

### Basic Usage (Automated)

```bash
python orchestrate.py run --config config/your_project.yaml
```

This will:
1. Load your Excel file
2. Resolve citations
3. Download PDFs
4. Extract metadata
5. Save results to `outputs/`

### Interactive Mode (Step-by-Step)

```bash
python orchestrate.py run --config config/your_project.yaml --mode interactive
```

You'll be prompted at each step to confirm actions.

### Advanced Orchestrators

```bash
# LangGraph (graph-based workflow)
python orchestrate.py run --config config/your_project.yaml --orchestrator langgraph

# AutoGen (multi-agent system)
python orchestrate.py run --config config/your_project.yaml --orchestrator autogen
```

## Example Workflow

Let's say you want to extract data from medical research papers:

### 1. Create Project

```bash
python setup_project.py
```

When prompted:
- **Project name**: "COVID Treatments Review"
- **Fields to extract**: "study_type, sample_size, treatment, outcome, p_value"
- **Has Excel**: No (generate template)
- **LLM provider**: gemini

### 2. Fill in Your Data

Open `data/papers.xlsx` and add your paper references:

| Paper_ID | Reference_1 | Reference_2 |
|----------|-------------|-------------|
| Study1 | https://doi.org/10.xxxx/xxxxx | Smith et al., 2023 |
| Study2 | Johnson et al., 2022 | https://doi.org/10.yyyy/yyyyy |

### 3. Run Pipeline

```bash
python orchestrate.py run --config config/covid_treatments_review.yaml
```

### 4. Check Results

Open `outputs/results_TIMESTAMP.xlsx` to see extracted data!

## Validation

Check your configuration before running:

```bash
python orchestrate.py validate --config config/your_project.yaml
```

This verifies:
- Config file is valid
- API keys are present
- Input file exists
- Schema is properly defined

## Common Commands

```bash
# Show project info
python orchestrate.py info --config config/your_project.yaml

# Check version
python orchestrate.py version

# Get help
python orchestrate.py --help
python orchestrate.py run --help
```

## Troubleshooting

### "No API key found"

Make sure `.env` file exists in the project root and contains your API key:

```bash
# Check if .env exists
ls -la .env

# Verify it has the right key
cat .env | grep GEMINI_API_KEY
```

### "Input file not found"

Check the path in your config file matches your actual Excel file:

```yaml
input_file: "data/papers.xlsx"  # Make sure this file exists!
```

### "PDF download failed"

Some publishers require authentication. The system will:
- Try to find open-access versions
- Report which PDFs failed
- Continue with available PDFs

### "Extraction returned empty"

Possible causes:
- PDF is scanned (needs OCR)
- PDF is password-protected
- Paper doesn't contain requested fields

Check logs for details.

## Next Steps

- **Customize extraction**: See [Schema Guide](schema_guide.md)
- **Try different LLMs**: See [LLM Providers Guide](llm_providers.md)
- **Advanced orchestration**: See [Orchestrators Guide](orchestrators.md)
- **Use with Claude Code**: See [Claude Code Usage](claude_code_usage.md)

## Need Help?

- 📖 **Full Documentation**: See `docs/` folder
- 🐛 **Report Issues**: GitHub Issues
- 💬 **Discussions**: GitHub Discussions
- 📧 **Contact**: [Your email or link]

---

**Ready to process your literature!** 🚀
