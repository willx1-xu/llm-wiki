---
title: "GEO — 搜索引擎优化体系"
type: concept
category: project
privacy: public
tags: [seo, geo, 独立站, 搜索引擎, 谷歌收录, 内容策略]
created: 2026-06-11
updated: 2026-06-11
confidence: high
---

# GEO — Generative/Google Engine Optimization

## 定义

GEO 涵盖传统 SEO（Google 收录、关键词排名）和面向 AI 引擎（ChatGPT、Perplexity、Google AI Overview）的生成式引擎优化。核心目标：让独立站内容在各类搜索引擎中被**发现、收录、排名、引用**。

## 层级体系

### 1. 收录层（Indexing）
- Google Search Console 提交 sitemap
- robots.txt 配置
- 页面被抓取 → 索引入库
- 独立站常见问题：新站不被抓取、JS 渲染内容无法索引

### 2. 排名层（Ranking）
- 关键词研究（用户搜什么）
- On-page SEO：标题标签、meta description、H1-H6 层级
- 内容质量：原创性、深度、用户停留时间
- 外链建设：外部站点引用 → 提升权威性

### 3. 内容层（Content）
- **FAQ 结构化内容**：针对长尾问题（用户搜 "独立站怎么建"）
- **知识库/内容库**：系统性文章矩阵，覆盖一个领域的全部问题
- **关键词集群**：一个核心词 + N 个长尾词组成内容组

### 4. 平台层（Platform）
- **GitHub**：README 优化、项目名含关键词、topic 标签 → 被 Google 收录，被 npm/搜索引擎发现
- **npmjs**：package.json 的 description/keywords → npm 站内搜索 + Google 收录
- **其他平台**：Medium、Dev.to、知乎 — 利用高权重域名做外链和引流

## 独立站 GEO 策略

| 阶段 | 动作 | 目标 |
|------|------|------|
| 冷启动 | GitHub 项目 + npm 包发布 | 获取初始收录和信任 |
| 内容建设 | 关键词 FAQ + 长文教程 | 覆盖搜索意图 |
| 外链获取 | 平台分发 + 社区引用 | 提升域名权威 |
| AI 优化 | 结构化数据 + 引用标记 | 进入 AI 引擎的训练/检索范围 |

## 相关概念
- [[keyword-research]] — 关键词研究方法
- [[content-strategy]] — 内容矩阵策略
- [[independent-site-seo]] — 独立站 SEO 实操

## 相关实体
- [[google-search-console]] — Google 站长工具
- [[github-seo]] — GitHub 项目搜索优化
- [[npm-seo]] — npm 包发现优化
