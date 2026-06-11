---
title: "AI 代码生成器"
type: source
tags: [ai, code-generation, deepseek, fastapi, vibe-coding]
created: 2026-06-10
updated: 2026-06-11
source_path: ai-code-generator/app.py
---

# AI 代码生成器 — 项目摘要

## 概述

基于 DeepSeek API 的 Vibe Coding Web 应用，用户用自然语言描述需求，AI 自动生成完整的、可直接运行的 HTML 页面（内嵌 CSS + JS），并在 iframe 中实时预览。

## 技术栈

| 层 | 技术 |
|---|------|
| 后端 | FastAPI + uvicorn |
| AI | DeepSeek Chat API |
| 前端输出 | 单文件 HTML (inline CSS/JS) |
| HTTP | httpx |

## 核心设计

1. **System Prompt 工程**：详细的规则约束——只输出纯 HTML、现代设计、移动响应、中文内容、真实媒体源
2. **自动媒体注入**：根据用户关键词（音乐/视频/图片）自动扩展 prompt，注入 iTunes API、SoundHelix、Picsum 等真实源
3. **iframe 实时预览**：LLM 返回的 HTML 直接展示在页面中，无需刷新

## 关键约束

- 必须生成 `<!DOCTYPE html>` 开头
- 不能用外链 CSS/JS 文件（但可用 CDN 库）
- 媒体 URL 必须真实（禁止编造）
- 音乐播放器必须用 iTunes Search API 获取真实歌曲

## 相关概念

- [[vibe-coding]] — 用自然语言描述需求，AI 直接生成可用代码
- [[deepseek-api]] — DeepSeek Chat API 使用方法
