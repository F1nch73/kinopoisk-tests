import re

import allure
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from pages.base_page import BasePage


class FilmPage(BasePage):
    """Карточка фильма на Кинопоиске."""

    # Адрес страницы авторизации, на которую уводит защищённое действие.
    AUTH_URL_PART = "passport.yandex.ru"

    # React навешивает на DOM-узел внутренние свойства после гидратации.
    # Их наличие означает, что обработчик клика уже работает.
    REACT_READY_SCRIPT = """
        const element = document.querySelector(arguments[0]);
        if (!element) {
            return false;
        }
        return Object.keys(element).some(
            (key) => key.startsWith('__reactProps$')
        );
    """

    # <h1 itemprop="name"><span>Дюна (2021)</span></h1>
    TITLE_LOCATOR = (
        By.CSS_SELECTOR,
        "h1[itemprop='name']",
    )

    # <a href="/lists/movies/year--2021/?b=films&amp;b=top">2021</a>
    YEAR_LOCATOR = (
        By.CSS_SELECTOR,
        "a[href^='/lists/movies/year--']",
    )

    # Значение рейтинга: <span aria-hidden="true">6.3</span>
    # внутри блока [data-tid='kp-movie-rating.rating-value'].
    RATING_LOCATOR = (
        By.CSS_SELECTOR,
        "[data-tid='kp-movie-rating.rating-value'] span[aria-hidden='true']",
    )

    # Кнопка «Смотреть»: ищем по точному title/aria-label,
    # а не по типу элемента — на странице много других кнопок
    # (например, «Смотреть трейлер»).
    WATCH_BUTTON_LOCATOR = (
        By.CSS_SELECTOR,
        "button[title='Смотреть'], "
        "button[aria-label='Смотреть'], "
        "[data-testid='watch-button']",
    )

    # <button title="Буду смотреть" aria-pressed="false">Буду смотреть</button>
    WATCHLIST_BUTTON_LOCATOR = (
        By.CSS_SELECTOR,
        "button[title='Буду смотреть'], "
        "button[aria-label='Буду смотреть'], "
        "[data-testid='add-to-watchlist']",
    )

    # Блок краткого описания (синопсиса) фильма. Класс CSS-модуля
    # сохраняет имя synopsisSection, меняется только хеш.
    DESCRIPTION_LOCATORS = (
        (By.CSS_SELECTOR, "div[class*='synopsisSection']"),
        (By.CSS_SELECTOR, "[itemprop='description']"),
    )

    # Жанры в таблице фактов «О фильме».
    GENRES_LOCATOR = (
        By.CSS_SELECTOR,
        "[data-test-id='genres'] a",
    )

    # Режиссёры в таблице фактов «О фильме».
    DIRECTORS_LOCATOR = (
        By.CSS_SELECTOR,
        "[data-test-id='directors'] a",
    )

    # Актёры главных ролей: список после заголовка «В главных ролях».
    CAST_LOCATOR = (
        By.XPATH,
        "//h3[normalize-space()='В главных ролях']"
        "/following::ul[1]//a[contains(@href, '/name/')]",
    )

    # Кнопка «Смотреть» в верхнем блоке карточки. Исключаем
    # «Смотреть трейлер» — это не доступность просмотра.
    WATCH_ACTION_LOCATOR = (
        By.XPATH,
        "//button[contains(normalize-space(.), 'Смотреть') "
        "and not(contains(normalize-space(.), 'трейлер'))]",
    )

    # Признаки доступности фильма по подписке или за покупку.
    AVAILABILITY_MARKERS = ("подписк", "купить", "аренда", "₽")

    # Радиокнопки виджета «Оценить фильм»: 10 скрытых input со
    # значением от 1 до 10, каждый обёрнут в label[data-value].
    # Клик по input перехватывает липкая навигация, а сам input
    # скрыт, поэтому кликаем по обёртке label.
    RATING_INPUT_TEMPLATE = "input[aria-label='Оценка {value}']"
    RATING_LABEL_TEMPLATE = "label[data-value='{value}']"
    RATING_INPUTS_LOCATOR = (
        By.CSS_SELECTOR,
        "input[aria-label^='Оценка']",
    )

    # Кнопка с текущей оценкой пользователя: «Изменить оценку\n8».
    USER_RATING_BUTTON_XPATH = (
        "//button[contains(normalize-space(.), 'Изменить оценку')]"
    )

    # Кнопка удаления оценки из раскрытого виджета.
    REMOVE_RATING_XPATH = "//button[normalize-space()='Удалить']"

    def __init__(
        self,
        driver: WebDriver,
        url: str,
        timeout: int = 15,
    ) -> None:
        super().__init__(driver, url, timeout)

    @allure.step("Читаем название фильма")
    def get_title(self) -> str:
        """Возвращает название фильма вместе с годом в скобках."""
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
        """Возвращает числовое значение рейтинга Кинопоиска."""
        element = self.wait.until(
            ec.visibility_of_element_located(self.RATING_LOCATOR)
        )
        return element.text.strip()

    @allure.step("Дожидаемся загрузки деталей карточки фильма")
    def wait_for_details(self, timeout: float = 20) -> None:
        """
        Дожидается загрузки блоков с деталями фильма.

        Часть карточки подгружается лениво, поэтому страницу нужно
        прокрутить до появления таблицы фактов с жанрами.
        """
        self.wait.until(
            ec.presence_of_element_located(self.TITLE_LOCATOR)
        )

        def genres_loaded(driver: WebDriver) -> bool:
            """Прокручивает страницу и проверяет появление жанров."""
            if driver.find_elements(*self.GENRES_LOCATOR):
                driver.execute_script("window.scrollTo(0, 0);")
                return True
            driver.execute_script(
                "window.scrollBy(0, window.innerHeight);"
            )
            return False

        try:
            WebDriverWait(self.driver, timeout, poll_frequency=0.5).until(
                genres_loaded
            )
        except TimeoutException as error:
            raise AssertionError(
                "Детали карточки фильма не загрузились. "
                f"Адрес: {self.driver.current_url}"
            ) from error

    @allure.step("Читаем описание фильма")
    def get_description(self) -> str:
        """Возвращает текст описания (синопсиса) фильма."""
        for locator in self.DESCRIPTION_LOCATORS:
            for element in self.driver.find_elements(*locator):
                text = (element.text or "").strip()
                if text:
                    return text
        return ""

    @allure.step("Читаем жанры фильма")
    def get_genres(self) -> list[str]:
        """Возвращает список жанров фильма."""
        return [
            element.text.strip()
            for element in self.driver.find_elements(*self.GENRES_LOCATOR)
            if element.text.strip()
        ]

    @allure.step("Читаем режиссёра фильма")
    def get_director(self) -> str:
        """Возвращает имя режиссёра фильма."""
        for element in self.driver.find_elements(*self.DIRECTORS_LOCATOR):
            text = element.text.strip()
            if text:
                return text
        return ""

    @allure.step("Читаем актёров главных ролей")
    def get_cast(self) -> list[str]:
        """Возвращает список актёров главных ролей."""
        return [
            element.text.strip()
            for element in self.driver.find_elements(*self.CAST_LOCATOR)
            if element.text.strip()
        ]

    @allure.step("Переходим на страницу первого актёра из главных ролей")
    def open_first_cast_member(self) -> None:
        """
        Кликает по первой ссылке на актёра (/name/...) и ждёт
        загрузки страницы актёра.
        """
        elements = self.driver.find_elements(*self.CAST_LOCATOR)
        if not elements:
            raise AssertionError(
                "Не удалось найти ссылки на актёров. "
                f"Адрес: {self.driver.current_url}"
            )

        link = elements[0]
        self.driver.execute_script("arguments[0].click();", link)

        try:
            self.wait.until(ec.url_contains("/name/"))
        except Exception as error:
            raise AssertionError(
                "Переход на страницу актёра не выполнен. "
                f"Текущий адрес: {self.driver.current_url}"
            ) from error

    @allure.step("Проверяем доступность фильма для просмотра")
    def has_availability_info(self) -> bool:
        """
        Проверяет кнопку «Смотреть» или информацию о подписке/покупке.

        Возвращает True, если в верхнем блоке карточки есть кнопка
        просмотра либо текст о подписке, покупке или аренде.
        """
        if self.driver.find_elements(*self.WATCH_ACTION_LOCATOR):
            return True

        hero_text = self._hero_text().lower()
        return any(
            marker in hero_text
            for marker in self.AVAILABILITY_MARKERS
        )

    def _hero_text(self, levels: int = 6) -> str:
        """Возвращает текст верхнего блока карточки фильма."""
        return self.driver.execute_script(
            """
            const title = document.querySelector("h1[itemprop='name']");
            if (!title) {
                return "";
            }
            let block = title;
            for (let i = 0; i < arguments[0] && block; i++) {
                block = block.parentElement;
            }
            return block ? (block.innerText || "") : "";
            """,
            levels,
        ) or ""

    @allure.step("Ждём появления виджета оценки")
    def wait_rating_widget(self, timeout: float = 20) -> None:
        """
        Дожидается, пока React отрендерит виджет «Оценить фильм».

        Виджет появляется не сразу: до гидратации radio-кнопок
        в DOM нет.
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                ec.presence_of_element_located(self.RATING_INPUTS_LOCATOR)
            )
        except TimeoutException as error:
            raise AssertionError(
                "Виджет оценки не появился на карточке фильма. "
                f"Адрес: {self.driver.current_url}"
            ) from error

    @allure.step("Ждём готовности блока оценки")
    def wait_rating_ui_ready(self, timeout: float = 20) -> None:
        """
        Дожидается, пока React отрендерит состояние оценки.

        Готовым считается либо кнопка «Изменить оценку» (оценка
        стоит), либо виджет со звёздами (оценки нет). До гидратации
        в DOM нет ни того, ни другого.
        """
        def block_ready(driver: WebDriver) -> bool:
            """Проверяет, отрендерился ли блок оценки."""
            if self.get_user_rating():
                return True
            return bool(driver.find_elements(*self.RATING_INPUTS_LOCATOR))

        try:
            WebDriverWait(
                self.driver, timeout, poll_frequency=0.5
            ).until(block_ready)
        except TimeoutException as error:
            raise AssertionError(
                "Блок оценки не отрендерился. "
                f"Адрес: {self.driver.current_url}"
            ) from error

    @allure.step("Читаем текущую оценку пользователя")
    def get_user_rating(self) -> str:
        """
        Возвращает оценку пользователя или пустую строку.

        Когда оценка стоит, вместо виджета показывается кнопка
        «Изменить оценку» с числом внутри.
        """
        buttons = self.driver.find_elements(
            By.XPATH, self.USER_RATING_BUTTON_XPATH
        )
        for button in buttons:
            text = (button.text or "").strip()
            match = re.search(r"(\d{1,2})\s*$", text)
            if match:
                return match.group(1)
        return ""

    @allure.step("Выбираем оценку {value} из 10")
    def select_rating(self, value: int) -> None:
        """
        Ставит оценку фильму кликом по звезде.

        Сам input скрыт и лежит внутри label[data-value], поэтому
        кликаем по обёртке. Клик по ней перехватывает липкая
        навигация, поэтому он программный.

        До гидратации React обработчик клика не работает, поэтому
        сначала ждём появления props у radio-кнопки.
        """
        self.wait_rating_widget()
        self.wait_rating_widget_ready()

        label_locator = (
            By.CSS_SELECTOR,
            self.RATING_LABEL_TEMPLATE.format(value=value),
        )
        label = self.wait.until(
            ec.presence_of_element_located(label_locator)
        )
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});"
            "arguments[0].click();",
            label,
        )

    @allure.step("Ставим оценку {value} с проверкой сохранения")
    def rate_film(self, value: int, attempts: int = 3) -> None:
        """
        Выбирает оценку и добивается её подтверждения в интерфейсе.

        Клик по звезде уходит в асинхронный запрос, и при задержке
        сети обработчик может не принять первое нажатие. Поэтому
        попытка повторяется: перед ней карточка перезагружается,
        что даёт React перерисовать виджет с нуля.
        """
        expected = str(value)
        last_error: AssertionError | None = None

        for attempt in range(1, attempts + 1):
            self.wait_rating_ui_ready()

            # Оценка уже нужна — ничего делать не требуется.
            if self.get_user_rating() == expected:
                return

            # Стоит другая оценка: виджет скрыт за кнопкой, снимаем.
            if self.get_user_rating():
                self.remove_rating()

            self.select_rating(value)
            try:
                self.wait_rating_selected(value)
                self.wait_rating_confirmed(value)
                return
            except AssertionError as error:
                last_error = error
                allure.attach(
                    f"Попытка {attempt}: {error}",
                    name="Сохранение не подтвердилось",
                )
                self.driver.refresh()
                self.wait_for_details()
                if self.get_user_rating() == expected:
                    return

        assert last_error is not None
        raise last_error

    @allure.step("Ждём, что оценка {value} стала активной")
    def wait_rating_selected(self, value: int, timeout: float = 15) -> None:
        """Ждёт, пока radio выбранной оценки получит checked=true."""
        locator = (
            By.CSS_SELECTOR,
            self.RATING_INPUT_TEMPLATE.format(value=value),
        )
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.find_element(*locator).is_selected()
            )
        except TimeoutException as error:
            raise AssertionError(
                f"Оценка {value} не стала активной после клика. "
                f"Адрес: {self.driver.current_url}"
            ) from error

    @allure.step("Ждём подтверждения оценки {value} на кнопке")
    def wait_rating_confirmed(self, value: int, timeout: float = 25) -> None:
        """
        Ждёт, пока оценка закрепится в UI: на кнопке «Изменить оценку».

        Виджет скрывается после сохранения, и вместо звёзд
        показывается кнопка с числом.
        """
        expected = str(value)
        try:
            WebDriverWait(
                self.driver, timeout, poll_frequency=0.5
            ).until(
                lambda driver: self.get_user_rating() == expected
            )
        except TimeoutException as error:
            raise AssertionError(
                f"Оценка {value} не подтвердилась на кнопке. "
                f"Текущая оценка: {self.get_user_rating()!r}. "
                f"Кнопки с оценкой: {self._rating_buttons_text()}. "
                f"Адрес: {self.driver.current_url}"
            ) from error

    def _rating_buttons_text(self) -> list[str]:
        """Возвращает тексты кнопок оценки для диагностики."""
        buttons = self.driver.find_elements(
            By.XPATH, self.USER_RATING_BUTTON_XPATH
        )
        return [
            repr((button.text or "").strip())[:60]
            for button in buttons
        ]

    @allure.step("Удаляем оценку пользователя")
    def remove_rating(self) -> None:
        """
        Снимает оценку: сначала кнопка «Изменить оценку», затем «Удалить».

        Если оценки нет, метод ничего не делает.
        """
        if not self.get_user_rating():
            return

        button = self.wait.until(
            ec.element_to_be_clickable(
                (By.XPATH, self.USER_RATING_BUTTON_XPATH)
            )
        )
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", button
        )
        button.click()

        try:
            remove = self.wait.until(
                ec.element_to_be_clickable(
                    (By.XPATH, self.REMOVE_RATING_XPATH)
                )
            )
        except TimeoutException as error:
            raise AssertionError(
                "Кнопка «Удалить» оценку не появилась. "
                f"Адрес: {self.driver.current_url}"
            ) from error

        remove.click()

        try:
            WebDriverWait(
                self.driver, self.timeout, poll_frequency=0.5
            ).until(
                lambda driver: not self.get_user_rating()
            )
        except TimeoutException as error:
            raise AssertionError(
                "Оценка не удалилась: "
                f"текущая оценка {self.get_user_rating()!r}. "
                f"Адрес: {self.driver.current_url}"
            ) from error

    @allure.step("Ждём появления кнопки «Смотреть»")
    def get_watch_button(self) -> WebElement:
        """Возвращает кнопку «Смотреть»."""
        return self.wait.until(
            ec.element_to_be_clickable(self.WATCH_BUTTON_LOCATOR)
        )

    @allure.step("Проверяем, доступен ли фильм для онлайн-просмотра")
    def is_watch_available(self, timeout: float = 3) -> bool:
        """
        Проверяет, есть ли на карточке кнопка «Смотреть».

        Кнопка отображается только для фильмов, доступных
        в онлайн-каталоге Кинопоиска.
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                ec.presence_of_element_located(self.WATCH_BUTTON_LOCATOR)
            )
            return True
        except TimeoutException:
            return False

    @allure.step("Ждём появления кнопки «Буду смотреть»")
    def get_watchlist_button(self) -> WebElement:
        """Возвращает кнопку «Буду смотреть»."""
        return self.wait.until(
            ec.element_to_be_clickable(self.WATCHLIST_BUTTON_LOCATOR)
        )

    @allure.step("Проверяем, что фильм в списке «Буду смотреть»")
    def is_in_watchlist(self) -> bool:
        """Возвращает True, если фильм добавлен в список."""
        self.get_watchlist_button()
        self.wait_watchlist_ready()
        return self._watchlist_pressed_value(self.driver) == "true"

    @allure.step("Перезагружаем карточку фильма")
    def reload(self) -> None:
        """Перезагружает страницу и закрывает рекламный popup."""
        self.driver.refresh()
        self.get_watchlist_button()
        self.close_popup_if_present(timeout=2)
        self.wait_watchlist_ready()

    @allure.step("Нажимаем «Буду смотреть»")
    def click_watchlist_button(self) -> None:
        """Нажимает кнопку «Буду смотреть»."""
        button = self.get_watchlist_button()
        try:
            button.click()
        except ElementClickInterceptedException:
            self.driver.execute_script("arguments[0].click();", button)

    @allure.step("Читаем визуальное состояние кнопки «Буду смотреть»")
    def get_watchlist_visual_state(self) -> dict[str, str]:
        """
        Возвращает видимое пользователю состояние кнопки.

        Словарь содержит подпись, aria-pressed и CSS-классы кнопки
        и её иконки: по ним видно, что состояние переключателя
        изменилось не только на уровне атрибута.
        """
        button = self.get_watchlist_button()
        return {
            "text": self._get_button_name(button),
            "pressed": button.get_attribute("aria-pressed") or "",
            "button_class": button.get_attribute("class") or "",
            "icon_class": self._watchlist_icon_class(button),
        }

    @allure.step("Ждём визуального подтверждения переключения кнопки")
    def wait_watchlist_visual_change(
        self,
        before: dict[str, str],
        timeout: float | None = None,
    ) -> dict[str, str]:
        """
        Ждёт, пока визуальное состояние кнопки изменится.

        Возвращает последнее прочитанное состояние: если за отведённое
        время ничего не изменилось, вернётся оно же, и тест покажет
        разницу в отчёте.
        """
        def changed(driver: WebDriver) -> dict[str, str] | None:
            current = self.get_watchlist_visual_state()
            return current if current != before else None

        try:
            return WebDriverWait(
                self.driver,
                timeout or self.timeout,
                poll_frequency=0.3,
            ).until(changed)  # type: ignore[return-value]
        except TimeoutException:
            return self.get_watchlist_visual_state()

    @staticmethod
    def _watchlist_icon_class(button: WebElement) -> str:
        """Возвращает CSS-классы иконок внутри кнопки."""
        icons = button.find_elements(By.CSS_SELECTOR, "span[class*='icon']")
        return " ".join(
            (icon.get_attribute("class") or "").strip()
            for icon in icons
        ).strip()

    @allure.step("Ждём, пока кнопка «Буду смотреть» станет интерактивной")
    def wait_watchlist_ready(self, timeout: float = 10) -> bool:
        """
        Ждёт, пока React навесит обработчик на кнопку.

        Кнопка приходит в HTML сразу, а обработчик клика появляется
        только после гидратации. Клик до этого теряется.
        """
        selector = self.WATCHLIST_BUTTON_LOCATOR[1]
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script(
                    self.REACT_READY_SCRIPT,
                    selector,
                )
            )
            return True
        except TimeoutException:
            return False

    @allure.step("Ждём гидратации виджета оценки")
    def wait_rating_widget_ready(self, timeout: float = 10) -> bool:
        """
        Ждёт, пока React навесит обработчики на radio-кнопки.

        Виджет оценки — React-компонент: кликаем по label-обёртке,
        поэтому проверяем гидратацию именно label.
        """
        selector = self.RATING_LABEL_TEMPLATE.format(value=1)
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script(
                    self.REACT_READY_SCRIPT,
                    selector,
                )
            )
            return True
        except TimeoutException:
            return False

    @allure.step("Приводим «Буду смотреть» к состоянию: {desired}")
    def set_watchlist_state(self, desired: bool, attempts: int = 3) -> None:
        """
        Приводит кнопку к нужному состоянию и подтверждает результат.

        Интерфейс меняет подпись кнопки оптимистично, поэтому после
        клика состояние сверяется с сервером через перезагрузку
        страницы. Если сервер его не принял, клик повторяется.
        """
        expected = "true" if desired else "false"

        for attempt in range(1, attempts + 1):
            if self._watchlist_pressed_value(self.driver) != expected:
                self.wait_watchlist_ready()
                self.click_watchlist_button()
                try:
                    self.wait_watchlist_pressed(desired, timeout=10)
                except AssertionError:
                    pass

            if self._is_state_saved(expected):
                return

            allure.attach(
                f"Попытка {attempt}: состояние {expected} не подтвердилось",
                name="Повтор переключения",
            )

        raise AssertionError(
            "Не удалось перевести «Буду смотреть» в состояние "
            f"{desired} за {attempts} попытки. Текущее значение: "
            f"{self._watchlist_pressed_value(self.driver)}"
        )

    def _is_state_saved(self, expected: str) -> bool:
        """Проверяет состояние после перезагрузки страницы."""
        self.reload()
        return self._watchlist_pressed_value(self.driver) == expected

    @allure.step("Ждём перехода на страницу авторизации")
    def wait_for_auth_redirect(self) -> None:
        """Дожидается перехода на страницу авторизации Яндекса."""
        try:
            self.wait.until(
                ec.url_contains(self.AUTH_URL_PART)
            )
        except TimeoutException as error:
            raise AssertionError(
                "Перехода на страницу авторизации не произошло. "
                f"Текущий адрес: {self.driver.current_url}"
            ) from error

    @allure.step("Ждём состояние кнопки «Буду смотреть»: {expected}")
    def wait_watchlist_pressed(
        self,
        expected: bool,
        timeout: float | None = None,
    ) -> None:
        """Ждёт, пока aria-pressed кнопки станет ожидаемым."""
        value = "true" if expected else "false"
        try:
            WebDriverWait(
                self.driver,
                timeout or self.timeout,
            ).until(
                lambda driver: self._watchlist_pressed_value(driver) == value
            )
        except TimeoutException as error:
            raise AssertionError(
                "Кнопка «Буду смотреть» не перешла в состояние "
                f"aria-pressed={value}. Текущее значение: "
                f"{self._watchlist_pressed_value(self.driver)}"
            ) from error

    def _watchlist_pressed_value(self, driver: WebDriver) -> str:
        """Возвращает текущее значение aria-pressed кнопки."""
        buttons = driver.find_elements(*self.WATCHLIST_BUTTON_LOCATOR)
        if not buttons:
            return ""
        return buttons[0].get_attribute("aria-pressed") or ""

    @allure.step("Читаем название кнопки «Смотреть»")
    def get_watch_button_name(self) -> str:
        """Возвращает подпись кнопки «Смотреть»."""
        return self._get_button_name(self.get_watch_button())

    @allure.step("Читаем название кнопки «Буду смотреть»")
    def get_watchlist_button_name(self) -> str:
        """Возвращает подпись кнопки «Буду смотреть»."""
        return self._get_button_name(self.get_watchlist_button())

    @staticmethod
    def _get_button_name(button: WebElement) -> str:
        """
        Возвращает доступное название кнопки.

        Берём текст, а если его нет — title или aria-label.
        """
        for value in (
            button.text,
            button.get_attribute("title"),
            button.get_attribute("aria-label"),
        ):
            if value and value.strip():
                return value.strip()
        return ""
