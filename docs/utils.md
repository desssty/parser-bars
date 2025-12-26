# Документация по utils/typing.py

## Описание

Файл `typing.py` содержит утилиту для имитации «печатающегося» состояния бота в Telegram.  
Позволяет создавать эффект, что бот думает или формирует ответ перед отправкой сообщения пользователю.

---

## Функции

### async send_typing(bot: Bot, chat_id: int, seconds: int = 3)

**Назначение:**  
Отправляет действие `ChatAction.TYPING` в чат, создавая визуальный эффект «бот печатает сообщение».

**Параметры:**

- `bot: Bot` — экземпляр Telegram-бота (aiogram.Bot)
- `chat_id: int` — идентификатор чата, в который нужно отправлять действие
- `seconds: int` — продолжительность эффекта в секундах (по умолчанию 3)

**Логика работы:**

1. Создаётся таймер `end_time` на указанное количество секунд.
2. Пока `end_time > 0`:
   - Отправляется `ChatAction.TYPING` в чат
   - Асинхронно ждём 1.5 секунды
   - Уменьшаем `end_time` на 1.5 секунды
3. После завершения цикла действие прекращается автоматически.

**Пример использования:**

```python
from aiogram import Bot
import asyncio
from utils.typing import send_typing

bot = Bot(token="YOUR_BOT_TOKEN")
chat_id = 123456789

async def main():
    await send_typing(bot, chat_id, seconds=4)
    await bot.send_message(chat_id, "Привет! Я здесь!")

asyncio.run(main())
```

---
