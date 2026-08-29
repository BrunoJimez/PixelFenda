from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
import json
import uuid


@dataclass
class LayerSpec:
    """Serializable processing layer used by PixelFenda v0.3+.

    kind: effect | filter | lut
    intensity controls the effect/filter/LUT itself.
    opacity controls how the processed result is blended back into the stack.
    mod_source selects a per-layer modulation source.
    """

    kind: str = "effect"
    key: str = "corrupted_memory"
    intensity: float = 0.72
    opacity: float = 1.0
    blend: str = "normal"
    mod_source: str = "none"
    mod_amount: float = 0.0
    enabled: bool = True
    scene_reset: bool = False
    lut_path: str | None = None
    name: str | None = None
    uid: str = field(default_factory=lambda: uuid.uuid4().hex[:10])

    def normalized(self) -> "LayerSpec":
        self.kind = self.kind if self.kind in {"effect", "filter", "lut"} else "effect"
        self.intensity = max(0.0, min(1.0, float(self.intensity)))
        self.opacity = max(0.0, min(1.0, float(self.opacity)))
        self.mod_amount = max(0.0, min(1.0, float(self.mod_amount)))
        self.enabled = bool(self.enabled)
        self.scene_reset = bool(self.scene_reset)
        return self

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "LayerSpec":
        allowed = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in raw.items() if k in allowed}).normalized()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProjectDocument:
    format_version: int = 3
    app_version: str = "0.3.0"
    name: str = "Projeto PixelFenda"
    input_path: str = ""
    output_path: str = ""
    resolution: str = "original"
    width: int = 1080
    height: int = 1920
    resize_mode: str = "crop"
    encoder_mode: str = "auto"
    gpu_mode: str = "auto"
    seed: int = 1337
    reactive_mode: str = "none"
    scene_mode: str = "off"
    scene_threshold: float = 0.22
    audio_mode: str = "original"
    music_path: str | None = None
    stem_vocals_path: str | None = None
    stem_instrumental_path: str | None = None
    layers: list[LayerSpec] = field(default_factory=lambda: [LayerSpec()])

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["layers"] = [x.to_dict() for x in self.layers]
        return d

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "ProjectDocument":
        kwargs = dict(raw)
        kwargs["layers"] = [LayerSpec.from_dict(x) for x in raw.get("layers", [])]
        allowed = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in kwargs.items() if k in allowed})

    def save(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "ProjectDocument":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("Projeto PixelFenda inválido: raiz JSON deve ser um objeto.")
        return cls.from_dict(raw)


@dataclass
class RenderJob:
    input_path: str
    output_path: str
    label: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "RenderJob":
        return cls(str(raw.get("input_path", "")), str(raw.get("output_path", "")), str(raw.get("label", "")))
