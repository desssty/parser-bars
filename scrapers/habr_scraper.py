import asyncio
import json
from playwright.async_api import async_playwright
from typing import Dict, List, Optional, Any


async def parse_header_data(card):
    """Парсим основную информацию из карточки"""
    result = {
        "full_name": None,
        "age": None,
        "directions": [],
        "salary": None,
        "skills": [],
        "city": None,
        "work_experience": [],
        "profile_url": None,
    }

    try:
        # 1. Парсинг основной информации из header(full_name,salary,directions,profile_url)
        result = await parse_basic_info(card, result)

        # 2. Парсинг остальной информации(age,skills,city,work_experience)
        result = await parse_all_sections(card, result)

    except Exception as e:
        print(f"Ошибка при парсинге карточки: {e}")

    return result


async def parse_basic_info(card, result):
    """Парсим базовую информацию из заголовка карточки"""
    try:
        # 1. Поиск имени и фамилии
        name_elem = await card.query_selector("h2 > a")
        if name_elem:
            full_name = await name_elem.text_content()
            if full_name and full_name.strip():
                result["full_name"] = full_name.strip()

        # 2. Поиск ссылки на профиль
        profile_url = await name_elem.get_attribute("href")
        if profile_url:
            if profile_url.startswith("/"):
                profile_url = f"https://career.habr.com{profile_url}"
            result["profile_url"] = profile_url

        # 3. Поиск остальных элементов span
        nested_spans = await card.query_selector_all("header span span span")

        for span in nested_spans:
            text = await span.text_content()
            if not text or not text.strip():
                continue

            text_clean = text.strip()

            # Пропуск разделителей
            parent_span = await span.query_selector("xpath=..")
            if parent_span:
                parent_class = await parent_span.get_attribute("class")
                if parent_class and "inline-separator" in parent_class:
                    continue

            # Игнорирование фраз
            ignore_phrases = ["Ищу работу", "Рассматриваю предложения"]
            if any(phrase in text_clean for phrase in ignore_phrases):
                continue

            # Отделение зарплаты
            if text_clean.startswith("От"):
                result["salary"] = text_clean
                continue

            # Остальное добавляем в directions
            result["directions"].append(text_clean)

    except Exception as e:
        print(f"Ошибка при парсинге базовой информации: {e}")

    return result


async def parse_all_sections(card, result):
    """Парсит все секции карточки"""
    try:
        sections = await card.query_selector_all("section")

        for section in sections:

            # Поиск заголовка блока section
            h3_elem = await section.query_selector("h3")
            if not h3_elem:
                continue

            h3_text = await h3_elem.text_content()
            if not h3_text:
                continue

            h3_text_clean = h3_text.strip()

            # Определение типа заголовка и обращение к нужному методу
            if "Профессиональные навыки" in h3_text_clean:
                result["skills"] = await parse_skills_section(section)

            elif "Возраст" in h3_text_clean:
                result["age"] = await parse_age_section(section)

            elif "Город" in h3_text_clean:
                result["city"] = await parse_city_section(section)

            elif "Опыт работы" in h3_text_clean:
                result["work_experience"] = await parse_experience_section(section)

    except Exception as e:
        print(f"Ошибка при парсинге секций: {e}")

    return result


# Парсинг конкретных секций
async def parse_skills_section(section):
    """Парсит секцию с профессиональными навыками"""
    skills = []
    try:
        skill_spans = await section.query_selector_all("span")

        for span in skill_spans:
            skill_text = await span.text_content()
            if skill_text and skill_text.strip():
                skill_clean = skill_text.strip()
                if len(skill_clean) < 100 and skill_clean not in skills:
                    skills.append(skill_clean)
    except Exception as e:
        print(f"Ошибка при парсинге навыков: {e}")
    return skills


async def parse_age_section(section):
    """Парсит секцию с возрастом"""
    try:
        age_span = await section.query_selector("span")
        if age_span:
            age_text = await age_span.text_content()
            if age_text:
                return age_text.strip()
    except Exception as e:
        print(f"Ошибка при парсинге возраста: {e}")
    return None


async def parse_city_section(section):
    """Парсит секцию с городом"""
    try:
        city_span = await section.query_selector("div span span span span")
        if city_span:
            city_text = await city_span.text_content()
            if city_text:
                return city_text.strip()
    except Exception as e:
        print(f"Ошибка при парсинге города: {e}")
    return None


