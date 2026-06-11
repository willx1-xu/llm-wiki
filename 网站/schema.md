# LLM Wiki Schema

You are a disciplined wiki maintainer. Your job is to build a high-quality, densely-linked personal knowledge base.

## Directory Structure
```
wiki/
├── index.md          # Master index
├── log.md            # Append-only operation log
├── concepts/         # Abstract concepts, methodologies, patterns
├── entities/         # Concrete things: people, tools, platforms, companies
├── sources/          # Source summaries (one per ingested article/project/doc)
└── comparisons/      # Side-by-side comparisons
raw/                  # Immutable raw sources — NEVER modify these
```

## Page Format (Frontmatter)
```yaml
---
title: "Page Title"
type: concept | entity | source | comparison
category: knowledge | project | personal | learning | work
privacy: public | private | internal
tags: [tag1, tag2]
created: 2026-01-01
updated: 2026-01-01
confidence: high | medium | low | stub
---
```

## Category Rules
- **knowledge**: General/domain knowledge (SEO, programming, AI). Public by default, meant to be shared.
- **project**: Project-specific info (your own projects, tools you built). Can be public if open-source.
- **personal**: Personal info, preferences, private notes. ALWAYS private — never commit to public repo.
- **learning**: Study notes, course summaries, book notes. Usually private or internal.
- **work**: Work-related info, company stuff, NDA-covered. ALWAYS private.

## Privacy Rules
- **public**: Safe to push to GitHub, share with anyone.
- **private**: NEVER commit. Contains personal data, keys, work secrets. Auto-detected: API keys, passwords, phone numbers, addresses, salary, internal URLs.
- **internal**: In repo but not listed in public index. For semi-sensitive project notes.

## Auto-Detection of Sensitive Content
When ingesting, if the content contains ANY of the following, automatically mark the page as `privacy: private`:
- API keys, tokens, passwords (any pattern like `sk-...`, `ghp_...`, `Bearer ...`)
- Phone numbers (Chinese mobile: 1xx-xxxx-xxxx)
- ID numbers, addresses, salary figures
- Internal company URLs (corp, internal, admin portals)
- Personal email addresses in non-public contexts

## Ingest Rules
1. Read the source content
2. Determine category based on content type (knowledge/project/personal/learning/work)
3. Auto-detect and flag sensitive content, set privacy accordingly
4. Write source summary → `wiki/sources/`
5. Extract concepts → `wiki/concepts/`
6. Extract entities → `wiki/entities/`
7. Ensure at least 2 [[wikilinks]] per page
8. Update `wiki/index.md`
9. Append to `wiki/log.md`

## Linking Rules
- Use `[[page-name]]` for wiki links
- Every page must have at least one inbound link
- When creating a new page, link from at least 2 existing related pages
