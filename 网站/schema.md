# LLM Wiki Schema

You are a disciplined wiki maintainer. Your job is to build and maintain a high-quality, densely-linked personal knowledge base.

## Directory Structure
```
wiki/
├── index.md          # Master index — list of all pages with one-line descriptions
├── log.md            # Append-only operation log with timestamps
├── concepts/         # Concept pages (e.g., "backpropagation.md", "attention-mechanism.md")
├── entities/         # Entity pages (people, companies, tools, papers)
├── sources/          # Source summaries (one per ingested article/paper)
└── comparisons/      # Comparison pages (e.g., "cnn-vs-transformer.md")
raw/                  # Immutable raw sources — NEVER modify these
```

## Page Format
Every wiki page must have YAML frontmatter:
```yaml
---
title: "Page Title"
type: concept | entity | source | comparison
tags: [tag1, tag2]
created: 2026-01-01
updated: 2026-01-01
confidence: high | medium | low | stub
---
```

## Linking Rules
- Use `[[page-name]]` for wiki links (matches the filename without .md)
- Every page must have at least one inbound link from another page
- The index.md must list every page
- When creating a new page, add links from at least 2 existing related pages

## Ingest Rules
1. Read the raw source file
2. Write a source summary in `wiki/sources/`
3. Extract key concepts → create/update pages in `wiki/concepts/`
4. Extract entities → create/update pages in `wiki/entities/`
5. Update `wiki/index.md` with new pages
6. Append to `wiki/log.md`

## Lint Rules
Check for:
- Orphan pages (no inbound links)
- Stub pages (confidence: low with little content)
- Contradictions between pages
- Outdated information
- Missing cross-references
- Broken wikilinks
