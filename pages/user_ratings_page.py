"""Страница «Мои оценки» пользователя."""

import allure
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from pages.base_page import BasePage


class UserRatingsPage(BasePage):
    """
    Личный раздел пользователя с оценками.

    Кинопоиск показывает оценки на странице вида
    /user/{user_id}/movies/voted-watched/, куда ведёт ссылка
    «Оценки» с /mykp/.
    """

    # Ссылка на раздел «Оценки» в профиле.
    RATINGS_TAB_XPATH = "//a[normalize-space()='Оценки']"

    # Карточка оценённого фильма: ссылка на страницу фильма.
    FILM_LINK_TEMPLATE = "a[href*='/film/{film_id}/']"

    # Значение оценки на карточке (звёздочка с числом).
    RATING_BADGE_SELECTOR = "[class*='styles_rating__']"

    def __init__(
        self,
        driver: WebDriver,
        base_url: str,
        timeout: int = 20,
    ) -> None:
        super().__init__(driver, base_url, timeout)

    @allure.step("Открываем раздел «Оценки» в профиле пользователя")
    def open(self) -> None:
        """
        Переходит в раздел «Оценки» через /mykp/.

        Ссылку берём из профиля, а не хардкодим: id пользователя
        у каждой сессии свой. Переход делаем по href, потому что
        клик по вкладке перехватывает модалка редактирования профиля.
        """
        self.driver.get(f"{self.url}/mykp/")
        try:
            link = self.wait.until(
                ec.presence_of_element_located(
                    (By.XPATH, self.RATINGS_TAB_XPATH)
                )
            )
        except TimeoutException as error:
            raise AssertionError(
                "Ссылка «Оценки» не найдена в профиле. "
                f"Адрес: {self.driver.current_url}"
            ) from error

        href = (link.get_attribute("href") or "").strip()
        if not href:
            raise AssertionError("У ссылки «Оценки» пустой href")

        self.driver.get(href)
        try:
            self.wait.until(
                lambda driver: "/movies/voted-watched/" in driver.current_url
            )
        except TimeoutException as error:
            raise AssertionError(
                "Переход в раздел «Оценки» не выполнен. "
                f"Адрес: {self.driver.current_url}"
            ) from error

        self._wait_films_loaded()

    @allure.step("Читаем оценку фильма {film_id} в разделе «Оценки»")
    def get_film_rating(
        self,
        film_id: int,
        timeout: float = 20,
        attempts: int = 3,
    ) -> str:
        """
        Возвращает оценку фильма из раздела или пустую строку.

        Список подгружается по мере прокрутки, поэтому страница
        постепенно пролистывается до появления нужной карточки.
        Карточка с бейджем может отрисоваться не сразу, поэтому при
        неудаче раздел перезагружается и поиск повторяется.
        """
        for attempt in range(1, attempts + 1):
            rating = self._search_film_rating(film_id, timeout)
            if rating:
                return rating
            if attempt < attempts:
                self._reopen()
        return ""

    def _search_film_rating(self, film_id: int, timeout: float) -> str:
        """Пролистывает раздел и читает бейдж оценки фильма."""
        self.driver.execute_script("window.scrollTo(0, 0);")
        film_locator = (
            By.CSS_SELECTOR,
            self.FILM_LINK_TEMPLATE.format(film_id=film_id),
        )

        def found(driver: WebDriver) -> str:
            """Прокручивает страницу и ищет оценку фильма."""
            cards = driver.find_elements(*film_locator)
            for card in cards:
                rating = self._extract_rating(card)
                if rating:
                    return rating
            driver.execute_script(
                "window.scrollBy(0, window.innerHeight);"
            )
            return ""

        try:
            return WebDriverWait(
                self.driver, timeout, poll_frequency=0.5
            ).until(found)
        except TimeoutException:
            return ""

    def _reopen(self) -> None:
        """Перезагружает раздел «Оценки» по текущему адресу."""
        self.driver.refresh()
        try:
            ready_state = "complete"
            WebDriverWait(self.driver, 3).until(
                lambda d: d.execute_script(
                    "return document.readyState"
                ) == ready_state
            )
        except TimeoutException:
            pass
        self._wait_films_loaded()

    def _wait_films_loaded(self, timeout: float = 10) -> None:
        """Ждёт появления хотя бы одной карточки фильма."""
        try:
            self.wait.until(
                ec.presence_of_element_located(
                    (By.CSS_SELECTOR, "a[href*='/film/']")
                )
            )
        except TimeoutException:
            pass

    def _extract_rating(self, film_link: WebElement) -> str:
        """
        Читает оценку рядом со ссылкой на фильм.

        Поднимается вверх по DOM до карточки, где лежит бейдж
        с классом styles_rating__.
        """
        result = self.driver.execute_script(
            """
            const link = arguments[0];
            if (!link) return '';
            let card = link;
            for (let i = 0; i < 8 && card; i++) {
                if (card.querySelector('[class*="styles_rating__"]')) {
                    break;
                }
                card = card.parentElement;
            }
            if (!card) return '';
            const badge = card.querySelector('[class*="styles_rating__"]');
            return badge ? badge.innerText.trim() : '';
            """,
            film_link,
        )
        return (result or "").strip()
