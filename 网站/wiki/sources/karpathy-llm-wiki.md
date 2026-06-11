---
title: "Karpathy LLM Wiki Gist 摘要"
type: source
tags: [llm, knowledge-base, gist, 2026]
created: 2026-06-11
updated: 2026-06-11
source_url: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
---

# Karpathy LLM Wiki — 原始 Gist 摘要

## 文档性质

Karpathy 刻意将此文档保持为"想法文件"（idea file），不包含具体代码实现。理由：在 LLM Agent 时代，你只需分享想法，每个人的 Agent 会根据自身需求定制构建。

## 关键引用

> "近期处理的 token 用量中，用于操作代码的部分大幅减少，而用于操作知识（Markdown + 图片）的部分显著增加。"

> "人类放弃 Wiki，是因为维护负担的增长速度快于价值增长速度。LLM 不会厌倦、不会忘记更新交叉引用、一次能操作 15 个文件。"

> "This document is intentionally abstract. It describes the idea, not a specific implementation. Your LLM can figure out the rest."

## 相关概念

- [[llm-knowledge-base]] — 完整架构说明
- [[memex]] — Bush 1945 年的原始愿景
- [[llm-wiki-vs-rag]] — 与 RAG 的对比

## 社区反应

Gist 发布一周内获得 5000+ 星标，社区涌现大量开源实现：
- llm-wiki-compiler（Claude Code 插件，token 消耗降低 84%）
- obsidian-llm-wiki-local（100% 本地 Ollama 运行）
- vir（Obsidian 原生集成）
- awesome-llm-knowledge-bases（收录 80+ 工具）
