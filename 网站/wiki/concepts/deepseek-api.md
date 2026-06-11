---
title: "DeepSeek API"
type: concept
tags: [ai, api, deepseek, llm]
created: 2026-06-11
updated: 2026-06-11
confidence: high
---

# DeepSeek API

## 概述

DeepSeek 提供的 Chat Completions API，兼容 OpenAI 接口格式，性价比高。

## 接入方式

```python
POST https://api.deepseek.com/chat/completions
Authorization: Bearer sk-xxx
Content-Type: application/json

{
  "model": "deepseek-chat",
  "messages": [...],
  "temperature": 0.7,
  "max_tokens": 8000
}
```

## 在本项目中的应用

- [[ai-code-generator]] 使用 DeepSeek API 作为代码生成的 LLM 后端
- [[llm-knowledge-base]] 使用 DeepSeek API 驱动 Ingest/Query/Lint 三大操作

## 关键参数

- `model`: `deepseek-chat`（当前推荐）
- `temperature`: 代码生成建议 0.3-0.5，创意任务 0.7-1.0
- `max_tokens`: 最大 8000，HTML 页面生成建议设满
