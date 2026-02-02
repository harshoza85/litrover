# Using LitRover with Claude Code

LitRover works seamlessly with Claude Code for true agentic orchestration!

## What is Claude Code?

Claude Code is Anthropic's agentic coding tool that can autonomously:
- Execute Python scripts
- Handle errors and retry logic
- Make intelligent decisions about workflow
- Coordinate multiple processes

**This is what makes LitRover truly "agentic"** - Claude Code acts as the intelligent orchestrator.

## Setup

### 1. Install LitRover

```bash
git clone https://github.com/yourusername/litrover.git
cd litrover
pip install -r requirements.txt
```

### 2. Configure Your Project

```bash
python setup_project.py
```

Set up your extraction schema and configuration.

### 3. Add Data

Fill in `data/your_template.xlsx` with paper references.

## Using Claude Code

### Basic Usage

Simply tell Claude Code:

```
"Run the LitRover pipeline on my project config at config/my_project.yaml"
```

Claude Code will autonomously:
1. Load the configuration
2. Validate API keys  
3. Execute the pipeline
4. Handle any errors
5. Report results

### Example Interactions

#### Process New Papers

**You:**
```
I have a new Excel file at data/new_papers.xlsx.
Update my config to use it and run the pipeline.
```

**Claude Code will:**
1. Update `config/your_project.yaml`
2. Run `python orchestrate.py run --config config/your_project.yaml`
3. Monitor progress
4. Report successful extractions

#### Debug Issues

**You:**
```
The pipeline failed on row 15. Can you check what went wrong and retry?
```

**Claude Code will:**
1. Examine error logs
2. Identify the issue (e.g., bad DOI, PDF download failed)
3. Suggest fixes or retry with different approach
4. Resume from row 15

#### Iterative Refinement

**You:**
```
The extraction quality is low. Can you:
1. Check a few PDFs manually
2. Refine the extraction prompt
3. Re-run extraction on those papers
```

**Claude Code will:**
1. Examine sample PDFs
2. Update extraction prompt in config
3. Re-run extraction
4. Compare results and suggest improvements

## Advanced Workflows

### Batch Processing with Quality Checks

**You:**
```
Process my papers in batches of 10.
After each batch, show me the results and I'll approve before continuing.
```

**Claude Code will:**
- Create batches
- Process each batch
- Present results for review
- Wait for approval
- Continue or adjust based on feedback

### Multi-Configuration Comparison

**You:**
```
I want to compare Gemini vs Claude for extraction quality.
Run the pipeline with both providers on the same data and compare results.
```

**Claude Code will:**
1. Create two configs (one for each provider)
2. Run both pipelines
3. Compare extracted data
4. Generate comparison report

### Automated Quality Control

**You:**
```
Set up automatic quality control:
- Extract metadata
- Check for null values
- Flag low-confidence extractions
- Retry those with a different LLM
```

**Claude Code will:**
- Implement the workflow
- Monitor confidence scores
- Automatically retry low-quality extractions
- Report final statistics

## Agentic Decision Making

Claude Code can make intelligent decisions:

### Error Recovery

If PDF download fails:
```
Claude Code: "Download failed for DOI 10.xxxx. Trying alternative URL from Semantic Scholar..."
```

### Optimization

```
Claude Code: "First 5 papers took 3 minutes. Enabling caching to speed up remaining 95 papers..."
```

### Resource Management

```
Claude Code: "API rate limit hit. Switching to cached results and continuing..."
```

## Best Practices

### 1. Start with Pilot Run

**You:**
```
"Process just the first 5 papers to test the configuration"
```

### 2. Iterative Refinement

**You:**
```
"After processing each batch:
1. Show summary statistics
2. Let me review sample extractions  
3. Ask if I want to adjust schema
4. Continue with next batch"
```

### 3. Error Handling

**You:**
```
"If any step fails:
1. Log the error
2. Skip that paper
3. Continue with rest
4. Give me a report at the end"
```

### 4. Cost Monitoring

**You:**
```
"Before running on all 500 papers:
1. Estimate API costs
2. Show estimated completion time
3. Wait for my approval"
```

## Example Complete Workflow

**You:**
```
I have 100 geological papers to process.

Schema:
- site_name, latitude, longitude
- core_depth, sediment_type
- dating_method, age_range

Please:
1. Set up the project
2. Process in batches of 10
3. Use Gemini (cheaper)
4. Show progress after each batch
5. Flag any papers where extraction fails
6. At the end, give me summary statistics
```

**Claude Code:**
```
I'll set up and run this workflow:

1. Creating config with your schema... ✓
2. Validating Gemini API key... ✓
3. Starting batch processing...

Batch 1/10 (papers 0-9):
- Citations resolved: 9/10 (1 failed)
- PDFs downloaded: 8/10 (1 not found)
- Extractions completed: 8/10
- Average confidence: 0.85

Continue with batch 2? [analyzing results... confidence good, proceeding]

Batch 2/10 (papers 10-19):
...

Final Summary:
- Total papers: 100
- Successfully processed: 89
- Failed: 11 (logged in failed_papers.txt)
- Average confidence: 0.82
- Total cost: $4.50
- Time: 45 minutes

Results saved to: outputs/results_20250129_143022.xlsx
```

## Comparison: Claude Code vs Manual

### Manual CLI
```bash
python orchestrate.py run --config config/my_project.yaml
# [wait, watch for errors, no automatic recovery]
```

### Claude Code (Agentic)
```
"Run the pipeline and handle any issues"
# [Claude monitors, handles errors, retries, optimizes]
```

## Tips for Working with Claude Code

### Be Specific About Error Handling

❌ **Vague:**
```
"Process my papers"
```

✅ **Specific:**
```
"Process my papers. If a PDF fails to download, try the publisher's website. If extraction confidence < 0.5, retry with Claude instead of Gemini."
```

### Leverage Autonomous Decision Making

**You:**
```
"Process these papers. You decide:
- Best batch size based on performance
- When to switch between cached and fresh extractions
- If any papers need manual review"
```

### Request Monitoring

**You:**
```
"Monitor the pipeline and alert me if:
- Success rate drops below 80%
- Average processing time > 30s per paper
- Cost exceeds $10"
```

## Integration with Other Tools

Claude Code can integrate LitRover with:
- **Google Drive**: Auto-upload results
- **Slack**: Send notifications
- **GitHub**: Commit results to repo
- **Zotero**: Import processed papers

**Example:**
```
"After processing:
1. Upload Excel to my Google Drive
2. Send summary to #research Slack channel
3. Commit results to my GitHub repo"
```

## Why This is True Agentic Orchestration

**Traditional automation:**
- Fixed scripts
- No error recovery
- Manual intervention needed

**Claude Code + LitRover:**
- Adaptive workflows
- Intelligent error handling
- Autonomous optimization
- Context-aware decisions

**This is the future of research automation!** 🚀

---

**Questions?** Claude Code can help with setup:
```
"I want to use LitRover with Claude Code. Help me get started."
```
