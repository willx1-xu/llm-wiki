---
title: "操作日志"
type: log
category: knowledge
privacy: public
updated: 2026-06-11
---

# 操作日志

## 2026-06-11 22:30 — 删除无效知识
- 删除 3 个微信相关页面（wechat-llm-article, wechat-content-distribution, wechat-official-account）
- 原因：微信是封闭平台，LLM 无法抓取原文，所有内容均为推测/编造，属于无效知识
- 新增页面删除功能（API + UI 按钮）

## 2026-06-11 22:00 — GEO 知识库修正
- **删除**：7 个错误的地理/GIS 页面（geo-knowledge, geospatial-data-analysis, gis-tools, geopandas, leaflet, openstreetmap, geo-github-knowledge）
- **根因**：Ingest 将 "GEO"（搜索引擎优化）误判为 "Geography"（地理学）
- **新建**：6 个 GEO/SEO 概念页 + 3 个实体页 + 1 个来源摘要
- **结论**：歧义术语需在 Ingest 前增加澄清确认步骤

## 2026-06-11 21:30 — 项目知识入库
- 新增来源摘要：`ai-code-generator`、`snake-game`
- 新增概念页：`vibe-coding`、`deepseek-api`、`html5-canvas-game`
- 更新 `index.md`

## 2026-06-11 21:00 — 知识库初始化
- 创建目录结构
- 种子页面：LLM Knowledge Base、Memex、Andrej Karpathy
- 写入 schema.md 行为规范
