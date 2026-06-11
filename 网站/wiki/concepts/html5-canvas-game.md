---
title: "HTML5 Canvas 游戏"
type: concept
category: project
privacy: public
tags: [html5, canvas, game-development, frontend]
created: 2026-06-11
updated: 2026-06-11
confidence: medium
---

# HTML5 Canvas 游戏

## 核心概念

使用 HTML5 `<canvas>` 元素 + JavaScript 的 2D 渲染上下文构建游戏，所有渲染由 JS 控制，无需 DOM 操作。

## 基础框架

```javascript
const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');

function gameLoop() {
  update();  // 更新游戏状态
  draw();    // 绘制画面
  requestAnimationFrame(gameLoop);
}
gameLoop();
```

## 适用范围

- 2D 游戏（平台、弹幕、贪吃蛇等）
- 粒子特效系统
- 数据可视化动画

## 本项目案例

- [[snake-game]]：Canvas 贪吃蛇 + 粒子特效 + 触屏操控
