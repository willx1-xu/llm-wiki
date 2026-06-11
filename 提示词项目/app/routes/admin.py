from fastapi import APIRouter, Depends, HTTPException, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models import PromptModel, CategoryModel, TagModel, PromptTagModel, PromptVersionModel, SourceType, Difficulty
from app.services.prompt_service import slugify, make_unique_slug, get_existing_slugs, save_version
from app.routes.public import templates

router = APIRouter(prefix="/admin", tags=["admin"])


# ── Dashboard ──

@router.get("/")
async def admin_dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    pc = (await db.execute(select(func.count(PromptModel.id)))).scalar()
    rc = (await db.execute(select(func.count(PromptModel.id)).where(PromptModel.is_published == True))).scalar()
    cats = await db.execute(select(CategoryModel).order_by(CategoryModel.sort_order))
    categories = list(cats.scalars().all())
    return templates.TemplateResponse(request, "admin/dashboard.html", {
        "prompt_count": pc, "published_count": rc, "categories": categories
    })


# ── Prompts CRUD ──

@router.get("/prompts")
async def admin_prompts_list(
    request: Request,
    search: str = "", category_id: str = "", page: int = 1,
    db: AsyncSession = Depends(get_db),
):
    q = select(PromptModel).options(selectinload(PromptModel.category))
    if search:
        q = q.where(or_(PromptModel.title.ilike(f"%{search}%"), PromptModel.content.ilike(f"%{search}%")))
    if category_id:
        q = q.where(PromptModel.category_id == category_id)
    q = q.order_by(PromptModel.updated_at.desc())
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    q = q.offset((page - 1) * 20).limit(20)
    result = await db.execute(q)
    prompts = list(result.unique().scalars().all())
    cats = await db.execute(select(CategoryModel).order_by(CategoryModel.sort_order))
    categories = list(cats.scalars().all())
    return templates.TemplateResponse(request, "admin/prompts_list.html", {
        "prompts": prompts, "categories": categories,
        "search": search, "category_id": category_id, "page": page, "total": total,
    })


@router.get("/prompts/new")
async def admin_prompt_new(request: Request, db: AsyncSession = Depends(get_db)):
    cats = await db.execute(select(CategoryModel).order_by(CategoryModel.sort_order))
    tags = await db.execute(select(TagModel).order_by(TagModel.name))
    return templates.TemplateResponse(request, "admin/prompt_edit.html", {
        "prompt": None, "categories": list(cats.scalars().all()),
        "tags": list(tags.scalars().all()),
    })


@router.get("/prompts/{prompt_id}/edit")
async def admin_prompt_edit(request: Request, prompt_id: str, db: AsyncSession = Depends(get_db)):
    q = select(PromptModel).options(selectinload(PromptModel.tags), selectinload(PromptModel.versions)).where(PromptModel.id == prompt_id)
    result = await db.execute(q)
    prompt = result.unique().scalar_one_or_none()
    if not prompt:
        raise HTTPException(404, "提示词不存在")
    cats = await db.execute(select(CategoryModel).order_by(CategoryModel.sort_order))
    tags = await db.execute(select(TagModel).order_by(TagModel.name))
    return templates.TemplateResponse(request, "admin/prompt_edit.html", {
        "prompt": prompt, "categories": list(cats.scalars().all()),
        "tags": list(tags.scalars().all()),
    })


