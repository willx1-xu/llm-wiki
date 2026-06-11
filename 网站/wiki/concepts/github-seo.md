---
title: "GitHub SEO — 项目搜索优化"
type: concept
category: project
privacy: public
tags: [github, seo, 开源, 项目推广, discoverability]
created: 2026-06-11
updated: 2026-06-11
confidence: high
---

# GitHub SEO — 让项目被搜索引擎发现

## 核心原理

GitHub 是高权重域名（DA 96），Google 会频繁抓取。优化 GitHub 项目页面 = 同时获得 **GitHub 站内搜索流量** + **Google 搜索流量** + **npm/PyPI 等生态发现**。

## 优化要点

### 1. 项目命名
- 名称含核心关键词：`react-data-grid` 优于 `rdg`
- 不要用花哨的内部代号，用户搜不到

### 2. README.md
- 第一段（Above the fold）最重要 — Google 会截取作为搜索结果摘要
- 必须包含：项目是什么、解决什么问题
- 用 `##` 做清晰层级，便于 Google 提取结构化摘要

### 3. About 设置
- Description：一句话，含主要关键词
- Topics/Tags：添加所有相关标签（github topics = 分类 + 搜索入口）
- Website：链接到独立站

### 4. 仓库活跃度信号
- 频繁 commit（Google 收录时间戳）
- Issues/Discussions 活跃（内容被索引）
- Star/Fork 数（社会信号）

### 5. 多平台联动
- GitHub → npm/PyPI 发布 → 包页面含 GitHub 链接
- GitHub README → 独立站文章 → 互相引用
- GitHub Discussions → Google 索引的 FAQ 内容

## 相关实体
- [[github]] — 代码托管平台
- [[npm-seo]] — npm 包发现优化
