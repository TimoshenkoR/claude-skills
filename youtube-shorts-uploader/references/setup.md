# Окружение и доступ youtube-shorts-uploader

Скилл работает через **YouTube Data API v3** (OAuth 2.0, доступ от имени пользователя к его
собственному каналу). Ничего не настраивается автоматически — ключи и токен нужно завести один раз.

## Что где лежит

| Что | Где | Примечание |
|-----|-----|-----------|
| OAuth client (`client_secret.json`) | `~/.yt/client_secret.json` | Создаётся в Google Cloud Console, см. ниже. Не коммитить в репозиторий. |
| Токен доступа (`token.json`) | `~/.yt/token.json` | **Главный секрет** — даёт доступ к каналу. Создаётся `yt_auth.py`. Не копировать, не пересылать, не показывать в чате. |
| Зависимости | `google-api-python-client`, `google-auth-oauthlib`, `google-auth-httplib2` | `pip3 install -r scripts/requirements.txt` |
| Чтение метаданных видео | `ffmpeg`/`ffprobe` | `brew install ffmpeg`, если нет |

`~/.yt/` не входит в репозиторий (секреты аккаунта). Каталог создаётся скриптами автоматически.

## Шаг 1. Создать проект и включить YouTube Data API v3

1. [console.cloud.google.com](https://console.cloud.google.com/) → создать новый проект (или
   выбрать существующий).
2. **APIs & Services → Library** → найти **YouTube Data API v3** → **Enable**.

## Шаг 2. Настроить OAuth consent screen

1. **APIs & Services → OAuth consent screen**.
2. User type: **External** (если это не Google Workspace-аккаунт с собственным доменом).
3. Заполнить название приложения (любое, например «YouTube Shorts Uploader»), контактный email.
4. **Scopes**: не обязательно добавлять здесь — скрипт запросит `youtube.upload` и
   `youtube.readonly` при первой авторизации.
5. **Test users**: добавить email аккаунта, с канала которого будет загрузка (пока приложение не
   прошло верификацию Google, работать может только с аккаунтами из этого списка — для личного
   использования этого достаточно, верификация не нужна).

## Шаг 3. Создать OAuth client ID

1. **APIs & Services → Credentials → Create Credentials → OAuth client ID**.
2. Application type: **Desktop app**.
3. Скачать JSON (кнопка «Download JSON») и положить его как:
   ```
   ~/.yt/client_secret.json
   ```
   (или указать свой путь через переменную `YT_CLIENT_SECRET`).

## Шаг 4. Авторизоваться

```bash
pip3 install -r ~/.claude/skills/youtube-shorts-uploader/scripts/requirements.txt
python3 ~/.claude/skills/youtube-shorts-uploader/scripts/yt_auth.py
```

Откроется браузер → логин Google-аккаунтом, владеющим нужным каналом → подтвердить доступ
(«Посмотреть и/или отправить ролики на YouTube» и «Просматривать аккаунт YouTube»). Скрипт сохранит
`~/.yt/token.json` и напечатает название авторизованного канала — проверь, что это тот канал,
который нужен.

## Переопределение через окружение (опционально)

- `YT_CLIENT_SECRET` — путь к `client_secret.json` (иначе `~/.yt/client_secret.json`);
- `YT_TOKEN` — путь к `token.json` (иначе `~/.yt/token.json`).

Полезно, если у пользователя несколько Google-аккаунтов/каналов — можно держать отдельные токены
и явно указывать, с каким работать.

## Проверка доступа

```bash
python3 ~/.claude/skills/youtube-shorts-uploader/scripts/yt_channel.py
```
Если печатает название канала и статистику — доступ жив.

## Если доступ отвалился

- **«Нет токена авторизации»** → `token.json` не создан или удалён, повтори `yt_auth.py`.
- **`invalid_grant` / просит заново войти** → access/refresh token отозван (например, пользователь
  убрал доступ в [myaccount.google.com/permissions](https://myaccount.google.com/permissions)) —
  удали `~/.yt/token.json` и пройди `yt_auth.py` снова.
- **Канал не тот** → проверь, под каким Google-аккаунтом логинился в браузере при `yt_auth.py`; у
  одного Google-аккаунта может быть несколько каналов/брендов — `yt_channel.py` показывает, какой
  именно сейчас активен для API (обычно основной канал аккаунта; переключение на дополнительный
  бренд-канал через OAuth API не всегда поддерживается Google — в таком случае нужно логиниться
  аккаунтом, на котором этот канал основной).
- **`quotaExceeded` / `uploadLimitExceeded`** → дневная квота YouTube Data API (по умолчанию 10 000
  «единиц» в день, загрузка видео стоит 1600 единиц — то есть ограничено число загрузок в день).
  Нужно подождать сброса квоты (полночь по Pacific Time) или запросить увеличение квоты в Google
  Cloud Console.
- **Приложение не верифицировано Google / «This app isn't verified»** → нормально для личного
  использования: нажать «Advanced» → «Go to <app name> (unsafe)». Это предупреждение относится к
  публичным сторонним приложениям, здесь это свой собственный OAuth client.
