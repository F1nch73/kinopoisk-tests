import allure
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    TimeoutException,
)
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

    # Адрес страницы результатов поиска.
    SEARCH_RESULTS_URL_PART = "/new-search/"

    def __init__(
        self,
        driver: WebDriver,
        base_url: str,
        timeout: int = 15,
    ) -> None:
        super().__init__(driver, base_url, timeout)

    @allure.step('Вводим запрос «{query}» и нажимаем Поиск')
    def search(self, query: str) -> None:
        """Вводит запрос, запускает поиск и ждёт страницу результатов."""
        search_input = self.wait.until(
            ec.element_to_be_clickable(self.SEARCH_INPUT_LOCATOR)
        )
        search_input.clear()
        search_input.send_keys(query)

        assert search_input.get_attribute("value") == query, (
            f"В поле поиска оказалось «"
            f"{search_input.get_attribute('value')}» вместо «{query}»"
        )

        search_button = self.wait.until(
            ec.element_to_be_clickable(self.SEARCH_BUTTON_LOCATOR)
        )
        try:
            search_button.click()
        except ElementClickInterceptedException:
            # Кнопку может перекрывать рекламный баннер.
            self.driver.execute_script(
                "arguments[0].click();",
                search_button,
            )

        self.wait_for_search_results()

    @allure.step("Ждём перехода на страницу результатов поиска")
    def wait_for_search_results(self) -> None:
        """Дожидается, что открылась страница результатов поиска."""
        try:
            self.wait.until(
                ec.url_contains(self.SEARCH_RESULTS_URL_PART)
            )
        except TimeoutException as error:
            raise AssertionError(
                "Поиск не привёл на страницу результатов: "
                f"текущий адрес — {self.driver.current_url}"
            ) from error
