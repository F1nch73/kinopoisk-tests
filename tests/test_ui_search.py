import allure
import pytest
from urllib.parse import unquote

from selenium.webdriver.remote.webdriver import WebDriver

from pages.film_page import FilmPage
from pages.main_page import MainPage
from pages.search_results_page import SearchResultsPage


@pytest.mark.smoke
@allure.feature("UI: Поиск")
@allure.story("Поиск фильма по названию")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Поиск фильма по названию")
def test_ui_search_film_by_name(
    driver: WebDriver,
    base_url: str,
) -> None:
    """Проверяет, что поиск по названию возвращает нужный фильм."""
    query = "Дюна"
    allure.dynamic.parameter("query", query)

    main_page = MainPage(driver, base_url)
    main_page.open()
    main_page.search(query)

    results_page = SearchResultsPage(driver, base_url)

    with allure.step("Проверяем, что открылась страница результатов"):
        current_url = unquote(driver.current_url)
        allure.attach(
            current_url,
            name="URL после поиска",
            attachment_type=allure.attachment_type.URI_LIST,
        )

        assert "/new-search/" in current_url, (
            f"Ожидалась страница /new-search/, получено: {current_url}"
        )
        assert f"text={query}" in current_url, (
            f"Запрос «{query}» не попал в адрес страницы: {current_url}"
        )

    with allure.step("Проверяем карточки в выдаче"):
        titles = results_page.get_film_titles()
        allure.attach(
            "\n".join(titles),
            name="Названия найденных карточек",
        )

        assert titles, "В результатах поиска нет ни одной карточки"
        assert results_page.has_film_with_title(query), (
            f"В результатах поиска нет фильма «{query}». "
            f"Найдены: {titles}"
        )

    with allure.step("Находим карточку с искомым фильмом"):
        card = results_page.get_film_card_by_title(query)

    with allure.step("Проверяем корректность названия фильма"):
        card_title = results_page.get_card_title(card)
        allure.attach(
            card_title,
            name="Название из карточки выдачи",
        )
        assert query.casefold() in card_title.casefold(), (
            f"Ожидалось название «{query}», получено: «{card_title}»"
        )

    with allure.step("Проверяем наличие года выпуска в карточке выдачи"):
        year = results_page.get_card_year(card)
        allure.attach(
            year,
            name="Год выпуска из карточки выдачи",
        )
        assert year, (
            f"В карточке «{card_title}» не найден год выпуска. "
            f"Текст карточки: {card.text!r}"
        )

    with allure.step("Проверяем наличие постера в карточке выдачи"):
        poster_url = results_page.get_card_poster(card)
        allure.attach(
            poster_url,
            name="URL постера из карточки выдачи",
            attachment_type=allure.attachment_type.URI_LIST,
        )
        assert poster_url, (
            f"В карточке «{card_title}» не найден постер"
        )

    with allure.step("Проверяем доступность перехода к карточке фильма"):
        film_url = results_page.get_film_url(card)
        allure.attach(
            film_url,
            name="URL карточки фильма",
            attachment_type=allure.attachment_type.URI_LIST,
        )
        assert film_url, (
            f"Не удалось получить ссылку на карточку фильма «{query}»"
        )
        assert "/film/" in film_url, (
            f"Ссылка не ведёт на карточку фильма: {film_url}"
        )

    with allure.step("Открываем карточку фильма и проверяем переход"):
        film_page = FilmPage(driver, film_url)
        film_page.open()
        film_title = film_page.get_title()
        allure.attach(
            film_title,
            name="Название на странице фильма",
        )
        assert query.casefold() in film_title.casefold(), (
            f"После перехода карточка не соответствует фильму «{query}». "
            f"Название на странице: «{film_title}»"
        )
