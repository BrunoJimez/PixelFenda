from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResolutionPreset:
    key: str
    label: str
    width: int | None
    height: int | None


RESOLUTION_PRESETS = [
    ResolutionPreset("original", "Tamanho original do vídeo", None, None),
    ResolutionPreset("tiktok", "TikTok / Shorts / Reels — 9:16 (1080×1920)", 1080, 1920),
    ResolutionPreset("youtube", "YouTube — 16:9 Full HD (1920×1080)", 1920, 1080),
    ResolutionPreset("instagram_reels", "Instagram Reels/Stories — 9:16 (1080×1920)", 1080, 1920),
    ResolutionPreset("instagram_square", "Instagram Feed — 1:1 (1080×1080)", 1080, 1080),
    ResolutionPreset("instagram_portrait", "Instagram Feed retrato — 4:5 (1080×1350)", 1080, 1350),
    ResolutionPreset("instagram_16_9", "Instagram / vídeo horizontal — 16:9 (1920×1080)", 1920, 1080),
    ResolutionPreset("instagram_landscape", "Instagram Feed paisagem — 1.91:1 (1080×566)", 1080, 566),
    ResolutionPreset("custom", "Resolução personalizada", None, None),
]

RESOLUTION_BY_KEY = {p.key: p for p in RESOLUTION_PRESETS}
RESOLUTION_BY_LABEL = {p.label: p for p in RESOLUTION_PRESETS}


EFFECT_PRESETS = {
    "corrupted_memory": "Corrupted Memory — mistura dinâmica (recomendado)",
    "tile_storm": "Tile Storm — repetição/mosaico de blocos",
    "palette_collapse": "Palette Collapse — saturação e bitplanes",
    "address_shift": "Address Shift — rasgos, stride e deslocamentos",
    "controlled": "Controlled Glitch — mais legível e menos destrutivo",
    "full_corruption": "Full Corruption — máximo caos visual",
}

EFFECT_BY_LABEL = {v: k for k, v in EFFECT_PRESETS.items()}

RESIZE_MODES = {
    "crop": "Preencher e recortar (crop)",
    "fit": "Encaixar com barras pretas (fit)",
    "stretch": "Esticar para a resolução",
}
RESIZE_BY_LABEL = {v: k for k, v in RESIZE_MODES.items()}

ENCODER_MODES = {
    "auto": "Automático (NVENC se disponível)",
    "cpu": "CPU — H.264 libx264",
    "nvenc": "NVIDIA NVENC — H.264",
}
ENCODER_BY_LABEL = {v: k for k, v in ENCODER_MODES.items()}
