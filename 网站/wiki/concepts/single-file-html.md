---
title: "Single File HTML"
type: concept
category: knowledge
privacy: public
tags: [html, web-development, architecture]
created: 2026-06-11
updated: 2026-06-11
confidence: medium
---

# Single File HTML

## Definition
A web development pattern where all HTML, CSS, and JavaScript are contained within a single `.html` file. This approach prioritizes simplicity and portability over modularity.

## Characteristics
- **Self-contained**: No external assets or dependencies
- **Portable**: Can be opened directly in a browser from any location
- **Easy to share**: Single file can be emailed, pasted, or downloaded
- **Quick prototyping**: Ideal for MVPs and demonstrations

## Use Cases
- Educational examples and tutorials
- Rapid prototyping
- Small tools and utilities
- AI-generated code (common output format)
- Personal projects and experiments

## Trade-offs
- **Scalability**: Becomes unwieldy for large applications
- **Maintainability**: Harder to navigate and debug
- **Reusability**: Code cannot be easily shared across projects
- **Performance**: No caching benefits for separate assets

## Best Practices
- Use `<style>` and `<script>` tags within the document
- Keep file size reasonable (< 1MB recommended)
- Use comments to separate sections
- Consider progressive enhancement for larger projects

## Related Concepts
- [[html5-canvas-game]] — Often implemented as single-file HTML
- [[vibe-coding]] — AI tools frequently generate single-file outputs
- [[wikilinks]] — Can be used in single-file documentation tools

## Tags
#html #web-development #architecture #single-file