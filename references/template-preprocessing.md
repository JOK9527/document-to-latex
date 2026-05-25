# Template Preprocessing

Most user-provided templates need preprocessing before content insertion. Do this carefully and preserve the original template as much as possible.

## Strategy

Template preprocessing has three levels. Apply them in order and stop at the lowest level that makes the template usable.

1. Extraction is mandatory.
2. Non-destructive cleanup is common.
3. Minimal restructuring is conditional.

Do not fully rebuild a user template into the skill's default structure unless the user explicitly asks for that or the original template cannot be made usable with smaller changes.

## Level 1: Extraction

Extraction means understanding the template without changing it.

Use `scripts/analyze_template.py` for a first-pass template profile, then inspect anything ambiguous manually.

Extract:

- compile entry point and alternate entry candidates
- `\documentclass` and class options
- loaded `.cls`, `.sty`, `.def`, and local macro files
- body, abstract, appendix, bibliography, figure, and table insertion points
- metadata commands and editable fields
- bibliography workflow and citation packages
- sample content boundaries
- required assets, fonts, logos, and bibliography files
- absolute paths and platform-specific assumptions
- template documentation and compile instructions

This level should happen for every template, even when preprocessing can otherwise be skipped.

## Level 2: Non-destructive Cleanup

Cleanup means making the template safe to receive converted content while preserving its structure.

Common cleanup actions:

- remove or isolate stale auxiliary files
- move sample content out of the active build
- normalize paths to relative paths when safe
- identify user-editable metadata values
- create a `content/` directory as the converted content landing zone
- add a small bridge file or `\input{...}` entry point
- compile the cleaned template if the toolchain is available

Prefer this level for most school, journal, Overleaf, GitHub, and prior-project templates.

## Level 3: Minimal Restructuring

Restructuring means changing the active template organization. Do this only when extraction and cleanup are not enough.

Use minimal restructuring when:

- multiple main files conflict and one build entry must be chosen
- sample content and reusable structure are inseparable
- the main file is too large and needs a generated content entry point
- content and style are mixed in a way that blocks maintainable conversion
- the template cannot compile without small structural repair

Keep restructuring narrow:

- preserve `.cls`, `.sty`, and `.def` files
- avoid changing style logic unless it causes a compile failure
- document every structural change in `conversion_report.md`
- keep original files or move inactive originals to a clearly named backup/sample area

## Common Template Problems

- multiple possible main `.tex` files
- sample thesis or article content mixed with template structure
- hard-coded author, title, school, advisor, date, or placeholder metadata
- absolute paths or platform-specific paths
- stale auxiliary files such as `.aux`, `.bbl`, `.blg`, `.toc`, `.out`, `.log`, `.synctex.gz`
- missing images, logos, fonts, or bibliography files
- package conflicts or duplicate package loading
- bibliography system unclear or inconsistent
- custom commands spread across `.tex`, `.cls`, `.sty`, and `.def` files
- template documentation separate from the actual compile entry

## Preprocessing Steps

1. Preserve the original template directory when possible.
2. Perform Level 1 extraction and write down the template profile.
3. Decide whether Level 2 cleanup is needed.
4. Remove or isolate generated auxiliary files.
5. Separate sample content from reusable structure.
6. Identify user-editable metadata fields.
7. Locate body, abstract, appendix, bibliography, figures, and tables insertion points.
8. Normalize relative paths without changing template semantics.
9. Compile the cleaned template before content insertion when the toolchain is available.
10. Use Level 3 restructuring only if the template still cannot safely receive content.
11. Record unresolved template issues and preprocessing decisions in `conversion_report.md`.

## Sample Content Handling

Do not silently mix sample content with converted content. Either remove sample content from the active build or move it to a clearly named folder such as:

```text
template-sample/
```

If sample content demonstrates required commands, preserve a short note in the report and reuse those commands in generated content.

## When Preprocessing Can Be Skipped

Skip explicit preprocessing only when all are true:

- one main file is obvious
- required class/style/assets are present
- sample content is already minimal or isolated
- paths are relative and portable
- the template compiles successfully

Even then, still inspect insertion points and bibliography method.

## Output

After preprocessing, the adapted project should have:

- original template archive or path recorded under `source/`
- a clear main entry file
- converted content under `content/`
- preserved class/style/template files
- no active stale auxiliary files
- a report entry listing preprocessing decisions
