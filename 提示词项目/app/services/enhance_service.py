import json
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
from app.config import DEEPSEEK_KEY, DS_URL


SYSTEM_MSG = """你是一个专业的 AI 提示词工程师。用户会输入模糊的需求描述或关键词，你需要生成一份结构化、专业、可直接复制使用的提示词。

输出 JSON 格式（不要 markdown 代码块），包含以下字段：
{
  "title": "标题（中文，简洁有力）",
  "category_path": "推荐分类路径，用 > 分隔，如：外贸 > 独立站 > SEO",
  "tags": ["标签1", "标签2", "标签3"],
  "content": "提示词正文（从领域专家视角编写，详细、可执行、可直接发给 AI 使用）",
  "description": "一句话描述这条提示词做什么",
  "scenario_desc": "什么场景下使用",
  "expected_output": "预期 AI 会产出什么",
  "model_suitability": "推荐使用的模型，如 GPT-4, Claude, DeepSeek",
  "difficulty": "beginner | intermediate | advanced"
}

规则：
- content 必须详细、有步骤感，让 AI 看了就能产出高质量结果
- 如果涉及技术领域，从该领域专家和程序员双视角编写
- 用中文编写提示词内容，保留必要的英文专业术语
- 一定要输出纯 JSON，不带 markdown 标记"""


async def enhance_prompt(db: AsyncSession, user_input: str) -> dict:
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            DS_URL,
            headers={
                "Authorization": f"Bearer {DEEPSEEK_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": SYSTEM_MSG},
                    {"role": "user", "content": user_input},
                ],
                "temperature": 0.7,
            },
        )
        if resp.status_code != 200:
            raise Exception(f"DeepSeek API 错误: {resp.status_code} {resp.text}")

        data = resp.json()
        text = data["choices"][0]["message"]["content"]
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text[:-3]
        return json.loads(text)
