#!/usr/bin/env python3
"""
Разовая интерактивная авторизация Google-аккаунта для загрузки на YouTube.

Открывает браузер, пользователь логинится и подтверждает доступ (scope
youtube.upload + youtube.readonly) к СВОЕМУ аккаунту/каналу. Результат —
token.json в ~/.yt/, который дальше переиспользуют yt_upload.py и yt_channel.py.

Предварительно нужен client_secret.json (OAuth client ID типа "Desktop app"
из Google Cloud Console) — см. references/setup.md. Сам этот скрипт ничего
не грузит на YouTube, только авторизуется.

Usage:
    python3 yt_auth.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _yt_common import SCOPES, DEFAULT_DIR, client_secret_path, token_path  # noqa: E402


def main():
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        sys.exit(
            "[yt_auth] Не установлены зависимости. Поставь:\n"
            "    pip3 install -r " + os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
        )

    cs = client_secret_path()
    if not os.path.exists(cs):
        sys.exit(
            f"[yt_auth] Не найден {cs}.\n"
            "Скачай OAuth client (тип Desktop app) из Google Cloud Console и положи его туда "
            "(или укажи путь в YT_CLIENT_SECRET). Подробности — references/setup.md."
        )

    os.makedirs(DEFAULT_DIR, exist_ok=True)

    flow = InstalledAppFlow.from_client_secrets_file(cs, SCOPES)
    creds = flow.run_local_server(port=0)

    tp = token_path()
    with open(tp, "w") as f:
        f.write(creds.to_json())
    os.chmod(tp, 0o600)

    print(f"[yt_auth] Готово. Токен сохранён: {tp}")
    print("[yt_auth] Проверка канала...")

    from googleapiclient.discovery import build
    yt = build("youtube", "v3", credentials=creds)
    resp = yt.channels().list(part="snippet", mine=True).execute()
    items = resp.get("items", [])
    if not items:
        print("[yt_auth] ⚠️ Авторизация прошла, но у аккаунта не нашлось канала YouTube.")
        return
    ch = items[0]["snippet"]
    print(f"[yt_auth] Авторизован канал: «{ch['title']}» (channelId: {items[0]['id']})")


if __name__ == "__main__":
    main()
