# tests/test_ui_film_card.py
import allure
from selenium.webdriver.remote.webdriver import WebDriver

from pages.main_page import MainPage
from pages.film_page import FilmPage


@allure.feature("UI: Карточка фильма")
@allure.story("Поля карточки")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Открытие карточки фильма и проверка названия, года и рейтинга")
def test_ui_open_film_card_and_check_fields(
        driver: WebDriver, base_url: str) -> None:
    """
    UI-тест:
      Открытие карточки фильма и проверка наличия названия,
      года и рейтинга.
    """
    query = "Дюна"
    allure.dynamic.parameter("query", query)

    main_page = MainPage(driver, base_url)
    main_page.open()
    main_page.search(query)

    with allure.step("Открываем первую карточку фильма из выдачи"):
        film_links = main_page.get_film_results()
        assert len(film_links) > 0, "Список результатов поиска пуст"

        first_film_link = film_links[0]
        film_url = first_film_link.get_attribute("href")
        allure.attach(
            film_url,
            name="URL карточки фильма",
            attachment_type=allure.attachment_type.URI_LIST,
        )

    film_page = FilmPage(driver, film_url)
    film_page.open()

    with allure.step("Читаем поля карточки фильма"):
        title = film_page.get_title()
        year = film_page.get_year()
        rating = film_page.get_rating()
        allure.attach(
            "\n".join([
                f"Название: {title}",
                f"Год: {year}",
                f"Рейтинг: {rating}",
            ]),
            name="Полученные значения",
        )

    assert title, "Название фильма не найдено"
    assert rating, "Рейтинг не найден"
    assert year.isdigit() and len(year) == 4, (
        f"Ожидался год выпуска из 4 цифр, получено: '{year}'"
    )
