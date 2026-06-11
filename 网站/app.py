import os, re
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
import httpx

BASE = Path(__file__).parent
load_dotenv(BASE / ".env")
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY")
DS_URL = "https://api.deepseek.com/chat/completions"
SCHEMA = (BASE / "schema.md").read_text("utf-8")

app = FastAPI(title="LLM Wiki · 知识库")

# ── helpers ──────────────────────────────────────────────

WIKI_ROOT = BASE / "wiki"
RAW_ROOT = BASE / "raw"

def safe_path(rel: str) -> Path:
    p = (BASE / rel).resolve()
    if not str(p).startswith(str(BASE.resolve())):
        raise HTTPException(403, "path traversal denied")
    return p

def tree(dir_path: Path, prefix: str = "") -> list:
    items = []
    for p in sorted(dir_path.iterdir()):
        rel = str(p.relative_to(BASE)).replace("\\", "/")
        if p.is_dir():
            items.append({"name": p.name, "type": "folder", "path": rel, "children": tree(p, rel)})
        elif p.suffix == ".md":
            items.append({"name": p.name, "type": "file", "path": rel})
    return items

def parse_frontmatter(text: str) -> tuple[dict, str]:
    fm = {}
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].strip().split("\n"):
                line = line.strip()
                if ":" in line:
                    k, v = line.split(":", 1)
                    fm[k.strip()] = v.strip()
            body = parts[2]
    return fm, body.strip()

def collect_wikilinks(text: str) -> list[str]:
    return re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', text)

def all_pages() -> list[Path]:
    pages = []
    for p in WIKI_ROOT.rglob("*.md"):
        pages.append(p)
    return pages

def build_graph_data() -> dict:
    nodes = []
    edges = []
    node_ids = set()
    pages = all_pages()
    # First pass: collect nodes
    for p in pages:
        name = p.stem
        if name in node_ids:
            continue
        node_ids.add(name)
        text = p.read_text("utf-8")
        fm, _ = parse_frontmatter(text)
        rel = str(p.relative_to(WIKI_ROOT)).replace("\\", "/")
        nodes.append({
            "id": name,
            "label": fm.get("title", name).strip('"'),
            "type": fm.get("type", "concept"),
            "path": "wiki/" + rel.replace("\\", "/"),
            "inCount": 0,
            "outCount": 0
        })
    # Second pass: build edges & count connections
    node_map = {n["id"]: n for n in nodes}
    edge_set = set()
    for p in pages:
        text = p.read_text("utf-8")
        links = collect_wikilinks(text)
        src = p.stem
        for tgt in links:
            if tgt in node_ids and tgt != src:
                key = tuple(sorted([src, tgt]))
                if key not in edge_set:
                    edge_set.add(key)
                    edges.append({"source": src, "target": tgt})
                    if node_map.get(src):
                        node_map[src]["outCount"] += 1
                    if node_map.get(tgt):
                        node_map[tgt]["inCount"] += 1
    # Compute weight = total connections (capped for sizing)
    max_conn = max((n["inCount"] + n["outCount"] for n in nodes), default=1)
    for n in nodes:
        total = n["inCount"] + n["outCount"]
        n["weight"] = round(total / max(max_conn, 1), 2)
        n["radius"] = 6 + int(n["weight"] * 14)  # 6–20px
    return {"nodes": nodes, "edges": edges}

async def call_llm(system: str, user: str, temperature: float = 0.3) -> str:
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(DS_URL, headers={
            "Authorization": f"Bearer {DEEPSEEK_KEY}",
            "Content-Type": "application/json"
        }, json={
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            "temperature": temperature,
            "max_tokens": 8000
        })
        if r.status_code != 200:
            raise HTTPException(502, f"LLM error: {r.text[:500]}")
        return r.json()["choices"][0]["message"]["content"]

def apply_llm_changes(response: str) -> list[dict]:
    """Parse LLM response for CODE blocks and apply file changes."""
    results = []
    blocks = re.findall(r'```(?:yaml|markdown|md)?\s*\{([^}]+)\}\s*\n(.*?)```', response, re.DOTALL)
    if not blocks:
        blocks = re.findall(r'```(?:yaml|markdown|md)?\s*\n?(FILE:\s*[^\n]+)\n(.*?)```', response, re.DOTALL)
    if not blocks:
        # Fallback: look for sections like "## FILE: path" followed by code blocks
        sections = re.split(r'(?:^|\n)##?\s*FILE:\s*([^\n]+)\n', response)
        if len(sections) > 1:
            for i in range(1, len(sections), 2):
                path_part = sections[i].strip()
                content = sections[i+1] if i+1 < len(sections) else ""
                code_match = re.search(r'```(?:.*?)\n(.*?)```', content, re.DOTALL)
                if code_match:
                    blocks.append((path_part, code_match.group(1)))
    for meta, content in blocks:
        path = meta.strip()
        if isinstance(meta, tuple):
            path = meta[0].strip()
            content = meta[1]
        if not path.endswith(".md"):
            path = path + ".md"
        if ".." in path:
            continue
        full = BASE / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content.strip(), "utf-8")
        results.append({"action": "written", "path": path})
    if not results:
        results.append({"action": "note", "content": response[:500]})
    return results

# ── API routes ──────────────────────────────────────────

