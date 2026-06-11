import json, re
import httpx
from bs4 import BeautifulSoup
from app.config import DEEPSEEK_KEY, DS_URL


async def fetch_page(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.text


def extract_prompts_heuristic(html: str) -> list[dict]:
    """Heuristic extraction of prompt-like content blocks."""
    soup = BeautifulSoup(html, "html.parser")
    results = []

    # Try common containers: code blocks, blockquotes, structured divs
    for tag in soup.find_all(["pre", "blockquote", "div", "section"]):
        text = tag.get_text(strip=True)
        if not text or len(text) < 50:
            continue
        # Check if it looks like a prompt (contains instruction-like language)
        score = 0
        prompt_indicators = [
            "prompt", "提示词", "instruction", "指令", "role", "system",
            "你是一个", "你是一位", "act as", "you are", "作为",
        ]
        for indicator in prompt_indicators:
            if indicator in text.lower():
                score += 1

        if score >= 1:
            results.append({"content": text[:5000], "confidence": score / len(prompt_indicators)})

    return results


async def extract_prompts_ai(html: str) -> list[dict]:
    """Use AI to extract prompts from page content."""
    text = BeautifulSoup(html, "html.parser").get_text()[:8000]

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            DS_URL,
            headers={"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"},
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "你是一个提示词提取器。从以下网页内容中提取所有可用的 AI 提示词。输出 JSON 数组，每个元素含 title 和 content。如果没有提示词则返回空数组。只输出纯 JSON，不带 markdown 标记。"},
                    {"role": "user", "content": text},
                ],
                "temperature": 0.3,
            },
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
        raw = data["choices"][0]["message"]["content"].strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return []


async def scrape_url(url: str) -> dict:
    """Scrape a URL and extract prompt content."""
    html = await fetch_page(url)

    # Try heuristic first
    heuristic_results = extract_prompts_heuristic(html)
    high_conf = [r for r in heuristic_results if r["confidence"] >= 0.3]
    low_conf = [r for r in heuristic_results if r["confidence"] < 0.3]

    # If heuristic found strong results, return them
    if high_conf:
        return {
            "url": url,
            "method": "heuristic",
            "items": high_conf,
            "confidence": "high",
        }

    # Try AI extraction for better results
    ai_results = await extract_prompts_ai(html)
    if ai_results:
        return {
            "url": url,
            "method": "ai",
            "items": [{"content": r.get("content", str(r)), "confidence": 0.7} for r in ai_results],
            "confidence": "medium",
        }

    return {"url": url, "method": "none", "items": low_conf, "confidence": "low"}
