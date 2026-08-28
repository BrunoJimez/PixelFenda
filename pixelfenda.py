from __future__ import annotations

import argparse
import json

from pixelfenda.app import run_gui
from pixelfenda.engine import probe_video, render_video
from pixelfenda.ffmpeg_utils import make_output_path
from pixelfenda.presets import RESOLUTION_BY_KEY


def main() -> None:
    parser = argparse.ArgumentParser(description="PixelFenda v0.1.0 — VRAM-inspired glitch video engine")
    parser.add_argument("--cli", action="store_true", help="Executa em modo linha de comando")
    parser.add_argument("-i", "--input")
    parser.add_argument("-o", "--output")
    parser.add_argument("--resolution", default="original", choices=list(RESOLUTION_BY_KEY))
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--resize", default="crop", choices=["crop", "fit", "stretch"])
    parser.add_argument("--effect", default="corrupted_memory", choices=["corrupted_memory", "tile_storm", "palette_collapse", "address_shift", "controlled", "full_corruption"])
    parser.add_argument("--intensity", type=float, default=72.0, help="0 a 100")
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--encoder", default="auto", choices=["auto", "cpu", "nvenc"])
    parser.add_argument("--no-audio", action="store_true")
    parser.add_argument("--max-seconds", type=float, default=None, help="Útil para testes/preview")
    args = parser.parse_args()

    if not args.cli:
        run_gui()
        return
    if not args.input:
        parser.error("--input é obrigatório no modo CLI")

    info = probe_video(args.input)
    preset = RESOLUTION_BY_KEY[args.resolution]
    if args.resolution == "original":
        w, h = info.width, info.height
    elif args.resolution == "custom":
        if not args.width or not args.height:
            parser.error("--width e --height são obrigatórios para --resolution custom")
        w, h = args.width, args.height
    else:
        assert preset.width is not None and preset.height is not None
        w, h = preset.width, preset.height

    output = args.output or make_output_path(args.input, args.effect)

    def progress(v: float, text: str) -> None:
        print(f"[{v*100:6.2f}%] {text}", flush=True)

    result = render_video(
        args.input,
        output,
        w,
        h,
        resize_mode=args.resize,
        effect_preset=args.effect,
        intensity=max(0.0, min(100.0, args.intensity)) / 100.0,
        seed=args.seed,
        preserve_audio=not args.no_audio,
        encoder_mode=args.encoder,
        max_seconds=args.max_seconds,
        progress=progress,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