@app.get("/api/search")
def search_wiki(q: str = Query(...), limit: int = 15):
    """Full-text search across all wiki pages, ranked by relevance."""
    if not q.strip():
        return []
    keywords = q.lower().split()
    results = []
    for p in all_pages():
        text = p.read_text("utf-8")
        fm, body = parse_frontmatter(text)
        title = fm.get("title", p.stem).strip('"')
        tags = fm.get("tags", "")
        ptype = fm.get("type", "page")

        # Score: title match (×10) + tag match (×5) + body match (×1)
        score = 0
        body_lower = body.lower()
        for kw in keywords:
            if kw in p.stem.lower() or kw in title.lower():
                score += 10
            if kw in tags.lower():
                score += 5
            score += body_lower.count(kw)

        if score > 0:
            # Extract snippet around first keyword match
            snippet = ""
            first_idx = 99999
            for kw in keywords:
                idx = body_lower.find(kw)
                if idx != -1 and idx < first_idx:
                    first_idx = idx
            if first_idx < 99999:
                start = max(0, first_idx - 40)
                end = min(len(body), first_idx + 120)
                snippet = ("..." if start > 0 else "") + body[start:end].replace("\n", " ").strip() + ("..." if end < len(body) else "")

            rel_path = str(p.relative_to(WIKI_ROOT)).replace("\\", "/")
            results.append({
                "id": p.stem,
                "title": title,
                "type": ptype,
                "tags": tags,
                "path": "wiki/" + rel_path.replace("\\", "/"),
                "score": score,
                "snippet": snippet,
                "links": collect_wikilinks(text),
                "linkCount": len(collect_wikilinks(text))
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]

@app.get("/api/tree")
def get_tree(dir: str = "wiki"):
    root = BASE / dir
    if not root.exists():
        return []
    return tree(root)

@app.get("/api/page")
def get_page(path: str = Query(...)):
    p = safe_path(path)
    if not p.exists():
        raise HTTPException(404, "page not found")
    text = p.read_text("utf-8")
    fm, body = parse_frontmatter(text)
    return {"path": str(p.relative_to(BASE)).replace("\\", "/"), "frontmatter": fm, "body": body, "links": collect_wikilinks(text)}

@app.post("/api/page")
def save_page(data: dict):
    p = safe_path(data["path"])
    p.parent.mkdir(parents=True, exist_ok=True)
    # Reconstruct markdown with frontmatter
    fm = data.get("frontmatter", {})
    body = data.get("body", "")
    fm_block = "---\n" + "\n".join(f"{k}: {v}" for k, v in fm.items()) + "\n---\n\n"
    p.write_text(fm_block + body, "utf-8")
    return {"ok": True}

@app.delete("/api/page")
def delete_page(path: str = Query(...)):
    """Delete a wiki page by path."""
    p = safe_path(path)
    if not p.exists():
        raise HTTPException(404, "page not found")
    if p.parent == WIKI_ROOT.parent or not str(p).startswith(str(WIKI_ROOT)):
        raise HTTPException(403, "can only delete files inside wiki/")
    p.unlink()
    return {"ok": True, "deleted": path}

@app.post("/api/fetch-url")
async def fetch_url(data: dict):
    """Fetch and extract text content from a URL for ingest."""
    url = data.get("url", "").strip()
    if not url:
        raise HTTPException(400, "url required")
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            r = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; LLMWiki/1.0; +https://github.com/willx1-xu/llm-wiki)"
            })
            if r.status_code != 200:
                raise HTTPException(502, f"HTTP {r.status_code}")
            html = r.text
            # Simple text extraction
            text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL|re.IGNORECASE)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL|re.IGNORECASE)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()
            # Truncate to reasonable size
            title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE|re.DOTALL)
            title = title_match.group(1).strip() if title_match else url
            # Quality check: detect login walls and empty pages
            closed_platforms = ['mp.weixin.qq.com', 'weibo.com', 'xiaohongshu.com', 'douyin.com']
            is_closed = any(domain in url for domain in closed_platforms)
            text_len = len(text)
            warnings = []
            if text_len < 200:
                warnings.append("内容过短（<200字符），可能是登录墙或JS渲染页面，摄入后质量无法保证")
            if is_closed:
                warnings.append(f"该域名属于封闭平台，抓取到的内容可能不完整。建议手动复制原文粘贴")
            return {"ok": True, "title": title[:200], "content": text[:8000], "url": url, "textLength": text_len, "warnings": warnings}
    except Exception as e:
        raise HTTPException(502, f"Fetch failed: {str(e)[:200]}")

@app.post("/api/precheck-ingest")
async def precheck_ingest(data: dict):
    """Check content for ambiguous terms before full ingest."""
    content = data.get("content", "").strip()
    if not content:
        raise HTTPException(400, "content required")

    system = """You are an ambiguity detector. Analyze the input for terms that have MULTIPLE distinct meanings across different domains.

Examples of ambiguous terms:
- "GEO" could mean: (A) Generative/Google Engine Optimization (SEO), or (B) Geography/Geospatial
- "Python" could mean: (A) Programming language, or (B) Snake species
- "苹果" could mean: (A) Apple company, or (B) Apple fruit

For each ambiguous term found, output a JSON array. If nothing is ambiguous, output [].

Format:
```json
[
  {"term": "GEO", "options": ["搜索引擎优化 (SEO)", "地理信息系统 (Geography/GIS)"], "context": "用户在描述...", "suggested": 0}
]
```

Only flag truly ambiguous terms. Don't flag terms that are clear from context."""

    user = f"## Content to check for ambiguities\n\n{content[:3000]}\n\nOutput ONLY the JSON array, no other text."

    try:
        resp = await call_llm(system, user, temperature=0)
        # Extract JSON
        json_match = re.search(r'\[.*\]', resp, re.DOTALL)
        if json_match:
            import json
            ambiguities = json.loads(json_match.group(0))
            return {"ok": True, "ambiguities": ambiguities}
        return {"ok": True, "ambiguities": []}
    except:
        return {"ok": True, "ambiguities": []}

