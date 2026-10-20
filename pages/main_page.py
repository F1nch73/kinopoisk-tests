import allure
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec

from pages.base_page import BasePage


class MainPage(BasePage):
    SEARCH_INPUT_LOCATOR = (
        By.CSS_SELECTOR,
        "input[name='text'][placeholder='Фильмы, сериалы, персоны']",
    )

    SEARCH_BUTTON_LOCATOR = (
        By.CSS_SELECTOR,
        "button[type='submit'][aria-label='Найти']",
    )

    FILM_LINK_LOCATOR = (
        By.CSS_SELECTOR,
        "a[href*='/film/']",
    )

    def __init__(
        self,
        driver: WebDriver,
        base_url: str,
        timeout: int = 15,
    ) -> None:
        super().__init__(driver, base_url, timeout)

    @allure.step('Вводим запрос «{query}» и нажимаем Поиск')
    def search(self, query: str) -> None:
        """Вводит запрос и запускает поиск."""
        search_input = self.wait.until(
            ec.element_to_be_clickable(self.SEARCH_INPUT_LOCATOR)
        )
        search_input.clear()
        search_input.send_keys(query)

        search_button = self.wait.until(
            ec.element_to_be_clickable(self.SEARCH_BUTTON_LOCATOR)
        )
        search_button.click()

    @allure.step('Ждём появления карточек фильмов в результатах поиска')
    def get_film_results(self) -> list:
        """
        Возвращает ссылки на фильмы в выдаче поиска.

        Страница /new-search/ отдаёт пустую оболочку, а карточки
        подгружаются асинхронно, поэтому дожидаемся их появления.
        """
        return self.wait.until(
            ec.presence_of_all_elements_located(self.FILM_LINK_LOCATOR)
        )
