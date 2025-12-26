import logging
from scrapers.hh_scraper import HHParser

# Настройка логирования для отслеживания процесса в консоли
logging.basicConfig(level=logging.INFO)


async def run_hh_parser(vacancy, city, progress_callback=None):
    """
    Запускает парсер HH, получает данные и возвращает их напрямую.
    Больше не читает из временных файлов, так как HHParser возвращает всё в run().
    """
    logging.info(f"Запуск парсера для вакансии: {vacancy} в городе: {city}")

    parser = HHParser(vacancy, city)

    # parser.run возвращает кортеж: (количество, список_результатов)
    count, results = await parser.run(
        limit_per_page=47, progress_callback=progress_callback
    )

    logging.info(f"Парсинг завершен. Найдено: {count}")

    return count, results
