#!/usr/bin/env python3
"""Lokaler Background-Remover für Vintage-/Produktbilder.

- Eingabe: Einzelbild oder Ordner
- Ausgabe: immer transparentes PNG
- Watch-Mode: neue Dateien in REIN_HIER werden sofort verarbeitet
- Dateiformat wird am Inhalt erkannt; HEIC/HEIF via pillow-heif
- Standardmodell: birefnet-general über rembg
"""
from __future__ import annotations

import argparse
import json
import queue
import sys
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError
from rembg import new_session, remove
from pillow_heif import register_heif_opener
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

register_heif_opener()

DEFAULT_MODEL = "birefnet-general"
DEFAULT_INPUT = "REIN_HIER"
DEFAULT_OUTPUT = "FREIGESTELLT"
DEFAULT_SUFFIX = "_freigestellt"


@dataclass(slots=True)
class Result:
    input: str
    output: str | None
    status: str
    seconds: float
    input_format: str | None = None
    original_size: tuple[int, int] | None = None
    output_size: tuple[int, int] | None = None
    message: str | None = None


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Bilder lokal freistellen und als PNG speichern.")
    p.add_argument("input", nargs="?", default=DEFAULT_INPUT)
    p.add_argument("output", nargs="?", default=DEFAULT_OUTPUT)
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--edge", choices=("decontaminate", "alpha", "none"), default="decontaminate")
    p.add_argument("--no-crop", action="store_true")
    p.add_argument("--padding", type=float, default=0.03)
    p.add_argument("--alpha-threshold", type=int, default=8)
    p.add_argument("--canvas", type=int, default=0)
    p.add_argument("--margin", type=float, default=0.06)
    p.add_argument("--background", choices=("transparent", "white"), default="transparent")
    p.add_argument("--recursive", action="store_true")
    p.add_argument("--overwrite", action="store_true")
    p.add_argument("--suffix", default=DEFAULT_SUFFIX)
    p.add_argument("--watch", action="store_true")
    p.add_argument("--stable-seconds", type=float, default=0.8)
    p.add_argument("--json", action="store_true")
    return p


def can_open(path: Path) -> bool:
    if not path.is_file() or path.name.startswith("."):
        return False
    try:
        with Image.open(path) as im:
            im.verify()
        return True
    except (UnidentifiedImageError, OSError, ValueError):
        return False


def load(path: Path) -> tuple[Image.Image, str | None]:
    with Image.open(path) as opened:
        fmt = opened.format
        if getattr(opened, "is_animated", False):
            opened.seek(0)
        im = ImageOps.exif_transpose(opened).convert("RGB")
        im.load()
    return im, fmt


def crop_alpha(im: Image.Image, threshold: int, padding: float) -> Image.Image:
    rgba = im.convert("RGBA")
    alpha = rgba.getchannel("A")
    mask = alpha.point(lambda x: 255 if x >= threshold else 0)
    bbox = mask.getbbox()
    if bbox is None:
        raise ValueError("Kein Vordergrundobjekt erkannt.")
    cut = rgba.crop(bbox)
    if padding <= 0:
        return cut
    pad = max(1, round(max(cut.size) * padding))
    out = Image.new("RGBA", (cut.width + 2 * pad, cut.height + 2 * pad), (0, 0, 0, 0))
    out.alpha_composite(cut, (pad, pad))
    return out


