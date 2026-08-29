from __future__ import annotations

from pathlib import Path

_SIZE = 17
_NAMES = {
    "PixelFenda_CobaltNoir.cube": "cobalt",
    "PixelFenda_AmberCrypt.cube": "amber",
    "PixelFenda_ChromeIce.cube": "chrome",
}


def _grade(r: float, g: float, b: float, kind: str) -> tuple[float, float, float]:
    # Authorial deterministic LUTs. Values are generated in normalized RGB.
    luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
    if kind == "cobalt":
        rr = 0.78 * r + 0.08 * luma
        gg = 0.84 * g + 0.07 * luma
        bb = 1.08 * b + 0.12 * (1.0 - luma)
        rr = rr ** 1.08
        gg = gg ** 1.04
        bb = bb ** 0.94
    elif kind == "amber":
        rr = 1.08 * r + 0.10 * luma
        gg = 0.92 * g + 0.05 * luma
        bb = 0.72 * b + 0.03 * luma
        rr = rr ** 0.95
        gg = gg ** 1.02
        bb = bb ** 1.10
    else:  # chrome
        # Cool metallic grade: suppress saturation around mid-tones and lift cyan highlights.
        rr = 0.88 * r + 0.11 * luma
        gg = 0.96 * g + 0.12 * luma
        bb = 1.04 * b + 0.10 * luma
        contrast = 0.5 + (luma - 0.5) * 1.12
        rr = 0.76 * rr + 0.24 * contrast
        gg = 0.72 * gg + 0.28 * contrast
        bb = 0.68 * bb + 0.32 * contrast
    return tuple(max(0.0, min(1.0, x)) for x in (rr, gg, bb))


def _cube_text(name: str, kind: str) -> str:
    lines = [
        f'TITLE "{Path(name).stem}"',
        f"LUT_3D_SIZE {_SIZE}",
        "DOMAIN_MIN 0.0 0.0 0.0",
        "DOMAIN_MAX 1.0 1.0 1.0",
        "",
    ]
    # .cube convention: R is the fastest-changing coordinate.
    den = float(_SIZE - 1)
    for bi in range(_SIZE):
        b = bi / den
        for gi in range(_SIZE):
            g = gi / den
            for ri in range(_SIZE):
                r = ri / den
                rr, gg, bb = _grade(r, g, b, kind)
                lines.append(f"{rr:.7f} {gg:.7f} {bb:.7f}")
    return "\n".join(lines) + "\n"


def ensure_builtin_lut(path: str | Path) -> Path:
    p = Path(path)
    if p.exists():
        return p
    kind = _NAMES.get(p.name)
    if kind is None:
        return p
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(_cube_text(p.name, kind), encoding="utf-8")
    return p


def ensure_all_builtin_luts(directory: str | Path) -> list[Path]:
    d = Path(directory)
    return [ensure_builtin_lut(d / name) for name in sorted(_NAMES)]
