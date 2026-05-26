# User Guidance

This branch is for NWPU thesis conversion. Keep preflight short.

## Mandatory Question

Ask only:

```text
请确认论文类型：本科、硕士、博士？
```

Do not ask about LaTeX templates or general formatting preferences. The embedded `nwputhesis` template is the default.

## When To Ask More

Ask one additional question only when:

- the source is not DOCX and no conversion path is available
- graduate degree type is ambiguous and the user explicitly mentions 专硕, 专业学位, 工程硕士, or professional degree
- user instructions conflict with NWPU template requirements
- required source content is missing and cannot be represented as a review item

## Avoid Mid-Process Interruptions

After thesis type is known, continue and record uncertainty in `conversion_report.md`.

Do not stop for:

- missing figure/table captions
- rough tables
- uncertain formulas
- missing student number
- missing committee members
- missing authorization signatures
- placeholder accomplishments

These should become placeholders or review items.

