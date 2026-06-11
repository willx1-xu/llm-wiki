import os
import re
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import httpx

load_dotenv(Path(__file__).parent / ".env")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"

app = FastAPI()

SYSTEM_PROMPT = """You are a senior full-stack developer. The user will describe an app or website they want. Generate a COMPLETE, self-contained, beautiful HTML page with inline CSS and JavaScript.

RULES:
- Output ONLY the raw HTML code. No markdown, no code fences, no explanations.
- Use modern design: nice colors, shadows, rounded corners, clean typography.
- Make it mobile-responsive.
- All CSS and JS must be inline, no external files.
- You may use CDN links for libraries (Tailwind, Font Awesome, etc).
- Use Chinese for any text content.
- Make the page interactive and functional, not just static.
- The first line must be <!DOCTYPE html>

CRITICAL - Real media sources:
- For music/audio apps, use these real MP3 URLs (SoundHelix, guaranteed working):
  https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3 (Song-2 through Song-16)
- For video, use: https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/Big_Buck_Bunny_720_10s_1MB.mp4
- For images, use: https://picsum.photos/400/300 (random real images)
- NEVER invent/fabricate media URLs. Always use the real sources listed above.
- For a music player, pre-populate the playlist with SoundHelix songs as defaults.
- You can also integrate the free iTunes Search API (no key needed) to let users search real songs:
  GET https://itunes.apple.com/search?term=SEARCH_TERM&media=music&limit=20
  Each result has .previewUrl (30s clip), .trackName, .artistName, .artworkUrl100."""


class GenerateRequest(BaseModel):
    prompt: str


def build_user_prompt(raw_prompt: str) -> str:
    """根据用户需求关键词，自动注入真实媒体源要求"""
    keywords_media = {
        "音乐": """
【媒体源要求 - 必须严格遵守，这是用户能听到音乐的唯一方式】
你必须通过 iTunes Search API 获取真实歌曲，previewUrl 就是真正的试听链接。
API 用法（免费，无需 Key，直接在 JS 里 fetch）：

  const term = encodeURIComponent('周杰伦'); // 搜索词
  const url = `https://itunes.apple.com/search?term=${term}&media=music&limit=15`;
  const res = await fetch(url);
  const data = await res.json();
  // data.results 里每首歌有：
  //   .trackName    — 真实歌名
  //   .artistName   — 真实歌手
  //   .previewUrl   — 真实 30 秒试听（直接用这个当音乐源）
  //   .artworkUrl100 — 真实专辑封面

- 页面加载时自动 fetch 一个默认歌单，把 previewUrl 设为 Audio 的 src。
- 加一个搜索框让用户搜真歌。
- 禁止编造任何 mp3 URL，禁止用 SoundHelix 或任何示例链接。
- 禁止用 emoji 做专辑封面，必须用 artworkUrl100。
- 歌曲列表里曲目名称必须和 audio.src 对应，不能张冠李戴。""",
        "视频": """
【媒体源要求】
- 使用 <video> 标签播放真实视频。
- 测试视频: https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/Big_Buck_Bunny_720_10s_1MB.mp4""",
        "图片": """
【媒体源要求】
- 使用真实图片 URL: https://picsum.photos/400/300 (可调尺寸)""",
    }

    for keyword, instruction in keywords_media.items():
        if keyword in raw_prompt:
            return raw_prompt + "\n\n" + instruction
    return raw_prompt


def extract_html(raw: str) -> str:
    """从 DeepSeek 回复中提取 HTML 代码"""
    # 去掉 ```html ... ``` 包裹
    m = re.search(r"```html\s*(.*?)\s*```", raw, re.DOTALL)
    if m:
        return m.group(1).strip()
    m = re.search(r"```\s*(.*?)\s*```", raw, re.DOTALL)
    if m:
        return m.group(1).strip()
    # 如果以 <!DOCTYPE 或 <html 开头就直接返回
    if raw.strip().startswith("<!DOCTYPE") or raw.strip().startswith("<html"):
        return raw.strip()
    return raw.strip()


