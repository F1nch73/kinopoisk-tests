from typing import Tuple

import allure
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


Locator = Tuple[str, str]


class BasePage:
    CLOSE_POPUP_BUTTON_LOCATOR: Locator = (
        By.CSS_SELECTOR,
        "button[data-tid='CloseButton']",
    )

    def __init__(
        self,
        driver: WebDriver,
        url: str,
        timeout: int = 15,
    ) -> None:
        self.driver = driver
        self.url = url
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)

    @allure.step("Открываем страницу")
    def open(self) -> None:
        """Открывает страницу и закрывает рекламный баннер."""
        self.driver.get(self.url)
        allure.attach(
            self.driver.current_url,
            name="Открыт URL",
            attachment_type=allure.attachment_type.URI_LIST,
        )

        # Ждём баннер до 3 секунд только при открытии страницы.
        self.close_popup_if_present(timeout=3)

    @allure.step("Закрываем рекламный popup, если он появился")
    def close_popup_if_present(self, timeout: float = 0.5) -> bool:
        """
        Закрывает рекламный popup, если он появился.

        Возвращает:
            True — popup был найден и закрыт.
            False — popup не появился за указанное время.
        """
        try:
            close_button = WebDriverWait(
                self.driver,
                timeout,
            ).until(
                ec.element_to_be_clickable(self.CLOSE_POPUP_BUTTON_LOCATOR)
            )

            try:
                close_button.click()
            except ElementClickInterceptedException:
                self.driver.execute_script(
                    "arguments[0].click();",
                    close_button,
                )

            return True

        except TimeoutException:
            return False
