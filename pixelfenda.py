from __future__ import annotations

import argparse
import json

from pixelfenda.app import run_gui
from pixelfenda.engine import probe_video, render_video
from pixelfenda.ffmpeg_utils import make_output_path
from pixelfenda.presets import EFFECT_PRESETS, FILTER_PRESETS, RESOLUTION_BY_KEY


def main() -> None:
    p=argparse.ArgumentParser(description="PixelFenda v0.2.1 — Video Mutation Studio")
    p.add_argument("--cli",action="store_true")
    p.add_argument("-i","--input"); p.add_argument("-o","--output")
    p.add_argument("--resolution",default="original",choices=list(RESOLUTION_BY_KEY)); p.add_argument("--width",type=int); p.add_argument("--height",type=int)
    p.add_argument("--resize",default="crop",choices=["crop","fit","stretch"])
    p.add_argument("--no-effect",action="store_true"); p.add_argument("--effect",default="corrupted_memory",choices=list(EFFECT_PRESETS)); p.add_argument("--effect-intensity",type=float,default=72)
    p.add_argument("--filter",default="none",choices=list(FILTER_PRESETS)); p.add_argument("--filter-intensity",type=float,default=100)
    p.add_argument("--reactive",default="none",choices=["none","motion","audio","both"])
    p.add_argument("--audio-mode",default="original",choices=["original","silent","replace","mix"]); p.add_argument("--music")
    p.add_argument("--seed",type=int,default=1337); p.add_argument("--encoder",default="auto",choices=["auto","cpu_h264","h264_nvenc","hevc_nvenc","av1_nvenc"])
    p.add_argument("--gpu",default="auto",choices=["auto","gpu","cpu"]); p.add_argument("--max-seconds",type=float)
    a=p.parse_args()
    if not a.cli: run_gui(); return
    if not a.input: p.error("--input é obrigatório no modo CLI")
    info=probe_video(a.input); rp=RESOLUTION_BY_KEY[a.resolution]
    if a.resolution=="original": w,h=info.width,info.height
    elif a.resolution=="custom":
        if not a.width or not a.height: p.error("--width/--height são obrigatórios com custom")
        w,h=a.width,a.height
    else: w,h=int(rp.width),int(rp.height)
    apply_filter=a.filter!="none"
    tag=a.effect if not a.no_effect else (a.filter if apply_filter else "convert")
    out=a.output or make_output_path(a.input,tag)
    def prog(v,t): print(f"[{v*100:6.2f}%] {t}",flush=True)
    r=render_video(a.input,out,w,h,resize_mode=a.resize,apply_effect=not a.no_effect,effect_preset=a.effect,effect_intensity=max(0,min(100,a.effect_intensity))/100,
        apply_filter=apply_filter,filter_preset=a.filter,filter_intensity=max(0,min(100,a.filter_intensity))/100,seed=a.seed,reactive_mode=a.reactive,
        audio_mode=a.audio_mode,music_path=a.music,encoder_mode=a.encoder,gpu_mode=a.gpu,max_seconds=a.max_seconds,progress=prog)
    print(json.dumps(r,ensure_ascii=False,indent=2))

if __name__=="__main__": main()
