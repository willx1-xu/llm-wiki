import asyncio, re
from urllib.parse import urljoin
import httpx
from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import PromptModel, SourceType


class CrawlConfig:
    def __init__(self, domain: str, list_selector: str, content_selector: str,
                 pagination_param: str = "page", max_pages: int = 10, rate_per_sec: float = 1.0):
        self.domain = domain
        self.list_selector = list_selector
        self.content_selector = content_selector
        self.pagination_param = pagination_param
        self.max_pages = max_pages
        self.rate_per_sec = rate_per_sec


async def crawl(config: CrawlConfig, db: AsyncSession) -> list[PromptModel]:
    """Batch crawl a domain for prompts."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    results = []

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        for page_num in range(1, config.max_pages + 1):
            list_url = f"{config.domain}?{config.pagination_param}={page_num}"
            try:
                resp = await client.get(list_url, headers=headers)
                if resp.status_code != 200:
                    break
                soup = BeautifulSoup(resp.text, "html.parser")

                cards = soup.select(config.list_selector)
                if not cards:
                    break

                for card in cards:
                    link = card.find("a", href=True)
                    if not link:
                        continue
                    detail_url = urljoin(config.domain, link["href"])

                    try:
                        detail_resp = await client.get(detail_url, headers=headers)
                        detail_soup = BeautifulSoup(detail_resp.text, "html.parser")
                        content_el = detail_soup.select_one(config.content_selector)
                        if content_el:
                            text = content_el.get_text(strip=True)[:5000]
                            results.append({"url": detail_url, "content": text, "source_type": SourceType.BATCH_CRAWL})
                    except Exception:
                        continue

                    await asyncio.sleep(1 / config.rate_per_sec)

            except Exception:
                break

    return results
