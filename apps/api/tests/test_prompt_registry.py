import os
import sys
from pathlib import Path

import pytest

os.environ["APP_ENV"] = "test"
os.environ["DEEPSEEK_API_KEY"] = ""
API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.core.prompt_registry import PromptRegistry
from app.core.settings import get_settings
from app.llm.deepseek_client import DeepSeekClient, RequirementExtractionResult


class FakeChunk:
    def __init__(self, content: str) -> None:
        self.content = content


class FakeRequirementExtractionResponse:
    def model_dump(self):
        return {"course_positioning": "入门课"}


class FakeStructured:
    def __init__(self, schema):
        self.schema = schema

    async def ainvoke(self, prompt: str):
        if self.schema is RequirementExtractionResult:
            return FakeRequirementExtractionResponse()
        return {"total_score": 8.5, "criteria": [], "suggestions": []}


class FakeModel:
    async def astream(self, prompt: str):
        yield FakeChunk("ok")

    async def ainvoke(self, prompt: str):
        return FakeChunk("ok")

    def with_structured_output(self, schema):
        return FakeStructured(schema)


@pytest.fixture
def prompt_registry():
    settings = get_settings()
    return PromptRegistry(settings.prompt_root_dir)


def test_prompt_registry_resolves_prompt_id(prompt_registry: PromptRegistry):
    spec = prompt_registry.resolve_prompt("generate.course_title")
    assert spec.mode == "single"
    assert spec.step_id == "course_title"
    assert spec.purpose == "generate"
    assert "slot_summary" in spec.input_vars
    assert spec.file == "deepseek/generate/course_title.md"


def test_prompt_registry_missing_required_input_vars_raises(prompt_registry: PromptRegistry):
    with pytest.raises(ValueError) as exc:
        prompt_registry.render_by_id("generate.course_title", step_label="课程标题")
    assert "generate.course_title" in str(exc.value)
    assert "generation_goal" in str(exc.value)


def test_load_legacy_reads_current_catalog_file(prompt_registry: PromptRegistry):
    content = prompt_registry.load_legacy("deepseek/clarify/course_title.md")
    assert "当前唯一需要确认的信息" in content


@pytest.mark.asyncio
async def test_clarify_prompt_id_is_step_specific(monkeypatch: pytest.MonkeyPatch):
    settings = get_settings()
    client = DeepSeekClient(settings)
    captured: list[str] = []

    monkeypatch.setattr(client, "can_use_remote_llm", lambda: True)
    monkeypatch.setattr(client, "_build_chat_model", lambda profile: FakeModel())

    def fake_render_by_id(prompt_id: str, **kwargs):
        captured.append(prompt_id)
        return "prompt"

    monkeypatch.setattr(client.prompts, "render_by_id", fake_render_by_id)

    chunks = []
    async for chunk in client.stream_clarification(
        {
            "prompt_id": "clarify.course_title",
            "step_label": "课程标题",
            "allowed_scope": "主题、对象、问题、结果、标题风格",
            "forbidden_scope": "案例、逐字稿、素材清单",
            "slot_summary": "主题: 三角函数",
            "missing_requirement": {"label": "标题风格", "prompt_hint": "希望偏实操还是偏讲解"},
        }
    ):
        chunks.append(chunk)

    assert captured == ["clarify.course_title"]
    assert chunks == ["ok"]


@pytest.mark.asyncio
async def test_generate_prompt_id_is_step_specific(monkeypatch: pytest.MonkeyPatch):
    settings = get_settings()
    client = DeepSeekClient(settings)
    captured: list[str] = []

    monkeypatch.setattr(client, "can_use_remote_llm", lambda: True)
    monkeypatch.setattr(client, "_build_chat_model", lambda profile: FakeModel())

    def fake_render_by_id(prompt_id: str, **kwargs):
        captured.append(prompt_id)
        return "prompt"

    monkeypatch.setattr(client.prompts, "render_by_id", fake_render_by_id)

    chunks = []
    async for chunk in client.stream_step_markdown(
        {
            "prompt_id": "generate.course_framework",
            "step_label": "课程框架",
            "generation_goal": "生成课程框架",
            "required_slots": "- 课程目标",
            "optional_slots": "- 时长",
            "forbidden_topics": "- 逐字稿",
            "slot_summary": "课程目标: 提分",
            "source_summary": "无上传资料",
            "prior_step_artifacts": "暂无",
            "constraint_summary": "无额外约束",
        }
    ):
        chunks.append(chunk)

    assert captured == ["generate.course_framework"]
    assert chunks == ["ok"]


@pytest.mark.asyncio
async def test_review_prompt_uses_step_artifact_prompt_id(monkeypatch: pytest.MonkeyPatch):
    settings = get_settings()
    client = DeepSeekClient(settings)
    captured: list[str] = []

    monkeypatch.setattr(client, "can_use_remote_llm", lambda: True)
    monkeypatch.setattr(client, "_build_chat_model", lambda profile: FakeModel())

    def fake_render_by_id(prompt_id: str, **kwargs):
        captured.append(prompt_id)
        return "prompt"

    monkeypatch.setattr(client.prompts, "render_by_id", fake_render_by_id)

    await client.review_markdown(markdown="# Title", rubric=[], threshold=8.0, step_label="课程标题", forbidden_topics="无")
    assert captured == ["review.step_artifact"]


@pytest.mark.asyncio
async def test_improve_prompt_uses_step_artifact_prompt_id(monkeypatch: pytest.MonkeyPatch):
    settings = get_settings()
    client = DeepSeekClient(settings)
    captured: list[str] = []

    monkeypatch.setattr(client, "can_use_remote_llm", lambda: True)
    monkeypatch.setattr(client, "_build_chat_model", lambda profile: FakeModel())

    def fake_render_by_id(prompt_id: str, **kwargs):
        captured.append(prompt_id)
        return "prompt"

    monkeypatch.setattr(client.prompts, "render_by_id", fake_render_by_id)

    await client.improve_markdown(
        markdown="# Title",
        approved_changes=["补强标题理由"],
        context_summary="上下文",
        source_version=1,
        revision_goal="补强标题",
        step_label="课程标题",
        prior_step_artifacts="暂无",
    )
    assert captured == ["improve.step_artifact"]


@pytest.mark.asyncio
async def test_extract_requirements_prompt_uses_prompt_id(monkeypatch: pytest.MonkeyPatch):
    settings = get_settings()
    client = DeepSeekClient(settings)
    captured: list[str] = []

    monkeypatch.setattr(client, "can_use_remote_llm", lambda: True)
    monkeypatch.setattr(client, "_build_chat_model", lambda profile: FakeModel())

    def fake_render_by_id(prompt_id: str, **kwargs):
        captured.append(prompt_id)
        return "prompt"

    monkeypatch.setattr(client.prompts, "render_by_id", fake_render_by_id)

    await client.extract_requirements(
        latest_user_message="我要做一门入门课",
        known_requirements={},
        requirement_defs=[{"slot_id": "course_positioning", "label": "课程定位", "prompt_hint": "入门课还是训练营"}],
    )
    assert captured == ["extract.requirements"]
