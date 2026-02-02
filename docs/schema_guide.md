# Schema Guide

Learn how to define custom extraction schemas for your domain.

## What is a Schema?

A schema defines **what information** you want to extract from papers. Each field in your schema becomes a column in your output Excel file.

## Schema Structure

```yaml
extraction_schema:
  - field: "field_name"
    type: "text" | "number" | "boolean"
    description: "What this field represents"
```

## Field Types

### `text`
For textual information.

**Examples:**
```yaml
- field: "methodology"
  type: "text"
  description: "Research methodology or approach used"

- field: "key_findings"
  type: "text"  
  description: "Main conclusions or results"
```

### `number`
For numeric values.

**Examples:**
```yaml
- field: "sample_size"
  type: "number"
  description: "Number of participants or samples"

- field: "p_value"
  type: "number"
  description: "Statistical significance value"
```

### `boolean`
For yes/no questions.

**Examples:**
```yaml
- field: "peer_reviewed"
  type: "boolean"
  description: "Whether the study was peer-reviewed"

- field: "data_available"
  type: "boolean"
  description: "Whether data is publicly available"
```

## Domain-Specific Examples

### Medical/Clinical Research

```yaml
extraction_schema:
  - field: "study_type"
    type: "text"
    description: "Type of study (RCT, cohort, case-control, etc.)"
  
  - field: "patient_count"
    type: "number"
    description: "Number of patients enrolled"
  
  - field: "intervention"
    type: "text"
    description: "Treatment or intervention tested"
  
  - field: "control_group"
    type: "text"
    description: "Control or comparison group"
  
  - field: "primary_outcome"
    type: "text"
    description: "Primary outcome measure"
  
  - field: "p_value"
    type: "number"
    description: "Statistical significance"
  
  - field: "adverse_events"
    type: "text"
    description: "Reported adverse events"
```

### Geological Research

```yaml
extraction_schema:
  - field: "site_name"
    type: "text"
    description: "Site or core identifier"
  
  - field: "latitude"
    type: "number"
    description: "Latitude in decimal degrees"
  
  - field: "longitude"
    type: "number"
    description: "Longitude in decimal degrees"
  
  - field: "core_depth"
    type: "number"
    description: "Total core depth in meters"
  
  - field: "sediment_type"
    type: "text"
    description: "Type of sediment (marine, terrestrial, etc.)"
  
  - field: "analysis_methods"
    type: "text"
    description: "Analytical methods used (XRF, dating, etc.)"
  
  - field: "age_range"
    type: "text"
    description: "Age range covered by the core"
```

### Business/Market Research

```yaml
extraction_schema:
  - field: "company_name"
    type: "text"
    description: "Company or organization studied"
  
  - field: "market_size"
    type: "number"
    description: "Market size in USD millions"
  
  - field: "growth_rate"
    type: "number"
    description: "Annual growth rate percentage"
  
  - field: "key_competitors"
    type: "text"
    description: "Main competitors mentioned"
  
  - field: "revenue"
    type: "number"
    description: "Company revenue in USD millions"
  
  - field: "market_share"
    type: "number"
    description: "Market share percentage"
```

## Best Practices

### 1. Be Specific

❌ **Bad:**
```yaml
- field: "data"
  description: "The data"
```

✅ **Good:**
```yaml
- field: "measurement_method"
  description: "Method used to measure temperature (thermometer type, precision)"
```

### 2. Use Consistent Naming

Choose a naming convention and stick to it:
- `snake_case` (recommended): `sample_size`, `p_value`
- `camelCase`: `sampleSize`, `pValue`
- `kebab-case`: `sample-size`, `p-value`

### 3. Provide Context

Help the LLM understand what you're looking for:

```yaml
- field: "elevation"
  type: "number"
  description: "Site elevation above sea level in meters"
```

### 4. Limit Field Count

**Optimal:** 5-15 fields
**Maximum:** 20 fields

Too many fields:
- Increases API costs
- Reduces extraction accuracy
- Slows processing

### 5. Choose Appropriate Types

```yaml
# Use number for quantities
- field: "temperature"
  type: "number"  # ✓ Correct

# Use text for categories
- field: "climate_zone"
  type: "text"    # ✓ Correct (not boolean)

# Use boolean for binary questions
- field: "is_marine"
  type: "boolean" # ✓ Correct
```

## Testing Your Schema

1. **Start Small**: Test with 3-5 papers first
2. **Review Results**: Check if extracted data matches expectations
3. **Refine Descriptions**: Update field descriptions based on results
4. **Add/Remove Fields**: Adjust schema as needed

## Interactive Schema Creation

The setup wizard helps you create schemas interactively:

```bash
python setup_project.py
```

You'll be prompted to:
1. List field names (comma-separated)
2. Set type for each field
3. Provide descriptions

## Modifying Existing Schemas

Edit your config file directly:

```bash
nano config/your_project.yaml
```

Then re-run the pipeline with the updated schema.

## Tips by LLM Provider

### Gemini
- Works well with 10-15 fields
- Good at extracting numbers and structured data
- Best for papers with clear sections

### Claude
- Excellent with complex descriptions
- Handles 15-20 fields well
- Best for nuanced information

### OpenAI (GPT-4)
- Strong with 8-12 fields
- Good at inferring information
- Best for papers with varied formats

## Common Patterns

### Location Data
```yaml
- field: "latitude"
  type: "number"
  description: "Latitude in decimal degrees (positive = North)"

- field: "longitude"
  type: "number"
  description: "Longitude in decimal degrees (positive = East)"
```

### Temporal Data
```yaml
- field: "start_date"
  type: "text"
  description: "Study start date (YYYY-MM-DD format)"

- field: "duration"
  type: "number"
  description: "Study duration in months"
```

### Statistical Data
```yaml
- field: "mean_value"
  type: "number"
  description: "Mean of the measured variable"

- field: "standard_deviation"
  type: "number"
  description: "Standard deviation"

- field: "confidence_interval"
  type: "text"
  description: "95% confidence interval"
```

## Troubleshooting

### "LLM returns null for all fields"
- Descriptions may be too vague
- Paper may not contain this information
- Try with different LLM provider

### "Extracted data is incorrect"
- Add more context to description
- Specify units/format expected
- Provide examples in description

### "Some fields always empty"
- Field may not be in most papers
- Description unclear
- Consider removing or making optional

---

**Need help?** Open an issue with your schema and sample papers!
