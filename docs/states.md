# Документация по states/form.py

Файл `form.py` содержит состояния для работы с формами ввода пользователя в Telegram-боте с использованием FSM (Finite State Machine) из aiogram.

---

## Классы

### VacancyForm

Используется для сбора информации о вакансии от пользователя.  
Содержит два состояния:

- `vacancy` — состояние, в котором бот ожидает ввод названия вакансии.
- `city` — состояние, в котором бот ожидает ввод города для поиска вакансии.

---

### TrackForm

Используется для управления трекингом вакансий. Содержит три состояния:

- `waiting_for_vacancy` — бот ожидает ввод вакансии для отслеживания.
- `waiting_for_city` — бот ожидает ввод города для отслеживания вакансии.
- `waiting_for_delete_id` — бот ожидает ввод ID вакансии для удаления из трекинга.

---

## Пример использования

```python
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from states.form import VacancyForm

router = Router()

@router.message()
async def start_vacancy_form(message: Message, state: FSMContext):
    await state.set_state(VacancyForm.vacancy)
    await message.answer("Введите название вакансии:")

@router.message(VacancyForm.vacancy)
async def get_vacancy(message: Message, state: FSMContext):
    vacancy_name = message.text
    await state.update_data(vacancy=vacancy_name)
    await state.set_state(VacancyForm.city)
    await message.answer("Введите город для поиска вакансии:")
```

---