@app.post("/api/ingest")
async def ingest(data: dict):
    content = data.get("content", "").strip()
    title = data.get("title", "Untitled")
    clarifications = data.get("clarifications", [])  # user-confirmed term meanings
    if not content:
        raise HTTPException(400, "content required")

    # Build clarification context
    clarification_note = ""
    if clarifications:
        clarification_note = "\n\n## ⚠️ 术语含义已确认\n用户已确认以下术语的含义，必须严格按此理解：\n"
        for c in clarifications:
            clarification_note += f"- **{c['term']}** = {c['chosen']}\n"

    # Check for existing similar pages
    existing_pages = []
    for p in all_pages():
        text = p.read_text("utf-8")
        fm, body = parse_frontmatter(text)
        existing_pages.append({
            "id": p.stem,
            "title": fm.get("title", p.stem).strip('"'),
            "type": fm.get("type", "page"),
            "body_preview": body[:300]
        })

    # Simple overlap detection
    overlaps = []
    content_lower = content.lower()
    for ep in existing_pages:
        # Check if key terms from existing pages appear in new content
        terms = ep["id"].replace("-", " ").split()
        match_count = sum(1 for t in terms if t.lower() in content_lower)
        if match_count >= len(terms) * 0.5 and len(terms) >= 2:
            overlaps.append(ep)

    # Build existing context for LLM
    existing_summary = "\n".join(
        f"- [{ep['type']}] {ep['title']} (id: {ep['id']})"
        for ep in existing_pages
    )

    index_content = ""
    idx_path = WIKI_ROOT / "index.md"
    if idx_path.exists():
        index_content = idx_path.read_text("utf-8")[:3000]

    overlap_warning = ""
    if overlaps:
        overlap_warning = f"\n\n⚠️ POTENTIAL DUPLICATES DETECTED: The following existing pages overlap with the new content. UPDATE these pages instead of creating duplicates: {json.dumps(overlaps, ensure_ascii=False)}"

    system = SCHEMA + "\n\nYou are a disciplined wiki maintainer. For each extracted piece of knowledge, assign a confidence level (high/medium/low). Skip content with confidence=low. If similar pages exist, UPDATE them instead of creating duplicates. Output each file as:\n\n```markdown {wiki/path/to/file.md}\n(full markdown with frontmatter)\n```"
    user = f"## Ingest Task\n\n**Source title**: {title}{clarification_note}\n\n**Existing pages**:\n{existing_summary}{overlap_warning}\n\n**Raw content**:\n\n{content}\n\nInstructions:\n1. Only extract knowledge with confidence=high or medium. Skip trivia.\n2. If a similar page already exists, UPDATE it (add new info, don't duplicate).\n3. Create source summary in wiki/sources/\n4. Create/update concept pages in wiki/concepts/\n5. Create/update entity pages in wiki/entities/\n6. Update wiki/index.md\n7. Append to wiki/log.md\n8. Each page MUST have at least 2 [[wikilinks]] to existing pages.\n\nOutput each file as a code block with the file path in braces."

    llm_resp = await call_llm(system, user)
    results = apply_llm_changes(llm_resp)
    return {
        "ok": True,
        "changes": results,
        "overlaps": overlaps,
        "llm_raw": llm_resp[:2000]
    }

@app.post("/api/query")
async def query_wiki(data: dict):
    question = data.get("question", "").strip()
    if not question:
        raise HTTPException(400, "question required")

    # Build context from wiki
    context_parts = []
    idx_path = WIKI_ROOT / "index.md"
    if idx_path.exists():
        context_parts.append(f"=== INDEX ===\n{idx_path.read_text('utf-8')[:2000]}")
    for p in list(all_pages())[:20]:
        text = p.read_text("utf-8")
        context_parts.append(f"=== {p.relative_to(WIKI_ROOT)} ===\n{text[:1500]}")
    context = "\n\n".join(context_parts)[:20000]

    system = "You are a knowledgeable assistant answering questions based on a personal wiki. Always cite specific pages using [[wikilinks]]. If the wiki doesn't contain enough information, say so honestly. Answer in Chinese."
    user = f"## Wiki Context\n\n{context}\n\n## Question\n\n{question}"

    answer = await call_llm(system, user, temperature=0.5)
    return {"answer": answer}

@app.post("/api/lint")
async def lint_wiki():
    context_parts = []
    for p in all_pages():
        text = p.read_text("utf-8")
        context_parts.append(f"=== {p.relative_to(WIKI_ROOT)} ===\n{text[:2000]}")
    context = "\n\n".join(context_parts)[:25000]

    system = "You are a wiki quality inspector. Scan the wiki for issues. Check: orphan pages, stub pages, contradictions, outdated info, missing cross-references, broken links. Be specific — reference page names with [[wikilinks]]. Output a structured report in Chinese."
    user = f"## Full Wiki Content\n\n{context}\n\n## Task\nScan all pages above and produce a lint report."

    report = await call_llm(system, user)
    return {"report": report}

@app.get("/api/graph")
def graph():
    return build_graph_data()

@app.get("/", response_class=HTMLResponse)
def index():
    return HTML_TEMPLATE