def canvas(im: Image.Image, size: int, margin: float, background: str) -> Image.Image:
    if size <= 0:
        return im.convert("RGBA")
    inner = max(1, round(size * (1 - 2 * margin)))
    scale = min(inner / im.width, inner / im.height)
    new_size = (max(1, round(im.width * scale)), max(1, round(im.height * scale)))
    resized = im.convert("RGBA").resize(new_size, Image.Resampling.LANCZOS)
    bg = (255, 255, 255, 255) if background == "white" else (0, 0, 0, 0)
    out = Image.new("RGBA", (size, size), bg)
    pos = ((size - resized.width) // 2, (size - resized.height) // 2)
    out.alpha_composite(resized, pos)
    return out


def save_png(im: Image.Image, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + ".tmp")
    try:
        im.save(tmp, format="PNG", optimize=True, compress_level=6)
        tmp.replace(target)
    finally:
        tmp.unlink(missing_ok=True)


def target_path(source: Path, out: Path, root: Path | None, suffix: str) -> Path:
    if root is None:
        if out.suffix.lower() == ".png":
            return out
        return out / f"{source.stem}{suffix}.png"
    rel_parent = source.parent.relative_to(root)
    return out / rel_parent / f"{source.stem}{suffix}.png"


def process(source: Path, target: Path, session, args) -> Result:
    started = time.perf_counter()
    if target.exists() and not args.overwrite:
        return Result(str(source), str(target), "skipped", 0.0, message="Zieldatei existiert bereits.")
    try:
        image, fmt = load(source)
        original = image.size
        cut = remove(
            image,
            session=session,
            decontaminate=args.edge == "decontaminate",
            alpha_matting=args.edge == "alpha",
        )
        if not isinstance(cut, Image.Image):
            raise TypeError("rembg lieferte kein PIL-Bild zurück.")
        cut = cut.convert("RGBA")
        if not args.no_crop:
            cut = crop_alpha(cut, args.alpha_threshold, args.padding)
        cut = canvas(cut, args.canvas, args.margin, args.background)
        save_png(cut, target)
        return Result(str(source), str(target), "ok", round(time.perf_counter() - started, 3), fmt, original, cut.size)
    except Exception as exc:
        return Result(str(source), str(target), "error", round(time.perf_counter() - started, 3), message=f"{type(exc).__name__}: {exc}")


def show(result: Result) -> None:
    if result.status == "ok":
        print(f"[OK] {Path(result.input).name} -> {result.output} ({result.seconds:.2f}s)", flush=True)
    elif result.status == "skipped":
        print(f"[SKIP] {Path(result.input).name}: {result.message}", flush=True)
    else:
        print(f"[FEHLER] {result.input}: {result.message}", file=sys.stderr, flush=True)


def images(folder: Path, recursive: bool):
    it = folder.rglob("*") if recursive else folder.glob("*")
    for path in sorted(it):
        if can_open(path):
            yield path


def batch(root: Path, out: Path, session, args) -> list[Result]:
    files = list(images(root, args.recursive))
    print(f"Gefundene Bilder: {len(files)}")
    results = []
    for i, source in enumerate(files, 1):
        print(f"[{i}/{len(files)}] ", end="")
        result = process(source, target_path(source, out, root, args.suffix), session, args)
        results.append(result)
        show(result)
    return results


def stable(path: Path, seconds: float, timeout: float = 60.0) -> bool:
    deadline = time.monotonic() + timeout
    last = None
    since = None
    while time.monotonic() < deadline:
        try:
            st = path.stat()
            sig = (st.st_size, st.st_mtime_ns)
        except OSError:
            time.sleep(0.2)
            continue
        if st.st_size > 0 and sig == last:
            since = since or time.monotonic()
            if time.monotonic() - since >= seconds:
                return True
        else:
            since = None
            last = sig
        time.sleep(min(0.25, seconds / 2))
    return False


class DedupQueue:
    def __init__(self):
        self.q = queue.Queue()
        self.pending = set()
        self.lock = threading.Lock()

    def put(self, path: Path):
        path = path.resolve()
        with self.lock:
            if path in self.pending:
                return
            self.pending.add(path)
            self.q.put(path)

    def done(self, path: Path):
        with self.lock:
            self.pending.discard(path.resolve())
        self.q.task_done()


class Handler(FileSystemEventHandler):
    def __init__(self, q: DedupQueue):
        super().__init__()
        self.q = q

    def on_created(self, event):
        if not event.is_directory:
            self.q.put(Path(event.src_path))

    def on_moved(self, event):
        if not event.is_directory:
            self.q.put(Path(event.dest_path))

    def on_modified(self, event):
        if not event.is_directory:
            self.q.put(Path(event.src_path))


def watch(root: Path, out: Path, session, args) -> int:
    root.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    batch(root, out, session, args)
    q = DedupQueue()
    observer = Observer()
    observer.schedule(Handler(q), str(root), recursive=args.recursive)
    observer.start()
    print("\nWATCH-MODUS AKTIV")
    print(f"Bilder hinein: {root}")
    print(f"PNG-Ausgabe:    {out}")
    print("Beenden mit Strg+C.\n")
    try:
        while True:
            try:
                path = q.q.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                if not stable(path, args.stable_seconds):
                    print(f"[SKIP] Datei nicht stabil: {path.name}")
                    continue
                if not can_open(path):
                    print(f"[SKIP] Kein lesbares Bild: {path.name}")
                    continue
                rel = path.relative_to(root)
                target = out / rel.parent / f"{path.stem}{args.suffix}.png"
                show(process(path, target, session, args))
            finally:
                q.done(path)
    except KeyboardInterrupt:
        print("\nWatch-Modus beendet.")
    finally:
        observer.stop()
        observer.join(timeout=5)
    return 0


def main() -> int:
    args = parser().parse_args()
    if not 0 <= args.alpha_threshold <= 255 or args.padding < 0 or args.canvas < 0 or not 0 <= args.margin < 0.5:
        print("Ungültige Parameter.", file=sys.stderr)
        return 2
    source = Path(args.input).expanduser().resolve()
    out = Path(args.output).expanduser().resolve()
    if args.watch:
        source.mkdir(parents=True, exist_ok=True)
    if not source.exists():
        print(f"Eingabe existiert nicht: {source}", file=sys.stderr)
        return 2
    print(f"Modell: {args.model}")
    print("Lade Segmentierungsmodell; beim ersten Start kann ein Download erfolgen …")
    try:
        session = new_session(args.model)
    except Exception as exc:
        print(f"Modell konnte nicht geladen werden: {exc}", file=sys.stderr)
        return 3
    if args.watch:
        if not source.is_dir():
            print("--watch benötigt einen Ordner.", file=sys.stderr)
            return 2
        return watch(source, out, session, args)
    if source.is_file():
        if not can_open(source):
            print("Datei ist kein lesbares Rasterbild.", file=sys.stderr)
            return 2
        results = [process(source, target_path(source, out, None, args.suffix), session, args)]
        show(results[0])
    else:
        results = batch(source, out, session, args)
    errors = sum(r.status == "error" for r in results)
    if args.json:
        print(json.dumps({"model": args.model, "errors": errors, "results": [asdict(r) for r in results]}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
