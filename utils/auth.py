"""Работа с cookies авторизованной сессии Кинопоиска."""

import json
import os
import time
from pathlib import Path
from urllib.parse import urlparse

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from utils.browser import build_chrome_options

# Selenium принимает только эти поля cookie.
ALLOWED_COOKIE_FIELDS = (
    "name",
    "value",
    "domain",
    "path",
    "expiry",
    "secure",
    "httpOnly",
)

DEFAULT_AUTH_COOKIES_PATH = Path(".auth") / "cookies.json"
DEFAULT_BASE_URL = "https://www.kinopoisk.ru/"

# Страница без редиректов: cookies можно добавить только в своём домене,
# а главная без сессии уводит на авторизацию Яндекса.
COOKIE_DOMAIN_PAGE = "https://www.kinopoisk.ru/robots.txt"

# Кнопка входа отображается только анонимному пользователю.
LOGIN_BUTTON_LOCATOR = (By.CSS_SELECTOR, "[data-testid='loginHeaderButton']")
HEADER_LOCATOR = (By.CSS_SELECTOR, "header")

# Cookies, по которым видно, что сессия вообще существует.
AUTH_COOKIE_NAMES = ("L", "yandex_login", "sessar", "ya_sess_id")

# Сколько ждать появления кнопки входа, прежде чем считать сессию активной.
LOGIN_BUTTON_WAIT = 3.0


def _is_kinopoisk_url(url: str) -> bool:
    """Проверяет, что адрес — Кинопоиск, а не авторизация Яндекса."""
    host = urlparse(url).netloc
    return host == "kinopoisk.ru" or host.endswith(".kinopoisk.ru")


def auth_cookies_path() -> Path:
    """Возвращает путь к файлу с cookies авторизации."""
    return Path(
        os.getenv("KINOPOISK_AUTH_COOKIES", str(DEFAULT_AUTH_COOKIES_PATH))
    )


def load_auth_cookies(path: Path | None = None) -> list[dict]:
    """
    Читает cookies авторизации из файла.

    Возвращает пустой список, если файла нет.
    """
    cookies_path = path or auth_cookies_path()
    if not cookies_path.exists():
        return []

    # utf-8-sig: файл может быть сохранён с BOM (например, PowerShell).
    data = json.loads(cookies_path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, list):
        raise ValueError(
            f"Ожидался список cookies в {cookies_path}, "
            f"получено: {type(data).__name__}"
        )
    return data


