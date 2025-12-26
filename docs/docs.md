# Документация

## Общая информация

Resume Search & Tracking Bot — асинхронный Telegram-бот, предназначенный для автоматизированного сбора и обработки резюме с платформ HeadHunter и Habr Career.  
Бот реализован на базе aiogram, использует Playwright для парсинга и поддерживает расширяемую архитектуру через роутеры и сервисы.

---

## Точка входа — bot.py

Файл: [bot.py](https://github.com/desssty/parser-bars/tree/main/bot.py)
Назначение: инициализация и запуск Telegram-бота.

Основные функции:

- Загрузка переменных окружения из .env
- Настройка логирования
- Инициализация Bot и Dispatcher
- Регистрация роутеров
- Запуск polling-цикла

Логика работы:

1. Загружаются переменные окружения
2. Создаётся экземпляр Bot с токеном
3. Создаётся Dispatcher
4. Подключаются роутеры (handlers)
5. Запускается асинхронный polling

Используемые модули:

- aiogram.Bot
- aiogram.Dispatcher
- asyncio
- logging
- dotenv

---

## Конфигурация — config.py

Файл: [config.py](https://github.com/desssty/parser-bars/tree/main/config.py)  
Назначение: централизованное хранение конфигурации и путей.

Переменные окружения:

- BOT_TOKEN — токен Telegram-бота
- EXTERNAL_URL — внешний API или endpoint для интеграций

Если одна из переменных отсутствует — приложение аварийно завершается с ошибкой.

Файловые константы:

- TRACK_FILE (time.json) — хранение информации об обработанных вакансиях
- RESUME_FILE (resume.json) — сохранение результатов парсинга резюме

---

## Архитектура приложения

Архитектура построена по принципу разделения ответственности:

- handlers/ — взаимодействие с пользователем (Telegram)
- scrapers/ — сбор данных с внешних платформ
- services/ — бизнес-логика и управление процессами
- config.py — конфигурация
- bot.py — запуск приложения

---

## Структура проекта

```bash
parser-bars
│
├── bot.py
├── config.py
├── handlers/
│ └── form.py
├── states/
│ └── form.py
├── utils/
│ └── typing.py
├── scrapers/
│ ├── hh_scraper.py
│ └── habr_scraper.py
├── services/
│ └── hh_service.py
├── docs/
│ ├── docs.md
│ ├── handlers.md
│ ├── scrapers.md
│ ├── typing.md
│ ├── utils.md
│ └── services.md
├── requirements.txt
├── .env
├── resume.json
└── time.json
```

---

## Документация по модулям

Вся расширенная документация разбита по файлам и находится в папке docs/:

- [docs/docs.md](https://github.com/desssty/parser-bars/tree/main/docs/docs.md) — общее описание проекта и архитектуры
- [docs/handlers.md](https://github.com/desssty/parser-bars/tree/main/docs/handlers.md) — описание всех Telegram-обработчиков (логика форм, состояний, команд)
- [docs/scrapers.md](https://github.com/desssty/parser-bars/tree/main/docs/scrapers.md) — описание парсеров HeadHunter и Habr Career (Playwright, сценарии, fallback-логика)
- [docs/services.md](https://github.com/desssty/parser-bars/tree/main/docs/services.md) — бизнес-логика, управление поиском и агрегацией данных
- [docs/typing.md](https://github.com/desssty/parser-bars/tree/main/docs/typing.md) — описание используемых типов данных и моделей
- [docs/utils.md](https://github.com/desssty/parser-bars/tree/main/docs/utils.md) — вспомогательные функции и утилиты проекта

---

## Безопасность

Следующие файлы не должны попадать в репозиторий:

- .env — токены и секреты
- resume.json — персональные данные
- time.json — служебные данные
- **pycache**/, .venv/ — временные файлы

---

## Расширение функциональности

Проект легко расширяется:

- добавлением новых scrapers
- подключением новых источников
- интеграцией внешних API через EXTERNAL_URL
- добавлением новых Telegram-сценариев

---
