---
title: "LLM Knowledge Base"
type: concept
tags: [llm, knowledge-management, wiki, karpathy]
created: 2026-06-11
updated: 2026-06-11
confidence: high
---

# LLM Knowledge Base（LLM 知识库）

**提出者**：[[andrej-karpathy]]，2026 年 4 月通过 GitHub Gist 公开发布。

## 核心洞见

传统 RAG（检索增强生成）是无状态的——每次查询都从零开始检索、重新推理。Karpathy 提出：**让 LLM 持续维护一组结构化、互相链接的 Markdown 文件作为中间知识层**，将知识"编译"进 Wiki，查询时直接读取即可。

> "Obsidian is the IDE; the LLM is the programmer; the wiki is the codebase."

## 三层架构

| 层 | 名称 | 职责 |
|---|------|------|
| Layer 1 | `raw/` | 原始资料，人策展，LLM 只读不写 |
| Layer 2 | `wiki/` | LLM 全权维护的编译产物 |
| Layer 3 | `schema.md` | 人+LLM 共同迭代的规范文件 |

## 三个核心操作

1. **Ingest（摄入）** — 丢新资料到 `raw/`，LLM 阅读后更新 10-15 个关联页面
2. **Query（查询）** — 对 Wiki 提问，LLM 通过索引导航，综合答案附引用
3. **Lint（健康检查）** — 扫描矛盾、孤立页面、过时内容

## 与 RAG 的关键区别

参见 [[llm-wiki-vs-rag]]

## 思想谱系

Bush (Memex, 1945) → Luhmann ([[zettelkasten]], 1950s-90s) → Karpathy (LLM 自动化, 2026)
