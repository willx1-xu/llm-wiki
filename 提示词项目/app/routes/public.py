from pathlib import Path
from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.prompt_service import get_all_prompts, get_prompt_by_slug, get_category_tree

router = APIRouter(tags=["public"])
TEMPLATES_DIR = str(Path(__file__).parent.parent / "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@router.get("/")
async def home(request: Request, db: AsyncSession = Depends(get_db)):
    category_tree = await get_category_tree(db)
    prompts = await get_all_prompts(db, published_only=True, limit=50)
    return templates.TemplateResponse(request, "public/home.html", {
        "prompts": prompts, "categories": category_tree,
    })


@router.get("/browse")
async def browse(
    request: Request,
    category: str = "",
    search: str = "",
    difficulty: str = "",
    tag: str = "",
    page: int = 1,
    db: AsyncSession = Depends(get_db),
):
    category_tree = await get_category_tree(db)
    offset = (page - 1) * 20
    prompts = await get_all_prompts(
        db,
        category_slug=category or None,
        search=search or None,
        difficulty=difficulty or None,
        tag_slug=tag or None,
        published_only=True,
        offset=offset,
        limit=20,
    )
    return templates.TemplateResponse(request, "public/browse.html", {
        "prompts": prompts, "categories": category_tree,
        "current_category": category, "search": search, "difficulty": difficulty, "tag": tag, "page": page,
    })


@router.get("/prompts/{slug}")
async def prompt_detail(request: Request, slug: str, db: AsyncSession = Depends(get_db)):
    prompt = await get_prompt_by_slug(db, slug)
    if not prompt or (prompt.is_private and not prompt.is_published):
        from fastapi import HTTPException
        raise HTTPException(404, "提示词不存在")
    prompt.view_count += 1
    await db.commit()
    return templates.TemplateResponse(request, "public/detail.html", {
        "prompt": prompt,
    })
