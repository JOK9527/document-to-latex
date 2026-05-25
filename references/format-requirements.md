# Format Requirements

Formatting requirements can come from typed user text, uploaded guides, or template documentation.

## Extract Requirements

Look for:

- paper size and margins
- font family and font size
- line spacing
- title and heading rules
- abstract, keywords, acknowledgements, and appendix requirements
- figure and table caption placement
- equation numbering
- reference style
- header and footer requirements
- one-column or two-column layout
- required compiler or engine

Use `scripts/extract_format_requirements.py` for a first-pass JSON extraction from typed notes or extracted guide text, then review and correct the result. It is a heuristic helper, not a source of truth.

## Normalize

Write requirements to `format_requirements.yaml` when practical:

```yaml
language: zh
document_type: thesis
page:
  size: A4
  margin: 2.5cm
bibliography:
  style: gb7714
figures:
  caption_position: bottom
```

## Conflict Handling

Follow this priority:

1. current typed user instruction
2. user template
3. uploaded format guide
4. defaults

Record conflicts and chosen resolutions in `conversion_report.md`.
