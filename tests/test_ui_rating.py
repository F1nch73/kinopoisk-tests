import allure

from selenium.webdriver.remote.webdriver import WebDriver

from pages.film_page import FilmPage


@allure.feature("UI: Карточка фильма")
@allure.story("Рейтинг")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Блок рейтинга присутствует на карточке фильма")
def test_ui_film_rating_block_exists(
    driver: WebDriver,
    base_url: str,
) -> None:
    """Проверяет наличие рейтинга на карточке фильма."""
    film_url = f"{base_url}/film/300/"

    film_page = FilmPage(driver, film_url)
    film_page.open()

    rating = film_page.get_rating()
    allure.attach(
        rating,
        name="Значение рейтинга",
    )

    assert rating, "Рейтинг фильма не найден"
