import re, unicodedata
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models import PromptModel, CategoryModel, TagModel, PromptTagModel, PromptVersionModel, SourceType


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "-", text)


def make_unique_slug(base: str, existing: set[str]) -> str:
    slug = slugify(base)
    if slug not in existing:
        return slug
    i = 2
    while f"{slug}-{i}" in existing:
        i += 1
    return f"{slug}-{i}"


async def get_all_prompts(
    db: AsyncSession,
    category_slug: str | None = None,
    search: str | None = None,
    difficulty: str | None = None,
    tag_slug: str | None = None,
    private_only: bool = False,
    published_only: bool = False,
    offset: int = 0,
    limit: int = 50,
):
    q = select(PromptModel).options(selectinload(PromptModel.category), selectinload(PromptModel.tags))

    if private_only:
        q = q.where(PromptModel.is_private == True)
    if published_only:
        q = q.where(PromptModel.is_published == True)

    if category_slug:
        q = q.join(CategoryModel, PromptModel.category_id == CategoryModel.id).where(CategoryModel.slug == category_slug)

    if search:
        q = q.where(or_(
            PromptModel.title.ilike(f"%{search}%"),
            PromptModel.content.ilike(f"%{search}%"),
            PromptModel.description.ilike(f"%{search}%"),
        ))

    if difficulty:
        q = q.where(PromptModel.difficulty == difficulty)

    if tag_slug:
        q = (q.join(PromptTagModel, PromptModel.id == PromptTagModel.prompt_id)
              .join(TagModel, PromptTagModel.tag_id == TagModel.id)
              .where(TagModel.slug == tag_slug))

    q = q.order_by(PromptModel.updated_at.desc()).offset(offset).limit(limit)
    result = await db.execute(q)
    return list(result.unique().scalars().all())


async def get_prompt_by_slug(db: AsyncSession, slug: str):
    q = (select(PromptModel)
         .options(selectinload(PromptModel.category), selectinload(PromptModel.tags), selectinload(PromptModel.versions))
         .where(PromptModel.slug == slug))
    result = await db.execute(q)
    return result.unique().scalar_one_or_none()


async def save_version(db: AsyncSession, prompt_id: str, content: str, change_note: str | None = None):
    vq = select(func.max(PromptVersionModel.version_number)).where(PromptVersionModel.prompt_id == prompt_id)
    vr = await db.execute(vq)
    max_v = vr.scalar() or 0
    version = PromptVersionModel(prompt_id=prompt_id, version_number=max_v + 1, content=content, change_note=change_note)
    db.add(version)


async def get_category_tree(db: AsyncSession):
    q = (select(CategoryModel)
         .where(CategoryModel.parent_id == None)
         .options(selectinload(CategoryModel.children).selectinload(CategoryModel.children))
         .order_by(CategoryModel.sort_order))
    result = await db.execute(q)
    return list(result.unique().scalars().all())


async def get_existing_slugs(db: AsyncSession) -> set[str]:
    q = select(PromptModel.slug)
    result = await db.execute(q)
    return set(result.scalars().all())
