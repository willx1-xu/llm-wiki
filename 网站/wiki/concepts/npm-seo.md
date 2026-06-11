---
title: "NPM SEO — 包发现优化"
type: concept
category: project
privacy: public
tags: [npm, seo,包管理, discoverability, frontend]
created: 2026-06-11
updated: 2026-06-11
confidence: medium
---

# NPM SEO — npm 包搜索优化

## 为什么重要

- npm 每天数百万次包搜索
- Google 索引 npm 页面（高权重域名）
- npm 包名 = 搜索关键词
- 包描述出现在 Google 搜索结果中

## 优化要点

### package.json
```json
{
  "name": "关键词-功能-描述",
  "description": "一句话，含核心搜索词，60-100字符",
  "keywords": ["seo", "react", "data-grid", ...]
}
```

### README
- 第一段是 Google 摘要来源
- 包含使用示例（代码块 = 长尾搜索词）
- 链接到 GitHub 仓库 + 独立站

### 生态联动
- npm → GitHub（repository 字段）
- npm → 独立站（homepage 字段）
- npm 搜索排名受下载量、星标、更新频率影响

## 相关概念
- [[github-seo]] — GitHub 搜索优化
- [[geo-search-optimization]] — GEO 完整体系
