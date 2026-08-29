from __future__ import annotations

from pathlib import Path


def load_split_source(prefix: str, namespace: dict) -> None:
    """Load a source module stored in readable numbered chunks.

    The split is only a repository transport/layout detail: chunks are plain UTF-8
    Python source and are concatenated byte-for-byte before compilation.
    """
    root = Path(__file__).resolve().parent / "_source_parts"
    parts = sorted(root.glob(f"{prefix}.*"))
    if not parts:
        raise ImportError(f"PixelFenda source parts not found for {prefix}")
    source = "".join(p.read_text(encoding="utf-8") for p in parts)
    exec(compile(source, str(namespace.get("__file__", prefix + ".py")), "exec"), namespace, namespace)