# ── HTML template ────────────────────────────────────────

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LLM Wiki · 知识库</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
:root {
  --bg: #0b0e14; --surface: #141821; --card: #1a1f2e;
  --border: #252b3a; --text: #c9d1d9; --muted: #6b7280;
  --accent: #f0c674; --accent2: #58a6ff; --purple: #a78bfa;
  --red: #f87171; --green: #4ade80;
  --radius: 10px; --shadow: 0 4px 24px rgba(0,0,0,.4);
}
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; background: var(--bg); color: var(--text); height: 100vh; display: flex; overflow: hidden; }
/* sidebar */
#sidebar { width: 280px; min-width: 280px; background: var(--surface); border-right: 1px solid var(--border); display: flex; flex-direction: column; }
#sidebar-header { padding: 16px 20px; border-bottom: 1px solid var(--border); font-size: 14px; font-weight: 700; letter-spacing: .5px; color: var(--accent); display: flex; align-items: center; gap: 8px; }
#sidebar-header .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--green); box-shadow: 0 0 8px var(--green); }
#tree { flex: 1; overflow-y: auto; padding: 8px 0; }
.tree-item { padding: 6px 20px; cursor: pointer; font-size: 13px; color: var(--muted); display: flex; align-items: center; gap: 8px; transition: all .15s; border-left: 2px solid transparent; }
.tree-item:hover { color: var(--text); background: rgba(255,255,255,.03); }
.tree-item.active { color: var(--accent); background: rgba(240,198,116,.06); border-left-color: var(--accent); }
.tree-item .icon { font-size: 15px; width: 20px; text-align: center; }
.tree-folder { padding-left: 12px; }
.tree-folder>.tree-children { padding-left: 12px; display: none; }
.tree-folder.open>.tree-children { display: block; }
.tree-folder-header { padding: 6px 20px; cursor: pointer; font-size: 13px; color: var(--muted); display: flex; align-items: center; gap: 8px; transition: all .15s; }
.tree-folder-header:hover { color: var(--text); }
.tree-folder-header .arrow { font-size: 10px; transition: transform .2s; }
.tree-folder.open>.tree-folder-header .arrow { transform: rotate(90deg); }
/* main */
#main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
#toolbar { padding: 12px 24px; border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 12px; background: var(--surface); }
#search-wrap { position: relative; flex: 0 1 360px; }
#search-input { width: 100%; padding: 8px 14px 8px 34px; background: var(--card); border: 1px solid var(--border); border-radius: 8px; color: var(--text); font-size: 13px; outline: none; transition: border .15s; }
#search-input:focus { border-color: var(--accent2); }
#search-input::placeholder { color: var(--muted); }
#search-icon { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); font-size: 14px; color: var(--muted); pointer-events: none; }
#search-results { position: absolute; top: 100%; left: 0; right: 0; margin-top: 4px; background: var(--card); border: 1px solid var(--border); border-radius: 8px; max-height: 360px; overflow-y: auto; z-index: 100; display: none; box-shadow: var(--shadow); }
#search-results.show { display: block; }
.search-result { padding: 10px 14px; cursor: pointer; border-bottom: 1px solid var(--border); transition: background .1s; }
.search-result:last-child { border-bottom: none; }
.search-result:hover { background: rgba(88,166,255,.08); }
.search-result .sr-title { font-weight: 600; font-size: 13px; color: var(--accent2); }
.search-result .sr-type { font-size: 10px; color: var(--muted); margin-left: 6px; }
.search-result .sr-snippet { font-size: 11px; color: var(--muted); margin-top: 3px; line-height: 1.4; }
.search-result .sr-score { float: right; font-size: 10px; color: var(--accent); }
#toolbar button { padding: 7px 16px; border: 1px solid var(--border); border-radius: 6px; background: var(--card); color: var(--text); cursor: pointer; font-size: 13px; transition: all .15s; white-space: nowrap; }
#toolbar button:hover { border-color: var(--accent2); color: var(--accent2); }
#toolbar button.active { background: var(--accent2); color: #fff; border-color: var(--accent2); }
#view-toggle { margin-left: auto; display: flex; gap: 4px; background: var(--card); border-radius: 6px; padding: 2px; }
#view-toggle button { border: none; border-radius: 4px; padding: 6px 14px; background: transparent; }
#view-toggle button.active { background: var(--accent2); }
#content-area { flex: 1; overflow-y: auto; display: flex; }
#content-view { flex: 1; padding: 32px 40px; overflow-y: auto; display: none; }
#content-view.active { display: block; }
#graph-view { flex: 1; display: none; position: relative; }
#graph-view.active { display: block; }
#graph-canvas { width: 100%; height: 100%; }
#graph-tooltip { position: absolute; background: var(--card); border: 1px solid var(--border); border-radius: 6px; padding: 8px 12px; font-size: 12px; pointer-events: none; display: none; z-index: 10; }
/* right panel */
#panel { width: 360px; min-width: 360px; background: var(--surface); border-left: 1px solid var(--border); display: flex; flex-direction: column; overflow-y: auto; }
#panel-header { padding: 16px 20px; border-bottom: 1px solid var(--border); font-size: 13px; font-weight: 600; color: var(--muted); letter-spacing: .5px; }
.panel-section { padding: 16px 20px; border-bottom: 1px solid var(--border); }
.panel-section h3 { font-size: 14px; font-weight: 600; margin-bottom: 10px; color: var(--accent); }
.panel-section textarea, .panel-section input { width: 100%; padding: 10px 12px; background: var(--card); border: 1px solid var(--border); border-radius: 6px; color: var(--text); font-size: 13px; resize: vertical; font-family: inherit; }
.panel-section textarea:focus, .panel-section input:focus { outline: none; border-color: var(--accent2); }
.panel-section textarea { min-height: 100px; }
.panel-section .btn { width: 100%; margin-top: 8px; padding: 10px; border: none; border-radius: 6px; font-size: 13px; font-weight: 600; cursor: pointer; transition: all .15s; }
.btn-primary { background: var(--accent2); color: #fff; }
.btn-primary:hover { filter: brightness(1.15); }
.btn-accent { background: var(--accent); color: #0b0e14; }
.btn-accent:hover { filter: brightness(1.1); }
.btn-purple { background: var(--purple); color: #fff; }
.btn-purple:hover { filter: brightness(1.1); }
.btn-danger { background: var(--red); color: #fff; }
.result-box { margin-top: 10px; padding: 12px; background: var(--card); border-radius: 6px; font-size: 12px; max-height: 300px; overflow-y: auto; white-space: pre-wrap; line-height: 1.6; }
.result-box:empty { display: none; }
.status-badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
.status-ok { background: rgba(74,222,128,.15); color: var(--green); }
.status-info { background: rgba(88,166,255,.15); color: var(--accent2); }
/* markdown content */
#content-view h1 { font-size: 28px; margin-bottom: 8px; color: #f0f6fc; }
#content-view h2 { font-size: 20px; margin: 24px 0 8px; color: #e6edf3; }
#content-view h3 { font-size: 16px; margin: 16px 0 6px; color: #d1d9e0; }
#content-view p { line-height: 1.75; margin-bottom: 12px; }
#content-view a { color: var(--accent2); text-decoration: none; }
#content-view a:hover { text-decoration: underline; }
#content-view code { background: var(--card); padding: 2px 6px; border-radius: 4px; font-size: .9em; }
#content-view pre { background: var(--card); padding: 16px; border-radius: 8px; overflow-x: auto; margin: 12px 0; }
#content-view pre code { background: none; padding: 0; }
#content-view table { border-collapse: collapse; width: 100%; margin: 12px 0; }
#content-view th, #content-view td { border: 1px solid var(--border); padding: 8px 12px; text-align: left; font-size: 13px; }
#content-view th { background: var(--card); font-weight: 600; }
#content-view blockquote { border-left: 3px solid var(--accent); padding: 8px 16px; margin: 12px 0; color: var(--muted); font-style: italic; }
#content-view hr { border: none; border-top: 1px solid var(--border); margin: 24px 0; }
.wikilink { color: var(--purple); cursor: pointer; text-decoration: underline; text-decoration-style: dotted; text-underline-offset: 4px; }
.wikilink:hover { color: var(--accent2); }
.fm-badge { display: inline-flex; align-items: center; gap: 4px; padding: 2px 10px; border-radius: 12px; font-size: 11px; margin-right: 6px; margin-bottom: 6px; }
.fm-badge.type { background: rgba(88,166,255,.15); color: var(--accent2); }
.fm-badge.conf { background: rgba(74,222,128,.15); color: var(--green); }
.fm-badge.tag { background: rgba(240,198,116,.15); color: var(--accent); }
.empty-state { text-align: center; padding: 60px 20px; color: var(--muted); }
.empty-state .icon { font-size: 48px; margin-bottom: 16px; }
.empty-state h2 { font-size: 18px; color: var(--text); margin-bottom: 8px; }
#page-path { font-size: 12px; color: var(--muted); margin-bottom: 16px; }
/* loading */
.spinner { display: inline-block; width: 16px; height: 16px; border: 2px solid var(--border); border-top-color: var(--accent2); border-radius: 50%; animation: spin .6s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
/* scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--muted); }
@media (max-width: 900px) { #sidebar { display: none; } #panel { width: 100%; min-width: unset; } }
</style>
</head>
<body>

<!-- Sidebar -->
<div id="sidebar">
  <div id="sidebar-header"><span class="dot"></span> LLM WIKI</div>
  <div id="tree"><div class="empty-state" style="padding:40px 20px"><div class="spinner"></div></div></div>
</div>

<!-- Main -->
<div id="main">
  <div id="toolbar">
    <span style="font-weight:600;color:var(--text)">📖 LLM Wiki</span>
    <div id="search-wrap">
      <span id="search-icon">🔍</span>
      <input id="search-input" type="text" placeholder="搜索知识库..." autocomplete="off" oninput="doSearch()" onfocus="doSearch()" onblur="setTimeout(()=>hideSearch(),200)">
      <div id="search-results"></div>
    </div>
    <div id="view-toggle">
      <button onclick="switchView('content')" class="active" id="btn-content">📄 内容</button>
      <button onclick="switchView('graph')" id="btn-graph">🕸 图谱</button>
    </div>
  </div>
  <div id="content-area">
    <div id="content-view" class="active">
      <div class="empty-state">
        <div class="icon">📚</div>
        <h2>选择一个页面开始阅读</h2>
        <p>左侧文件树浏览 Wiki，或使用右侧面板摄入新知识</p>
      </div>
    </div>
    <div id="graph-view">
      <canvas id="graph-canvas"></canvas>
      <div id="graph-tooltip"></div>
    </div>
  </div>
</div>

<!-- Right Panel -->
<div id="panel">
  <div id="panel-header">⚡ 操作面板</div>

  <div class="panel-section">
    <h3>📥 Ingest · 摄入</h3>
    <div style="display:flex;gap:6px;margin-bottom:6px">
      <button class="btn" style="flex:1;padding:6px;font-size:11px" id="tab-paste" onclick="switchIngestTab('paste')">📋 粘贴</button>
      <button class="btn" style="flex:1;padding:6px;font-size:11px" id="tab-url" onclick="switchIngestTab('url')">🌐 网址</button>
    </div>
    <div id="ingest-paste">
      <input id="ingest-title" placeholder="来源标题（可选）" style="margin-bottom:6px">
      <textarea id="ingest-content" placeholder="粘贴文章或任何内容..."></textarea>
    </div>
    <div id="ingest-url" style="display:none">
      <input id="ingest-url-input" placeholder="粘贴网址 URL，如 https://..." style="margin-bottom:6px">
      <div class="result-box" id="url-preview"></div>
    </div>
    <div id="ambiguity-box" style="display:none;margin-top:8px;padding:10px;background:rgba(240,198,116,.08);border:1px solid var(--accent);border-radius:6px">
      <div style="font-size:12px;font-weight:600;color:var(--accent);margin-bottom:6px">⚠️ 检测到歧义术语，请确认含义：</div>
      <div id="ambiguity-options"></div>
    </div>
    <button class="btn btn-accent" onclick="doIngest()" id="btn-ingest">摄入知识</button>
    <div class="result-box" id="ingest-result"></div>
  </div>

  <div class="panel-section">
    <h3>🔍 Query · 查询</h3>
    <textarea id="query-input" placeholder="对知识库提问，例如：Karpathy 的知识库架构是什么？" style="min-height:70px"></textarea>
    <button class="btn btn-primary" onclick="doQuery()" id="btn-query">查询知识库</button>
    <div class="result-box" id="query-result"></div>
  </div>

  <div class="panel-section">
    <h3>🩺 Lint · 健康检查</h3>
    <button class="btn btn-purple" onclick="doLint()" id="btn-lint">扫描知识库</button>
    <div class="result-box" id="lint-result"></div>
  </div>

  <div class="panel-section" style="border-bottom:none">
    <h3>📊 统计</h3>
    <div id="stats" style="font-size:13px;color:var(--muted)">加载中...</div>
  </div>
</div>

<script>
// ── state ──
let currentPage = null;
let graphData = null;
let currentView = 'content';

// ── init ──
marked.setOptions({ breaks: true, gfm: true });

async function init() {
  await loadTree();
  await loadStats();
}

// ── search ──
let searchTimeout;
async function doSearch() {
  clearTimeout(searchTimeout);
  const q = document.getElementById('search-input').value.trim();
  const results = document.getElementById('search-results');
  if (!q) { results.classList.remove('show'); return; }
  searchTimeout = setTimeout(async () => {
    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
      const data = await res.json();
      if (data.length === 0) {
        results.innerHTML = '<div class="search-result" style="color:var(--muted)">未找到匹配结果</div>';
      } else {
        results.innerHTML = data.map(r => `
          <div class="search-result" onclick="loadPage('${r.path}');hideSearch()">
            <span class="sr-score">${r.score}</span>
            <span class="sr-title">${r.title}</span>
            <span class="sr-type">${r.type} · ${r.linkCount}个链接</span>
            <div class="sr-snippet">${r.snippet || ''}</div>
          </div>`).join('');
      }
      results.classList.add('show');
    } catch(e) {}
  }, 200);
}
function hideSearch() {
  document.getElementById('search-results').classList.remove('show');
}

// ── tree ──
async function loadTree() {
  try {
    const res = await fetch('/api/tree?dir=wiki');
    const data = await res.json();
    renderTree(data);
  } catch(e) { document.getElementById('tree').innerHTML = '<div class="empty-state">加载失败</div>'; }
}

function renderTree(nodes, container) {
  container = container || document.getElementById('tree');
  container.innerHTML = '';
  nodes.forEach(n => {
    if (n.type === 'folder') {
      const div = document.createElement('div');
      div.className = 'tree-folder';
      div.innerHTML = `<div class="tree-folder-header" onclick="toggleFolder(this)"><span class="arrow">▶</span><span class="icon">📁</span>${n.name}</div><div class="tree-children"></div>`;
      container.appendChild(div);
      if (n.children && n.children.length > 0) {
        renderTree(n.children, div.querySelector('.tree-children'));
      }
    } else {
      const div = document.createElement('div');
      div.className = 'tree-item';
      div.innerHTML = `<span class="icon">📄</span>${n.name.replace('.md','')}`;
      div.onclick = () => loadPage(n.path);
      container.appendChild(div);
    }
  });
}

function toggleFolder(el) {
  el.parentElement.classList.toggle('open');
}

// ── page loading ──
async function loadPage(path) {
  try {
    const res = await fetch(`/api/page?path=${encodeURIComponent(path)}`);
    if (!res.ok) throw new Error('not found');
    const data = await res.json();
    currentPage = { path: data.path, ...data.frontmatter, body: data.body, links: data.links };

    // Highlight active tree item
    document.querySelectorAll('.tree-item').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tree-item').forEach(el => {
      if (el.textContent.includes(path.split('/').pop().replace('.md',''))) el.classList.add('active');
    });

    renderPage(data);
    switchView('content');
  } catch(e) {
    document.getElementById('content-view').innerHTML = '<div class="empty-state"><h2>页面未找到</h2></div>';
  }
}

function renderPage(data) {
  const cv = document.getElementById('content-view');
  let html = `<div id="page-path" style="display:flex;align-items:center;gap:12px"><span>📄 ${data.path}</span><button onclick="deletePage('${data.path}')" style="padding:4px 10px;font-size:11px;background:transparent;border:1px solid var(--red);color:var(--red);border-radius:4px;cursor:pointer;opacity:.6" onmouseover="this.style.opacity=1" onmouseout="this.style.opacity=.6">🗑 删除</button></div>`;

  // Frontmatter badges
  if (data.frontmatter && Object.keys(data.frontmatter).length > 0) {
    const fm = data.frontmatter;
    html += '<div style="margin-bottom:16px">';
    if (fm.type) html += `<span class="fm-badge type">📌 ${fm.type}</span>`;
    if (fm.confidence) html += `<span class="fm-badge conf">🎯 ${fm.confidence}</span>`;
    if (fm.tags) {
      const tags = fm.tags.replace(/[\[\]]/g,'').split(',').map(t => t.trim());
      tags.forEach(t => { html += `<span class="fm-badge tag">#${t}</span>`; });
    }
    html += '</div>';
  }

  // Render markdown body
  let md = data.body || '';
  // Convert [[wikilinks]]
  md = md.replace(/\[\[([^\]]+)\]\]/g, (match, target) => {
    const label = target.includes('|') ? target.split('|')[1] : target;
    const id = target.includes('|') ? target.split('|')[0] : target;
    return `<span class="wikilink" onclick="navigateToWikiPage('${id}')" title="${id}">${label}</span>`;
  });

  html += marked.parse(md);
  cv.innerHTML = html;
  cv.classList.add('active');
}

async function deletePage(path) {
  if (!confirm(`确定删除 ${path}？此操作不可恢复。`)) return;
  try {
    const res = await fetch(`/api/page?path=${encodeURIComponent(path)}`, { method: 'DELETE' });
    if (res.ok) {
      document.getElementById('content-view').innerHTML = '<div class="empty-state"><div class="icon">🗑</div><h2>已删除</h2><p>' + path + '</p></div>';
      loadTree();
      loadStats();
      loadGraph();
    }
  } catch(e) { alert('删除失败'); }
}

// ── wikilink navigation ──
async function navigateToWikiPage(name) {
  // Search for the page in the wiki
  try {
    const res = await fetch('/api/tree?dir=wiki');
    const tree = await res.json();
    const found = findPageInTree(tree, name);
    if (found) {
      await loadPage(found.path);
    } else {
      alert(`页面 "${name}" 尚未创建`);
    }
  } catch(e) { alert('导航失败'); }
}

function findPageInTree(nodes, name) {
  for (const n of nodes) {
    if (n.type === 'file' && n.name.replace('.md','') === name) return n;
    if (n.type === 'folder' && n.children) {
      const found = findPageInTree(n.children, name);
      if (found) return found;
    }
  }
  return null;
}

// ── view switching ──
function switchView(view) {
  currentView = view;
  document.getElementById('content-view').classList.toggle('active', view === 'content');
  document.getElementById('graph-view').classList.toggle('active', view === 'graph');
  document.getElementById('btn-content').classList.toggle('active', view === 'content');
  document.getElementById('btn-graph').classList.toggle('active', view === 'graph');
  if (view === 'graph' && graphData) renderGraph();
  if (view === 'graph' && !graphData) loadGraph();
}

// ── graph ──
async function loadGraph() {
  try {
    const res = await fetch('/api/graph');
    graphData = await res.json();
    if (currentView === 'graph') renderGraph();
  } catch(e) {}
}

function renderGraph() {
  const container = document.getElementById('graph-view');
  const canvas = document.getElementById('graph-canvas');
  const tooltip = document.getElementById('graph-tooltip');

  canvas.width = container.clientWidth;
  canvas.height = container.clientHeight;
  const ctx = canvas.getContext('2d');

  const nodes = graphData.nodes.map(n => ({
    ...n, x: Math.random() * canvas.width, y: Math.random() * canvas.height,
    vx: 0, vy: 0
  }));
  const edgeSet = new Set();
  const edges = graphData.edges.filter(e => {
    const key = [e.source, e.target].sort().join('|');
    if (edgeSet.has(key)) return false;
    edgeSet.add(key);
    return true;
  });

  const nodeMap = {};
  nodes.forEach(n => nodeMap[n.id] = n);

  // Color by type
  const typeColors = { concept: '#58a6ff', entity: '#f0c674', source: '#4ade80', comparison: '#a78bfa', index: '#f87171', log: '#6b7280' };

  let hoverNode = null;
  let dragNode = null;
  let dragMoved = false;
  let animId;

  function getMousePos(e) {
    const rect = canvas.getBoundingClientRect();
    return { x: e.clientX - rect.left, y: e.clientY - rect.top };
  }

  canvas.onmousedown = (e) => {
    const pos = getMousePos(e);
    for (const n of nodes) {
      const dx = pos.x - n.x, dy = pos.y - n.y;
      if (Math.sqrt(dx*dx+dy*dy) < 14) {
        dragNode = n;
        dragMoved = false;
        n.fixed = true;
        n.x = pos.x;
        n.y = pos.y;
        canvas.style.cursor = 'grabbing';
        break;
      }
    }
  };

  canvas.onmousemove = (e) => {
    const pos = getMousePos(e);
    if (dragNode) {
      dragNode.x = pos.x;
      dragNode.y = pos.y;
      dragMoved = true;
      tooltip.style.display = 'none';
      return;
    }
    hoverNode = null;
    for (const n of nodes) {
      const dx = pos.x - n.x, dy = pos.y - n.y;
      if (Math.sqrt(dx*dx+dy*dy) < 12) { hoverNode = n; break; }
    }
    if (hoverNode) {
      tooltip.style.display = 'block';
      tooltip.style.left = (pos.x + 15) + 'px';
      tooltip.style.top = (pos.y - 10) + 'px';
      const conns = (hoverNode.inCount||0) + (hoverNode.outCount||0);
      tooltip.innerHTML = `<strong>${hoverNode.label}</strong><br><span style="color:var(--muted)">${hoverNode.type} · ${conns}个关联</span>`;
      canvas.style.cursor = 'pointer';
    } else {
      tooltip.style.display = 'none';
      canvas.style.cursor = 'grab';
    }
  };

  canvas.onmouseup = canvas.onmouseleave = () => {
    if (dragNode && !dragMoved) {
      // Click without drag — navigate
      if (dragNode.path) loadPage(dragNode.path);
    }
    if (dragNode) {
      dragNode.fixed = false;
    }
    dragNode = null;
    dragMoved = false;
    canvas.style.cursor = hoverNode ? 'pointer' : 'grab';
  };

  // Prevent context menu on canvas
  canvas.oncontextmenu = (e) => e.preventDefault();
  // Global mouseup to release drag even outside canvas
  window.addEventListener('mouseup', () => {
    if (dragNode) {
      dragNode.fixed = false;
      dragNode = null;
      dragMoved = false;
      canvas.style.cursor = 'grab';
    }
  });

  function sim() {
    // Forces
    const cx = canvas.width / 2, cy = canvas.height / 2;
    const kRep = 8000, kAtt = 0.003, kCenter = 0.002;
    const damp = 0.85;

    for (const n of nodes) {
      if (n.fixed) { n.vx = 0; n.vy = 0; continue; }
      n.vx *= damp; n.vy *= damp;
      // Center pull
      n.vx += (cx - n.x) * kCenter;
      n.vy += (cy - n.y) * kCenter;
      // Gentle perpetual rotation
      n.vx += (cy - n.y) * 0.00015;
      n.vy += (n.x - cx) * 0.00015;
    }

    // Repulsion
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[j].x - nodes[i].x, dy = nodes[j].y - nodes[i].y;
        const dist = Math.sqrt(dx*dx+dy*dy) || 1;
        const f = kRep / (dist * dist);
        const fx = dx / dist * f, fy = dy / dist * f;
        if (!nodes[i].fixed) { nodes[i].vx -= fx; nodes[i].vy -= fy; }
        if (!nodes[j].fixed) { nodes[j].vx += fx; nodes[j].vy += fy; }
      }
    }

    // Attraction (edges)
    for (const e of edges) {
      const s = nodeMap[e.source], t = nodeMap[e.target];
      if (!s || !t) continue;
      const dx = t.x - s.x, dy = t.y - s.y;
      const dist = Math.sqrt(dx*dx+dy*dy) || 1;
      const f = dist * kAtt;
      const fx = dx / dist * f, fy = dy / dist * f;
      if (!s.fixed) { s.vx += fx; s.vy += fy; }
      if (!t.fixed) { t.vx -= fx; t.vy -= fy; }
    }

    // Apply velocity
    for (const n of nodes) {
      if (n.fixed) continue;
      n.x += n.vx;
      n.y += n.vy;
      n.x = Math.max(20, Math.min(canvas.width - 20, n.x));
      n.y = Math.max(20, Math.min(canvas.height - 20, n.y));
    }

    // Draw
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Edges
    ctx.strokeStyle = '#252b3a';
    ctx.lineWidth = 1;
    for (const e of edges) {
      const s = nodeMap[e.source], t = nodeMap[e.target];
      if (!s || !t) continue;
      ctx.beginPath();
      ctx.moveTo(s.x, s.y);
      ctx.lineTo(t.x, t.y);
      ctx.stroke();
    }

    // Nodes
    for (const n of nodes) {
      const baseR = n.radius || 7;
      const r = n === hoverNode ? baseR + 4 : baseR;
      const color = typeColors[n.type] || '#6b7280';
      ctx.beginPath();
      ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.globalAlpha = 0.85;
      ctx.fill();
      ctx.globalAlpha = 1;
      if (n === hoverNode) {
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      ctx.fillStyle = '#c9d1d9';
      ctx.font = '10px system-ui';
      ctx.textAlign = 'center';
      ctx.fillText(n.label.length > 12 ? n.label.slice(0,12)+'..' : n.label, n.x, n.y + 18);
    }

    animId = requestAnimationFrame(sim);
  }

  if (animId) cancelAnimationFrame(animId);
  sim();
}

// ── ingest ──
let ingestTab = 'paste';
let urlFetchedContent = '';
let urlFetchedTitle = '';
let pendingClarifications = [];

function switchIngestTab(tab) {
  ingestTab = tab;
  document.getElementById('ingest-paste').style.display = tab === 'paste' ? 'block' : 'none';
  document.getElementById('ingest-url').style.display = tab === 'url' ? 'block' : 'none';
  document.getElementById('tab-paste').classList.toggle('active', tab === 'paste');
  document.getElementById('tab-url').classList.toggle('active', tab === 'url');
}

async function fetchURL() {
  const url = document.getElementById('ingest-url-input').value.trim();
  if (!url) return;
  const preview = document.getElementById('url-preview');
  preview.innerHTML = '<span class="spinner"></span> 抓取中...';
  try {
    const res = await fetch('/api/fetch-url', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({url})
    });
    const data = await res.json();
    if (data.ok) {
      urlFetchedContent = data.content;
      urlFetchedTitle = data.title;
      preview.innerHTML = `<span class="status-badge status-ok">✓</span> ${data.title}<br><span style="color:var(--muted);font-size:11px">${data.content.length} 字符</span>`;
    } else {
      preview.innerHTML = '<span style="color:var(--red)">抓取失败</span>';
    }
  } catch(e) {
    preview.innerHTML = '<span style="color:var(--red)">抓取失败</span>';
  }
}
document.addEventListener('DOMContentLoaded', () => {
  const urlInput = document.getElementById('ingest-url-input');
  if (urlInput) urlInput.addEventListener('change', fetchURL);
});

async function doIngest() {
  const btn = document.getElementById('btn-ingest');
  const result = document.getElementById('ingest-result');
  let content, title;

  if (ingestTab === 'url') {
    if (!urlFetchedContent) {
      await fetchURL();
      if (!urlFetchedContent) return alert('请先输入网址并抓取内容');
    }
    content = urlFetchedContent;
    title = urlFetchedTitle || document.getElementById('ingest-url-input').value.trim();
  } else {
    content = document.getElementById('ingest-content').value.trim();
    title = document.getElementById('ingest-title').value.trim() || 'Untitled';
  }
  if (!content) return alert('请输入要摄入的内容');

  // Step 1: Precheck for ambiguities
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> 检测歧义...';
  result.innerHTML = '';

  let clarifications = [];
  try {
    const pcRes = await fetch('/api/precheck-ingest', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({content})
    });
    const pcData = await pcRes.json();
    const ambs = pcData.ambiguities || [];

    if (ambs.length > 0 && pendingClarifications.length === 0) {
      // Show ambiguity UI
      const box = document.getElementById('ambiguity-box');
      const opts = document.getElementById('ambiguity-options');
      pendingClarifications = ambs;
      opts.innerHTML = ambs.map((a, i) => `
        <div style="margin-bottom:8px;font-size:12px">
          <strong>${a.term}</strong> <span style="color:var(--muted)">${a.context||''}</span>
          <div style="display:flex;gap:6px;margin-top:4px;flex-wrap:wrap">
            ${a.options.map((o, j) => `
              <label style="cursor:pointer;font-size:11px;padding:3px 8px;border-radius:4px;background:${j===a.suggested?'rgba(88,166,255,.2)':'var(--card)'};border:1px solid ${j===a.suggested?'var(--accent2)':'var(--border)'}">
                <input type="radio" name="amb_${i}" value="${o}" ${j===a.suggested?'checked':''} style="display:none"> ${o}
              </label>`).join('')}
          </div>
        </div>`).join('');
      box.style.display = 'block';
      btn.innerHTML = '确认并摄入';
      btn.disabled = false;
      return;
    }

    // Collect user choices if ambiguity was shown
    if (pendingClarifications.length > 0) {
      clarifications = pendingClarifications.map((a, i) => {
        const selected = document.querySelector(`input[name="amb_${i}"]:checked`);
        return { term: a.term, chosen: selected ? selected.value : a.options[a.suggested||0] };
      });
      pendingClarifications = [];
      document.getElementById('ambiguity-box').style.display = 'none';
    }
  } catch(e) { /* precheck failed, proceed without */ }

  // Step 2: Do the actual ingest
  btn.innerHTML = '<span class="spinner"></span> 摄入中...';
  try {
    const res = await fetch('/api/ingest', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, content, clarifications })
    });
    const data = await res.json();
    let msg = '<span class="status-badge status-ok">✓ 摄入完成</span>\n\n';
    if (data.overlaps && data.overlaps.length > 0) {
      msg += '<span class="status-badge status-info">⚠ 检测到重叠: ' + data.overlaps.map(o=>o.title).join(', ') + '</span>\n\n';
    }
    msg += data.changes.map(c => `• ${c.action}: ${c.path || (c.content||'').slice(0, 80)}`).join('\n');
    result.innerHTML = msg;
    loadTree();
    loadStats();
    loadGraph();
    // Reset URL state
    urlFetchedContent = '';
    urlFetchedTitle = '';
  } catch(e) {
    result.innerHTML = '<span class="status-badge" style="background:rgba(248,113,113,.15);color:var(--red)">✗ 失败</span>';
  }
  btn.disabled = false;
  btn.innerHTML = '摄入知识';
}

