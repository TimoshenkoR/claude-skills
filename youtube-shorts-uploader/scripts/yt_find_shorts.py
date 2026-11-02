#!/usr/bin/env python3
"""
Read-only: ищет в папке видеофайлы, похожие на шортсы (вертикальное/квадратное видео
до 3 минут), и печатает их параметры (длительность, разрешение, размер) в JSON.
Ничего не грузит и не трогает — только сканирует диск и читает метаданные через ffprobe.

Usage:
    python3 yt_find_shorts.py [папка] [--all] [--max-seconds 180]

    [папка]            где искать (по умолчанию ~/Downloads, ~/Movies, ~/Desktop)
    --all              показать все видео в папке, а не только похожие на шортсы
    --max-seconds N    порог длительности для "похож на шортс" (по умолчанию 180 — лимит YouTube Shorts)
"""
import argparse
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _yt_common import human_size, human_duration, probe_video  # noqa: E402

VIDEO_EXT = {".mp4", ".mov", ".m4v", ".webm", ".avi", ".mkv"}


def main():
    ap = argparse.ArgumentParser(description="Поиск видео-шортсов на диске (read-only)")
    ap.add_argument("folders", nargs="*", help="папки для поиска")
    ap.add_argument("--all", action="store_true", help="показать все видео, не только похожие на шортсы")
    ap.add_argument("--max-seconds", type=int, default=180, help="порог длительности шортса (сек)")
    args = ap.parse_args()

    if not shutil.which("ffprobe"):
        sys.exit("[yt_find_shorts] ffprobe не найден. Поставь ffmpeg: brew install ffmpeg")

    folders = args.folders or [
        os.path.expanduser("~/Downloads"),
        os.path.expanduser("~/Movies"),
        os.path.expanduser("~/Desktop"),
    ]

    results = []
    for folder in folders:
        if not os.path.isdir(folder):
            continue
        for name in os.listdir(folder):
            ext = os.path.splitext(name)[1].lower()
            if ext not in VIDEO_EXT:
                continue
            path = os.path.join(folder, name)
            if not os.path.isfile(path):
                continue
            info = probe_video(path)
            if not info:
                continue
            w, h, dur = info["width"], info["height"], info["duration"]
            is_vertical_or_square = bool(w and h and h >= w)
            is_short_enough = bool(dur and dur <= args.max_seconds)
            looks_like_short = is_vertical_or_square and is_short_enough
            if not args.all and not looks_like_short:
                continue
            size = os.path.getsize(path)
            results.append({
                "path": path,
                "resolution": f"{w}x{h}" if w and h else None,
                "duration_seconds": round(dur, 1) if dur else None,
                "duration_human": human_duration(dur) if dur else None,
                "size_human": human_size(size),
                "looks_like_short": looks_like_short,
                "modified": os.path.getmtime(path),
            })

    results.sort(key=lambda r: r["modified"], reverse=True)
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"\nНайдено: {len(results)}", file=sys.stderr)


if __name__ == "__main__":
    main()
