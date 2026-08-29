from __future__ import annotations

import os
import threading
import traceback
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import cv2
from PIL import Image, ImageTk

from .engine import preview_process, probe_video, render_video
from .ffmpeg_utils import make_output_path
from .presets import (
    AUDIO_BY_LABEL, AUDIO_MODES, EFFECT_BY_LABEL, EFFECT_PRESETS, ENCODER_BY_LABEL,
    ENCODER_MODES, FILTER_BY_LABEL, FILTER_PRESETS, GPU_BY_LABEL, GPU_MODES,
    REACTIVE_BY_LABEL, REACTIVE_MODES, RESIZE_BY_LABEL, RESIZE_MODES,
    RESOLUTION_BY_LABEL, RESOLUTION_PRESETS,
)


class ScrollableFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0)
        self.scroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas)
        self.window = self.canvas.create_window((0,0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scroll.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scroll.pack(side="right", fill="y")
        self.inner.bind("<Configure>", lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self.window, width=e.width))
        self.canvas.bind_all("<MouseWheel>", self._wheel)
        self.canvas.bind_all("<Button-4>", lambda _e: self.canvas.yview_scroll(-3,"units"))
        self.canvas.bind_all("<Button-5>", lambda _e: self.canvas.yview_scroll(3,"units"))

    def _wheel(self, event):
        delta = -1 if event.delta > 0 else 1
        self.canvas.yview_scroll(delta * 3, "units")


class PixelFendaApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("PixelFenda v0.2.1 — Video Mutation Studio")
        self.geometry("1060x820")
        self.minsize(720, 590)
        self.configure(bg="#11161d")
        self.worker: threading.Thread | None = None
        self.preview_photo = None
        self._style()

        self.input_var=tk.StringVar(); self.output_var=tk.StringVar(); self.music_var=tk.StringVar()
        self.res_var=tk.StringVar(value=RESOLUTION_PRESETS[0].label)
        self.custom_w=tk.StringVar(value="1080"); self.custom_h=tk.StringVar(value="1920")
        self.resize_var=tk.StringVar(value=RESIZE_MODES["crop"])
        self.encoder_var=tk.StringVar(value=ENCODER_MODES["auto"])
        self.gpu_var=tk.StringVar(value=GPU_MODES["auto"])
        self.effect_enabled=tk.BooleanVar(value=True)
        self.filter_enabled=tk.BooleanVar(value=False)
        self.effect_var=tk.StringVar(value=EFFECT_PRESETS["corrupted_memory"])
        self.effect_intensity=tk.DoubleVar(value=72)
        self.filter_var=tk.StringVar(value=FILTER_PRESETS["vintage_70"])
        self.filter_intensity=tk.DoubleVar(value=82)
        self.reactive_var=tk.StringVar(value=REACTIVE_MODES["none"])
        self.audio_mode_var=tk.StringVar(value=AUDIO_MODES["original"])
        self.seed_var=tk.StringVar(value="1337")
        self.status_var=tk.StringVar(value="Pronto.")
        self._build_ui()

    def _style(self):
        style=ttk.Style(self)
        try: style.theme_use("clam")
        except tk.TclError: pass
        bg="#11161d"; panel="#171e27"; field="#202a36"; fg="#d8e1ea"; muted="#8ea1b2"; accent="#8fb7c9"
        style.configure(".", background=bg, foreground=fg, font=("Segoe UI",10))
        style.configure("TFrame", background=bg); style.configure("Panel.TFrame", background=panel)
        style.configure("TLabelframe", background=panel, foreground=fg, bordercolor="#2b3948")
        style.configure("TLabelframe.Label", background=panel, foreground=accent, font=("Segoe UI",10,"bold"))
        style.configure("TLabel", background=bg, foreground=fg); style.configure("Panel.TLabel", background=panel, foreground=fg)
        style.configure("Muted.TLabel", background=bg, foreground=muted)
        style.configure("TCheckbutton", background=panel, foreground=fg)
        style.configure("TButton", background=field, foreground=fg, padding=(9,6))
        style.map("TButton", background=[("active","#2a3746")])
        style.configure("Accent.TButton", background="#244254", foreground="#eef8ff", font=("Segoe UI",10,"bold"), padding=(13,8))
        style.map("Accent.TButton", background=[("active","#31586e")])
        style.configure("TEntry", fieldbackground=field, foreground=fg, insertcolor=fg)
        style.configure("TCombobox", fieldbackground=field, background=field, foreground=fg, arrowcolor=fg)
        style.configure("Horizontal.TScale", background=panel, troughcolor="#263443")
        style.configure("TProgressbar", troughcolor="#202a36", background="#789fb2")

    def _section(self, parent, title):
        f=ttk.LabelFrame(parent,text=title)
        f.pack(fill="x", padx=16, pady=(0,10))
        return f

    def _build_ui(self):
        scroll=ScrollableFrame(self); scroll.pack(fill="both",expand=True)
        root=scroll.inner
        head=ttk.Frame(root); head.pack(fill="x",padx=18,pady=(15,12))
        ttk.Label(head,text="PIXELFENDA",font=("Segoe UI",24,"bold")).pack(anchor="w")
        ttk.Label(head,text="v0.2.1 · efeitos + filtros independentes · VRAM 1024×512 · reatividade · GPU OpenGL/RTX",style="Muted.TLabel").pack(anchor="w")

        files=self._section(root,"1 · Arquivos")
        for label,var,cmd in [("Vídeo",self.input_var,self._choose_input),("Saída",self.output_var,self._choose_output)]:
            row=ttk.Frame(files,style="Panel.TFrame"); row.pack(fill="x",padx=10,pady=6)
            ttk.Label(row,text=label,width=9,style="Panel.TLabel").pack(side="left")
            ttk.Entry(row,textvariable=var).pack(side="left",fill="x",expand=True)
            ttk.Button(row,text="Selecionar…",command=cmd).pack(side="left",padx=(8,0))

        fmt=self._section(root,"2 · Formato e renderização")
        grid=ttk.Frame(fmt,style="Panel.TFrame"); grid.pack(fill="x",padx=10,pady=8)
        for c in (1,3): grid.columnconfigure(c,weight=1)
        ttk.Label(grid,text="Resolução",style="Panel.TLabel").grid(row=0,column=0,sticky="w",padx=(0,7),pady=5)
        rc=ttk.Combobox(grid,textvariable=self.res_var,state="readonly",values=[p.label for p in RESOLUTION_PRESETS]); rc.grid(row=0,column=1,sticky="ew",pady=5); rc.bind("<<ComboboxSelected>>",lambda _e:self._update_states())
        custom=ttk.Frame(grid,style="Panel.TFrame"); custom.grid(row=0,column=2,columnspan=2,sticky="e",padx=(12,0))
        ttk.Label(custom,text="W",style="Panel.TLabel").pack(side="left"); self.custom_w_entry=ttk.Entry(custom,textvariable=self.custom_w,width=7); self.custom_w_entry.pack(side="left",padx=(4,8))
        ttk.Label(custom,text="H",style="Panel.TLabel").pack(side="left"); self.custom_h_entry=ttk.Entry(custom,textvariable=self.custom_h,width=7); self.custom_h_entry.pack(side="left",padx=(4,0))
        ttk.Label(grid,text="Enquadramento",style="Panel.TLabel").grid(row=1,column=0,sticky="w",pady=5)
        ttk.Combobox(grid,textvariable=self.resize_var,state="readonly",values=list(RESIZE_MODES.values())).grid(row=1,column=1,sticky="ew",pady=5)
        ttk.Label(grid,text="Encoder",style="Panel.TLabel").grid(row=1,column=2,sticky="w",padx=(12,7),pady=5)
        ttk.Combobox(grid,textvariable=self.encoder_var,state="readonly",values=list(ENCODER_MODES.values())).grid(row=1,column=3,sticky="ew",pady=5)
        ttk.Label(grid,text="Processamento",style="Panel.TLabel").grid(row=2,column=0,sticky="w",pady=5)
        ttk.Combobox(grid,textvariable=self.gpu_var,state="readonly",values=list(GPU_MODES.values())).grid(row=2,column=1,sticky="ew",pady=5)
        ttk.Label(grid,text="Seed",style="Panel.TLabel").grid(row=2,column=2,sticky="w",padx=(12,7),pady=5)
        ttk.Entry(grid,textvariable=self.seed_var).grid(row=2,column=3,sticky="ew",pady=5)

        proc=self._section(root,"3 · Efeitos e filtros")
        toggles=ttk.Frame(proc,style="Panel.TFrame"); toggles.pack(fill="x",padx=10,pady=(8,2))
        ttk.Checkbutton(toggles,text="Aplicar EFEITO",variable=self.effect_enabled,command=self._update_states).pack(side="left")
        ttk.Checkbutton(toggles,text="Aplicar FILTRO",variable=self.filter_enabled,command=self._update_states).pack(side="left",padx=(24,0))
        ttk.Label(toggles,text="Você pode usar só um, os dois, ou nenhum.",style="Panel.TLabel").pack(side="right")
        pg=ttk.Frame(proc,style="Panel.TFrame"); pg.pack(fill="x",padx=10,pady=6); pg.columnconfigure(1,weight=1)
        ttk.Label(pg,text="Efeito",style="Panel.TLabel").grid(row=0,column=0,sticky="w",padx=(0,7),pady=5)
        self.effect_combo=ttk.Combobox(pg,textvariable=self.effect_var,state="readonly",values=list(EFFECT_PRESETS.values())); self.effect_combo.grid(row=0,column=1,sticky="ew",pady=5)
        ttk.Label(pg,text="Intensidade",style="Panel.TLabel").grid(row=1,column=0,sticky="w",pady=5)
        self.effect_scale=ttk.Scale(pg,from_=0,to=100,variable=self.effect_intensity,orient="horizontal"); self.effect_scale.grid(row=1,column=1,sticky="ew",pady=5)
        ttk.Label(pg,textvariable=self.effect_intensity,style="Panel.TLabel",width=6).grid(row=1,column=2,padx=(8,0))
        ttk.Separator(pg).grid(row=2,column=0,columnspan=3,sticky="ew",pady=7)
        ttk.Label(pg,text="Filtro",style="Panel.TLabel").grid(row=3,column=0,sticky="w",padx=(0,7),pady=5)
        self.filter_combo=ttk.Combobox(pg,textvariable=self.filter_var,state="readonly",values=list(FILTER_PRESETS.values())); self.filter_combo.grid(row=3,column=1,sticky="ew",pady=5)
        ttk.Label(pg,text="Intensidade",style="Panel.TLabel").grid(row=4,column=0,sticky="w",pady=5)
        self.filter_scale=ttk.Scale(pg,from_=0,to=100,variable=self.filter_intensity,orient="horizontal"); self.filter_scale.grid(row=4,column=1,sticky="ew",pady=5)
        ttk.Label(pg,textvariable=self.filter_intensity,style="Panel.TLabel",width=6).grid(row=4,column=2,padx=(8,0))
        ttk.Label(pg,text="Reatividade do efeito",style="Panel.TLabel").grid(row=5,column=0,sticky="w",pady=5)
        self.reactive_combo=ttk.Combobox(pg,textvariable=self.reactive_var,state="readonly",values=list(REACTIVE_MODES.values())); self.reactive_combo.grid(row=5,column=1,sticky="ew",pady=5)

        audio=self._section(root,"4 · Áudio")
        ag=ttk.Frame(audio,style="Panel.TFrame"); ag.pack(fill="x",padx=10,pady=8); ag.columnconfigure(1,weight=1)
        ttk.Label(ag,text="Saída de áudio",style="Panel.TLabel").grid(row=0,column=0,sticky="w",padx=(0,7),pady=5)
        ac=ttk.Combobox(ag,textvariable=self.audio_mode_var,state="readonly",values=list(AUDIO_MODES.values())); ac.grid(row=0,column=1,columnspan=2,sticky="ew",pady=5); ac.bind("<<ComboboxSelected>>",lambda _e:self._update_states())
        ttk.Label(ag,text="Nova música",style="Panel.TLabel").grid(row=1,column=0,sticky="w",pady=5)
        self.music_entry=ttk.Entry(ag,textvariable=self.music_var); self.music_entry.grid(row=1,column=1,sticky="ew",pady=5)
        self.music_btn=ttk.Button(ag,text="Abrir…",command=self._choose_music); self.music_btn.grid(row=1,column=2,padx=(8,0),pady=5)
        ttk.Label(ag,text="A música escolhida também pode dirigir os efeitos quando Reatividade = Áudio ou Movimento + Áudio.",style="Panel.TLabel",wraplength=840).grid(row=2,column=0,columnspan=3,sticky="w",pady=(2,4))

        preview=self._section(root,"5 · Prévia")
        bar=ttk.Frame(preview,style="Panel.TFrame"); bar.pack(fill="x",padx=10,pady=(7,3))
        ttk.Button(bar,text="Gerar prévia do quadro central",command=self._preview).pack(side="left")
        ttk.Label(bar,text="A prévia usa valores reativos simulados; o render usa análise real.",style="Panel.TLabel").pack(side="left",padx=12)
        self.preview_label=ttk.Label(preview,anchor="center",style="Panel.TLabel"); self.preview_label.pack(fill="both",expand=True,padx=10,pady=(4,12),ipady=12)

        # fixed footer stays visible even when the content is scrolled
        foot=ttk.Frame(self); foot.pack(fill="x",padx=14,pady=(7,12))
        self.progress=ttk.Progressbar(foot,maximum=100); self.progress.pack(fill="x",side="left",expand=True,padx=(0,10))
        ttk.Label(foot,textvariable=self.status_var,width=38).pack(side="left",padx=(0,10))
        self.render_btn=ttk.Button(foot,text="GERAR VÍDEO",style="Accent.TButton",command=self._start_render); self.render_btn.pack(side="right")
        self._update_states()

    def _choose_input(self):
        p=filedialog.askopenfilename(title="Selecione um vídeo",filetypes=[("Vídeos","*.mp4 *.mov *.mkv *.avi *.webm *.m4v"),("Todos","*.*")])
        if p:
            self.input_var.set(p)
            tag=EFFECT_BY_LABEL.get(self.effect_var.get(),"video") if self.effect_enabled.get() else FILTER_BY_LABEL.get(self.filter_var.get(),"filter")
            self.output_var.set(make_output_path(p,tag))
    def _choose_output(self):
        p=filedialog.asksaveasfilename(title="Salvar vídeo",defaultextension=".mp4",filetypes=[("MP4","*.mp4")]);
        if p: self.output_var.set(p)
    def _choose_music(self):
        p=filedialog.askopenfilename(title="Selecione música/áudio",filetypes=[("Áudio","*.mp3 *.wav *.flac *.m4a *.aac *.ogg *.opus *.mp4"),("Todos","*.*")]);
        if p: self.music_var.set(p)

    def _update_states(self):
        custom=RESOLUTION_BY_LABEL[self.res_var.get()].key=="custom"
        for e in (self.custom_w_entry,self.custom_h_entry): e.configure(state="normal" if custom else "disabled")
        eff=self.effect_enabled.get(); fil=self.filter_enabled.get()
        self.effect_combo.configure(state="readonly" if eff else "disabled"); self.effect_scale.configure(state="normal" if eff else "disabled")
        self.reactive_combo.configure(state="readonly" if eff else "disabled")
        self.filter_combo.configure(state="readonly" if fil else "disabled"); self.filter_scale.configure(state="normal" if fil else "disabled")
        need_music=AUDIO_BY_LABEL[self.audio_mode_var.get()] in {"replace","mix"}
        self.music_entry.configure(state="normal" if need_music else "disabled"); self.music_btn.configure(state="normal" if need_music else "disabled")

    def _resolve_size(self):
        inp=self.input_var.get().strip()
        if not inp: raise ValueError("Selecione um vídeo de entrada.")
        p=RESOLUTION_BY_LABEL[self.res_var.get()]
        if p.key=="original":
            i=probe_video(inp); return i.width,i.height
        if p.key=="custom":
            w,h=int(self.custom_w.get()),int(self.custom_h.get())
            if w<64 or h<64: raise ValueError("A resolução personalizada deve ter pelo menos 64×64.")
            return w,h
        return int(p.width),int(p.height)

    def _format_error(self, exc: BaseException, context: str) -> str:
        message = str(exc).strip() or repr(exc)
        detail = f"{type(exc).__name__}: {message}"
        try:
            log_path = Path(__file__).resolve().parent.parent / "pixelfenda_error.log"
            stamp = datetime.now().isoformat(timespec="seconds")
            trace = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            with log_path.open("a", encoding="utf-8") as fh:
                fh.write(f"\n[{stamp}] {context}\n{trace}\n")
        except Exception:
            pass
        return detail

    def _preview(self):
        try:
            inp=self.input_var.get().strip(); w,h=self._resolve_size()
            cap=cv2.VideoCapture(inp)
            if not cap.isOpened(): raise RuntimeError("Não foi possível abrir o vídeo.")
            n=int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            if n: cap.set(cv2.CAP_PROP_POS_FRAMES,n//2)
            ok,frame=cap.read(); cap.release()
            if not ok: raise RuntimeError("Não foi possível ler o quadro de prévia.")
            out,renderer=preview_process(frame,w,h,resize_mode=RESIZE_BY_LABEL[self.resize_var.get()],
                apply_effect=self.effect_enabled.get(),effect_preset=EFFECT_BY_LABEL[self.effect_var.get()],effect_intensity=float(self.effect_intensity.get())/100,
                apply_filter=self.filter_enabled.get(),filter_preset=FILTER_BY_LABEL[self.filter_var.get()],filter_intensity=float(self.filter_intensity.get())/100,
                seed=int(self.seed_var.get()),gpu_mode=GPU_BY_LABEL[self.gpu_var.get()])
            rgb=cv2.cvtColor(out,cv2.COLOR_BGR2RGB); im=Image.fromarray(rgb); im.thumbnail((900,480))
            self.preview_photo=ImageTk.PhotoImage(im); self.preview_label.configure(image=self.preview_photo)
            self.status_var.set(f"Prévia · {w}×{h} · {renderer}")
        except Exception as exc:
            messagebox.showerror("PixelFenda", self._format_error(exc, "Falha na prévia"))

    def _start_render(self):
        if self.worker and self.worker.is_alive(): return
        try:
            inp=self.input_var.get().strip(); out=self.output_var.get().strip(); w,h=self._resolve_size()
            if not inp or not os.path.isfile(inp): raise ValueError("Selecione um arquivo de vídeo válido.")
            if not out: raise ValueError("Informe o arquivo de saída.")
            seed=int(self.seed_var.get()); audio_mode=AUDIO_BY_LABEL[self.audio_mode_var.get()]
            music=self.music_var.get().strip() or None
            if audio_mode in {"replace","mix"} and (not music or not os.path.isfile(music)): raise ValueError("Selecione uma música/áudio válido.")
        except Exception as exc:
            messagebox.showerror("PixelFenda", self._format_error(exc, "Validação antes do render"))
            return
        # Capture all Tk variables on the UI thread. Tk/Tcl variables must not be
        # read by the background render worker on some Windows/Tk builds.
        effect_on=bool(self.effect_enabled.get()); filter_on=bool(self.filter_enabled.get())
        settings=dict(
            resize_mode=RESIZE_BY_LABEL[self.resize_var.get()],
            apply_effect=effect_on,
            effect_preset=EFFECT_BY_LABEL[self.effect_var.get()],
            effect_intensity=float(self.effect_intensity.get())/100,
            apply_filter=filter_on,
            filter_preset=FILTER_BY_LABEL[self.filter_var.get()],
            filter_intensity=float(self.filter_intensity.get())/100,
            seed=seed,
            reactive_mode=REACTIVE_BY_LABEL[self.reactive_var.get()] if effect_on else "none",
            audio_mode=audio_mode,
            music_path=music,
            encoder_mode=ENCODER_BY_LABEL[self.encoder_var.get()],
            gpu_mode=GPU_BY_LABEL[self.gpu_var.get()],
        )
        self.render_btn.configure(state="disabled"); self.progress["value"]=0; self.status_var.set("Iniciando…")
        def progress(v,t): self.after(0,lambda:self._set_progress(v,t))
        def work():
            try:
                result=render_video(inp,out,w,h,progress=progress,**settings)
                self.after(0,lambda:self._done(result))
            except Exception as exc:
                # Exception variables are cleared by Python when leaving an except block.
                # Capture the formatted text *before* scheduling the Tk callback.
                detail = self._format_error(exc, "Falha durante a renderização")
                self.after(0, lambda text=detail: self._failed(text))
        self.worker=threading.Thread(target=work,daemon=True); self.worker.start()

    def _set_progress(self,v,t): self.progress["value"]=v*100; self.status_var.set(t)
    def _done(self,r):
        self.render_btn.configure(state="normal"); self.progress["value"]=100; self.status_var.set(f"Concluído · {r['encoder']} · {r['gpu_renderer']}")
        messagebox.showinfo("PixelFenda",f"Vídeo gerado com sucesso:\n{r['output']}")
    def _failed(self,t): self.render_btn.configure(state="normal"); self.status_var.set("Falha na renderização."); messagebox.showerror("PixelFenda",t)


def run_gui() -> None:
    PixelFendaApp().mainloop()
