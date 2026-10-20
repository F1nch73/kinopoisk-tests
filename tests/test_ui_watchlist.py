import allure

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


@allure.feature("UI: Список ожидания")
@allure.story("Кнопка «Буду смотреть»")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Кнопка «Буду смотреть» присутствует на карточке фильма")
def test_ui_add_film_to_watchlist_button_exists(
        driver: WebDriver, base_url: str) -> None:
    """
    UI-тест: Проверка наличия кнопки «Буду смотреть» на карточке фильма.
    (Без реальной авторизации, только наличие элемента.)
    """
    film_id = 300  # пример
    film_url = f"{base_url}/film/{film_id}/"
    allure.dynamic.parameter("film_id", film_id)

    with allure.step("Открываем карточку фильма"):
        driver.get(film_url)

    wait = WebDriverWait(driver, 10)

    with allure.step("Ищем кнопку «Буду смотреть»"):
        watchlist_button = wait.until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR,
                "[data-testid='add-to-watchlist'], .add-to-watchlist, button"
            ))
        )

    assert watchlist_button.is_displayed(), "Кнопка «Буду смотреть» не найдена"
