import asyncio
import random
import re
import json
import aiohttp
from pathlib import Path
from playwright.async_api import async_playwright


class HHParser:
    def __init__(self, specialty: str, city_name: str):
        self.specialty = specialty
        self.city_name = city_name
        self.area_id = "1"
        self.results = []

    async def _resolve_area_id(self):
        url = "https://api.hh.ru/areas"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                areas = await resp.json()

        def find_city(areas):
            for area in areas:
                if area["name"].lower() == self.city_name.lower():
                    return area["id"]
                if area.get("areas"):
                    found = find_city(area["areas"])
                    if found:
                        return found
            return None

        self.area_id = find_city(areas) or "1"

    async def run(self, max_pages=5, limit_per_page=47, progress_callback=None):
        await self._resolve_area_id()

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()

            search_url = (
                f"https://{self.city_name.lower()}.hh.ru/search/resume?"
                f"text={self.specialty}&pos=full_text&logic=normal&exp_period=all_time&ored_clusters=true&order_by=relevance&search_period=0"
            )

            for pnum in range(max_pages):
                await page.goto(f"{search_url}&page={pnum}")
                try:
                    await page.wait_for_selector(
                        '[data-qa="serp-item__title"]', timeout=10000
                    )
                except:
                    break  # Если страниц больше нет

                links = await page.locator('[data-qa="serp-item__title"]').evaluate_all(
                    "els => els.map(e => e.href)"
                )
                titles = await page.locator(
                    '[data-qa="serp-item__title"]'
                ).all_inner_texts()

                # Фильтруем по вакансии
                keywords = [w.lower() for w in self.specialty.split()]
                filtered_links = [
                    link
                    for link, title in zip(links, titles)
                    if all(word in title.lower() for word in keywords)
                ]

                for link in filtered_links:
                    try:
                        await page.goto(
                            link, timeout=60000, wait_until="domcontentloaded"
                        )
                        await asyncio.sleep(random.uniform(1.5, 3))

                        resume = await self._parse_resume(page, link)
                        self.results.append(resume)

                        if progress_callback:
                            percent = int(len(self.results) / limit_per_page * 100)
                            await progress_callback(min(percent, 100))

                        if len(self.results) >= limit_per_page:
                            break
                    except Exception as e:
                        print(f"❌ Ошибка загрузки резюме {link}: {e}")
                        continue

                if len(self.results) >= limit_per_page:
                    break

            await browser.close()

        # Возвращаем количество и сами данные
        return len(self.results), self.results

    async def _parse_resume(self, page, link):
        full_text = await page.locator(".resume-wrapper").inner_text()

        blocks = await page.evaluate(
            """
            () => {
                const res = {};
                document.querySelectorAll('[data-qa^="resume-block"]').forEach(b => {
                    const title = b.querySelector('h2')?.innerText || 'Прочее';
                    res[title] = b.innerText;
                });
                return res;
            }
            """
        )

        emails = re.findall(
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", full_text
        )
        tgs = re.findall(r"(?:@|t\.me\/)([a-zA-Z0-9_]{5,})", full_text)

        return {
            "url": link,
            "title": await self._get_text(
                page, '[data-qa="resume-block-title-position"]'
            ),
            "city": self.city_name,
            "contacts": {
                "emails": list(set(emails)),
                "telegrams": list(set(tgs)),
            },
            "external_links": await self._get_links(page),
            "blocks": self._normalize_blocks(blocks),
            "full_text": full_text,
        }

    def _normalize_blocks(self, blocks: dict):
        normalized = {}
        for title, text in blocks.items():
            key = title.lower()
            if "опыт" in key:
                normalized["experience"] = {"raw": text}
            elif "образование" in key:
                normalized["education"] = {"raw": text}
            elif "навык" in key:
                normalized["skills"] = {
                    "list": [l.strip() for l in text.split("\n") if l.strip()]
                }
            elif "обо мне" in key:
                normalized["about"] = {"raw": text}
            else:
                normalized[title] = {"raw": text}
        return normalized

    async def _get_text(self, page, selector):
        try:
            return await page.locator(selector).inner_text()
        except:
            return "Не указано"

    async def _get_links(self, page):
        return await page.locator(".resume-wrapper a").evaluate_all(
            "els => els.map(e => e.href).filter(h => h && !h.includes('hh.ru'))"
        )


# Функция-помощник для вызова из роутера
async def run_hh_parser(specialty: str, city: str, progress_callback=None):
    parser = HHParser(specialty, city)
    return await parser.run(progress_callback=progress_callback)
