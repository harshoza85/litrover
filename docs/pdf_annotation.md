# PDF Annotation Guide

LitRover can create **annotated PDFs** with color-coded highlights showing exactly where each piece of data was extracted from!

## 🎨 What is PDF Annotation?

PDF annotation highlights the source text in your downloaded papers with:
- **Color-coded highlights** - Different colors for different field types
- **Tooltips** - Hover over highlights to see field name and identifier
- **Legend** - Color key on the first page
- **Source traceability** - Know exactly where each value came from

## Why Use It?

✅ **Verification** - Quickly verify extraction accuracy  
✅ **Quality Control** - Spot errors immediately  
✅ **Citation** - Know exact page/text for citing  
✅ **Review** - Makes manual review 10x faster  
✅ **Transparency** - See what the LLM "read"  
✅ **Collaboration** - Share annotated PDFs with colleagues  

## How to Enable

Edit your `config.yaml`:

```yaml
extraction:
  annotate_pdfs: true  # Create highlighted PDFs
  annotation_dir: "annotated_papers/"
  include_legend: true  # Add color legend
  request_source_refs: true  # Ask LLM for sources
```

## Color Scheme

| Color | Field Type | Examples |
|-------|------------|----------|
| 🔵 Blue | Location | latitude, longitude, coordinates |
| 🟢 Green | Environment | marine, terrestrial, sediment |
| 🟠 Orange | Measurement | depth, length, temperature |
| 🟣 Purple | Methods | analysis, techniques |
| 🔴 Red | Instruments | XRF machine, equipment |
| 🟡 Yellow | Statistical | sample count, p-value |
| ⚫ Gray | Other | miscellaneous |

## Example Output

Open an annotated PDF to see:
- All extracted values highlighted in color
- Hover for tooltips showing field names
- Legend on first page explaining colors

## Performance

- **Time**: +1-2 seconds per PDF
- **Cost**: +10-20% tokens (minimal)
- **Value**: Massive time savings in review

---

**PDF annotation makes LitRover a professional research tool!** 🎨
