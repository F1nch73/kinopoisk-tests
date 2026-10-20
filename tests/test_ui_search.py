import allure

from selenium.webdriver.remote.webdriver import WebDriver

from pages.main_page import MainPage
from pages.search_results_page import SearchResultsPage


@allure.feature("UI: Поиск")
@allure.story("Поиск фильма по названию")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Поиск фильма по названию")
def test_ui_search_film_by_name(
    driver: WebDriver,
    base_url: str,
) -> None:
    """Проверяет поиск фильма по названию."""
    query = "Дюна"
    allure.dynamic.parameter("query", query)

    main_page = MainPage(driver, base_url)
    main_page.open()
    main_page.search(query)

    results_page = SearchResultsPage(driver, base_url)
    allure.attach(
        driver.current_url,
        name="URL после поиска",
        attachment_type=allure.attachment_type.URI_LIST,
    )

    assert results_page.has_film_with_title(query), (
        f"Фильм с названием '{query}' не найден в результатах поиска"
    )
