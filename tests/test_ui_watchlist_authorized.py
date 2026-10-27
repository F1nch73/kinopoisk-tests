import allure

from selenium.webdriver.remote.webdriver import WebDriver

from config import FILM_ID_SEARCH
from pages.film_page import FilmPage
from pages.watchlist_page import WatchlistPage


@allure.feature("UI: Список ожидания")
@allure.story("Добавление фильма авторизованным пользователем")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title(
    "Авторизованный пользователь добавляет фильм в «Буду смотреть»"
)
def test_ui_add_film_to_watchlist_with_auth(
    authorized_driver: WebDriver,
    base_url: str,
) -> None:
    """
    UI-тест: добавление фильма в «Буду смотреть» авторизованным
    пользователем.

    Проверяется весь сценарий тест-кейса:
      1. фильм добавляется в список;
      2. кнопка визуально меняет состояние;
      3. фильм появляется в разделе «Моё кино» → «Буду смотреть».

    Требует cookies, сохранённые save_auth_cookies.py.
    """
    film_id = FILM_ID_SEARCH
    film_url = f"{base_url}/film/{film_id}/"
    allure.dynamic.parameter("film_id", film_id)

    film_page = FilmPage(authorized_driver, film_url)
    film_page.open()

    with allure.step("Проверяем, что сессия авторизована"):
        assert film_page.is_logged_in(), (
            "Cookies не авторизуют пользователя: "
            "повторите python save_auth_cookies.py"
        )

    # Исходное состояние запоминаем, чтобы вернуть его после теста.
    initial_state = film_page.is_in_watchlist()
    allure.attach(
        f"Исходное состояние: в списке = {initial_state}",
        name="До теста",
    )

    try:
        with allure.step("Готовим фильм: убираем его из списка"):
            film_page.set_watchlist_state(False)
            assert not film_page.is_in_watchlist(), (
                "Не удалось убрать фильм из списка перед проверкой добавления"
            )

        with allure.step("Читаем состояние кнопки до нажатия"):
            state_before = film_page.get_watchlist_visual_state()
            allure.attach(
                "\n".join(
                    f"{key}: {value}"
                    for key, value in state_before.items()
                ),
                name="Кнопка до нажатия",
            )
            assert state_before["pressed"] == "false", (
                "Перед добавлением кнопка должна быть неактивной: "
                f"aria-pressed={state_before['pressed']}"
            )

        with allure.step("Нажимаем «Буду смотреть»"):
            film_page.wait_watchlist_ready()
            film_page.click_watchlist_button()

        with allure.step(
            "Проверяем визуальное подтверждение изменения кнопки"
        ):
            state_after = film_page.wait_watchlist_visual_change(state_before)
            allure.attach(
                "\n".join(
                    f"{key}: {value}"
                    for key, value in state_after.items()
                ),
                name="Кнопка после нажатия",
            )

            assert state_after != state_before, (
                "Внешний вид кнопки «Буду смотреть» не изменился после "
                f"нажатия: {state_after}"
            )
            assert state_after["pressed"] == "true", (
                "Кнопка не перешла в состояние «в списке»: "
                f"aria-pressed={state_after['pressed']}"
            )

        # Интерфейс меняет кнопку оптимистично, а запрос на сервер
        # уходит асинхронно: без ожидания перезагрузка обрывает его.
        with allure.step("Дожидаемся сохранения фильма на сервере"):
            film_page.set_watchlist_state(True)

        with allure.step("Проверяем, что фильм сохранился в списке"):
            film_page.open()
            assert film_page.is_in_watchlist(), (
                "После перезагрузки карточки фильм не числится "
                "в «Буду смотреть»"
            )

        with allure.step(
            "Проверяем, что фильм доступен в разделе «Моё кино»"
        ):
            watchlist_page = WatchlistPage(authorized_driver, base_url)
            watchlist_page.open_section()

            assert watchlist_page.has_film(film_id), (
                "Фильм отсутствует в разделе «Буду смотреть». "
                f"Найдены: {watchlist_page.get_film_titles()[:20]}. "
                f"Адрес: {authorized_driver.current_url}"
            )
    finally:
        with allure.step("Возвращаем исходное состояние фильма"):
            film_page.open()
            film_page.set_watchlist_state(initial_state)
