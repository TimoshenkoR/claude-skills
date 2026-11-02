#!/usr/bin/env python3
"""
Read-only: показывает, какой канал YouTube авторизован сейчас (куда уйдёт загрузка).

Используй перед любой загрузкой, если не уверен, какой аккаунт/канал подключён —
особенно если у пользователя несколько каналов на одном Google-аккаунте.

Usage:
    python3 yt_channel.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _yt_common import get_service  # noqa: E402


def main():
    yt = get_service()
    resp = yt.channels().list(part="snippet,statistics", mine=True).execute()
    items = resp.get("items", [])
    if not items:
        sys.exit("[yt_channel] У авторизованного аккаунта нет канала YouTube.")

    for ch in items:
        sn = ch["snippet"]
        st = ch.get("statistics", {})
        print(f"Канал: «{sn['title']}»")
        print(f"  channelId: {ch['id']}")
        print(f"  подписчиков: {st.get('subscriberCount', '?')}  видео: {st.get('videoCount', '?')}")


if __name__ == "__main__":
    main()
