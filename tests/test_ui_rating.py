import re

import allure
import pytest

from selenium.webdriver.remote.webdriver import WebDriver

from config import FILM_ID_RATING, FILM_ID_SEARCH, USER_RATING_VALUE
from pages.film_page import FilmPage
from pages.user_ratings_page import UserRatingsPage

# Рейтинг Кинопоиска — число от 0 до 10 с одной цифрой после точки: «6.3».
RATING_PATTERN = re.compile(r"^\d{1,2}(\.\d)?$")


@pytest.mark.smoke
@allure.feature("UI: Карточка фильма")
@allure.story("Рейтинг")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Блок рейтинга присутствует на карточке фильма")
def test_ui_film_rating_block_exists(
    driver: WebDriver,
    base_url: str,
) -> None:
    """Проверяет, что на карточке фильма отображается корректный рейтинг."""
    film_id = FILM_ID_RATING
    film_url = f"{base_url}/film/{film_id}/"
    allure.dynamic.parameter("film_id", film_id)

    film_page = FilmPage(driver, film_url)
    film_page.open()

    with allure.step("Читаем рейтинг фильма"):
        rating = film_page.get_rating()
        allure.attach(
            rating,
            name="Значение рейтинга",
        )

    assert RATING_PATTERN.match(rating), (
        f"Рейтинг «{rating}» не похож на число от 0 до 10"
    )
    assert 0 <= float(rating) <= 10, (
        f"Рейтинг {rating} вне допустимого диапазона 0..10"
    )


@allure.feature("UI: Карточка фильма")
@allure.story("Личная оценка пользователя")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title(
    "Авторизованный пользователь ставит оценку и видит её в профиле"
)
def test_ui_user_can_rate_film(
    authorized_driver: WebDriver,
    base_url: str,
) -> None:
    """
    UI-тест: авторизованный пользователь ставит оценку фильму.

    Проверяется весь сценарий тест-кейса:
      1. на карточке есть блок с рейтингом/звёздами;
      2. пользователь выбирает оценку;
      3. оценка успешно сохранена и видна на карточке;
      4. личный рейтинг пользователя отображается в разделе «Оценки».

    Требует cookies, сохранённые save_auth_cookies.py.
    """
    film_id = FILM_ID_SEARCH
    film_url = f"{base_url}/film/{film_id}/"
    allure.dynamic.parameter("film_id", film_id)
    allure.dynamic.parameter("rating", USER_RATING_VALUE)

    film_page = FilmPage(authorized_driver, film_url)
    film_page.open()
    film_page.wait_for_details()

    with allure.step("Проверяем, что сессия авторизована"):
        assert film_page.is_logged_in(), (
            "Cookies не авторизуют пользователя: "
            "повторите python save_auth_cookies.py"
        )

    # Запоминаем исходную оценку, чтобы вернуть её в конце теста.
    film_page.wait_rating_ui_ready()
    initial_rating = film_page.get_user_rating()
    allure.attach(
        initial_rating or "(оценки нет)",
        name="Исходная оценка",
    )

    try:
        with allure.step("Готовим карточку: снимаем текущую оценку"):
            if initial_rating:
                film_page.remove_rating()
            assert not film_page.get_user_rating(), (
                "Не удалось снять оценку перед проверкой: "
                f"осталась {film_page.get_user_rating()!r}"
            )

        with allure.step("Проверяем блок с рейтингом/звёздами"):
            film_page.wait_rating_widget()
            allure.attach(
                "Виджет с 10 звёздами отображается",
                name="Блок рейтинга",
            )

        with allure.step(f"Выбираем оценку {USER_RATING_VALUE} из 10"):
            film_page.rate_film(USER_RATING_VALUE)
            allure.attach(
                f"Звезда {USER_RATING_VALUE} отмечена, "
                "оценка подтверждена в интерфейсе",
                name="Выбранная оценка",
            )

        with allure.step("Проверяем оценку на карточке после перезагрузки"):
            authorized_driver.refresh()
            film_page.wait_for_details()
            # После перезагрузки страница может краткое время показывать
            # звёзды, пока не подтянет сохранённую оценку. Ждём именно
            # кнопку с числом, а не любое состояние блока.
            film_page.wait_rating_confirmed(USER_RATING_VALUE, timeout=30)
            saved_rating = film_page.get_user_rating()
            allure.attach(
                saved_rating,
                name="Оценка после перезагрузки",
            )
            assert saved_rating == str(USER_RATING_VALUE), (
                f"Оценка не сохранилась: ожидалась {USER_RATING_VALUE}, "
                f"получено {saved_rating!r}"
            )

        with allure.step(
            "Проверяем оценку в разделе «Мои оценки» в профиле"
        ):
            ratings_page = UserRatingsPage(authorized_driver, base_url)
            ratings_page.open()
            profile_rating = ratings_page.get_film_rating(film_id)
            allure.attach(
                profile_rating,
                name="Оценка в профиле",
            )
            assert profile_rating == str(USER_RATING_VALUE), (
                f"В профиле оценка {profile_rating!r}, "
                f"ожидалась {USER_RATING_VALUE}"
            )
    finally:
        with allure.step("Возвращаем исходную оценку"):
            film_page.open()
            film_page.wait_for_details()
            if initial_rating:
                film_page.rate_film(int(initial_rating))
            else:
                film_page.remove_rating()
