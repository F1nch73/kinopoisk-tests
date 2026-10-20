import os
import sys
from pathlib import Path
from typing import Iterator

import allure
import pytest
import selenium
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver

try:
    from dotenv import load_dotenv
except ImportError:
    pass
else:
    load_dotenv(override=True)

DEFAULT_BASE_URL = "https://www.kinopoisk.ru"
DEFAULT_API_BASE_URL = "https://api.poiskkino.dev"
API_KEY = os.getenv("API_KEY", "")


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
    options = webdriver.ChromeOptions()
    if os.getenv("HEADLESS", "").lower() in {"1", "true", "yes"}:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    return options


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
