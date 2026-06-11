# 贪吃蛇游戏实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建独立可玩的可爱风贪吃蛇游戏（snake.html），触屏 + 键盘操作，含特殊食物系统

**Architecture:** 单 HTML 文件，Canvas 2D 渲染，requestAnimationFrame 游戏循环，localStorage 存高分

**Tech Stack:** HTML5 Canvas, vanilla JavaScript, CSS3

---

## 文件结构

| 文件 | 职责 |
|---|---|
| `snake.html` (新建) | 全部游戏代码：CSS 样式 + Canvas 画布 + 游戏逻辑 |

---

### Task 1: HTML 骨架 + CSS 样式 + Canvas 初始化

**文件:**
- Create: `D:\牛逼666\snake.html`

- [ ] **Step 1: 创建 HTML 结构和 CSS 样式**

写入完整骨架：
- meta viewport 移动适配
- 渐变背景（蜜桃粉紫柔和色调）
- 居中容器 + 顶部分数栏（当前分数 + 最高分）
- Canvas 画布 + 圆角边框
- 底部方向键按钮区域（4 个方向键）
- 游戏结束遮罩层（隐藏）
- 特殊食物状态指示器

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<title>贪吃蛇</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body {
    background: linear-gradient(135deg, #fce4ec, #f3e5f5, #e8eaf6);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
    overflow: hidden;
    touch-action: none;
    user-select: none;
    -webkit-user-select: none;
    -webkit-tap-highlight-color: transparent;
  }
  .game-wrapper {
    background: rgba(255,255,255,0.7);
    backdrop-filter: blur(20px);
    border-radius: 24px;
    padding: 20px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.1), 0 0 0 1px rgba(255,255,255,0.5);
  }
  .score-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding: 0 8px;
  }
  .score-item { text-align: center; }
  .score-label { font-size: 12px; color: #999; }
  .score-value { font-size: 28px; font-weight: 700; color: #5c6bc0; }
  .power-indicator {
    height: 4px;
    background: #e0e0e0;
    border-radius: 2px;
    margin-bottom: 12px;
    overflow: hidden;
    opacity: 0;
    transition: opacity 0.3s;
  }
  .power-indicator.active { opacity: 1; }
  .power-fill {
    height: 100%;
    border-radius: 2px;
    transition: width 0.3s;
  }
  .power-fill.speed  { background: #ff7043; }
  .power-fill.slow   { background: #66bb6a; }
  .power-fill.double { background: #ffa726; }
  .power-fill.ghost  { background: #ab47bc; }
  canvas {
    display: block;
    border-radius: 16px;
    background: rgba(255,255,255,0.5);
    box-shadow: inset 0 2px 8px rgba(0,0,0,0.06);
  }
  .controls {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    margin-top: 16px;
  }
  .ctrl-row { display: flex; gap: 8px; }
  .ctrl-btn {
    width: 56px; height: 56px;
    border-radius: 16px;
    border: none;
    background: rgba(255,255,255,0.8);
    font-size: 24px;
    cursor: pointer;
    transition: all 0.15s;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .ctrl-btn:active { transform: scale(0.9); background: #e8eaf6; }
  .ctrl-btn.empty { visibility: hidden; }

  .game-over-overlay {
    position: fixed; inset: 0;
    background: rgba(0,0,0,0.4);
    display: none;
    align-items: center;
    justify-content: center;
    z-index: 10;
  }
  .game-over-overlay.show { display: flex; }
  .game-over-card {
    background: white;
    border-radius: 28px;
    padding: 40px 32px;
    text-align: center;
    box-shadow: 0 30px 60px rgba(0,0,0,0.2);
  }
  .game-over-card h2 { font-size: 28px; color: #5c6bc0; margin-bottom: 8px; }
  .game-over-card .final-score { font-size: 48px; font-weight: 800; color: #ec407a; }
  .game-over-card .btn-restart {
    margin-top: 24px;
    padding: 14px 48px;
    border: none;
    border-radius: 50px;
    background: linear-gradient(135deg, #7c4dff, #536dfe);
    color: white;
    font-size: 18px;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 8px 24px rgba(124,77,255,0.3);
    transition: all 0.2s;
  }
  .game-over-card .btn-restart:active { transform: scale(0.95); }

  @media (min-width: 768px) {
    .controls { display: none; }
  }
</style>
</head>
<body>
  <div class="game-wrapper">
    <div class="score-bar">
      <div class="score-item">
        <div class="score-label">分数</div>
        <div class="score-value" id="score">0</div>
      </div>
      <div class="score-item">
        <div class="score-label">最高分</div>
        <div class="score-value" id="highScore">0</div>
      </div>
    </div>
    <div class="power-indicator" id="powerBar">
      <div class="power-fill" id="powerFill"></div>
    </div>
    <canvas id="canvas"></canvas>
    <div class="controls" id="controls">
      <div class="ctrl-row">
        <div class="ctrl-btn empty"></div>
        <button class="ctrl-btn" data-dir="up">&#9650;</button>
        <div class="ctrl-btn empty"></div>
      </div>
      <div class="ctrl-row">
        <button class="ctrl-btn" data-dir="left">&#9664;</button>
        <button class="ctrl-btn" data-dir="down">&#9660;</button>
        <button class="ctrl-btn" data-dir="right">&#9654;</button>
      </div>
    </div>
  </div>

  <div class="game-over-overlay" id="gameOverOverlay">
    <div class="game-over-card">
      <h2>游戏结束</h2>
      <div class="final-score" id="finalScore">0</div>
      <p style="color:#999;margin-top:4px;">最高分：<span id="finalHighScore">0</span></p>
      <button class="btn-restart" id="restartBtn">再来一局</button>
    </div>
  </div>

  <script>
    // --- 常量 ---
    const GRID = 20;
    const CELL = 20;
    let W, H;

    const canvas = document.getElementById('canvas');
    const ctx = canvas.getContext('2d');

    // --- DOM ---
    const scoreEl = document.getElementById('score');
    const highScoreEl = document.getElementById('highScore');
    const powerBar = document.getElementById('powerBar');
    const powerFill = document.getElementById('powerFill');
    const overlay = document.getElementById('gameOverOverlay');
    const finalScoreEl = document.getElementById('finalScore');
    const finalHighScoreEl = document.getElementById('finalHighScore');
    const restartBtn = document.getElementById('restartBtn');

    // --- 游戏状态 ---
    let snake, food, specialFood, direction, nextDirection;
    let score, highScore, gameOver, speed, frameCount;
    let powerType, powerTimer;
    let particles;

    function resizeCanvas() {
      const maxW = Math.min(window.innerWidth - 40, 400);
      const maxH = Math.min(window.innerHeight - 320, 400);
      const size = Math.floor(Math.min(maxW, maxH) / GRID) * GRID;
      canvas.width = size;
      canvas.height = size;
      W = size / CELL;
      H = size / CELL;
    }

    function initGame() {
      resizeCanvas();
      snake = [
        {x: Math.floor(W/2), y: Math.floor(H/2)},
        {x: Math.floor(W/2)-1, y: Math.floor(H/2)},
        {x: Math.floor(W/2)-2, y: Math.floor(H/2)},
      ];
      direction = {x:1, y:0};
      nextDirection = {x:1, y:0};
      score = 0;
      speed = 150; // ms per step
      gameOver = false;
      powerType = null;
      powerTimer = 0;
      frameCount = 0;
      particles = [];
      specialFood = null;
      spawnFood();
      updateScoreDisplay();
      overlay.classList.remove('show');
      updatePowerBar();
    }
  </script>
</body>
</html>
```

- [ ] **Step 2: 浏览器打开 snake.html 验证骨架**

打开 `snake.html`，确认看到分数栏、空白 canvas、底部方向键。

- [ ] **Step 3: Commit**

```bash
git add snake.html
git commit -m "feat: 贪吃蛇 HTML 骨架 + CSS 样式"
```

---

### Task 2: 游戏循环 + Canvas 渲染

**文件:**
- Modify: `D:\牛逼666\snake.html` — 完善 initGame()，添加渲染函数和游戏循环

- [ ] **Step 1: 添加绘制函数**

在 `<script>` 中 initGame() 之前添加：

```javascript
function drawGrid() {
  ctx.strokeStyle = 'rgba(0,0,0,0.04)';
  ctx.lineWidth = 0.5;
  for (let x = 0; x <= W; x++) {
    ctx.beginPath();
    ctx.moveTo(x * CELL, 0);
    ctx.lineTo(x * CELL, H * CELL);
    ctx.stroke();
  }
  for (let y = 0; y <= H; y++) {
    ctx.beginPath();
    ctx.moveTo(0, y * CELL);
    ctx.lineTo(W * CELL, y * CELL);
    ctx.stroke();
  }
}

function drawSnake() {
  snake.forEach((seg, i) => {
    const x = seg.x * CELL, y = seg.y * CELL;
    const pad = 2, r = 6;
    // 身体
    if (i === 0) {
      ctx.fillStyle = '#7c4dff';
    } else {
      const t = i / Math.max(snake.length - 1, 1);
      const g = Math.floor(200 - t * 100);
      ctx.fillStyle = `rgb(160,${g},255)`;
    }
    ctx.beginPath();
    ctx.roundRect(x + pad, y + pad, CELL - pad*2, CELL - pad*2, r);
    ctx.fill();

    // 头部眼睛
    if (i === 0) {
      ctx.fillStyle = 'white';
      const ex = x + CELL/2, ey = y + CELL/3;
      ctx.beginPath();
      ctx.arc(ex - 2, ey, 3, 0, Math.PI*2);
      ctx.arc(ex + 4, ey, 3, 0, Math.PI*2);
      ctx.fill();
      ctx.fillStyle = '#333';
      ctx.beginPath();
      ctx.arc(ex - 1, ey, 1.5, 0, Math.PI*2);
      ctx.arc(ex + 5, ey, 1.5, 0, Math.PI*2);
      ctx.fill();
    }
  });
}

function drawFood() {
  const x = food.x * CELL + CELL/2, y = food.y * CELL + CELL/2;
  ctx.font = `${CELL-2}px sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(food.emoji, x, y);
}

function drawSpecialFood() {
  if (!specialFood) return;
  const pulse = Math.sin(Date.now() / 200) * 1.5;
  const x = specialFood.x * CELL + CELL/2, y = specialFood.y * CELL + CELL/2;
  ctx.save();
  ctx.font = `${CELL + pulse}px sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(specialFood.emoji, x, y);
  // 光晕
  ctx.beginPath();
  ctx.arc(x, y, CELL/2 + 3, 0, Math.PI*2);
  ctx.strokeStyle = 'rgba(255,200,0,0.4)';
  ctx.lineWidth = 2;
  ctx.stroke();
  ctx.restore();
}

function drawParticles() {
  particles.forEach((p, i) => {
    p.x += p.vx;
    p.y += p.vy;
    p.life -= 0.03;
    p.vy += 0.1; // gravity
    if (p.life <= 0) { particles.splice(i,1); return; }
    ctx.globalAlpha = p.life;
    ctx.fillStyle = p.color;
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.size, 0, Math.PI*2);
    ctx.fill();
  });
  ctx.globalAlpha = 1;
}

function render() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  drawGrid();
  drawFood();
  drawSpecialFood();
  drawSnake();
  drawParticles();
}
```

- [ ] **Step 2: 添加食物生成函数**

```javascript
const FOOD_EMOJIS = ['🍎','🍊','🍇','🍓','🍒','🍉','🍑','🥝','🍌','🫐'];
const SPECIAL_FOODS = [
  { type: 'speed',  emoji: '⚡', color: '#ff7043' },
  { type: 'slow',   emoji: '🐢', color: '#66bb6a' },
  { type: 'double', emoji: '💎', color: '#ffa726' },
  { type: 'ghost',  emoji: '👻', color: '#ab47bc' },
];

function randomFoodPos() {
  while (true) {
    const pos = { x: Math.floor(Math.random() * W), y: Math.floor(Math.random() * H) };
    if (!snake.some(s => s.x === pos.x && s.y === pos.y)) return pos;
  }
}

function spawnFood() {
  food = { ...randomFoodPos(), emoji: FOOD_EMOJIS[Math.floor(Math.random() * FOOD_EMOJIS.length)] };
}

function spawnSpecialFood() {
  if (specialFood) return;
  if (Math.random() < 0.3) { // 30% 几率出现
    const sp = SPECIAL_FOODS[Math.floor(Math.random() * SPECIAL_FOODS.length)];
    specialFood = { ...randomFoodPos(), ...sp };
  }
}
```

- [ ] **Step 3: 添加游戏循环和步进逻辑**

```javascript
let lastStep = 0;

function gameLoop(timestamp) {
  if (gameOver) { requestAnimationFrame(gameLoop); return; }

  frameCount++;

  if (!lastStep) lastStep = timestamp;
  const effectiveSpeed = powerType === 'speed' ? speed / 2 : powerType === 'slow' ? speed * 2 : speed;

  if (timestamp - lastStep >= effectiveSpeed) {
    step();
    lastStep = timestamp;
  }

  // 特殊食物计时
  if (specialFood && frameCount % 60 === 0) {
    specialFood._timer = (specialFood._timer || 0) + 1;
    if (specialFood._timer >= 5) specialFood = null;
  }

  // 特殊效果计时
  if (powerType && frameCount % 60 === 0) {
    powerTimer--;
    if (powerTimer <= 0) { powerType = null; updatePowerBar(); }
    updatePowerBar();
  }

  // 定期尝试生成特殊食物
  if (!specialFood && frameCount % 180 === 0) spawnSpecialFood();

  render();
  requestAnimationFrame(gameLoop);
}
```

- [ ] **Step 4: 浏览器验证**

打开 snake.html，应看到蛇静止不动（step 还没连接方向控制），有食物 emoji 随机出现。

- [ ] **Step 5: Commit**

```bash
git add snake.html
git commit -m "feat: 游戏循环 + Canvas 渲染"
```

---

### Task 3: 蛇的移动 + 食物吃掉 + 碰撞检测

**文件:**
- Modify: `D:\牛逼666\snake.html` — 完善 step() 函数

- [ ] **Step 1: 实现 step() 核心逻辑**

```javascript
function spawnParticles(x, y, color) {
  for (let i = 0; i < 8; i++) {
    particles.push({
      x: x * CELL + CELL/2,
      y: y * CELL + CELL/2,
      vx: (Math.random() - 0.5) * 4,
      vy: (Math.random() - 0.5) * 4 - 2,
      size: 2 + Math.random() * 3,
      color: color,
      life: 1,
    });
  }
}

function step() {
  direction = { ...nextDirection };
  const head = { x: snake[0].x + direction.x, y: snake[0].y + direction.y };

  // 穿墙检查
  if (powerType === 'ghost') {
    head.x = ((head.x % W) + W) % W;
    head.y = ((head.y % H) + H) % H;
  } else if (head.x < 0 || head.x >= W || head.y < 0 || head.y >= H) {
    endGame();
    return;
  }

  // 撞自己
  if (snake.some(s => s.x === head.x && s.y === head.y)) {
    endGame();
    return;
  }

  snake.unshift(head);

  // 吃普通食物
  if (head.x === food.x && head.y === food.y) {
    const points = powerType === 'double' ? 20 : 10;
    score += points;
    spawnParticles(food.x, food.y, '#ff9800');
    spawnFood();
    // 加速
    if (speed > 60) speed -= 1;
    updateScoreDisplay();
  }
  // 吃特殊食物
  else if (specialFood && head.x === specialFood.x && head.y === specialFood.y) {
    powerType = specialFood.type;
    powerTimer = 5;
    spawnParticles(specialFood.x, specialFood.y, specialFood.color);
    specialFood = null;
    updatePowerBar();
  } else {
    snake.pop();
  }
}

function endGame() {
  gameOver = true;
  if (score > highScore) {
    highScore = score;
    localStorage.setItem('snakeHighScore', highScore);
  }
  finalScoreEl.textContent = score;
  finalHighScoreEl.textContent = highScore;
  overlay.classList.add('show');
  updateScoreDisplay();
}

function updateScoreDisplay() {
  scoreEl.textContent = score;
  highScoreEl.textContent = highScore;
}

function updatePowerBar() {
  if (powerType) {
    powerBar.classList.add('active');
    powerFill.className = 'power-fill ' + powerType;
    powerFill.style.width = (powerTimer / 5 * 100) + '%';
  } else {
    powerBar.classList.remove('active');
  }
}
```

- [ ] **Step 2: 在 initGame() 中加载最高分**

在 initGame() 函数开头添加：

```javascript
highScore = parseInt(localStorage.getItem('snakeHighScore') || '0');
```

- [ ] **Step 3: 在 initGame() 末尾启动循环**

```javascript
lastStep = 0;
requestAnimationFrame(gameLoop);
```

- [ ] **Step 4: 浏览器验证**

打开游戏，蛇应该向右移动，但还无法控制方向。撞墙应触发游戏结束弹窗。

- [ ] **Step 5: Commit**

```bash
git add snake.html
git commit -m "feat: 蛇移动 + 食物 + 碰撞 + 游戏结束"
```

---

### Task 4: 方向控制（键盘 + 触屏 + 按钮）

**文件:**
- Modify: `D:\牛逼666\snake.html` — 在 initGame() 中添加事件绑定

- [ ] **Step 1: 添加方向切换函数和键盘事件**

```javascript
function setDirection(dx, dy) {
  // 禁止反向
  if (dx !== 0 && direction.x === -dx) return;
  if (dy !== 0 && direction.y === -dy) return;
  if (dx === 0 && dy === 0) return;
  nextDirection = { x: dx, y: dy };
}

// 在 initGame() 中添加键盘事件
document.addEventListener('keydown', (e) => {
  const keyMap = {
    'ArrowUp':    [0,-1], 'ArrowDown':  [0,1],
    'ArrowLeft':  [-1,0], 'ArrowRight': [1,0],
    'w': [0,-1], 's': [0,1], 'a': [-1,0], 'd': [1,0],
    'W': [0,-1], 'S': [0,1], 'A': [-1,0], 'D': [1,0],
  };
  const dir = keyMap[e.key];
  if (dir) { e.preventDefault(); setDirection(dir[0], dir[1]); }
});
```

- [ ] **Step 2: 添加触屏滑动事件**

```javascript
let touchStart = null;

canvas.addEventListener('touchstart', (e) => {
  e.preventDefault();
  touchStart = { x: e.touches[0].clientX, y: e.touches[0].clientY };
}, { passive: false });

canvas.addEventListener('touchmove', (e) => {
  e.preventDefault();
}, { passive: false });

canvas.addEventListener('touchend', (e) => {
  if (!touchStart) return;
  const touch = e.changedTouches[0];
  const dx = touch.clientX - touchStart.x;
  const dy = touch.clientY - touchStart.y;
  const threshold = 20;
  if (Math.abs(dx) < threshold && Math.abs(dy) < threshold) return;
  if (Math.abs(dx) > Math.abs(dy)) {
    setDirection(dx > 0 ? 1 : -1, 0);
  } else {
    setDirection(0, dy > 0 ? 1 : -1);
  }
  touchStart = null;
});
```

- [ ] **Step 3: 添加方向键按钮事件**

```javascript
document.querySelectorAll('.ctrl-btn[data-dir]').forEach(btn => {
  const dirMap = {
    'up': [0,-1], 'down': [0,1], 'left': [-1,0], 'right': [1,0],
  };
  btn.addEventListener('click', () => {
    const dir = dirMap[btn.dataset.dir];
    setDirection(dir[0], dir[1]);
  });
  btn.addEventListener('touchstart', (e) => {
    e.preventDefault();
    const dir = dirMap[btn.dataset.dir];
    setDirection(dir[0], dir[1]);
  });
});
```

- [ ] **Step 4: 添加重新开始按钮事件**

```javascript
restartBtn.addEventListener('click', initGame);
restartBtn.addEventListener('touchstart', (e) => { e.preventDefault(); initGame(); });
```

- [ ] **Step 5: 浏览器验证**

打开游戏：键盘方向键、触屏滑动、底部按钮三种方式都能控制蛇的方向。反向操作被阻止。

- [ ] **Step 6: Commit**

```bash
git add snake.html
git commit -m "feat: 方向控制 — 键盘 + 触屏 + 按钮"
```

---

### Task 5: 最终打磨 + 提交

**文件:**
- Modify: `D:\牛逼666\snake.html` — 润色调整

- [ ] **Step 1: 添加窗口大小变化响应**

在 initGame() 中添加：

```javascript
window.addEventListener('resize', () => {
  if (gameOver) return;
  resizeCanvas();
  // 确保蛇不超出新边界
  const outOfBounds = snake.some(s => s.x >= W || s.y >= H);
  if (outOfBounds) endGame();
});
```

- [ ] **Step 2: 移动端禁用双击缩放和长按菜单**

确认 CSS 中已有 `touch-action: none; user-select: none; -webkit-user-select: none;`。

在 body 上确认这些样式。

- [ ] **Step 3: 全量测试**

1. 桌面端键盘控制正常
2. 手机触屏滑动灵敏
3. 手机底部按钮可用
4. 吃食物蛇变长，分数增加
5. 特殊食物出现，效果生效
6. 加速时蛇更快，减速时更慢
7. 双倍分时吃食物得 20 分
8. 穿墙时撞墙不死，穿到对面
9. 撞墙/撞自己游戏结束
10. 最高分 localStorage 持久化
11. 重新开始正常
12. 窗口缩放后游戏仍正常

- [ ] **Step 4: Commit**

```bash
git add snake.html
git commit -m "feat: 最终打磨 — 响应式 + 移动端优化"
```
