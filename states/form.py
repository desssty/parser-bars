from aiogram.fsm.state import StatesGroup, State


class VacancyForm(StatesGroup):
    vacancy = State()
    city = State()


class TrackForm(StatesGroup):
    waiting_for_vacancy = State()
    waiting_for_city = State()
    waiting_for_delete_id = State()
