# 🔍 LitRover

**Agentic AI System for Automated Literature Survey and Data Extraction**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![GitHub](https://img.shields.io/badge/github-harshoza85%2Flitrover-blue)](https://github.com/harshoza85/litrover)

**Author**: Harsh Oza | **Email**: harshoza85@gmail.com

LitRover is an intelligent, multi-agent orchestration system that automates the entire research paper processing pipeline: from citation resolution to PDF extraction to AI-powered metadata extraction. Built for researchers, analysts, and data scientists across any domain.

## ✨ Key Features

### 🤖 Agentic Orchestration
- **Multiple orchestration modes**: CLI automation, interactive step-by-step, LangGraph workflows, AutoGen multi-agent
- **Autonomous decision-making**: Handles errors, retries, and adaptive workflows
- **Pluggable architecture**: Swap orchestrators based on your needs

### 🧠 Multi-LLM Support
- **Gemini** (Google): Fast, cost-effective, great for bulk processing
- **Claude** (Anthropic): High accuracy, excellent reasoning
- **OpenAI GPT-4**: Vision-based extraction, broad capabilities
- **Pluggable design**: Easy to add new providers

### 🎨 PDF Annotation (New!)
- **Color-coded highlights**: See exactly where data was extracted
- **Source traceability**: Every value linked to its source text
- **Quality verification**: Instantly spot extraction errors
- **Collaboration-ready**: Share annotated PDFs with colleagues

### 📊 Dynamic Schema Definition
- Define extraction fields via interactive wizard
- No coding required - just specify what you want to extract
- Automatic Excel template generation
- Works across any domain: geology, medicine, business, legal, etc.

### 🔄 Complete Pipeline
1. **Citation Resolution**: Semantic Scholar API + fuzzy matching
2. **PDF Download**: Multi-publisher strategies with smart fallbacks
3. **AI Extraction**: LLM-powered metadata extraction with validation
4. **PDF Annotation**: Color-coded source highlighting (optional)
5. **Data Export**: Clean Excel output with audit trails

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/harshoza85/litrover.git
cd litrover

# Install dependencies
pip install -r requirements.txt

# Or install as package
pip install -e .
```

### Setup Your Project

```bash
# Run the interactive setup wizard
python setup_project.py

# The wizard will ask:
# - Project name
# - Fields to extract (comma-separated)
# - Excel column mappings
# - LLM provider preference
```

This generates:
- `config/your_project.yaml` - Configuration file
- `data/template.xlsx` - Excel template for your data

### Run the Pipeline

**Option 1: Automated (Recommended for first-time users)**
```bash
python orchestrate.py --config config/your_project.yaml --mode auto
```

**Option 2: Interactive (Step-by-step control)**
```bash
python orchestrate.py --config config/your_project.yaml --mode interactive
```

**Option 3: Advanced Orchestration**
```bash
# LangGraph workflow
python orchestrate.py --config config/your_project.yaml --orchestrator langgraph

# AutoGen multi-agent
python orchestrate.py --config config/your_project.yaml --orchestrator autogen
```

**Option 4: Claude Code (Agentic)**
Just tell Claude Code: *"Run the LitRover pipeline on my config"*
See [docs/claude_code_usage.md](docs/claude_code_usage.md) for details.

## 📖 Example: Geological Survey

See the complete example in [`examples/geological_survey/`](examples/geological_survey/)

**Scenario**: Extract core sample metadata from 100+ geology papers

**Fields extracted**:
- Site name, coordinates (lat/lon)
- Core depth, sediment type
- XRF machine model
- Data availability

**Results**: 95% reduction in manual processing time

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│           Orchestration Layer                    │
│  ┌──────────┬──────────┬──────────┬──────────┐ │
│  │   CLI    │Interactive│LangGraph │ AutoGen  │ │
│  └──────────┴──────────┴──────────┴──────────┘ │
└─────────────────────────────────────────────────┘
                      │
┌─────────────────────────────────────────────────┐
│              Agent Layer                         │
│  ┌──────────┬──────────┬──────────────────────┐ │
│  │ Citation │   PDF    │   LLM Extraction     │ │
│  │ Resolver │Downloader│ (Gemini/Claude/GPT)  │ │
│  └──────────┴──────────┴──────────────────────┘ │
└─────────────────────────────────────────────────┘
```

## 🛠️ Configuration

### API Keys

Create `.env` file:
```bash
GEMINI_API_KEY=your_gemini_key
ANTHROPIC_API_KEY=your_claude_key
OPENAI_API_KEY=your_openai_key
```

### Project Config

`config/your_project.yaml`:
```yaml
project_name: "My Literature Survey"
input_file: "data/papers.xlsx"
output_dir: "outputs/"

# Define what to extract
extraction_schema:
  - field: "sample_size"
    type: "number"
    description: "Number of samples or participants"
  - field: "methodology"
    type: "text"
    description: "Research methodology used"

# Excel column mapping
columns:
  identifier: "Paper_ID"
  paper_refs: ["Reference", "Citation_1", "Citation_2"]

# LLM settings
llm:
  provider: "gemini"  # or "claude", "openai"
  model: "gemini-2.0-flash-exp"
  temperature: 0.1
```

## 📚 Documentation

- [Quick Start Guide](docs/quickstart.md)
- [Schema Definition](docs/schema_guide.md)
- [PDF Annotation](docs/pdf_annotation.md) - Color-coded source highlighting
- [LLM Providers](docs/llm_providers.md)
- [Orchestrators Guide](docs/orchestrators.md)
- [Claude Code Usage](docs/claude_code_usage.md)

## 🎯 Use Cases

### Academia
- Literature reviews and meta-analyses
- Systematic reviews
- Dataset compilation from papers

### Business
- Market research surveys
- Competitive analysis
- Patent analysis

### Healthcare
- Clinical trial data extraction
- Medical literature reviews
- Treatment outcome analysis

### Legal
- Case law research
- Regulatory compliance tracking
- Contract analysis

## 🤝 Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## ⚖️ License

MIT License - see [LICENSE](LICENSE) for details.

## ⚠️ Important Notes

### Publisher Compliance
- Respects API rate limits and caching
- Users must comply with publisher Terms of Service
- Intended for legitimate research use only
- Users responsible for ensuring legal access to papers

### API Costs
- LLM APIs incur costs based on usage
- Gemini: ~$0.50-2 per 100 papers
- Claude: ~$2-5 per 100 papers  
- OpenAI: ~$5-10 per 100 papers
- Estimate costs before large runs

### Privacy
- All processing happens locally or via your API keys
- No data sent to third parties except chosen LLM provider
- Downloaded PDFs stored locally only

## 📧 Contact

- **Author**: Harsh Oza
- **Email**: harshoza85@gmail.com
- **Issues**: [GitHub Issues](https://github.com/harshoza85/litrover/issues)
- **Discussions**: [GitHub Discussions](https://github.com/harshoza85/litrover/discussions)

## 🙏 Acknowledgments

- **Semantic Scholar API**: Citation resolution
- **Google Gemini**: AI extraction capabilities
- **Anthropic Claude**: High-quality reasoning
- **OpenAI**: GPT-4 vision capabilities
- **LangChain/LangGraph**: Orchestration framework
- **Microsoft AutoGen**: Multi-agent framework

---

**Built with ❤️ for researchers by researchers**

*Reducing manual literature processing from days to hours*
