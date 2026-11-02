"""
Общий код для скриптов youtube-shorts-uploader: доступ к OAuth-токену и клиенту YouTube Data API v3.

Секреты (client_secret.json, token.json) НИКОГДА не лежат в репозитории — только в ~/.yt/.
Переопределяются через переменные окружения:
    YT_CLIENT_SECRET — путь к client_secret.json (иначе ~/.yt/client_secret.json)
    YT_TOKEN         — путь к token.json           (иначе ~/.yt/token.json)
"""
import os
import sys

SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.readonly"]

DEFAULT_DIR = os.path.expanduser("~/.yt")


def client_secret_path():
    return os.environ.get("YT_CLIENT_SECRET", os.path.join(DEFAULT_DIR, "client_secret.json"))


def token_path():
    return os.environ.get("YT_TOKEN", os.path.join(DEFAULT_DIR, "token.json"))


def load_credentials():
    """Загружает сохранённые OAuth-credentials, тихо обновляет истёкший access token."""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
    except ImportError:
        sys.exit(
            "[yt] Не установлены зависимости. Поставь:\n"
            "    pip3 install -r " + os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
        )

    tp = token_path()
    if not os.path.exists(tp):
        sys.exit(
            f"[yt] Нет токена авторизации ({tp}).\n"
            f"Запусти сначала: python3 {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'yt_auth.py')}"
        )

    creds = Credentials.from_authorized_user_file(tp, SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(tp, "w") as f:
            f.write(creds.to_json())
    return creds


def get_service():
    """Возвращает авторизованный клиент YouTube Data API v3."""
    creds = load_credentials()
    try:
        from googleapiclient.discovery import build
    except ImportError:
        sys.exit(
            "[yt] Не установлены зависимости. Поставь:\n"
            "    pip3 install -r " + os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
        )
    return build("youtube", "v3", credentials=creds)


def human_size(num_bytes):
    for unit in ("B", "KB", "MB", "GB"):
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} TB"


def human_duration(seconds):
    seconds = int(round(seconds))
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def probe_video(path):
    """ffprobe: длительность (сек) и разрешение (w, h) с учётом поворота. None, если не видео/нет ffprobe."""
    import json
    import subprocess

    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height,duration:format=duration",
             "-show_entries", "stream_tags=rotate",
             "-of", "json", path],
            capture_output=True, text=True, timeout=30,
        )
        data = json.loads(out.stdout or "{}")
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return None

    streams = data.get("streams", [])
    fmt = data.get("format", {})
    if not streams:
        return None
    s = streams[0]
    w, h = s.get("width"), s.get("height")
    rotate = (s.get("tags") or {}).get("rotate")
    if rotate in ("90", "270") and w and h:
        w, h = h, w
    duration = s.get("duration") or fmt.get("duration")
    try:
        duration = float(duration)
    except (TypeError, ValueError):
        duration = None
    return {"width": w, "height": h, "duration": duration}
