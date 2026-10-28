# tests/test_ui_film_card.py
import re

import allure
import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from config import FILM_NAME_AVAILABLE
from pages.film_page import FilmPage
from pages.main_page import MainPage
from pages.search_results_page import SearchResultsPage

YEAR_PATTERN = re.compile(r"^\d{4}$")
RATING_PATTERN = re.compile(r"^\d{1,2}(\.\d)?$")


@pytest.mark.smoke
@allure.feature("UI: Карточка фильма")
@allure.story("Поля карточки")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Открытие карточки фильма и проверка всех полей")
def test_ui_open_film_card_and_check_fields(
        driver: WebDriver, base_url: str) -> None:
    """
    UI-тест:
      Поиск фильма, переход в карточку кликом по карточке и проверка
      названия, года, рейтинга, описания, актёров, режиссёра, жанров
      и доступности просмотра.

    Используется фильм «Чебурашка»: он доступен в онлайн-кинотеатре,
    поэтому на карточке есть кнопка «Смотреть» и блок подписки.
    """
    query = FILM_NAME_AVAILABLE
    allure.dynamic.parameter("query", query)

    main_page = MainPage(driver, base_url)
    main_page.open()
    main_page.search(query)

    results_page = SearchResultsPage(driver, base_url)

    with allure.step("Кликаем по карточке фильма в выдаче"):
        card = results_page.get_film_card_by_title(query)
        results_page.click_film_card(card)
        allure.attach(
            driver.current_url,
            name="URL открытой карточки",
            attachment_type=allure.attachment_type.URI_LIST,
        )

    film_page = FilmPage(driver, driver.current_url)
    film_page.wait_for_details()

    with allure.step("Проверяем, что открылась карточка фильма"):
        current_url = driver.current_url
        assert "/film/" in current_url, (
            f"Ожидалась карточка фильма, получено: {current_url}"
        )

    with allure.step("Проверяем название фильма"):
        title = film_page.get_title()
        allure.attach(title, name="Название фильма")
        assert query.casefold() in title.casefold(), (
            f"В названии «{title}» нет искомого «{query}»"
        )

    with allure.step("Проверяем год выпуска"):
        year = film_page.get_year()
        allure.attach(year, name="Год выпуска")
        assert YEAR_PATTERN.match(year), (
            f"Ожидался год выпуска из 4 цифр, получено: «{year}»"
        )

    with allure.step("Проверяем рейтинг"):
        rating = film_page.get_rating()
        allure.attach(rating, name="Рейтинг")
        assert RATING_PATTERN.match(rating), (
            f"Ожидался рейтинг от 0 до 10, получено: «{rating}»"
        )

    with allure.step("Проверяем описание фильма"):
        description = film_page.get_description()
        allure.attach(description, name="Описание фильма")
        assert description, "На карточке фильма отсутствует описание"
        assert len(description) > 20, (
            f"Описание слишком короткое: «{description}»"
        )

    with allure.step("Проверяем режиссёра фильма"):
        director = film_page.get_director()
        allure.attach(director, name="Режиссёр фильма")
        assert director, "На карточке фильма не указан режиссёр"

    with allure.step("Проверяем актёров фильма"):
        cast = film_page.get_cast()
        allure.attach("\n".join(cast), name="Актёры главных ролей")
        assert cast, "На карточке фильма не указаны актёры"

    with allure.step("Проверяем жанры фильма"):
        genres = film_page.get_genres()
        allure.attach("\n".join(genres), name="Жанры фильма")
        assert genres, "На карточке фильма не указаны жанры"

    with allure.step("Проверяем кнопку «Смотреть» или доступность фильма"):
        has_availability = film_page.has_availability_info()
        allure.attach(
            str(has_availability),
            name="Доступность просмотра",
        )
        assert has_availability, (
            "На карточке фильма нет кнопки «Смотреть» и информации "
            "о доступности по подписке или покупке"
        )
