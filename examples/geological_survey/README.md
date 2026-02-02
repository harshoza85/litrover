# Geological Survey Example

This example demonstrates using LitRover for extracting metadata from geological research papers.

## Scenario

You're compiling a database of coastal groundwater research sites from published papers. You need to extract:
- Site locations (lat/lon)
- Core depths and types
- Analytical methods used
- Data availability

## Files

- `config.yaml` - Project configuration
- `sample_data.xlsx` - Example input data with 5 papers
- `outputs/` - Results will be saved here (after running)
- `papers/` - Downloaded PDFs (after running)

## Sample Data

The example includes 5 real geological papers:

1. **Site U1425** - IODP Expedition 346 (Japan Sea)
2. **Lake Rinihue** - Chilean lake sediments
3. **Taiwan Coast** - Coastal groundwater study
4. **Arctic Core** - Arctic Ocean sediments
5. **Mediterranean Site** - Eastern Mediterranean cores

## Running the Example

### Prerequisites

1. Install LitRover:
```bash
pip install -r requirements.txt
```

2. Set up API keys in `.env`:
```bash
GEMINI_API_KEY=your_key_here
```

### Run the Pipeline

From the project root:

```bash
python orchestrate.py run --config examples/geological_survey/config.yaml
```

This will:
1. Load the 5 sample papers
2. Resolve citations and DOIs
3. Download PDFs (where available)
4. Extract metadata using Gemini
5. Save results to `examples/geological_survey/outputs/`

### Expected Output

The output Excel will contain extracted data like:

| Site | latitude | longitude | core_depth_m | sediment_type | xrf_machine | ... |
|------|----------|-----------|--------------|---------------|-------------|-----|
| Site_U1425 | 39.49 | 134.44 | 922.5 | marine sediment | Avaatech XRF | ... |
| Lake_Rinihue | -39.82 | -72.47 | 12.0 | lake sediment | ITRAX | ... |
| ... | ... | ... | ... | ... | ... | ... |

### Processing Time

- **First run** (with downloads): ~5-10 minutes
- **Subsequent runs** (cached): ~1-2 minutes

### Estimated Cost

Using Gemini 2.0 Flash:
- **Per paper**: ~$0.05-0.10
- **Total (5 papers)**: ~$0.25-0.50

## Customization

### Modify Extraction Schema

Edit `config.yaml` to add/remove fields:

```yaml
extraction_schema:
  - field: "your_new_field"
    type: "text"
    description: "What to extract"
```

### Add More Papers

Edit `sample_data.xlsx` and add rows with:
- Site identifier
- Paper references (DOIs or citations)

### Try Different LLMs

Change in `config.yaml`:

```yaml
llm:
  provider: "claude"  # or "openai"
  model: "claude-sonnet-4-20250514"
```

## Interactive Mode

For step-by-step control:

```bash
python orchestrate.py run --config examples/geological_survey/config.yaml --mode interactive
```

You'll be prompted to confirm each step:
- Resolve citations?
- Download PDFs?
- Extract metadata?

## Advanced: LangGraph Workflow

Try the graph-based orchestrator:

```bash
python orchestrate.py run --config examples/geological_survey/config.yaml --orchestrator langgraph
```

This uses conditional decision nodes for adaptive workflow.

## Validation

Check your configuration:

```bash
python orchestrate.py validate --config examples/geological_survey/config.yaml
```

View project info:

```bash
python orchestrate.py info --config examples/geological_survey/config.yaml
```

## Troubleshooting

### "PDF download failed"

Some papers require institutional access. The system will:
- Try to find open-access versions
- Continue with available PDFs
- Log failed downloads

### "Extraction returned null"

Possible causes:
- PDF is scanned (OCR needed)
- Paper doesn't contain specific fields
- Field description needs refinement

Check logs in `examples/geological_survey/litrover.log`

### "API rate limit"

If you hit Semantic Scholar rate limits:
- Add delays between requests (already configured)
- Get a Semantic Scholar API key (free)
- Process in smaller batches

## Expected Results

After running, you should see:
- ✓ 4-5 citations resolved (depends on availability)
- ✓ 3-4 PDFs downloaded (some may not be open access)
- ✓ 3-4 successful extractions
- ✓ High confidence scores (0.7-0.9)

## Next Steps

1. **Customize for your domain**: Modify schema for your research area
2. **Add your papers**: Replace sample data with your references
3. **Optimize**: Test different LLMs for quality vs. cost
4. **Scale**: Process hundreds of papers with same configuration

## Questions?

- Check main documentation in `docs/`
- Open an issue on GitHub
- See `docs/schema_guide.md` for schema help

---

**This example demonstrates the complete LitRover workflow!** 🚀
