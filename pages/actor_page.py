"""Страница актёра /name/{id}/."""

import allure
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from pages.base_page import BasePage


class ActorPage(BasePage):
    """Страница актёра с фильмографией."""

    # Имя актёра в <h1> с классом CSS-модуля primaryName.
    NAME_LOCATOR = (
        By.CSS_SELECTOR,
        "h1[class*='primaryName']",
    )

    # Запасной вариант — обычный h1 страницы.
    NAME_FALLBACK_LOCATOR = (
        By.CSS_SELECTOR,
        "h1",
    )

    # Список фильмов в фильмографии: ссылки на /film/.
    FILMOGRAPHY_LINKS_LOCATOR = (
        By.CSS_SELECTOR,
        "a[href*='/film/']",
    )

    # Контейнер фильмографии: если пустой — список пуст.
    FILMOGRAPHY_CONTAINER = (
        By.CSS_SELECTOR,
        "[data-test-id='films']",
    )

    def __init__(
        self,
        driver: WebDriver,
        url: str,
        timeout: int = 15,
    ) -> None:
        super().__init__(driver, url, timeout)

    @allure.step("Ждём загрузки страницы актёра")
    def wait_loaded(self, attempts: int = 2) -> None:
        """
        Дожидается появления имени актёра.

        Страница открывается кликом, поэтому рекламный попап не
        закрывается автоматически. При задержке отдачи страница
        перезагружается один раз.
        """
        self.close_popup_if_present(timeout=2)
        for attempt in range(1, attempts + 1):
            if self._h1_present():
                return
            if attempt < attempts:
                self.driver.refresh()
                self.close_popup_if_present(timeout=2)

        raise AssertionError(
            "Имя актёра не отрисовалось на странице. "
            f"Адрес: {self.driver.current_url}. "
            f"Заголовок: {self.driver.title}"
        )

    def _h1_present(self) -> bool:
        """Проверяет, есть ли в DOM заголовок имени актёра."""
        def found(driver: WebDriver) -> bool:
            primary = driver.find_elements(*self.NAME_LOCATOR)
            fallback = driver.find_elements(*self.NAME_FALLBACK_LOCATOR)
            return bool(primary or fallback)

        try:
            WebDriverWait(
                self.driver, self.timeout, poll_frequency=0.5
            ).until(found)
            return True
        except TimeoutException:
            return False

    @allure.step("Читаем имя актёра")
    def get_name(self) -> str:
        """Возвращает имя актёра с верхней страницы."""
        try:
            element = self.wait.until(
                ec.visibility_of_element_located(self.NAME_LOCATOR)
            )
        except TimeoutException:
            element = self.wait.until(
                ec.visibility_of_element_located(self.NAME_FALLBACK_LOCATOR)
            )
        return element.text.strip()

    @allure.step("Проверяем наличие фильмографии")
    def has_filmography(self) -> bool:
        """
        Возвращает True, если на странице есть хотя бы одна ссылка
        на фильм в разделе фильмографии.
        """
        return len(self.get_filmography_links()) > 0

    @allure.step("Читаем ссылки на фильмы из фильмографии")
    def get_filmography_links(self) -> list[str]:
        """
        Возвращает список href ссылок на фильмы из фильмографии.

        Каждый элемент — относительный URL вида /film/...
        """
        return [
            link.get_attribute("href").strip()
            for link in self.driver.find_elements(
                *self.FILMOGRAPHY_LINKS_LOCATOR
            )
            if link.get_attribute("href").strip()
        ]

    @allure.step("Переходим к первому фильму из фильмографии")
    def open_first_film(self) -> None:
        """
        Кликает по первой ссылке на фильм в фильмографии
        и ждёт загрузки страницы фильма.
        """
        links = self.get_filmography_links()
        if not links:
            raise AssertionError(
                "Невозможно перейти к фильму: фильмография пуста."
            )

        first_link = self.driver.find_element(*self.FILMOGRAPHY_LINKS_LOCATOR)
        self.driver.execute_script("arguments[0].click();", first_link)

        try:
            self.wait.until(ec.url_contains("/film/"))
        except TimeoutException as error:
            raise AssertionError(
                "Переход к фильму из фильмографии не выполнен. "
                f"Текущий адрес: {self.driver.current_url}"
            ) from error