// ── query ──
async function doQuery() {
  const question = document.getElementById('query-input').value.trim();
  if (!question) return alert('请输入问题');

  const btn = document.getElementById('btn-query');
  const result = document.getElementById('query-result');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> 查询中...';
  result.innerHTML = '';

  try {
    const res = await fetch('/api/query', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question })
    });
    const data = await res.json();
    // Render wikilinks in answer
    let answer = data.answer;
    answer = answer.replace(/\[\[([^\]]+)\]\]/g, '<span class="wikilink" onclick="navigateToWikiPage(\'$1\')">$1</span>');
    result.innerHTML = answer;
  } catch(e) {
    result.innerHTML = '<span style="color:var(--red)">查询失败</span>';
  }
  btn.disabled = false;
  btn.innerHTML = '查询知识库';
}

// ── lint ──
async function doLint() {
  const btn = document.getElementById('btn-lint');
  const result = document.getElementById('lint-result');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> 扫描中...';
  result.innerHTML = '';

  try {
    const res = await fetch('/api/lint', { method: 'POST' });
    const data = await res.json();
    let report = data.report;
    report = report.replace(/\[\[([^\]]+)\]\]/g, '<span class="wikilink" onclick="navigateToWikiPage(\'$1\')">$1</span>');
    result.innerHTML = report;
  } catch(e) {
    result.innerHTML = '<span style="color:var(--red)">检查失败</span>';
  }
  btn.disabled = false;
  btn.innerHTML = '扫描知识库';
}

// ── stats ──
async function loadStats() {
  try {
    const res = await fetch('/api/tree?dir=wiki');
    const tree = await res.json();
    const countFiles = (nodes) => {
      let c = 0;
      for (const n of nodes) {
        if (n.type === 'file') c++;
        if (n.children) c += countFiles(n.children);
      }
      return c;
    };
    const total = countFiles(tree);
    document.getElementById('stats').innerHTML = `
      <span class="status-badge status-ok">${total} 个页面</span>
      <span class="status-badge status-info">wiki/</span>
    `;
  } catch(e) {}
}

// ── start ──
init();
loadGraph();
</script>
</body>
</html>"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