async def parse_experience_section(section):
    """Парсит секцию с опытом работы"""
    experience_items = []
    try:
        experience_span = await section.query_selector_all("span")
        for span in experience_span:

            # Пропускаем разделители
            span_class = await span.get_attribute("class")
            if span_class and "inline-separator inline-separator" in span_class:
                continue

            text = await span.text_content()
            text_clean = text.strip()

            # Убираем разделители если все-же спарсились
            text_clean = text_clean.replace("•", "").strip()
            if not text_clean or not text_clean.strip():
                continue

            if text_clean not in experience_items:
                experience_items.append(text_clean.strip())

    except Exception as e:
        print(f"Ошибка при парсинге опыта работы: {e}")
    return experience_items


async def parse_habr_resumes(query, max_pages=2):
    """Основной парсер Habr Career"""
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            for page_num in range(1, max_pages + 1):
                url = f"https://career.habr.com/resumes?q={query}&page={page_num}"
                print(f"📄 Загружаю страницу {page_num}: {query}")

                await page.goto(url)
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(2)

                # Поиск карточек резюме
                cards = await page.query_selector_all(".base-section")
                print(f"   Найдено .base-section элементов: {len(cards)}")

                # Пропуска первого .base-section с ненужной информацией
                start_index = 1 if len(cards) > 1 else 0

                for i, card in enumerate(cards[start_index:], start=1):
                    # Парсинг данных карточки
                    card_data = await parse_header_data(card)

                    # Сбор данных в структурированном виде
                    resume_data = {
                        "query": query,
                        "source_page": page_num,
                        "card_index": i,
                        "full_name": card_data["full_name"],
                        "directions": card_data["directions"],
                        "salary": card_data["salary"],
                        "skills": card_data["skills"],
                        "age": card_data["age"],
                        "city": card_data["city"],
                        "work_experience": card_data["work_experience"],
                        "profile_url": card_data["profile_url"],
                    }

                    results.append(resume_data)

                    # Вывод информации
                    if card_data["full_name"]:
                        directions_str = ", ".join(card_data["directions"])
                        salary_str = card_data["salary"] or "Зарплата не указана"
                        skills_str = ", ".join(card_data["skills"])
                        age_str = card_data["age"] or "Возраст не указан"
                        exp_items = (
                            ", ".join(card_data["work_experience"]) or "Опыт не указан"
                        )
                        city_str = card_data["city"] or "Город не указан"
                        profile_url = card_data["profile_url"]

                        print(f"   {i}. {card_data['full_name']}")
                        print(f"      Направления: {directions_str}")
                        print(f"      Зарплата: {salary_str}")
                        print(f"      Навыки: {skills_str}")
                        print(f"      Возраст: {age_str}")
                        print(f"      Опыт работы: {exp_items}")
                        print(f"      Город: {city_str}")
                        print(f"      Профиль: {profile_url}\n")

                    else:
                        print(f"   ⚠️  {i}. Имя не найдено")

                print(
                    f"   📊 Обработано на странице: {len(cards) - start_index} резюме"
                )

                # Проверка следующей страницы
                next_button = await page.query_selector("a.next_page")
                if not next_button:
                    break

                await asyncio.sleep(1)

        except Exception as e:
            print(f" Ошибка: {e}")

        finally:
            await browser.close()

    return results


def save_results(results, filename="resumes.json"):
    """Сохраняем результаты в JSON файл"""
    if not results:
        print(" Нет данных для сохранения")
        return None

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Сохранено {len(results)} резюме в {filename}")
    return filename


async def main():

    # ============================================
    # Настройки парсинга
    # ============================================

    # 1. Фильтр
    QUERY = "python"

    # 2. Количество страниц
    PAGES = 2

    # 3. Файл для сохранения
    OUTPUT_FILE = "resumes_data.json"

    # ============================================
    # Запуск парсера
    # ============================================

    print("=" * 50)
    print("ПАРСЕР HABR CAREER")
    print("=" * 50)

    print(f"\n🔍 Ищем: '{QUERY}'")
    print(f"📖 Парсим {PAGES} страниц")

    results = await parse_habr_resumes(QUERY, PAGES)

    if results:
        save_results(results, OUTPUT_FILE)

        # Простая статистика
        print(f"\n📊 СТАТИСТИКА:")
        print(f"   Всего собрано: {len(results)} резюме")

    else:
        print("\n⚠️ Ничего не найдено")


# Запуск программы
if __name__ == "__main__":
    asyncio.run(main())
