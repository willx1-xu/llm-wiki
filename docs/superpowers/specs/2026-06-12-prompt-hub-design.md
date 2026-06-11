# 提示词库 (Prompt Hub) 设计文档

## 概述

一个按真实场景分类的 AI 提示词管理平台。用户输入模糊需求（如"谷歌深度收录外贸独立站"），系统通过 AI 自动补齐为专业级可直接使用的提示词。支持手工录入、URL 抓取、批量采集三种入库方式，后台管理 + 公开浏览双模式。

## 架构

```
提示词项目/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 入口 + 生命周期
│   ├── config.py            # 环境变量 & 配置
│   ├── database.py          # SQLAlchemy async engine + session
│   │
│   ├── models/              # ORM 模型
│   │   ├── category.py      # 分类（树形结构）
│   │   ├── tag.py           # 标签
│   │   ├── prompt.py        # 提示词
│   │   └── version.py       # 版本历史
│   │
│   ├── routes/              # 路由层（只处理请求/响应）
│   │   ├── admin.py         # 后台 CRUD
│   │   ├── public.py        # 公开浏览/搜索
│   │   └── api.py           # REST API（爬虫触发、AI 增强等）
│   │
│   ├── services/            # 业务逻辑层
│   │   ├── prompt_service.py
│   │   ├── enhance_service.py   # AI 增强引擎
│   │   ├── scrape_service.py    # URL 抓取
│   │   └── crawl_service.py     # 批量采集调度
│   │
│   ├── templates/           # Jinja2 模板
│   │   ├── base.html
│   │   ├── admin/
│   │   └── public/
│   │
│   └── static/              # CSS + HTMX + Alpine.js
│
├── alembic/                 # 数据库迁移
├── requirements.txt
├── Dockerfile
└── render.yaml
```

**技术选型**：FastAPI + SQLAlchemy 2.0 (async) + Alembic + PostgreSQL/SQLite + Jinja2 + HTMX + Alpine.js + httpx + BeautifulSoup4 + DeepSeek API

## 数据模型

### Category（分类 - 树形）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| name | str | 分类名 |
| slug | str | URL 友好标识 |
| parent_id | UUID? | 父分类，可空 |
| description | str? | 分类描述 |
| icon | str? | 图标 |
| sort_order | int | 排序 |

示例层级：`内容创作 > 视频制作 > YouTube 脚本`

### Tag（标签 - 多对多）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| name | str | 标签名 |
| slug | str | URL 友好标识 |

### Prompt（提示词 - 核心）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| title | str | 标题 |
| slug | str | URL 友好标识 |
| content | text | 提示词正文 |
| description | str? | 简短描述 |
| scenario_desc | str? | 使用场景描述 |
| difficulty | enum | 初级/中级/高级 |
| expected_output | text? | 预期输出示例 |
| model_suitability | str? | 适用模型 |
| source_url | str? | 来源 URL |
| source_type | enum | 手工/URL抓取/批量采集/AI增强 |
| is_published | bool | 是否发布 |
| is_private | bool | 是否私密 |
| view_count | int | 浏览次数 |
| category_id | FK | 关联分类 |
| created_at | datetime | |
| updated_at | datetime | |

### PromptTag（关联表）
| 字段 | 类型 |
|------|------|
| prompt_id | FK |
| tag_id | FK |

### PromptVersion（版本历史）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| prompt_id | FK | 关联提示词 |
| version_number | int | 版本号 |
| content | text | 当时的完整内容 |
| change_note | str? | 修改说明 |
| created_at | datetime | |

## 功能模块

### 后台管理
- 提示词 CRUD：创建/编辑/删除，编辑时自动保存版本历史
- 分类树管理：增删改、排序
- 标签管理 + 关联提示词
- 导入方式切换：手工录入 / 粘贴 URL 抓取 / 配置爬虫规则 / AI 增强创建
- 审核队列：批量采集的提示词先入队列，审核后发布
- 公开/私密一键切换

### AI 提示词增强（核心差异化）
用户输入模糊关键词 → DeepSeek API 自动生成结构化专业提示词：

```
用户输入："谷歌深度收录级别的独立站"
        │
        ▼
  DeepSeek API 增强
        │
        ▼
  输出：
  - 标题：自动提炼
  - 推荐分类：自动匹配树形分类
  - 提示词正文：从程序员 + 领域专家双视角编写，可直接复制使用
  - 适用模型建议：GPT-4 / Claude / DeepSeek 等
  - 预期输出示例
  - 难度评级
        │
        ▼
  预填到编辑表单 → 用户修改/直接保存
```

### 公开页面
- 分类树侧边栏 + 提示词列表，按分类过滤
- 全文搜索（标题 + 正文 + 标签）
- 详情页：一键复制、版本历史查看、来源链接跳转
- 筛选：热度、难度、模型

### URL 抓取
- 输入 URL → httpx + BeautifulSoup 抓取页面
- 启发式 + AI 提取提示词内容块（识别 markdown 代码块、结构化段落、列表）
- 置信度评分：高（90%+）自动填充，低标记人工复核
- 预填表单确认后入库

### 批量采集
- 配置：目标域名、CSS 选择器（列表/内容/翻页）、采集频率
- 后台任务异步执行
- 结果入审核队列
- 隐私约束：只抓公开页面、遵守 robots.txt、必须标注来源 URL

### API
- `GET /api/prompts` — 搜索/列表
- `GET /api/prompts/{id}` — 单条详情
- `POST /api/prompts/enhance` — AI 增强生成（需认证）
- `POST /api/prompts/scrape` — URL 抓取触发（需认证）

## 隐私边界

- 只抓取公开页面，不爬需登录的页面
- robots.txt 自动检查并遵守
- 每条提示词必须标注来源 URL
- 私密提示词仅后台可见，不暴露到公开页面
- API 端点需要 Bearer Token 认证
- 私密提示词不参与公开搜索和列表

## 开发阶段

| 阶段 | 内容 |
|------|------|
| P0 | 数据库模型 + Alembic 迁移 + 管理后台 CRUD |
| P1 | 公开浏览页 + 搜索 + 分类过滤 |
| P2 | AI 提示词增强（核心差异化） |
| P3 | URL 抓取 + 批量采集 |
