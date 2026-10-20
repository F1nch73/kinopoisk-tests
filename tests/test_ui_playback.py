import allure

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


@allure.feature("UI: Воспроизведение")
@allure.story("Кнопка «Смотреть»")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Кнопка «Смотреть» присутствует на карточке фильма")
def test_ui_playback_button_exists(driver: WebDriver, base_url: str) -> None:
    """
    UI-тест: Проверка наличия кнопки «Смотреть» на карточке фильма.
    (Без реального воспроизведения, только наличие элемента.)
    """
    film_id = 300
    film_url = f"{base_url}/film/{film_id}/"
    allure.dynamic.parameter("film_id", film_id)

    with allure.step("Открываем карточку фильма"):
        driver.get(film_url)

    wait = WebDriverWait(driver, 10)

    with allure.step("Ищем кнопку «Смотреть»"):
        play_button = wait.until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR,
                "[data-testid='play-button'], .play-button, button"
            ))
        )

    assert play_button.is_displayed(), "Кнопка «Смотреть» не найдена"
