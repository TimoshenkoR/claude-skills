# YouTube Shorts Uploader

**Паблишер шортсов на YouTube с обязательным согласованием** — находит вертикальные/короткие
видео на компьютере пользователя и загружает выбранное на его YouTube-канал через YouTube Data
API v3 (OAuth от имени пользователя).

## Что делает

Три шага: **найти** видеофайлы-кандидаты в шортсы на диске (по расширению, вертикальной/квадратной
ориентации и длительности ≤ 3 минут — лимит YouTube Shorts), **показать**, какой канал сейчас
авторизован, и **загрузить** выбранное видео с заголовком/описанием/тегами/приватностью, которые
явно согласовал пользователь.

## Главное правило

Ни одно видео не публикуется без явного согласия пользователя в текущем диалоге: перед загрузкой
скилл показывает карточку (канал + файл + все метаданные 1:1) и ждёт «да». Секреты
(`client_secret.json`, `token.json`) **не входят в репозиторий** — настраиваются локально по
`references/setup.md`.

## Установка

```bash
cp -r youtube-shorts-uploader/ ~/.claude/skills/youtube-shorts-uploader/
cd ~/.claude/skills/youtube-shorts-uploader/
pip3 install -r scripts/requirements.txt
brew install ffmpeg   # если ещё не стоит — нужен ffprobe для чтения параметров видео
python3 scripts/yt_auth.py
```

Подробный разбор получения `client_secret.json` (Google Cloud Console, OAuth consent screen,
OAuth client ID) — `references/setup.md`.

## Как использовать

Скажите Claude Code что-то вроде:

- «Найди на компе шортсы и покажи, что есть»
- «Залей вот этот ролик на YouTube как unlisted»
- «Загрузи видео из Downloads на мой канал, заголовок такой-то»
- «Какой канал у меня сейчас авторизован для загрузки?»

Скилл сам проведёт через поиск файла, сбор метаданных, карточку согласования и подтвердит ссылку
после загрузки.

## Структура

```
youtube-shorts-uploader/
├── SKILL.md                  # Протокол согласования и обзор скриптов
├── README.md                 # Этот файл
├── .gitignore                # client_secret.json / token.json никогда не коммитятся
├── references/
│   └── setup.md              # Google Cloud Console, OAuth, восстановление доступа, квоты
└── scripts/
    ├── requirements.txt
    ├── _yt_common.py         # OAuth-клиент, ffprobe-хелпер, форматирование
    ├── yt_auth.py            # разовая OAuth-авторизация в браузере
    ├── yt_channel.py         # read-only: какой канал авторизован
    ├── yt_find_shorts.py     # read-only: поиск видео-шортсов на диске
    └── yt_upload.py          # загрузка; без --yes — сухой прогон, с --yes — реальная публикация
```
