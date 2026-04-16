from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class PromptSpec:
    prompt_id: str
    version: str
    provider: str
    mode: str
    step_id: str | None
    purpose: str
    input_vars: tuple[str, ...]
    output_contract: str
    file: str


class PromptRegistry:
    def __init__(self, prompt_root: Path) -> None:
        self.prompt_root = prompt_root
        self.catalog_path = prompt_root / "prompt_catalog.yaml"
        self._catalog = self._load_catalog()

    def _load_catalog(self) -> dict[str, PromptSpec]:
        if not self.catalog_path.exists():
            return {}
        payload = yaml.safe_load(self.catalog_path.read_text(encoding="utf-8")) or {}
        prompts = payload.get("prompts", [])
        catalog: dict[str, PromptSpec] = {}
        for item in prompts:
            spec = PromptSpec(
                prompt_id=item["prompt_id"],
                version=str(item["version"]),
                provider=item["provider"],
                mode=item["mode"],
                step_id=item.get("step_id"),
                purpose=item["purpose"],
                input_vars=tuple(item.get("input_vars", [])),
                output_contract=item["output_contract"],
                file=item["file"],
            )
            catalog[spec.prompt_id] = spec
        return catalog

    def resolve_prompt(self, prompt_id: str) -> PromptSpec:
        if prompt_id not in self._catalog:
            raise KeyError(f"Unknown prompt_id: {prompt_id}")
        return self._catalog[prompt_id]

    def validate_inputs(self, prompt_id: str, kwargs: dict[str, Any]) -> None:
        spec = self.resolve_prompt(prompt_id)
        missing = [name for name in spec.input_vars if name not in kwargs or kwargs[name] is None]
        if missing:
            raise ValueError(f"Prompt '{prompt_id}' missing required input vars: {', '.join(missing)}")

    def load_legacy(self, relative_path: str) -> str:
        return (self.prompt_root / relative_path).read_text(encoding="utf-8").strip()

    def load(self, relative_path: str) -> str:
        return self.load_legacy(relative_path)

    def exists(self, relative_path: str) -> bool:
        return (self.prompt_root / relative_path).exists()

    def load_optional(self, relative_path: str) -> str | None:
        path = self.prompt_root / relative_path
        if not path.exists():
            return None
        content = path.read_text(encoding="utf-8").strip()
        return content or None

    def render(self, relative_path: str, **kwargs: object) -> str:
        template = self.load_legacy(relative_path)
        return template.format(**kwargs)

    def render_by_id(self, prompt_id: str, **kwargs: object) -> str:
        self.validate_inputs(prompt_id, kwargs)
        spec = self.resolve_prompt(prompt_id)
        template = self.load_legacy(spec.file)
        return template.format(**kwargs)
