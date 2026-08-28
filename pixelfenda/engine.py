from __future__ import annotations

import math
import os
import subprocess
from dataclasses import dataclass
from typing import Callable

import cv2
import numpy as np

from .ffmpeg_utils import ensure_parent, find_ffmpeg, nvenc_works


ProgressFn = Callable[[float, str], None]


@dataclass
class VideoInfo:
    width: int
    height: int
    fps: float
    frames: int
    duration: float


def probe_video(path: str) -> VideoInfo:
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError(f"Não foi possível abrir o vídeo: {path}")
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    cap.release()
    duration = frames / fps if fps > 0 and frames > 0 else 0.0
    return VideoInfo(width, height, fps, frames, duration)


def fit_frame(frame: np.ndarray, width: int, height: int, mode: str) -> np.ndarray:
    src_h, src_w = frame.shape[:2]
    if mode == "stretch":
        return cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)

    src_ratio = src_w / src_h
    dst_ratio = width / height

    if mode == "crop":
        if src_ratio > dst_ratio:
            new_h = height
            new_w = int(round(height * src_ratio))
        else:
            new_w = width
            new_h = int(round(width / src_ratio))
        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
        x = max(0, (new_w - width) // 2)
        y = max(0, (new_h - height) // 2)
        return resized[y : y + height, x : x + width].copy()

    # fit
    if src_ratio > dst_ratio:
        new_w = width
        new_h = max(1, int(round(width / src_ratio)))
    else:
        new_h = height
        new_w = max(1, int(round(height * src_ratio)))
    resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    x = (width - new_w) // 2
    y = (height - new_h) // 2
    canvas[y : y + new_h, x : x + new_w] = resized
    return canvas


def _pack_bgr555(img: np.ndarray) -> np.ndarray:
    b = (img[..., 0].astype(np.uint16) >> 3) & 31
    g = (img[..., 1].astype(np.uint16) >> 3) & 31
    r = (img[..., 2].astype(np.uint16) >> 3) & 31
    return (r << 10) | (g << 5) | b


def _unpack_bgr555(mem: np.ndarray) -> np.ndarray:
    b = (mem & 31).astype(np.uint8)
    g = ((mem >> 5) & 31).astype(np.uint8)
    r = ((mem >> 10) & 31).astype(np.uint8)
    # Replicate high bits to fill 8-bit range: abcde -> abcdeabc
    b8 = (b << 3) | (b >> 2)
    g8 = (g << 3) | (g >> 2)
    r8 = (r << 3) | (r >> 2)
    return np.dstack([b8, g8, r8])


def _ordered_dither(img: np.ndarray, amount: float) -> np.ndarray:
    if amount <= 0:
        return img
    bayer = np.array(
        [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]],
        dtype=np.float32,
    )
    h, w = img.shape[:2]
    tiled = np.tile(bayer, (math.ceil(h / 4), math.ceil(w / 4)))[:h, :w]
    offset = ((tiled / 15.0) - 0.5) * (amount * 26.0)
    out = img.astype(np.float32) + offset[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)


class PixelFendaEffect:
    """VRAM-inspired video corruption on a 15-bit packed virtual framebuffer.

    It intentionally works on frame data rather than applying a static overlay.
    The design is inspired by low-level memory/addressing artifacts: rectangle
    blits, stride errors, persistent framebuffer fragments and bitplane damage.
    """

    def __init__(
        self,
        output_width: int,
        output_height: int,
        intensity: float = 0.72,
        seed: int = 1337,
        preset: str = "corrupted_memory",
    ) -> None:
        self.out_w = int(output_width)
        self.out_h = int(output_height)
        self.intensity = float(np.clip(intensity, 0.0, 1.0))
        self.seed = int(seed)
        self.preset = preset
        self.rng = np.random.default_rng(self.seed)
        self.frame_index = 0
        self.event_left = 0
        self.event_mode = "mixed"
        self.prev_mem: np.ndarray | None = None

        # Keep a low-resolution virtual framebuffer so nearest-neighbour output
        # has authentic large pixels. Aspect ratio follows the selected output.
        ratio = self.out_w / self.out_h
        if ratio >= 1:
            self.core_w = min(360, self.out_w)
            self.core_h = max(64, int(round(self.core_w / ratio)))
            if self.core_h > 240:
                self.core_h = 240
                self.core_w = max(64, int(round(self.core_h * ratio)))
        else:
            self.core_h = min(320, self.out_h)
            self.core_w = max(64, int(round(self.core_h * ratio)))
            if self.core_w > 240:
                self.core_w = 240
                self.core_h = max(64, int(round(self.core_w / ratio)))

    def _new_event(self) -> None:
        modes_by_preset = {
            "corrupted_memory": ["tiles", "palette", "address", "mixed", "sparse", "mixed"],
            "tile_storm": ["tiles", "tiles", "mixed"],
            "palette_collapse": ["palette", "palette", "mixed"],
            "address_shift": ["address", "address", "mixed"],
            "controlled": ["sparse", "tiles", "palette"],
            "full_corruption": ["mixed", "address", "palette", "tiles", "mixed"],
        }
        choices = modes_by_preset.get(self.preset, modes_by_preset["corrupted_memory"])
        self.event_mode = str(self.rng.choice(choices))
        base = int(self.rng.integers(5, 26))
        if self.preset == "controlled":
            base = int(self.rng.integers(12, 45))
        self.event_left = base

    def _tile_blits(self, mem: np.ndarray, severity: float) -> None:
        h, w = mem.shape
        n = max(1, int(1 + severity * 14))
        for _ in range(n):
            tw = int(self.rng.integers(max(2, w // 40), max(3, w // 5)))
            th = int(self.rng.integers(max(2, h // 40), max(3, h // 4)))
            sx = int(self.rng.integers(0, max(1, w - tw)))
            sy = int(self.rng.integers(0, max(1, h - th)))
            dx = int(self.rng.integers(0, max(1, w - tw)))
            dy = int(self.rng.integers(0, max(1, h - th)))
            tile = mem[sy : sy + th, sx : sx + tw].copy()
            if self.rng.random() < 0.35:
                tile = np.flip(tile, axis=int(self.rng.integers(0, 2)))
            mem[dy : dy + th, dx : dx + tw] = tile

    def _address_shifts(self, mem: np.ndarray, severity: float) -> None:
        h, w = mem.shape
        n = max(1, int(1 + severity * 12))
        for _ in range(n):
            if self.rng.random() < 0.68:
                y0 = int(self.rng.integers(0, h))
                bh = int(self.rng.integers(1, max(2, h // 5)))
                y1 = min(h, y0 + bh)
                shift = int(self.rng.integers(-max(2, w // 2), max(3, w // 2)))
                mem[y0:y1] = np.roll(mem[y0:y1], shift, axis=1)
            else:
                x0 = int(self.rng.integers(0, w))
                bw = int(self.rng.integers(1, max(2, w // 5)))
                x1 = min(w, x0 + bw)
                shift = int(self.rng.integers(-max(2, h // 2), max(3, h // 2)))
                mem[:, x0:x1] = np.roll(mem[:, x0:x1], shift, axis=0)

        if self.rng.random() < 0.4 + 0.45 * severity:
            y0 = int(self.rng.integers(0, max(1, h - 4)))
            bh = int(self.rng.integers(3, max(4, h // 2)))
            y1 = min(h, y0 + bh)
            band = mem[y0:y1].copy().reshape(-1)
            delta = int(self.rng.integers(-max(2, w * 3), max(3, w * 3)))
            band = np.roll(band, delta)
            mem[y0:y1] = band.reshape(y1 - y0, w)

    def _palette_damage(self, mem: np.ndarray, severity: float) -> None:
        h, w = mem.shape
        n = max(1, int(1 + severity * 8))
        masks = np.array([0x001F, 0x03E0, 0x7C00, 0x7FFF, 0x4210, 0x2108], dtype=np.uint16)
        for _ in range(n):
            x0 = int(self.rng.integers(0, w))
            y0 = int(self.rng.integers(0, h))
            x1 = int(self.rng.integers(x0 + 1, w + 1))
            y1 = int(self.rng.integers(y0 + 1, h + 1))
            block = mem[y0:y1, x0:x1]
            op = int(self.rng.integers(0, 4))
            mask = np.uint16(self.rng.choice(masks))
            if op == 0:
                block ^= mask
            elif op == 1:
                block |= mask
                block &= np.uint16(0x7FFF)
            elif op == 2:
                block &= mask
            else:
                shift = int(self.rng.integers(1, 6))
                block[:] = ((block << shift) | (block >> (15 - shift))) & np.uint16(0x7FFF)

    def _line_patterns(self, mem: np.ndarray, severity: float) -> None:
        h, w = mem.shape
        spacing = max(2, int(round(12 - severity * 9)))
        start = int(self.rng.integers(0, spacing))
        rows = np.arange(start, h, spacing)
        if len(rows):
            shifts = self.rng.integers(-max(2, w // 3), max(3, w // 3), size=len(rows))
            for row, shift in zip(rows, shifts):
                mem[row : row + 1] = np.roll(mem[row : row + 1], int(shift), axis=1)
        if self.rng.random() < 0.5:
            spacing_x = max(3, int(round(18 - severity * 12)))
            cols = np.arange(int(self.rng.integers(0, spacing_x)), w, spacing_x)
            mem[:, cols] ^= np.uint16(self.rng.choice([0x001F, 0x03E0, 0x7C00]))

    def _feedback(self, mem: np.ndarray, severity: float) -> None:
        if self.prev_mem is None or self.prev_mem.shape != mem.shape:
            return
        h, w = mem.shape
        n = max(1, int(severity * 6))
        for _ in range(n):
            tw = int(self.rng.integers(max(2, w // 30), max(3, w // 4)))
            th = int(self.rng.integers(max(2, h // 30), max(3, h // 3)))
            x = int(self.rng.integers(0, max(1, w - tw)))
            y = int(self.rng.integers(0, max(1, h - th)))
            mem[y : y + th, x : x + tw] = self.prev_mem[y : y + th, x : x + tw]

    def process(self, frame_bgr: np.ndarray) -> np.ndarray:
        self.frame_index += 1
        if self.event_left <= 0:
            self._new_event()
        self.event_left -= 1

        small = cv2.resize(frame_bgr, (self.core_w, self.core_h), interpolation=cv2.INTER_AREA)

        # Dynamic ordered dithering before 15-bit packing.
        dither_amount = 0.12 + self.intensity * 0.65
        if self.preset == "controlled":
            dither_amount *= 0.45
        small = _ordered_dither(small, dither_amount)
        mem = _pack_bgr555(small)

        sev = self.intensity
        if self.preset == "full_corruption":
            sev = min(1.0, 0.25 + sev * 0.95)
        elif self.preset == "controlled":
            sev *= 0.48

        # Persistent fragments emulate stale framebuffer regions.
        if self.prev_mem is not None and self.prev_mem.shape == mem.shape:
            feedback_prob = 0.12 + 0.55 * sev
            if self.rng.random() < feedback_prob:
                self._feedback(mem, sev)

        mode = self.event_mode
        if mode in ("tiles", "mixed"):
            self._tile_blits(mem, sev)
        if mode in ("address", "mixed"):
            self._address_shifts(mem, sev)
        if mode in ("palette", "mixed"):
            self._palette_damage(mem, sev)
        if mode in ("sparse", "address", "mixed"):
            self._line_patterns(mem, sev)

        # Rare full-frame memory events create the abrupt radical changes seen
        # in genuine glitch workflows.
        if self.rng.random() < 0.012 + 0.05 * sev:
            op = int(self.rng.integers(0, 3))
            if op == 0:
                mem[:] = np.roll(mem.reshape(-1), int(self.rng.integers(-mem.size // 5, mem.size // 5))).reshape(mem.shape)
            elif op == 1:
                mem ^= np.uint16(self.rng.choice([0x001F, 0x03E0, 0x7C00, 0x4210]))
            else:
                step = int(self.rng.integers(2, 7))
                mem[::step] = np.roll(mem[::step], int(self.rng.integers(-self.core_w // 2, self.core_w // 2)), axis=1)

        self.prev_mem = mem.copy()
        out_small = _unpack_bgr555(mem)

        # Palette exaggeration is done after unpacking, without using a static LUT.
        if mode == "palette" or self.preset in ("palette_collapse", "full_corruption"):
            hsv = cv2.cvtColor(out_small, cv2.COLOR_BGR2HSV)
            sat_gain = 1.1 + 1.6 * sev
            val_gain = 0.93 + 0.25 * sev
            hsv[..., 1] = np.clip(hsv[..., 1].astype(np.float32) * sat_gain, 0, 255).astype(np.uint8)
            hsv[..., 2] = np.clip(hsv[..., 2].astype(np.float32) * val_gain, 0, 255).astype(np.uint8)
            out_small = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

        return cv2.resize(out_small, (self.out_w, self.out_h), interpolation=cv2.INTER_NEAREST)


def render_video(
    input_path: str,
    output_path: str,
    width: int,
    height: int,
    resize_mode: str = "crop",
    effect_preset: str = "corrupted_memory",
    intensity: float = 0.72,
    seed: int = 1337,
    preserve_audio: bool = True,
    encoder_mode: str = "auto",
    max_seconds: float | None = None,
    progress: ProgressFn | None = None,
) -> dict:
    ensure_parent(output_path)
    info = probe_video(input_path)
    fps = info.fps if info.fps > 0 else 30.0
    total_frames = info.frames
    if max_seconds is not None and max_seconds > 0:
        total_frames = min(total_frames, int(round(max_seconds * fps))) if total_frames else int(round(max_seconds * fps))

    ffmpeg = find_ffmpeg()
    use_nvenc = encoder_mode == "nvenc" or (encoder_mode == "auto" and nvenc_works(ffmpeg))
    if encoder_mode == "nvenc" and not use_nvenc:
        raise RuntimeError("NVENC foi solicitado, mas não está funcional neste computador/FFmpeg.")

    def encode_once(nvenc: bool) -> tuple[int, int]:
        codec_args = ["-c:v", "h264_nvenc", "-preset", "p5", "-cq", "19", "-b:v", "0"] if nvenc else ["-c:v", "libx264", "-preset", "medium", "-crf", "18"]
        cmd = [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "bgr24",
            "-s",
            f"{width}x{height}",
            "-r",
            f"{fps:.8f}",
            "-i",
            "-",
        ]
        if preserve_audio:
            cmd += ["-i", input_path, "-map", "0:v:0", "-map", "1:a?"]
        else:
            cmd += ["-map", "0:v:0"]
        cmd += codec_args
        cmd += ["-pix_fmt", "yuv420p"]
        if preserve_audio:
            cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest"]
        else:
            cmd += ["-an"]
        cmd += ["-movflags", "+faststart", output_path]

        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise RuntimeError(f"Não foi possível abrir o vídeo: {input_path}")
        effect = PixelFendaEffect(width, height, intensity, seed, effect_preset)
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        rendered = 0
        try:
            while True:
                if total_frames and rendered >= total_frames:
                    break
                ok, frame = cap.read()
                if not ok:
                    break
                fitted = fit_frame(frame, width, height, resize_mode)
                glitched = effect.process(fitted)
                assert proc.stdin is not None
                proc.stdin.write(glitched.tobytes())
                rendered += 1
                if progress and (rendered == 1 or rendered % 5 == 0):
                    denom = total_frames if total_frames else max(1, rendered)
                    progress(min(0.995, rendered / denom), f"Processando quadro {rendered}/{total_frames or '?'}")
        except BrokenPipeError:
            pass
        finally:
            cap.release()
            if proc.stdin:
                try:
                    proc.stdin.close()
                except Exception:
                    pass
        stderr = b""
        if proc.stderr:
            stderr = proc.stderr.read()
        code = proc.wait()
        if code != 0:
            message = stderr.decode("utf-8", errors="replace")[-4000:]
            raise RuntimeError(f"FFmpeg encerrou com erro ({code}).\n{message}")
        return rendered, code

    if progress:
        progress(0.0, "Preparando renderização")
    try:
        rendered, _ = encode_once(use_nvenc)
        encoder = "h264_nvenc" if use_nvenc else "libx264"
    except Exception:
        if use_nvenc and encoder_mode == "auto":
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except OSError:
                    pass
            if progress:
                progress(0.0, "NVENC indisponível; repetindo com CPU/libx264")
            rendered, _ = encode_once(False)
            encoder = "libx264"
        else:
            raise

    if progress:
        progress(1.0, "Concluído")
    return {
        "input": input_path,
        "output": output_path,
        "width": width,
        "height": height,
        "fps": fps,
        "frames": rendered,
        "encoder": encoder,
        "effect": effect_preset,
        "intensity": intensity,
        "seed": seed,
        "audio": preserve_audio,
    }
