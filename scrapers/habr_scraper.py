import asyncio
import random
import re
import json
from pathlib import Path
from playwright.async_api import async_playwright


class HabrCareerParser:
    def __init__(self, specialty: str, city_name: str):
        self.specialty = specialty
        self.city_name = city_name
        self.output_file = Path(f"resumes_{self.specialty}_{self.city_name}_habr.json")
        self.results = []

    async def run(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                )
            )
            page = await context.new_page()

            search_url = f"https://career.habr.com/resumes?q={self.specialty}"
            await page.goto(search_url)
            await asyncio.sleep(2)

            while True:
                next_btn = page.locator('button:has-text("Далее")')
                if await next_btn.count() == 0 or await next_btn.is_disabled():
                    break
                await next_btn.click()
                print("📄 Нажата кнопка 'Далее'")
                await asyncio.sleep(random.uniform(1, 2))

            start_btn = page.locator('button:has-text("Поехали")')
            if await start_btn.count() > 0 and not await start_btn.is_disabled():
                await start_btn.click()
                print("🚀 Нажата кнопка 'Поехали'")
                await asyncio.sleep(3)
            cards = page.locator('div[data-qa="resume-card"]')
            links = []

            for _ in range(15):
                total_cards = await cards.count()
                if total_cards > 0:
                    links = [
                        "https://career.habr.com"
                        + await cards.nth(i)
                        .locator('a[href^="/resumes/"]')
                        .get_attribute("href")
                        for i in range(total_cards)
                    ]
                    break
                await asyncio.sleep(1.5)

            print(f"Найдено резюме: {len(links)}")
            if not links:
                print(
                    "❌ Нет резюме на странице, возможно нужно авторизоваться или сменить фильтры"
                )

            for i in range(total_cards):
                card = cards.nth(i)
                try:
                    expand_btn = card.locator('button:has-text("Развернуть")')
                    if await expand_btn.count() > 0:
                        await expand_btn.click()
                        await asyncio.sleep(0.5)

                    full_text = await card.inner_text()
                    data = await self._parse_resume_text(full_text)
                    self.results.append(data)
                    print(f"✅ {data['title']}")

                except Exception as e:
                    print(f"[ОШИБКА] {e}")

            await browser.close()
            self._save_json()

    async def _parse_resume_text(self, text: str):
        emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
        tgs = re.findall(r"(?:@|t\.me/)([a-zA-Z0-9_]{5,})", text)

        # Простейшее извлечение заголовка (первое имя или строка)
        title = text.split("\n")[0] if text else "Не указано"

        # Разделение на блоки (опыт, образование, навыки)
        blocks = {}
        if "Опыт работы" in text:
            blocks["experience"] = {"raw": self._extract_block(text, "Опыт работы")}
        if "Образование" in text:
            blocks["education"] = {"raw": self._extract_block(text, "Образование")}
        if "Профессиональные навыки" in text:
            skills_text = self._extract_block(text, "Профессиональные навыки")
            skills_list = [
                line.strip() for line in skills_text.split("\n") if line.strip()
            ]
            blocks["skills"] = {"list": skills_list}

        return {
            "source": "habr_career",
            "url": None,
            "title": title,
            "city": self.city_name,
            "contacts": {"emails": list(set(emails)), "telegrams": list(set(tgs))},
            "external_links": [],
            "blocks": blocks,
            "full_text": text,
        }

    def _extract_block(self, text: str, block_name: str):
        try:
            start = text.index(block_name) + len(block_name)
            rest = text[start:]
            end = rest.find("\n\n")
            return rest[:end].strip() if end != -1 else rest.strip()
        except ValueError:
            return ""

    def _save_json(self):
        with self.output_file.open("w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Сохранено в {self.output_file}")


# ==============================
# ENTRY POINT
# ==============================
if __name__ == "__main__":
    parser = HabrCareerParser("python", "Казань")
    asyncio.run(parser.run())
