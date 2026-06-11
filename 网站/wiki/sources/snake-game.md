---
title: "可爱风贪吃蛇"
type: source
category: project
privacy: public
tags: [game, html5, canvas, snake, touch-controls, particles]
created: 2026-06-10
updated: 2026-06-11
source_path: snake-game/snake.html
---

# 可爱风贪吃蛇 — 项目摘要

## 概述

HTML5 Canvas 贪吃蛇游戏，采用可爱/卡哇伊风格设计，支持触屏和键盘双操控，含特殊食物系统和粒子特效。

## 技术栈

| 层 | 技术 |
|---|------|
| 渲染 | HTML5 Canvas 2D |
| 样式 | 渐变背景 + 毛玻璃效果 |
| 交互 | 触屏滑动 + 键盘方向键 |
| 特效 | 粒子系统（Canvas 绘制） |

## 核心特性

1. **双操控模式**：
   - 触屏：滑动方向控制
   - 键盘：方向键 / WASD
2. **特殊食物系统**：不同食物有不同效果（加分、加速、减速、穿墙等）
3. **粒子特效**：吃食物时爆发粒子动画
4. **毛玻璃 UI**：`backdrop-filter: blur()` 半透明卡片风格
5. **分数系统**：实时分数显示

## 设计风格

- 粉色/紫色渐变背景
- 圆角毛玻璃游戏容器
- 柔和阴影与光泽边框
- 适合移动端竖屏游玩

## 相关概念

- [[html5-canvas-game]] — HTML5 Canvas 游戏开发基础
- [[particle-effects]] — 粒子特效实现
