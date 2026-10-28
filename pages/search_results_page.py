import re

from collections.abc import Callable

import allure
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec

from pages.base_page import BasePage

# Паттерн для извлечения года из текста карточки (4-значное число).
YEAR_IN_TEXT_PATTERN = re.compile(r"\b(\d{4})\b")


class SearchResultsPage(BasePage):
    """Страница результатов поиска /new-search/."""

    # <div data-test-id="movie-list-item"> — карточка результата.
    CARD_LOCATOR = (
        By.CSS_SELECTOR,
        "[data-test-id='movie-list-item']",
    )

    # Запасной вариант карточки: ссылка на фильм внутри секции выдачи.
    # Кинопоиск иногда отдаёт разметку без data-test-id.
    CARD_FALLBACK_LOCATOR = (
        By.CSS_SELECTOR,
        "section[data-testid='search-films'] a[href*='/film/']",
    )

    # Ссылка с названием фильма внутри карточки.
    CARD_LINK_LOCATOR = (
        By.CSS_SELECTOR,
        "a[data-test-id='next-link']",
    )

    # Постер карточки: в alt лежит точное название фильма.
    CARD_POSTER_LOCATOR = (
        By.CSS_SELECTOR,
        "img[alt]",
    )

    def __init__(
        self,
        driver: WebDriver,
        base_url: str,
        timeout: int = 25,
    ) -> None:
        super().__init__(driver, base_url, timeout)

    @allure.step("Ждём появления карточек в результатах поиска")
    def get_film_cards(self) -> list[WebElement]:
        """
        Возвращает видимые карточки фильмов из выдачи.

        Ждём появления хотя бы одной видимой карточки, а затем берём
        все карточки и отсеиваем невидимые: часть разметки Кинопоиска
        может лежать в скрытых блоках.
        """
        try:
            return self.wait.until(self._visible_cards)
        except TimeoutException as error:
            raise AssertionError(
                "Карточки не появились в результатах поиска. "
                f"Адрес: {self.driver.current_url}. "
                f"Заголовок: {self.driver.title}. "
                f"Фрагмент страницы: {self._page_snippet()}"
            ) from error

    @allure.step("Читаем названия найденных карточек")
    def get_film_titles(self) -> list[str]:
        """Возвращает названия фильмов из выдачи."""
        return [self._get_card_title(card) for card in self.get_film_cards()]

    @allure.step("Читаем название фильма из карточки")
    def get_card_title(self, card: WebElement) -> str:
        """Публичный доступ к названию фильма из конкретной карточки."""
        return self._get_card_title(card)

    @allure.step('Проверяем наличие фильма «{title}» в результатах поиска')
    def has_film_with_title(self, title: str) -> bool:
        """Проверяет, что в выдаче есть фильм с указанным названием."""
        return any(
            title.casefold() in card_title.casefold()
            for card_title in self.get_film_titles()
        )

    @allure.step('Находим карточку фильма «{title}»')
    def get_film_card_by_title(self, title: str) -> WebElement:
        """
        Возвращает карточку, в названии которой есть указанный текст.

        Выдача подгружается частями, поэтому ждём нужную карточку
        до истечения таймаута, а не читаем выдачу один раз.
        """
        try:
            return self.wait.until(self._card_with_title(title))
        except TimeoutException as error:
            raise AssertionError(
                f"Карточка фильма «{title}» не найдена в результатах поиска. "
                f"Найдены: {self._safe_titles()}. "
                f"Адрес: {self.driver.current_url}. "
                f"Фрагмент страницы: {self._page_snippet()}"
            ) from error

    @allure.step("Читаем ссылку на карточку фильма")
    def get_film_url(self, card: WebElement) -> str:
        """Возвращает адрес карточки фильма."""
        if card.tag_name == "a":
            return (card.get_attribute("href") or "").strip()

        links = card.find_elements(*self.CARD_LINK_LOCATOR)
        if not links:
            links = card.find_elements(By.CSS_SELECTOR, "a[href*='/film/']")
        if not links:
            return ""
        return (links[0].get_attribute("href") or "").strip()

    @allure.step("Кликаем по карточке фильма и ждём открытия карточки")
    def click_film_card(self, card: WebElement) -> None:
        """
        Кликает по названию/постеру карточки и ждёт страницу фильма.

        Если клик перехвачен рекламным баннером, используется
        программный клик по ссылке.
        """
        if card.tag_name == "a":
            target = card
        else:
            links = card.find_elements(*self.CARD_LINK_LOCATOR)
            if not links:
                links = card.find_elements(
                    By.CSS_SELECTOR, "a[href*='/film/']"
                )
            target = links[0] if links else card

        try:
            target.click()
        except ElementClickInterceptedException:
            self.driver.execute_script("arguments[0].click();", target)

        try:
            self.wait.until(
                ec.url_contains("/film/")
            )
        except TimeoutException as error:
            raise AssertionError(
                "Клик по карточке не открыл страницу фильма. "
                f"Текущий адрес: {self.driver.current_url}"
            ) from error

    def _visible_cards(self, driver: WebDriver) -> list[WebElement]:
        """Предикат ожидания: список видимых карточек."""
        try:
            cards = driver.find_elements(*self.CARD_LOCATOR)
            if not cards:
                cards = driver.find_elements(*self.CARD_FALLBACK_LOCATOR)
            return [card for card in cards if card.is_displayed()]
        except StaleElementReferenceException:
            return []

    def _card_with_title(
        self, title: str
    ) -> "Callable[[WebDriver], WebElement | None]":
        """Предикат ожидания: карточка с нужным названием."""
        def find(driver: WebDriver) -> WebElement | None:
            for card in self._visible_cards(driver):
                try:
                    card_title = self._get_card_title(card)
                except StaleElementReferenceException:
                    continue
                if title.casefold() in card_title.casefold():
                    return card
            return None

        return find

    def _safe_titles(self) -> list[str]:
        """Возвращает названия карточек, не роняя диагностику."""
        titles: list[str] = []
        try:
            cards = self.driver.find_elements(*self.CARD_LOCATOR)
            if not cards:
                cards = self.driver.find_elements(*self.CARD_FALLBACK_LOCATOR)
            for card in cards:
                try:
                    title = self._get_card_title(card)
                except StaleElementReferenceException:
                    continue
                if title:
                    titles.append(title)
        except Exception:  # noqa: BLE001 - только для текста ошибки
            return titles
        return titles

    def _page_snippet(self, limit: int = 200) -> str:
        """Возвращает фрагмент текста страницы для диагностики."""
        try:
            body = self.driver.find_element(By.TAG_NAME, "body")
            return " ".join(body.text.split())[:limit]
        except Exception:  # noqa: BLE001 - только для текста ошибки
            return "<недоступно>"

    @allure.step("Читаем год выпуска из карточки фильма")
    def get_card_year(self, card: WebElement) -> str:
        """
        Возвращает год выпуска фильма из карточки на странице результатов.

        Год ищется в тексте карточки как 4-значное число.
        """
        text = card.text.strip()
        match = YEAR_IN_TEXT_PATTERN.search(text)
        if match:
            return match.group(1)
        return ""

    @allure.step("Проверяем наличие постера в карточке фильма")
    def get_card_poster(self, card: WebElement) -> str:
        """
        Возвращает URL постера из карточки фильма.

        Если постер не найден, возвращает пустую строку.
        """
        try:
            posters = card.find_elements(By.CSS_SELECTOR, "img[src]")
            if posters:
                src = posters[0].get_attribute("src")
                if src:
                    return src.strip()
        except StaleElementReferenceException:
            pass
        return ""

    def _get_card_title(self, card: WebElement) -> str:
        """Возвращает название фильма из карточки."""
        posters = card.find_elements(*self.CARD_POSTER_LOCATOR)
        if posters:
            alt = (posters[0].get_attribute("alt") or "").strip()
            if alt:
                return alt

        links = card.find_elements(*self.CARD_LINK_LOCATOR)
        if links:
            return links[0].text.strip()

        # Запасной вариант: карточка — это сама ссылка на фильм.
        if card.tag_name == "a":
            return card.text.strip()

        return ""
