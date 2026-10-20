import allure
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec

from pages.base_page import BasePage


class SearchResultsPage(BasePage):
    def __init__(
        self,
        driver: WebDriver,
        base_url: str,
        timeout: int = 15,
    ) -> None:
        super().__init__(driver, base_url, timeout)

    @allure.step('Проверяем наличие фильма «{title}» в результатах поиска')
    def has_film_with_title(self, title: str) -> bool:
        """Проверяет наличие фильма с указанным названием в результатах."""
        film_locator = (
            By.XPATH,
            f"//a[contains(@href, '/film/') and "
            f".//*[contains(normalize-space(), '{title}')]]",
        )

        try:
            element = self.wait.until(
                ec.visibility_of_element_located(film_locator)
            )
            return element.is_displayed()
        except Exception:
            return False
