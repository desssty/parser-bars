import asyncio
import json
import aiohttp
from aiogram import Router, Bot, F
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from states.form import VacancyForm, TrackForm
from utils.typing import send_typing
from services.hh_service import run_hh_parser
from scrapers.habr_scraper import parse_habr_resumes
from config import TRACK_FILE, RESUME_FILE, EXTERNAL_URL

router = Router()


# --- Функции для работы с JSON ---
def load_tracks():
    if not TRACK_FILE.exists():
        return []
    try:
        with TRACK_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_tracks(data):
    with TRACK_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# --- Клавиатуры ---
def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Начать новый поиск")],
            [KeyboardButton(text="📡 Отслеживать")],
        ],
        resize_keyboard=True,
    )


def get_tracking_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить"), KeyboardButton(text="📋 Список")],
            [KeyboardButton(text="🗑️ Удалить"), KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True,
    )


# --- Вспомогательные функции меню ---
async def show_main_menu(message: Message, bot: Bot):
    await bot.send_message(
        message.chat.id, "Выберите действие:", reply_markup=get_main_keyboard()
    )


async def show_tracking_menu(message: Message, bot: Bot):
    await bot.send_message(
        message.chat.id, "Меню отслеживания:", reply_markup=get_tracking_keyboard()
    )


async def send_data_to_url(data):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(EXTERNAL_URL, json=data) as response:
                print(f"--- Ответ сервера ({response.status}) ---")
                print(await response.text())
    except Exception as e:
        print(f"Ошибка отправки: {e}")


# --- Хендлеры ---
@router.message(CommandStart())
async def start(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    await message.answer(
        "Добро пожаловать в бот поиска резюме!", reply_markup=get_main_keyboard()
    )


@router.message(F.text == "📡 Отслеживать")
async def open_tracking(message: Message, bot: Bot):
    await show_tracking_menu(message, bot)


@router.message(F.text == "⬅️ Назад")
async def back_to_main(message: Message, bot: Bot):
    await show_main_menu(message, bot)


@router.message(F.text == "📋 Список")
async def list_tracks_handler(message: Message, bot: Bot):
    tracks = load_tracks()
    if not tracks:
        await message.answer("Список пуст.")
    else:
        resp = "\n".join(
            [f"🆔 {t['id']} | {t['vacancy']} ({t['city']})" for t in tracks]
        )
        await message.answer(
            f"📌 **Список отслеживания:**\n\n{resp}", parse_mode="Markdown"
        )
    await show_tracking_menu(message, bot)


@router.message(F.text == "➕ Добавить")
async def add_track_start(message: Message, state: FSMContext):
    await message.answer(
        "Вакансия для отслеживания:", reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(TrackForm.waiting_for_vacancy)


@router.message(TrackForm.waiting_for_vacancy)
async def add_track_vac(message: Message, state: FSMContext):
    await state.update_data(track_vacancy=message.text)
    await message.answer("Город:")
    await state.set_state(TrackForm.waiting_for_city)


@router.message(TrackForm.waiting_for_city)
async def add_track_city(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    tracks = load_tracks()
    new_id = 1 if not tracks else tracks[-1]["id"] + 1
    tracks.append(
        {"id": new_id, "vacancy": data["track_vacancy"], "city": message.text}
    )
    save_tracks(tracks)
    await message.answer(f"✅ Запись добавлена (ID: {new_id})")
    await state.clear()
    await show_tracking_menu(message, bot)


@router.message(F.text == "🗑️ Удалить")
async def delete_track_start(message: Message, state: FSMContext):
    await message.answer("Введите ID для удаления:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(TrackForm.waiting_for_delete_id)


@router.message(TrackForm.waiting_for_delete_id)
async def delete_track_process(message: Message, state: FSMContext, bot: Bot):
    if message.text.isdigit():
        tracks = load_tracks()
        filtered = [t for t in tracks if t["id"] != int(message.text)]
        save_tracks(filtered)
        await message.answer("Удалено.")
    else:
        await message.answer("Ошибка: введите число.")
    await state.clear()
    await show_tracking_menu(message, bot)


@router.message(F.text == "🔍 Начать новый поиск")
async def start_search_flow(message: Message, state: FSMContext):
    await message.answer(
        "Напишите название вакансии:", reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(VacancyForm.vacancy)


@router.message(VacancyForm.vacancy)
async def get_vacancy(message: Message, state: FSMContext):
    await state.update_data(vacancy=message.text)
    await message.answer("В каком городе искать?")
    await state.set_state(VacancyForm.city)


@router.message(VacancyForm.city)
async def get_city(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    vacancy, city = data["vacancy"], message.text
    progress_msg = await message.answer(
        f"🔎 Поиск «{vacancy}» в «{city}»...\n⏳ Прогресс: 0%"
    )

    async def progress_callback(percent):
        if percent % 10 == 0:
            try:
                await bot.edit_message_text(
                    chat_id=progress_msg.chat.id,
                    message_id=progress_msg.message_id,
                    text=f"🔎 Поиск «{vacancy}» в «{city}»...\n⏳ Прогресс: {percent}%",
                )
            except TelegramBadRequest:
                pass
            except Exception:
                pass

    async def background_search():
        try:
            # 1. Запуск основного парсера (HH)
            count, results = await run_hh_parser(
                vacancy, city, progress_callback=progress_callback
            )

            # 2. Условие: если результатов меньше 47, добираем из Хабра
            if count < 47:
                # Можно добавить принт для логов (пользователь не увидит)
                print(f"Мало данных ({count}), запускаем парсинг Habr...")

                # Запускаем ваш парсер Habr Career
                # Передаем vacancy как query. max_pages можно настроить
                habr_results = await parse_habr_resumes(query=vacancy, max_pages=3)

                if habr_results:
                    # Объединяем списки
                    results.extend(habr_results)
                    # Обновляем общее количество для отчета
                    count = len(results)

            # 3. Сохранение ОБЪЕДИНЕННОГО списка в один JSON
            with open(RESUME_FILE, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=4)

            print(f"\n--- ПАРСИНГ ЗАВЕРШЕН: {vacancy} ---")

            # Отправка полных данных на внешний URL
            await send_data_to_url(
                {"vacancy": vacancy, "city": city, "count": count, "results": results}
            )

            # Сообщение пользователю (просто общее число)
            await bot.edit_message_text(
                chat_id=progress_msg.chat.id,
                message_id=progress_msg.message_id,
                text=f"✅ Поиск «{vacancy}» завершен!\nНайдено резюме: {count}\nДанные отправлены.",
            )

        except Exception as e:
            print(f"Ошибка в фоновом поиске: {e}")
            await bot.send_message(message.chat.id, "⚠️ Ошибка во время поиска.")
        finally:
            await state.clear()
            await show_main_menu(message, bot)

    asyncio.create_task(background_search())
