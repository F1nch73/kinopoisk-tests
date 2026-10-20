import allure
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec

from pages.base_page import BasePage


class FilmPage(BasePage):
    TITLE_LOCATOR = (
        By.CSS_SELECTOR,
        "h1",
    )

    YEAR_LOCATOR = (
        By.CSS_SELECTOR,
        "a[href^='/lists/movies/year--']",
    )

    RATING_LOCATOR = (
        By.CSS_SELECTOR,
        "[data-testid='film-rating'], "
        "span[itemprop='ratingValue'], "
        "[class*='rating']",
    )

    def __init__(
        self,
        driver: WebDriver,
        url: str,
        timeout: int = 15,
    ) -> None:
        super().__init__(driver, url, timeout)

    @allure.step("Читаем название фильма")
    def get_title(self) -> str:
        """Возвращает название фильма."""
        element = self.wait.until(
            ec.visibility_of_element_located(self.TITLE_LOCATOR)
        )
        return element.text.strip()

    @allure.step("Читаем год выпуска фильма")
    def get_year(self) -> str:
        """Возвращает год выпуска фильма."""
        element = self.wait.until(
            ec.visibility_of_element_located(self.YEAR_LOCATOR)
        )
        return element.text.strip()

    @allure.step("Читаем рейтинг фильма")
    def get_rating(self) -> str:
        """Возвращает отображаемый рейтинг фильма."""
        element = self.wait.until(
            ec.visibility_of_element_located(self.RATING_LOCATOR)
        )
        return element.text.strip()
