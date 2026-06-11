import uuid, enum
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, Text, Enum, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID


class Base(DeclarativeBase):
    pass


def gen_uuid():
    return str(uuid.uuid4())


class SourceType(str, enum.Enum):
    MANUAL = "manual"
    URL_SCRAPE = "url_scrape"
    BATCH_CRAWL = "batch_crawl"
    AI_ENHANCE = "ai_enhance"


class Difficulty(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class CategoryModel(Base):
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    parent_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True, default="📁")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    children: Mapped[list["CategoryModel"]] = relationship(back_populates="parent", remote_side="CategoryModel.id", order_by="CategoryModel.sort_order")
    parent: Mapped["CategoryModel | None"] = relationship(back_populates="children", remote_side="CategoryModel.parent_id")
    prompts: Mapped[list["PromptModel"]] = relationship(back_populates="category")


class TagModel(Base):
    __tablename__ = "tags"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)

    prompts: Mapped[list["PromptModel"]] = relationship(back_populates="tags", secondary="prompt_tags")


class PromptModel(Base):
    __tablename__ = "prompts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    slug: Mapped[str] = mapped_column(String(350), unique=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    scenario_desc: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty: Mapped[Difficulty] = mapped_column(Enum(Difficulty), default=Difficulty.BEGINNER)
    expected_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_suitability: Mapped[str | None] = mapped_column(String(200), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    source_type: Mapped[SourceType] = mapped_column(Enum(SourceType), default=SourceType.MANUAL)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    is_private: Mapped[bool] = mapped_column(Boolean, default=True)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    category_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category: Mapped[CategoryModel | None] = relationship(back_populates="prompts")
    tags: Mapped[list[TagModel]] = relationship(back_populates="prompts", secondary="prompt_tags")
    versions: Mapped[list["PromptVersionModel"]] = relationship(back_populates="prompt", order_by="desc(PromptVersionModel.version_number)")


class PromptTagModel(Base):
    __tablename__ = "prompt_tags"
    __table_args__ = (UniqueConstraint("prompt_id", "tag_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    prompt_id: Mapped[str] = mapped_column(String(36), ForeignKey("prompts.id", ondelete="CASCADE"), nullable=False)
    tag_id: Mapped[str] = mapped_column(String(36), ForeignKey("tags.id", ondelete="CASCADE"), nullable=False)


class PromptVersionModel(Base):
    __tablename__ = "prompt_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    prompt_id: Mapped[str] = mapped_column(String(36), ForeignKey("prompts.id", ondelete="CASCADE"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    change_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    prompt: Mapped[PromptModel] = relationship(back_populates="versions")
