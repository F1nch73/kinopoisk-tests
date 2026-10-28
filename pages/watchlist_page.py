from urllib.parse import urlparse

import allure
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

from pages.base_page import BasePage


class WatchlistPage(BasePage):
    """
    Раздел «Моё кино» → «Буду смотреть».

    Кинопоиск держит несколько версий раздела, поэтому адрес
    подбирается перебором: первый, который открылся без редиректа
    на страницу авторизации.
    """

    # Адрес страницы авторизации: признак того, что раздел недоступен.
    AUTH_URL_PART = "passport.yandex.ru"

    # Возможные адреса раздела «Буду смотреть» (от нового к старому).
    SECTION_PATHS = (
        "/mykp/movies/watchlist/",
        "/mykp/folders/",
        "/mykp/movies/",
    )

    # Карточка фильма в списке: ссылка на страницу фильма.
    FILM_LINK_TEMPLATE = "a[href*='/film/{film_id}/']"

    def __init__(
        self,
        driver: WebDriver,
        base_url: str,
        timeout: int = 20,
    ) -> None:
        super().__init__(driver, base_url, timeout)

    @allure.step("Открываем раздел «Моё кино» → «Буду смотреть»")
    def open_section(self) -> None:
        """
        Открывает раздел «Буду смотреть».

        Перебирает известные адреса и ссылки из шапки профиля, пока
        не откроется страница раздела, а не страница авторизации
        или главная.
        """
        attempts: list[str] = []

        for url in self._section_urls():
            self.driver.get(url)

            if self.AUTH_URL_PART in self.driver.current_url:
                attempts.append(f"{url} → авторизация")
                continue

            if self._wait_section_loaded():
                allure.attach(
                    self.driver.current_url,
                    name="URL раздела «Буду смотреть»",
                    attachment_type=allure.attachment_type.URI_LIST,
                )
                return

            attempts.append(f"{url} → не раздел")

        raise AssertionError(
            "Не удалось открыть раздел «Буду смотреть». "
            f"Попытки: {attempts}. "
            f"Текущий адрес: {self.driver.current_url}"
        )

    def _section_urls(self) -> list[str]:
        """Возвращает адреса раздела: известные и найденные в шапке."""
        urls = [f"{self.url}{path}" for path in self.SECTION_PATHS]
        for href in self._header_mykp_links():
            if href not in urls:
                urls.append(href)
        return urls

    def _header_mykp_links(self) -> list[str]:
        """
        Ищет ссылки на «Моё кино» в шапке сайта.

        Нужен запасной путь на случай, если Кинопоиск сменит адреса
        разделов: ссылка в профиле всегда актуальна.
        """
        self.driver.get(self.url)

        links: list[str] = []
        for link in self.driver.find_elements(
            By.CSS_SELECTOR,
            "a[href*='/mykp/']",
        ):
            href = (link.get_attribute("href") or "").strip()
            if href and href not in links:
                links.append(href)
        return links

    @allure.step("Проверяем, что фильм {film_id} есть в «Буду смотреть»")
    def has_film(self, film_id: int, timeout: float = 15) -> bool:
        """
        Проверяет, что в списке есть карточка указанного фильма.

        Список подгружается по мере прокрутки, поэтому страница
        постепенно пролистывается до появления нужной карточки.
        """
        locator = (
            By.CSS_SELECTOR,
            self.FILM_LINK_TEMPLATE.format(film_id=film_id),
        )

        def found(driver: WebDriver) -> bool:
            """Прокручивает страницу и проверяет появление карточки."""
            if driver.find_elements(*locator):
                return True
            driver.execute_script(
                "window.scrollBy(0, window.innerHeight);"
            )
            return False

        try:
            WebDriverWait(self.driver, timeout, poll_frequency=0.5).until(
                found
            )
            return True
        except TimeoutException:
            return False

    @allure.step("Читаем названия фильмов в «Буду смотреть»")
    def get_film_titles(self) -> list[str]:
        """Возвращает названия фильмов из списка (для диагностики)."""
        titles: list[str] = []
        links = self.driver.find_elements(
            By.CSS_SELECTOR,
            "a[href*='/film/'], a[href*='/series/']",
        )
        for link in links:
            text = (link.text or "").strip()
            if text and text not in titles:
                titles.append(text)
        return titles

    def _wait_section_loaded(self, timeout: float = 15) -> bool:
        """
        Ждёт загрузки страницы раздела.

        Проверяется именно путь: при отсутствии авторизации Кинопоиск
        уводит на главную с параметром `?from=mykp`, поэтому поиск
        подстроки «mykp» в адресе даёт ложное срабатывание.
        """
        try:
            self.wait.until(
                lambda driver: urlparse(driver.current_url).path.startswith(
                    "/mykp/"
                )
            )
        except TimeoutException:
            return False

        try:
            self.wait.until(
                lambda driver: driver.execute_script(
                    "return document.readyState"
                ) == "complete"
            )
        except TimeoutException:
            return False

        return True
