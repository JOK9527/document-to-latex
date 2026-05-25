# Conversion Workflow

Use the least lossy route available for the source format. Prefer semantic structure over visual mimicry unless the user asks for exact layout replication.

## Source Strategy

- DOCX: try Pandoc first. Use `python-docx` or direct OOXML inspection when Pandoc loses metadata, images, comments, or formulas.
- Markdown: convert with Pandoc or clean directly when the Markdown is already structured.
- HTML: clean boilerplate with readability or BeautifulSoup, then convert with Pandoc or semantic mapping.
- TXT: infer headings from numbering, capitalization, indentation, and repeated separators.
- Text PDF: extract text blocks with PyMuPDF or pdfplumber. Preserve reading order cautiously.
- Scanned PDF or images: use OCR or VLM extraction. Mark OCR-sensitive content in the report.

For PDFs with figures, tables, formulas, or multi-column text, build a semantic intermediate representation before writing LaTeX. Use `scripts/build_pdf_semantic_ir.py` for the first pass when PyMuPDF can read the document. Do not directly dump PDF lines into `.tex` files. Read `layout-aware-pdf-extraction.md`.

## Risk Areas

- PDF reading order can be wrong for two-column, footnote-heavy, or margin-note layouts.
- Formulas from DOCX/PDF/image sources need manual review unless extracted as reliable LaTeX.
- Complex tables should be converted to maintainable LaTeX and may need source data files.
- References should become BibTeX when reliable; otherwise keep a review warning.

## Output Contract

Always produce a project that can be inspected and edited:

- source directory with original inputs or references to their original paths
- main entry point
- content files
- figures and tables directories
- bibliography file when references exist
- format requirements summary
- conversion report