def save_auth_cookies(
    cookies: list[dict],
    path: Path | None = None,
) -> Path:
    """Сохраняет cookies авторизации в файл."""
    cookies_path = path or auth_cookies_path()
    cookies_path.parent.mkdir(parents=True, exist_ok=True)
    cookies_path.write_text(
        json.dumps(cookies, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return cookies_path


def apply_auth_cookies(
    driver: webdriver.Chrome,
    cookies: list[dict],
    errors: list[str] | None = None,
) -> int:
    """
    Добавляет cookies в браузер.

    Возвращает количество успешно добавленных cookies.
    Домен должен быть уже открыт, иначе Selenium отклонит cookies.
    Если передан список errors, в него попадают описания сбоев.
    """
    added = 0
    for cookie in cookies:
        payload = {
            key: value
            for key, value in cookie.items()
            if key in ALLOWED_COOKIE_FIELDS and value is not None
        }
        if not payload.get("name"):
            continue
        if isinstance(payload.get("expiry"), float):
            payload["expiry"] = int(payload["expiry"])

        try:
            driver.add_cookie(payload)
        except Exception as error:  # noqa: BLE001 - битые cookies пропускаем
            if errors is not None:
                errors.append(
                    f"{payload.get('name')}: "
                    f"{type(error).__name__}: {error}"
                )
            continue
        added += 1
    return added


def has_auth_cookies(cookies: list[dict]) -> bool:
    """Проверяет, что среди cookies есть признаки сессии."""
    names = {cookie.get("name") for cookie in cookies}
    return any(name in names for name in AUTH_COOKIE_NAMES)


def cookies_expired(cookies: list[dict]) -> bool:
    """
    Проверяет, истёк ли срок хранения cookies сессии.

    Cookies без срока хранения считаются действующими.
    """
    now = time.time()
    for cookie in cookies:
        if cookie.get("name") not in AUTH_COOKIE_NAMES:
            continue
        expiry = cookie.get("expiry")
        if isinstance(expiry, (int, float)) and expiry < now:
            return True
    return False


def is_authorized(
    driver: webdriver.Chrome,
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = 15,
) -> bool:
    """
    Проверяет, что браузер работает с авторизованной сессией.

    Открывает страницу и смотрит, есть ли в шапке кнопка входа.
    """
    driver.get(base_url)

    try:
        WebDriverWait(driver, timeout).until(
            ec.presence_of_element_located(HEADER_LOCATOR)
        )
    except TimeoutException:
        return False

    if driver.find_elements(*LOGIN_BUTTON_LOCATOR):
        return False

    # Кнопка входа может появиться чуть позже шапки: ждём её появления
    # явным ожиданием. Если за время ожидания кнопка так и не
    # появилась — пользователь авторизован.
    try:
        WebDriverWait(driver, LOGIN_BUTTON_WAIT).until_not(
            ec.presence_of_element_located(LOGIN_BUTTON_LOCATOR)
        )
    except TimeoutException:
        return False
    return True


def validate_auth_cookies(
    cookies: list[dict],
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = 15,
) -> bool:
    """
    Проверяет cookies в отдельном браузере.

    Возвращает True, если с этими cookies пользователь авторизован.
    """
    if not cookies or not has_auth_cookies(cookies):
        return False

    driver = webdriver.Chrome(options=build_chrome_options(headless=True))
    try:
        # Главная страница без сессии редиректит на авторизацию Яндекса,
        # где cookies применить нельзя, поэтому открываем robots.txt.
        driver.get(COOKIE_DOMAIN_PAGE)
        if apply_auth_cookies(driver, cookies) == 0:
            return False
        return is_authorized(driver, base_url, timeout)
    except Exception:  # noqa: BLE001 - сетевые сбои не должны ломать прогон
        return False
    finally:
        driver.quit()


def is_logged_in_page(driver: webdriver.Chrome) -> bool:
    """
    Проверяет авторизацию на уже открытой странице.

    В отличие от is_authorized не переходит на другой адрес.

    Требует, чтобы браузер был именно на Кинопоиске и шапка успела
    отрисоваться: иначе отсутствие кнопки входа означает лишь, что
    страница ещё грузится или открыт домен авторизации Яндекса.
    """
    if not _is_kinopoisk_url(driver.current_url):
        return False

    if not driver.find_elements(*HEADER_LOCATOR):
        return False

    return not driver.find_elements(*LOGIN_BUTTON_LOCATOR)


def interactive_login(
    base_url: str = DEFAULT_BASE_URL,
    timeout: float | None = None,
) -> list[dict]:
    """
    Открывает браузер и ждёт, пока пользователь войдёт в аккаунт.

    Как только вход выполнен, cookies сохраняются в файл.
    Возвращает cookies или пустой список, если вход не выполнен
    либо cookies не авторизуют пользователя.
    """
    if timeout is None:
        timeout = float(os.getenv("KINOPOISK_AUTH_TIMEOUT", "300"))

    driver = webdriver.Chrome(options=build_chrome_options(headless=False))
    try:
        driver.get(base_url)
        print("=" * 70, flush=True)
        print("Нужна авторизация на Кинопоиске.", flush=True)
        print(
            "Войдите в аккаунт в открытом окне браузера — "
            f"тесты продолжат сами (жду до {int(timeout)} с).",
            flush=True,
        )
        print("=" * 70, flush=True)

        if not _wait_for_login(driver, timeout):
            print("Вход не выполнен: время ожидания истекло.", flush=True)
            return []

        cookies = driver.get_cookies()
        if not cookies:
            print("Cookies не найдены: вход не выполнен.", flush=True)
            return []

        if not has_auth_cookies(cookies):
            print(
                "Среди cookies нет признаков сессии "
                f"({', '.join(AUTH_COOKIE_NAMES)}). "
                "Вход ещё не завершён — дождитесь возврата на Кинопоиск.",
                flush=True,
            )
            return []

        # Проверяем cookies в этом же браузере после очистки сессии.
        driver.delete_all_cookies()

        # После очистки Кинопоиск может увести на авторизацию Яндекса:
        # в этом домене cookies применить нельзя, поэтому возвращаемся.
        if not _ensure_on_kinopoisk(driver):
            print(
                "Не удалось вернуться на Кинопоиск после очистки cookies. "
                f"Текущий адрес: {driver.current_url}",
                flush=True,
            )
            return []

        errors: list[str] = []
        added = apply_auth_cookies(driver, cookies, errors)
        if added == 0:
            print("Не удалось применить cookies.", flush=True)
            print(f"  адрес: {driver.current_url}", flush=True)
            domains = sorted({cookie.get("domain") for cookie in cookies})
            print(f"  домены cookies: {domains}", flush=True)
            print(f"  cookies: {len(cookies)}, добавлено: {added}", flush=True)
            for message in errors[:5]:
                print(f"  - {message}", flush=True)
            return []

        driver.refresh()
        if not is_authorized(driver, base_url):
            print(
                "Проверка не пройдена: cookies не авторизуют пользователя.",
                flush=True,
            )
            return []
    finally:
        driver.quit()

    path = save_auth_cookies(cookies)
    print(f"Сохранено cookies: {len(cookies)} -> {path}", flush=True)
    return cookies


def _ensure_on_kinopoisk(
    driver: webdriver.Chrome,
    timeout: float = 15,
) -> bool:
    """
    Возвращает браузер на Кинопоиск, если его увело на авторизацию.

    Cookies можно добавить только в том домене, которому они принадлежат.
    Главная страница без сессии уводит на авторизацию Яндекса, поэтому
    открываем нейтральный адрес robots.txt, который не редиректит.
    """
    driver.get(COOKIE_DOMAIN_PAGE)

    def on_kinopoisk(current_driver: webdriver.Chrome) -> bool:
        """Проверяет адрес и при необходимости повторяет переход."""
        if _is_kinopoisk_url(current_driver.current_url):
            return True
        current_driver.get(COOKIE_DOMAIN_PAGE)
        return False

    try:
        WebDriverWait(driver, timeout, poll_frequency=1).until(
            on_kinopoisk
        )
    except TimeoutException:
        pass

    return _is_kinopoisk_url(driver.current_url)


def _wait_for_login(
    driver: webdriver.Chrome,
    timeout: float,
    poll: float = 2.0,
) -> bool:
    """Ждёт, пока пользователь авторизуется в открытом браузере."""
    def logged_in(current_driver: webdriver.Chrome) -> bool:
        try:
            return is_logged_in_page(current_driver)
        except Exception:  # noqa: BLE001 - страница может перезагружаться
            return False

    try:
        WebDriverWait(driver, timeout, poll_frequency=poll).until(
            logged_in
        )
        return True
    except TimeoutException:
        return False


def refresh_auth_cookies(base_url: str = DEFAULT_BASE_URL) -> list[dict]:
    """
    Возвращает рабочие cookies авторизации.

    Сначала проверяет файл, при необходимости запускает ручной вход.
    """
    cookies = load_auth_cookies()
    if cookies and not cookies_expired(cookies):
        if validate_auth_cookies(cookies, base_url):
            print("[auth] cookies из файла действуют.", flush=True)
            return cookies
        print("[auth] cookies из файла больше не авторизуют.", flush=True)

    print("[auth] запускаем вход в аккаунт.", flush=True)
    return interactive_login(base_url)
