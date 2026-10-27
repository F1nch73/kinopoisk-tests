# tests/test_ui_actor.py
import allure
from selenium.webdriver.remote.webdriver import WebDriver

from config import FILM_NAME_AVAILABLE
from pages.actor_page import ActorPage
from pages.film_page import FilmPage
from pages.main_page import MainPage
from pages.search_results_page import SearchResultsPage


@allure.feature("UI: Страница актёра")
@allure.story("Просмотр страницы актёра из карточки фильма")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Открытие страницы актёра и проверка всех полей")
def test_ui_open_actor_page_and_check_fields(
        driver: WebDriver, base_url: str) -> None:
    """
    UI-тест:
      Поиск фильма → открытие карточки → клик по первому актёру
      → проверка страницы актёра:
        - имя
        - URL (/name/...)
        - наличие фильмографии
        - возможность перехода к фильму
    """
    query = FILM_NAME_AVAILABLE
    allure.dynamic.parameter("query", query)

    main_page = MainPage(driver, base_url)
    main_page.open()
    main_page.search(query)

    results_page = SearchResultsPage(driver, base_url)

    with allure.step("Кликаем по карточке фильма в выдаче"):
        card = results_page.get_film_card_by_title(query)
        results_page.click_film_card(card)
        allure.attach(
            driver.current_url,
            name="URL открытой карточки",
            attachment_type=allure.attachment_type.URI_LIST,
        )

    film_page = FilmPage(driver, driver.current_url)
    film_page.wait_for_details()

    with allure.step("Переходим на страницу первого актёра из главных ролей"):
        film_page.open_first_cast_member()

    actor_page = ActorPage(driver, driver.current_url)

    with allure.step("Проверяем, что открылась страница актёра"):
        current_url = driver.current_url
        assert "/name/" in current_url, (
            f"Ожидалась страница актёра, получено: {current_url}"
        )
        allure.attach(current_url, name="URL страницы актёра",
                      attachment_type=allure.attachment_type.URI_LIST)

    with allure.step("Ждём загрузки страницы актёра"):
        actor_page.wait_loaded()

    with allure.step("Проверяем имя актёра"):
        name = actor_page.get_name()
        allure.attach(name, name="Имя актёра")
        assert name, "На странице актёра не найдено имя"
        assert len(name.split()) >= 2, (
            f"Ожидалось имя из минимум двух слов, получено: «{name}»"
        )

    with allure.step("Проверяем наличие фильмографии"):
        has_films = actor_page.has_filmography()
        allure.attach(str(has_films), name="Наличие фильмографии")
        assert has_films, (
            "На странице актёра отсутствует фильмография "
            "(не найдено ссылок на фильмы)"
        )

    with allure.step("Переходим к первому фильму из фильмографии"):
        actor_page.open_first_film()

    with allure.step("Проверяем, что открылась страница фильма"):
        film_url = driver.current_url
        allure.attach(film_url, name="URL страницы фильма",
                      attachment_type=allure.attachment_type.URI_LIST)
        assert "/film/" in film_url, (
            f"Ожидался переход к фильму, получено: {film_url}"
        )
