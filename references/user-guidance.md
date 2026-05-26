# User Guidance

Ask only for information that materially changes the output. The goal is a short preflight, then steady execution.

## Mandatory Preflight Gate

Do not start extraction, template adaptation, IR building, or LaTeX generation until the preflight state is explicit.

Use this compact prompt:

```text
Before I start: do you have a LaTeX template or formatting guide to use? If not, I can choose a default. Should I prioritize strict template compliance or clean maintainable LaTeX?
```

Proceed without asking only when one of these is true:

- the user has already answered the template, formatting requirement, and output-priority question
- the user explicitly says to use defaults, decide for them, or perform a quick conversion
- the request itself includes the template and formatting context

## Avoid Mid-Process Interruptions

After preflight, continue working and record manageable uncertainty in `conversion_report.md`.

Do not stop for:

- missing figure captions that can be marked for review
- rough table structure that can be preserved with notes
- uncertain formulas that can be kept as review items
- placeholder metadata in a template
- minor punctuation or spacing cleanup

Stop and ask only when:

- no DOC/DOCX source exists
- a `.doc` file cannot be converted or inspected locally
- template and user instructions directly conflict in a way that changes the deliverable
- required source content is missing

## Suggested Defaults

- Chinese short academic paper: `ctexart` with XeLaTeX
- English short academic paper: `article`
- long report: `report`
- thesis or graduation project: `thesis-lite`
- default priority: strict template compliance when a template exists; clean maintainable LaTeX when no template exists

Record assumptions in `conversion_report.md`.
