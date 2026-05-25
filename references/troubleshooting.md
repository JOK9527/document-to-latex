# Troubleshooting

Compile before delivery when possible. Inspect `build.log` and fix the smallest responsible issue.

## Common Failures

- Unescaped special characters: `_`, `%`, `&`, `#`, `{`, `}`
- Bad image path or unsupported image format
- Unicode character unsupported by the selected engine
- Chinese text compiled with pdfLaTeX
- Table too wide for the page
- Missing package
- Wrong BibTeX versus biber workflow
- `minted` used without shell escape
- Duplicate labels

## Repair Strategy

1. Fix syntax and path errors first.
2. Switch to XeLaTeX for Chinese or Unicode-heavy documents when allowed.
3. Reduce table width using `tabularx`, `longtable`, or smaller local layout.
4. Preserve user template choices unless they are the cause of failure.
5. Record unresolved issues in `conversion_report.md`.

