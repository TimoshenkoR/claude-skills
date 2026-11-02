#!/usr/bin/env python3
"""
Загрузка видео на YouTube. ⚠️ ЕДИНСТВЕННЫЙ скрипт скилла, который публикует контент.

ПРЕДОХРАНИТЕЛЬ: без флага --yes скрипт работает в режиме СУХОГО ПРОГОНА — проверяет
файл, резолвит канал и печатает карточку (что именно и куда будет загружено), но
НИЧЕГО НЕ ЗАГРУЖАЕТ. Реальная загрузка — только с --yes, и только после того, как
пользователь явно согласовал карточку в этом диалоге.

Usage:
    # сухой прогон (безопасно, ничего не загружается):
    python3 yt_upload.py --file video.mp4 --title "Заголовок" --privacy unlisted \
        --not-made-for-kids [--description "..."] [--tags "a,b,c"] [--playlist-id PL...]

    # реальная загрузка (после согласования, тот же вызов + --yes):
    python3 yt_upload.py --file video.mp4 --title "Заголовок" --privacy unlisted \
        --not-made-for-kids --yes
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _yt_common import get_service, human_size, human_duration, probe_video  # noqa: E402

PRIVACY_CHOICES = ("public", "unlisted", "private")


def build_card(args, info, size, channel_title, channel_id):
    lines = []
    lines.append("📤 Готов загрузить на YouTube:")
    lines.append(f"Канал:       «{channel_title}» (channelId: {channel_id})")
    lines.append(f"Файл:        {args.file}")
    if info and info.get("width") and info.get("height"):
        lines.append(f"Разрешение:  {info['width']}x{info['height']}")
    if info and info.get("duration"):
        lines.append(f"Длительность: {human_duration(info['duration'])}")
    lines.append(f"Размер:      {human_size(size)}")
    lines.append(f"Заголовок:   {args.title}")
    lines.append(f"Описание:    {args.description or '(пусто)'}")
    if args.tags:
        lines.append(f"Теги:        {args.tags}")
    lines.append(f"Приватность: {args.privacy}")
    lines.append(f"Для детей:   {'да' if args.made_for_kids else 'нет'}")
    if args.playlist_id:
        lines.append(f"Плейлист:    {args.playlist_id}")
    if args.publish_at:
        lines.append(f"Публикация запланирована на: {args.publish_at}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Загрузка видео на YouTube (по умолчанию — сухой прогон)")
    ap.add_argument("--file", required=True, help="путь к видеофайлу")
    ap.add_argument("--title", required=True, help="заголовок видео (до 100 символов)")
    ap.add_argument("--description", default="", help="описание видео")
    ap.add_argument("--tags", default="", help="теги через запятую")
    ap.add_argument("--privacy", required=True, choices=PRIVACY_CHOICES,
                     help="приватность: public / unlisted / private")
    ap.add_argument("--category", default="22", help="videoCategoryId (по умолчанию 22 — People & Blogs)")
    ap.add_argument("--playlist-id", default=None, help="добавить видео в плейлист после загрузки")
    ap.add_argument("--publish-at", default=None,
                     help="RFC3339 timestamp для отложенной публикации (требует --privacy private)")
    kids = ap.add_mutually_exclusive_group(required=True)
    kids.add_argument("--made-for-kids", dest="made_for_kids", action="store_true",
                       help="пометить видео как контент для детей (юридически обязательное поле YouTube)")
    kids.add_argument("--not-made-for-kids", dest="made_for_kids", action="store_false",
                       help="пометить видео как НЕ для детей")
    ap.add_argument("--yes", action="store_true", help="РЕАЛЬНО загрузить. Без него — только сухой прогон.")
    args = ap.parse_args()

    if not os.path.isfile(args.file):
        sys.exit(f"[yt_upload] Файл не найден: {args.file}")
    if args.publish_at and args.privacy != "private":
        sys.exit("[yt_upload] --publish-at требует --privacy private (YouTube планирует публикацию только из private).")

    size = os.path.getsize(args.file)
    info = probe_video(args.file)

    yt = get_service()
    ch_resp = yt.channels().list(part="snippet", mine=True).execute()
    ch_items = ch_resp.get("items", [])
    if not ch_items:
        sys.exit("[yt_upload] У авторизованного аккаунта нет канала YouTube.")
    channel_title = ch_items[0]["snippet"]["title"]
    channel_id = ch_items[0]["id"]

    if not args.yes:
        print(build_card(args, info, size, channel_title, channel_id))
        print()
        print("⚠️ Сухой прогон — видео НЕ загружено. После явного «да» от пользователя — повтори с --yes.")
        return

    from googleapiclient.http import MediaFileUpload

    body = {
        "snippet": {
            "title": args.title,
            "description": args.description,
            "tags": [t.strip() for t in args.tags.split(",") if t.strip()],
            "categoryId": args.category,
        },
        "status": {
            "privacyStatus": args.privacy,
            "selfDeclaredMadeForKids": args.made_for_kids,
        },
    }
    if args.publish_at:
        body["status"]["publishAt"] = args.publish_at

    media = MediaFileUpload(args.file, chunksize=-1, resumable=True)
    request = yt.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"[yt_upload] загружено {int(status.progress() * 100)}%", file=sys.stderr)

    video_id = response["id"]
    url = f"https://youtu.be/{video_id}"
    print(f"[yt_upload] ЗАГРУЖЕНО: {url} (videoId: {video_id}, канал: «{channel_title}»)")

    if args.playlist_id:
        yt.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": args.playlist_id,
                    "resourceId": {"kind": "youtube#video", "videoId": video_id},
                }
            },
        ).execute()
        print(f"[yt_upload] добавлено в плейлист {args.playlist_id}")


if __name__ == "__main__":
    main()
