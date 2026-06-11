from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.enhance_service import enhance_prompt
from app.services.scrape_service import scrape_url
from app.services.crawl_service import crawl, CrawlConfig

router = APIRouter(prefix="/api", tags=["api"])


def verify_token(token: str = ""):
    from app.config import SECRET_TOKEN
    if token != SECRET_TOKEN:
        raise HTTPException(403, "Invalid token")
    return True


@router.post("/enhance")
async def api_enhance(user_input: str = Form(""), db: AsyncSession = Depends(get_db)):
    """AI enhance: convert vague input to structured professional prompt."""
    if not user_input.strip():
        raise HTTPException(400, "请输入内容")
    try:
        result = await enhance_prompt(db, user_input.strip())
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(500, f"增强失败: {str(e)}")


@router.post("/scrape")
async def api_scrape(url: str = Form(""), _auth=Depends(verify_token)):
    """Scrape prompts from a URL."""
    if not url.strip():
        raise HTTPException(400, "请输入 URL")
    try:
        result = await scrape_url(url.strip())
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(500, f"抓取失败: {str(e)}")


@router.post("/crawl")
async def api_crawl(
    domain: str = Form(""),
    list_selector: str = Form(""),
    content_selector: str = Form(""),
    max_pages: int = Form(10),
    rate_per_sec: float = Form(1.0),
    _auth=Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    """Batch crawl a domain."""
    if not domain.strip():
        raise HTTPException(400, "请输入目标域名")
    config = CrawlConfig(
        domain=domain.strip(),
        list_selector=list_selector.strip(),
        content_selector=content_selector.strip(),
        max_pages=min(max_pages, 50),
        rate_per_sec=min(rate_per_sec, 5.0),
    )
    try:
        results = await crawl(config, db)
        return {"success": True, "items_found": len(results), "items": results}
    except Exception as e:
        raise HTTPException(500, f"采集失败: {str(e)}")
