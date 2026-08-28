from __future__ import annotations

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import cv2
from PIL import Image, ImageTk

from .engine import PixelFendaEffect, fit_frame, probe_video, render_video
from .ffmpeg_utils import make_output_path
from .presets import (
    EFFECT_BY_LABEL,
    EFFECT_PRESETS,
    ENCODER_BY_LABEL,
    ENCODER_MODES,
    RESIZE_BY_LABEL,
    RESIZE_MODES,
    RESOLUTION_BY_LABEL,
    RESOLUTION_PRESETS,
)


class PixelFendaApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("PixelFenda v0.1.0 — VRAM Corruption Video Engine")
        self.geometry("980x780")
        self.minsize(900, 700)
        self.preview_photo = None
        self.worker: threading.Thread | None = None

        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.res_var = tk.StringVar(value=RESOLUTION_PRESETS[0].label)
        self.custom_w = tk.StringVar(value="1080")
        self.custom_h = tk.StringVar(value="1920")
        self.resize_var = tk.StringVar(value=RESIZE_MODES["crop"])
        self.effect_var = tk.StringVar(value=EFFECT_PRESETS["corrupted_memory"])
        self.intensity_var = tk.DoubleVar(value=72)
        self.seed_var = tk.StringVar(value="1337")
        self.audio_var = tk.BooleanVar(value=True)
        self.encoder_var = tk.StringVar(value=ENCODER_MODES["auto"])
        self.status_var = tk.StringVar(value="Pronto.")

        self._build_ui()

    def _build_ui(self) -> None:
        pad = {"padx": 10, "pady": 6}
        root = ttk.Frame(self)
        root.pack(fill="both", expand=True, padx=14, pady=12)

        title = ttk.Label(root, text="PIXELFENDA", font=("Segoe UI", 22, "bold"))
        title.pack(anchor="w")
        ttk.Label(
            root,
            text="v0.1.0 — núcleo VRAM Corruption: pixels, tiles, bitplanes, tearing e framebuffer persistente",
        ).pack(anchor="w", pady=(0, 10))

        io = ttk.LabelFrame(root, text="1. Arquivos")
        io.pack(fill="x")
        row = ttk.Frame(io)
        row.pack(fill="x", **pad)
        ttk.Label(row, text="Entrada:", width=10).pack(side="left")
        ttk.Entry(row, textvariable=self.input_var).pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Abrir...", command=self._choose_input).pack(side="left", padx=(8, 0))
        row = ttk.Frame(io)
        row.pack(fill="x", **pad)
        ttk.Label(row, text="Saída:", width=10).pack(side="left")
        ttk.Entry(row, textvariable=self.output_var).pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Salvar como...", command=self._choose_output).pack(side="left", padx=(8, 0))

        settings = ttk.LabelFrame(root, text="2. Formato e efeito")
        settings.pack(fill="x", pady=(10, 0))

        grid = ttk.Frame(settings)
        grid.pack(fill="x", **pad)
        grid.columnconfigure(1, weight=1)
        grid.columnconfigure(3, weight=1)

        ttk.Label(grid, text="Resolução:").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=4)
        res_combo = ttk.Combobox(grid, textvariable=self.res_var, state="readonly", values=[p.label for p in RESOLUTION_PRESETS])
        res_combo.grid(row=0, column=1, sticky="ew", pady=4)
        res_combo.bind("<<ComboboxSelected>>", lambda _e: self._update_custom_state())

        custom = ttk.Frame(grid)
        custom.grid(row=0, column=2, columnspan=2, sticky="e", padx=(12, 0))
        ttk.Label(custom, text="W:").pack(side="left")
        self.custom_w_entry = ttk.Entry(custom, textvariable=self.custom_w, width=7)
        self.custom_w_entry.pack(side="left", padx=(3, 8))
        ttk.Label(custom, text="H:").pack(side="left")
        self.custom_h_entry = ttk.Entry(custom, textvariable=self.custom_h, width=7)
        self.custom_h_entry.pack(side="left", padx=(3, 0))

        ttk.Label(grid, text="Ajuste:").grid(row=1, column=0, sticky="w", padx=(0, 6), pady=4)
        ttk.Combobox(grid, textvariable=self.resize_var, state="readonly", values=list(RESIZE_MODES.values())).grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(grid, text="Encoder:").grid(row=1, column=2, sticky="w", padx=(12, 6), pady=4)
        ttk.Combobox(grid, textvariable=self.encoder_var, state="readonly", values=list(ENCODER_MODES.values())).grid(row=1, column=3, sticky="ew", pady=4)

        ttk.Label(grid, text="Efeito:").grid(row=2, column=0, sticky="w", padx=(0, 6), pady=4)
        ttk.Combobox(grid, textvariable=self.effect_var, state="readonly", values=list(EFFECT_PRESETS.values())).grid(row=2, column=1, columnspan=3, sticky="ew", pady=4)

        ttk.Label(grid, text="Intensidade:").grid(row=3, column=0, sticky="w", padx=(0, 6), pady=4)
        ttk.Scale(grid, from_=0, to=100, variable=self.intensity_var, orient="horizontal").grid(row=3, column=1, sticky="ew", pady=4)
        ttk.Label(grid, textvariable=self.intensity_var, width=6).grid(row=3, column=2, sticky="w", padx=(12, 0))

        seed_frame = ttk.Frame(grid)
        seed_frame.grid(row=4, column=0, columnspan=4, sticky="ew", pady=4)
        ttk.Label(seed_frame, text="Semente:").pack(side="left")
        ttk.Entry(seed_frame, textvariable=self.seed_var, width=12).pack(side="left", padx=(6, 18))
        ttk.Checkbutton(seed_frame, text="Preservar áudio original", variable=self.audio_var).pack(side="left")

        actions = ttk.Frame(root)
        actions.pack(fill="x", pady=(10, 0))
        ttk.Button(actions, text="Pré-visualizar quadro", command=self._preview).pack(side="left")
        self.render_btn = ttk.Button(actions, text="GERAR VÍDEO", command=self._start_render)
        self.render_btn.pack(side="right")

        preview_box = ttk.LabelFrame(root, text="Prévia")
        preview_box.pack(fill="both", expand=True, pady=(10, 0))
        self.preview_label = ttk.Label(preview_box, anchor="center")
        self.preview_label.pack(fill="both", expand=True, padx=8, pady=8)

        self.progress = ttk.Progressbar(root, maximum=100)
        self.progress.pack(fill="x", pady=(10, 3))
        ttk.Label(root, textvariable=self.status_var).pack(anchor="w")
        self._update_custom_state()

    def _choose_input(self) -> None:
        path = filedialog.askopenfilename(
            title="Selecione um vídeo",
            filetypes=[("Vídeos", "*.mp4 *.mov *.mkv *.avi *.webm *.m4v"), ("Todos os arquivos", "*.*")],
        )
        if path:
            self.input_var.set(path)
            effect_key = EFFECT_BY_LABEL.get(self.effect_var.get(), "corrupted_memory")
            self.output_var.set(make_output_path(path, effect_key))

    def _choose_output(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Salvar vídeo",
            defaultextension=".mp4",
            filetypes=[("MP4", "*.mp4")],
        )
        if path:
            self.output_var.set(path)

    def _update_custom_state(self) -> None:
        custom = RESOLUTION_BY_LABEL[self.res_var.get()].key == "custom"
        state = "normal" if custom else "disabled"
        self.custom_w_entry.configure(state=state)
        self.custom_h_entry.configure(state=state)

    def _resolve_size(self) -> tuple[int, int]:
        inp = self.input_var.get().strip()
        if not inp:
            raise ValueError("Selecione um vídeo de entrada.")
        p = RESOLUTION_BY_LABEL[self.res_var.get()]
        if p.key == "original":
            info = probe_video(inp)
            return info.width, info.height
        if p.key == "custom":
            w = int(self.custom_w.get())
            h = int(self.custom_h.get())
            if w < 64 or h < 64:
                raise ValueError("A resolução personalizada deve ter pelo menos 64×64.")
            return w, h
        assert p.width is not None and p.height is not None
        return p.width, p.height

    def _preview(self) -> None:
        try:
            inp = self.input_var.get().strip()
            w, h = self._resolve_size()
            cap = cv2.VideoCapture(inp)
            if not cap.isOpened():
                raise RuntimeError("Não foi possível abrir o vídeo.")
            count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            if count > 0:
                cap.set(cv2.CAP_PROP_POS_FRAMES, count // 2)
            ok, frame = cap.read()
            cap.release()
            if not ok:
                raise RuntimeError("Não foi possível ler um quadro para a prévia.")
            frame = fit_frame(frame, w, h, RESIZE_BY_LABEL[self.resize_var.get()])
            effect = PixelFendaEffect(
                w,
                h,
                float(self.intensity_var.get()) / 100.0,
                int(self.seed_var.get()),
                EFFECT_BY_LABEL[self.effect_var.get()],
            )
            # Prime a state for a more representative glitch event.
            for _ in range(4):
                out = effect.process(frame)
            rgb = cv2.cvtColor(out, cv2.COLOR_BGR2RGB)
            im = Image.fromarray(rgb)
            im.thumbnail((820, 390))
            self.preview_photo = ImageTk.PhotoImage(im)
            self.preview_label.configure(image=self.preview_photo)
            self.status_var.set(f"Prévia: {w}×{h} | seed {self.seed_var.get()}")
        except Exception as exc:
            messagebox.showerror("PixelFenda", str(exc))

    def _start_render(self) -> None:
        if self.worker and self.worker.is_alive():
            return
        try:
            inp = self.input_var.get().strip()
            out = self.output_var.get().strip()
            if not inp or not os.path.isfile(inp):
                raise ValueError("Selecione um arquivo de vídeo válido.")
            if not out:
                raise ValueError("Informe o arquivo de saída.")
            w, h = self._resolve_size()
            seed = int(self.seed_var.get())
        except Exception as exc:
            messagebox.showerror("PixelFenda", str(exc))
            return

        self.render_btn.configure(state="disabled")
        self.progress["value"] = 0
        self.status_var.set("Iniciando...")

        def progress(value: float, text: str) -> None:
            self.after(0, lambda: self._set_progress(value, text))

        def work() -> None:
            try:
                result = render_video(
                    inp,
                    out,
                    w,
                    h,
                    resize_mode=RESIZE_BY_LABEL[self.resize_var.get()],
                    effect_preset=EFFECT_BY_LABEL[self.effect_var.get()],
                    intensity=float(self.intensity_var.get()) / 100.0,
                    seed=seed,
                    preserve_audio=bool(self.audio_var.get()),
                    encoder_mode=ENCODER_BY_LABEL[self.encoder_var.get()],
                    progress=progress,
                )
                self.after(0, lambda: self._done(result))
            except Exception as exc:
                self.after(0, lambda: self._failed(str(exc)))

        self.worker = threading.Thread(target=work, daemon=True)
        self.worker.start()

    def _set_progress(self, value: float, text: str) -> None:
        self.progress["value"] = value * 100.0
        self.status_var.set(text)

    def _done(self, result: dict) -> None:
        self.render_btn.configure(state="normal")
        self.progress["value"] = 100
        self.status_var.set(f"Concluído — {result['encoder']} — {result['frames']} quadros")
        messagebox.showinfo("PixelFenda", f"Vídeo gerado com sucesso:\n{result['output']}")

    def _failed(self, text: str) -> None:
        self.render_btn.configure(state="normal")
        self.status_var.set("Falha na renderização.")
        messagebox.showerror("PixelFenda", text)


def run_gui() -> None:
    app = PixelFendaApp()
    app.mainloop()
