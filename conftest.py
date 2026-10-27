import os
import sys
from pathlib import Path
from typing import Iterator

import allure
import pytest
import selenium
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver

from utils.auth import (
    apply_auth_cookies,
    auth_cookies_path,
    cookies_expired,
    interactive_login,
    load_auth_cookies,
    validate_auth_cookies,
)
from utils.browser import build_chrome_options, is_headless

try:
    from dotenv import load_dotenv
except ImportError:
    pass
else:
    load_dotenv(override=True)

DEFAULT_BASE_URL = "https://www.kinopoisk.ru"
DEFAULT_API_BASE_URL = "https://api.poiskkino.dev"
API_KEY = os.getenv("API_KEY", "")

# Кэш cookies на сессию: проверяем и обновляем их один раз за прогон.
_AUTH_CACHE: dict[str, list[dict] | None] = {"cookies": None}


def pytest_addoption(parser: pytest.Parser) -> None:
    """Добавляет опцию принудительного обновления cookies."""
    parser.addoption(
        "--refresh-auth",
        action="store_true",
        default=False,
        help="заново получить cookies авторизации перед прогоном",
    )


@pytest.fixture(scope="session")
def base_url() -> str:
    """Базовый адрес сайта для UI-тестов."""
    return os.getenv("KINOPOISK_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


@pytest.fixture(scope="session")
def api_base_url() -> str:
    """Базовый адрес API для API-тестов."""
    return os.getenv(
        "KINOPOISK_API_BASE_URL",
        DEFAULT_API_BASE_URL,
    ).rstrip("/")


@pytest.fixture(scope="session")
def api_key() -> str:
    """Ключ Kinopoisk API (берётся из переменной окружения)."""
    key = os.getenv("KINOPOISK_API_KEY") or os.getenv("API_KEY", "")
    if not key:
        pytest.skip("Переменная окружения KINOPOISK_API_KEY не задана")
    return key


@pytest.fixture(scope="session", autouse=True)
def allure_environment(request: pytest.FixtureRequest) -> None:
    """
    Записывает environment.properties в папку Allure-результатов.

    Блок "Environments" в отчёте показывает версии окружения и
    используемые адреса, чтобы отчёт был воспроизводим.
    """
    results_dir = getattr(request.config.option, "allure_report_dir", None)
    if not results_dir:
        return

    Path(results_dir).mkdir(parents=True, exist_ok=True)

    environment = {
        "Python": sys.version.split()[0],
        "Pytest": pytest.__version__,
        "Selenium": selenium.__version__,
        "UI_Base_URL": os.getenv("KINOPOISK_BASE_URL", DEFAULT_BASE_URL),
        "API_Base_URL": os.getenv(
            "KINOPOISK_API_BASE_URL",
            DEFAULT_API_BASE_URL,
        ),
        "Headless": os.getenv("HEADLESS", "0"),
        "OS": sys.platform,
    }

    content = "\n".join(f"{key}={value}" for key, value in environment.items())
    (Path(results_dir) / "environment.properties").write_text(
        content,
        encoding="utf-8",
    )


def _build_chrome_options() -> webdriver.ChromeOptions:
    """Опции Chrome для тестов (режим берётся из HEADLESS)."""
    return build_chrome_options()


@pytest.fixture
def driver() -> Iterator[WebDriver]:
    """Драйвер Chrome: создаётся на тест и закрывается после него."""
    web_driver = webdriver.Chrome(options=_build_chrome_options())
    allure.dynamic.parameter(
        "browser",
        f"{web_driver.capabilities.get('browserName', 'unknown')} "
        f"{web_driver.capabilities.get('browserVersion', '')}".strip(),
    )
    try:
        yield web_driver
    finally:
        web_driver.quit()


def _session_needs_auth(items: list[pytest.Item]) -> bool:
    """Проверяет, есть ли в прогоне тесты с авторизацией."""
    return any(
        "authorized_driver" in getattr(item, "fixturenames", ())
        for item in items
    )


def _can_login_interactively() -> bool:
    """
    Проверяет, можно ли открыть браузер для входа.

    Вход невозможен в headless-режиме и если он отключён
    переменной окружения KINOPOISK_AUTO_LOGIN=0.
    """
    if os.getenv("KINOPOISK_AUTO_LOGIN", "1").lower() in {"0", "false", "no"}:
        return False
    return not is_headless()


def _prepare_auth_cookies(
    config: pytest.Config,
    base_url: str,
) -> list[dict]:
    """
    Готовит cookies авторизации один раз за прогон.

    Если cookies в файле ещё действуют, берём их. Иначе запускаем
    вход в браузере и сохраняем новые cookies.
    """
    if _AUTH_CACHE["cookies"] is not None:
        return _AUTH_CACHE["cookies"]

    force_refresh = bool(config.getoption("refresh_auth", False))
    cookies = [] if force_refresh else load_auth_cookies()

    if cookies and not cookies_expired(cookies):
        if validate_auth_cookies(cookies, base_url):
            print(
                f"[auth] используем cookies из {auth_cookies_path()}",
                flush=True,
            )
            _AUTH_CACHE["cookies"] = cookies
            return cookies
        print("[auth] cookies из файла больше не действуют.", flush=True)
    elif cookies:
        print("[auth] срок действия cookies истёк.", flush=True)

    if not _can_login_interactively():
        print(
            "[auth] cookies нужно обновить вручную: включён HEADLESS "
            "или автовход отключён (KINOPOISK_AUTO_LOGIN=0). "
            "Запустите python save_auth_cookies.py",
            flush=True,
        )
        _AUTH_CACHE["cookies"] = []
        return []

    _AUTH_CACHE["cookies"] = interactive_login(base_url)
    return _AUTH_CACHE["cookies"]


@pytest.fixture(scope="session", autouse=True)
def prepare_auth(
    request: pytest.FixtureRequest,
    base_url: str,
) -> None:
    """
    Обновляет cookies до запуска UI-тестов, которым нужна авторизация.

    Фикстура ничего не делает, если таких тестов в прогоне нет.
    """
    if not _session_needs_auth(request.session.items):
        return

    _prepare_auth_cookies(request.config, base_url)


@pytest.fixture(scope="session")
def auth_cookies(
    request: pytest.FixtureRequest,
    base_url: str,
) -> list[dict]:
    """
    Cookies авторизованной сессии Кинопоиска.

    Перед использованием cookies проверяются: при необходимости
    выполняется вход в браузере и файл перезаписывается.
    """
    cookies = _prepare_auth_cookies(request.config, base_url)
    if not cookies:
        pytest.skip(
            "Нет действующих cookies авторизации. Выполните: "
            "python save_auth_cookies.py "
            f"(файл: {auth_cookies_path()})"
        )
    return cookies


@pytest.fixture
def authorized_driver(
    driver: WebDriver,
    auth_cookies: list[dict],
    base_url: str,
) -> Iterator[WebDriver]:
    """Драйвер с подставленными cookies авторизованной сессии."""
    driver.get(base_url)
    added = apply_auth_cookies(driver, auth_cookies)
    if added == 0:
        pytest.skip("Не удалось применить cookies авторизации")

    driver.refresh()
    yield driver


def _attach_driver_state(web_driver: WebDriver, stage: str) -> None:
    """Прикрепляет скриншот и адрес страницы к Allure-отчёту."""
    try:
        allure.attach(
            web_driver.get_screenshot_as_png(),
            name=f"Скриншот ({stage})",
            attachment_type=allure.attachment_type.PNG,
        )
        allure.attach(
            web_driver.current_url,
            name=f"URL ({stage})",
            attachment_type=allure.attachment_type.URI_LIST,
        )
    except Exception:  # noqa: BLE001 - отчёт не должен ломать прогон
        return


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item,
    call: pytest.CallInfo,
):
    """Дополняет падение UI-теста скриншотом браузера."""
    report = yield

    if report.passed:
        return report

    funcargs = getattr(item, "funcargs", {})
    web_driver = funcargs.get("driver")
    if web_driver is not None:
        _attach_driver_state(web_driver, report.when)

    return report