@router.post("/prompts/save")
async def admin_prompt_save(
    request: Request,
    prompt_id: str = Form(""),
    title: str = Form(""),
    content: str = Form(""),
    description: str = Form(""),
    scenario_desc: str = Form(""),
    difficulty: str = Form("beginner"),
    expected_output: str = Form(""),
    model_suitability: str = Form(""),
    source_url: str = Form(""),
    source_type: str = Form("manual"),
    category_id: str = Form(""),
    tag_ids: str = Form(""),
    is_published: bool = Form(False),
    is_private: bool = Form(True),
    db: AsyncSession = Depends(get_db),
):
    existing_slugs = await get_existing_slugs(db)
    if prompt_id:
        q = select(PromptModel).where(PromptModel.id == prompt_id)
        r = await db.execute(q)
        prompt = r.scalar_one_or_none()
        if not prompt:
            raise HTTPException(404)
        if prompt.content and prompt.content != content:
            await save_version(db, prompt_id, prompt.content, "编辑修改")
    else:
        prompt = PromptModel(source_type=SourceType(source_type))
        db.add(prompt)

    slug = slugify(title)
    if not prompt_id or slug != prompt.slug:
        slug = make_unique_slug(title, existing_slugs - {prompt.slug if prompt_id else ""})

    prompt.title = title
    prompt.slug = slug
    prompt.content = content
    prompt.description = description or None
    prompt.scenario_desc = scenario_desc or None
    prompt.difficulty = Difficulty(difficulty)
    prompt.expected_output = expected_output or None
    prompt.model_suitability = model_suitability or None
    prompt.source_url = source_url or None
    prompt.category_id = category_id if category_id else None
    prompt.is_published = is_published
    prompt.is_private = is_private

    prompt.tags = []
    if tag_ids:
        tag_list = [t.strip() for t in tag_ids.split(",") if t.strip()]
        if tag_list:
            tr = await db.execute(select(TagModel).where(TagModel.id.in_(tag_list)))
            prompt.tags = list(tr.scalars().all())

    await db.commit()
    return RedirectResponse("/admin/prompts", status_code=303)


@router.post("/prompts/{prompt_id}/delete")
async def admin_prompt_delete(prompt_id: str, db: AsyncSession = Depends(get_db)):
    q = select(PromptModel).where(PromptModel.id == prompt_id)
    r = await db.execute(q)
    prompt = r.scalar_one_or_none()
    if prompt:
        await db.delete(prompt)
        await db.commit()
    return RedirectResponse("/admin/prompts", status_code=303)


# ── Categories ──

@router.get("/categories")
async def admin_categories(request: Request, db: AsyncSession = Depends(get_db)):
    cats = await db.execute(select(CategoryModel).order_by(CategoryModel.sort_order))
    return templates.TemplateResponse(request, "admin/categories.html", {
        "categories": list(cats.scalars().all()),
    })


@router.post("/categories/save")
async def admin_category_save(
    cat_id: str = Form(""),
    name: str = Form(""),
    slug: str = Form(""),
    parent_id: str = Form(""),
    description: str = Form(""),
    icon: str = Form("📁"),
    db: AsyncSession = Depends(get_db),
):
    if cat_id:
        q = select(CategoryModel).where(CategoryModel.id == cat_id)
        r = await db.execute(q)
        cat = r.scalar_one_or_none()
        if not cat:
            raise HTTPException(404)
    else:
        cat = CategoryModel()
        db.add(cat)
    cat.name = name
    cat.slug = slug or slugify(name)
    cat.parent_id = parent_id if parent_id else None
    cat.description = description or None
    cat.icon = icon or "📁"
    await db.commit()
    return RedirectResponse("/admin/categories", status_code=303)


@router.post("/categories/{cat_id}/delete")
async def admin_category_delete(cat_id: str, db: AsyncSession = Depends(get_db)):
    q = select(CategoryModel).where(CategoryModel.id == cat_id)
    r = await db.execute(q)
    cat = r.scalar_one_or_none()
    if cat:
        await db.delete(cat)
        await db.commit()
    return RedirectResponse("/admin/categories", status_code=303)


# ── Tags ──

@router.get("/tags")
async def admin_tags(request: Request, db: AsyncSession = Depends(get_db)):
    t = await db.execute(select(TagModel).order_by(TagModel.name))
    return templates.TemplateResponse(request, "admin/tags.html", {"tags": list(t.scalars().all())})


@router.post("/tags/save")
async def admin_tag_save(
    tag_id: str = Form(""),
    name: str = Form(""),
    slug: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    if tag_id:
        q = select(TagModel).where(TagModel.id == tag_id)
        r = await db.execute(q)
        tag = r.scalar_one_or_none()
        if not tag:
            raise HTTPException(404)
    else:
        tag = TagModel()
        db.add(tag)
    tag.name = name
    tag.slug = slug or slugify(name)
    await db.commit()
    return RedirectResponse("/admin/tags", status_code=303)


@router.post("/tags/{tag_id}/delete")
async def admin_tag_delete(tag_id: str, db: AsyncSession = Depends(get_db)):
    q = select(TagModel).where(TagModel.id == tag_id)
    r = await db.execute(q)
    tag = r.scalar_one_or_none()
    if tag:
        await db.delete(tag)
        await db.commit()
    return RedirectResponse("/admin/tags", status_code=303)