@app.get("/", response_class=HTMLResponse)
async def home():
    return PAGE_HTML


@app.post("/api/generate")
async def generate(req: GenerateRequest):
    if not DEEPSEEK_API_KEY:
        raise HTTPException(status_code=500, detail="未配置 DEEPSEEK_API_KEY，请在 .env 文件中填写")

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120)) as client:
            resp = await client.post(
                DEEPSEEK_URL,
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": build_user_prompt(req.prompt)},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 8192,
                },
            )
            data = resp.json()

        if resp.status_code != 200:
            detail = data.get("error", {}).get("message", str(data))
            raise HTTPException(status_code=resp.status_code, detail=f"DeepSeek API 错误: {detail}")

        if "choices" not in data or not data["choices"]:
            raise HTTPException(status_code=500, detail="DeepSeek 返回为空")

        raw = data["choices"][0]["message"]["content"]
        html_code = extract_html(raw)
        return {"code": html_code, "raw": raw}

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="DeepSeek API 响应超时，请重试")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"请求 DeepSeek 失败: {str(e)}")


# ============================================================
# 前端页面 (内嵌)
# ============================================================

PAGE_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI 代码生成器</title>
<style>
  :root {
    --bg: #0f172a;
    --panel: #1e293b;
    --border: #334155;
    --text: #e2e8f0;
    --muted: #94a3b8;
    --accent: #6366f1;
    --accent-hover: #818cf8;
    --success: #22c55e;
    --danger: #ef4444;
    --radius: 10px;
  }
  * { margin:0; padding:0; box-sizing:border-box; }
  body {
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    background: var(--bg);
    color: var(--text);
    height: 100vh;
    display: flex;
  }

  /* ---- 左侧面板 ---- */
  .left {
    width: 50%;
    display: flex;
    flex-direction: column;
    border-right: 1px solid var(--border);
  }
  .top {
    padding: 20px;
    border-bottom: 1px solid var(--border);
  }
  .top h1 {
    font-size: 22px;
    margin-bottom: 6px;
    background: linear-gradient(135deg, var(--accent), #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  .top p { color: var(--muted); font-size:13px; }
  .input-area {
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    border-bottom: 1px solid var(--border);
  }
  .input-area textarea {
    width: 100%;
    height: 120px;
    background: var(--bg);
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 14px;
    font-size: 14px;
    font-family: inherit;
    resize: vertical;
    outline: none;
    transition: border .2s;
  }
  .input-area textarea:focus { border-color: var(--accent); }
  .input-area textarea::placeholder { color: #64748b; }

  .btn-row { display:flex; gap:10px; }
  .btn {
    padding: 10px 24px;
    border: none;
    border-radius: var(--radius);
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: all .2s;
  }
  .btn-primary { background: var(--accent); color: #fff; flex:1; }
  .btn-primary:hover { background: var(--accent-hover); }
  .btn-primary:disabled { opacity: .5; cursor: not-allowed; }
  .btn-secondary { background: var(--panel); color: var(--text); border: 1px solid var(--border); }
  .btn-secondary:hover { background: var(--border); }

  .code-panel {
    flex: 1;
    overflow: auto;
    padding: 16px;
    position: relative;
  }
  .code-panel pre {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 16px;
    font-size: 13px;
    line-height: 1.6;
    overflow: auto;
    white-space: pre-wrap;
    word-break: break-all;
    max-height: 100%;
    font-family: 'Cascadia Code', 'Fira Code', Consolas, monospace;
  }
  .empty-hint {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: var(--muted);
    font-size: 14px;
    flex-direction: column;
    gap: 10px;
  }
  .empty-hint .icon { font-size: 48px; opacity: .3; }

  /* ---- 右侧面板 ---- */
  .right {
    width: 50%;
    display: flex;
    flex-direction: column;
  }
  .right-header {
    padding: 12px 20px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 13px;
    color: var(--muted);
  }
  .preview-frame {
    flex: 1;
    border: none;
    background: #fff;
  }

  /* ---- Loading ---- */
  .spinner {
    display: inline-block;
    width: 16px; height: 16px;
    border: 2px solid transparent;
    border-top-color: #fff;
    border-radius: 50%;
    animation: spin .6s linear infinite;
    vertical-align: middle;
    margin-right: 6px;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* ---- Toast ---- */
  .toast {
    position: fixed;
    top: 20px;
    right: 20px;
    background: var(--danger);
    color: #fff;
    padding: 12px 20px;
    border-radius: var(--radius);
    font-size: 14px;
    z-index: 999;
    animation: slideIn .3s ease;
    max-width: 400px;
  }
  @keyframes slideIn { from { transform: translateX(100%); opacity:0; } to { transform: translateX(0); opacity:1; } }

  @media (max-width: 768px) {
    body { flex-direction: column; }
    .left, .right { width: 100%; height: 50vh; }
  }
</style>
</head>
<body>

<div class="left">
  <div class="top">
    <h1>AI 代码生成器</h1>
    <p>描述你想要的应用，AI 自动生成并预览</p>
  </div>

  <div class="input-area">
    <textarea id="promptInput" placeholder="例如：做一个带番茄钟功能的任务管理页面，可以添加、删除、标记完成"></textarea>
    <div class="btn-row">
      <button class="btn btn-primary" id="generateBtn" onclick="generate()">
        生成代码
      </button>
      <button class="btn btn-secondary" onclick="copyCode()">复制代码</button>
      <button class="btn btn-secondary" onclick="downloadCode()">下载 HTML</button>
    </div>
  </div>

  <div class="code-panel" id="codePanel">
    <div class="empty-hint">
      <div class="icon">&#x1F4A1;</div>
      <div>输入需求描述，点击"生成代码"开始</div>
    </div>
  </div>
</div>

<div class="right">
  <div class="right-header">
    <span>实时预览</span>
    <span id="statusDot" style="color: var(--muted);">&#x25CF; 等待输入</span>
  </div>
  <iframe class="preview-frame" id="previewFrame" sandbox="allow-scripts allow-same-origin allow-forms"></iframe>
</div>

<script>
let currentCode = '';

async function generate() {
  const prompt = document.getElementById('promptInput').value.trim();
  if (!prompt) return;

  const btn = document.getElementById('generateBtn');
  const statusDot = document.getElementById('statusDot');
  const codePanel = document.getElementById('codePanel');

  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>生成中...';
  statusDot.innerHTML = '&#x25CF; 生成中...';
  statusDot.style.color = '#f59e0b';

  try {
    const resp = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt }),
    });

    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.detail || '请求失败');
    }

    const data = await resp.json();
    currentCode = data.code;

    // 显示代码
    codePanel.innerHTML = `<pre>${escapeHtml(data.code)}</pre>`;

    // 预览
    const frame = document.getElementById('previewFrame');
    frame.srcdoc = data.code;

    statusDot.innerHTML = '&#x25CF; 生成完成';
    statusDot.style.color = '#22c55e';

  } catch (e) {
    showToast(e.message);
    statusDot.innerHTML = '&#x25CF; 生成失败';
    statusDot.style.color = '#ef4444';
  } finally {
    btn.disabled = false;
    btn.innerHTML = '生成代码';
  }
}

function escapeHtml(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function copyCode() {
  if (!currentCode) return;
  navigator.clipboard.writeText(currentCode).then(() => showToast('已复制到剪贴板', true));
}

function downloadCode() {
  if (!currentCode) return;
  const blob = new Blob([currentCode], { type: 'text/html' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'generated.html';
  a.click();
  URL.revokeObjectURL(url);
}

function showToast(msg, isSuccess) {
  const existing = document.querySelector('.toast');
  if (existing) existing.remove();
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.style.background = isSuccess ? '#22c55e' : 'var(--danger)';
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

// Enter 提交
document.getElementById('promptInput').addEventListener('keydown', e => {
  if (e.key === 'Enter' && e.ctrlKey) generate();
});
</script>
</body>
</html>"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
