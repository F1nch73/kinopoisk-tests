"""
Захват cookies авторизованной сессии Кинопоиска вручную.

Запуск:
    python save_auth_cookies.py

Откроется окно браузера: войдите в аккаунт Кинопоиска
(телефон, QR-код или сохранённый профиль). Скрипт сам заметит
завершение входа и сохранит cookies в .auth/cookies.json.
По умолчанию ждёт до 300 секунд (KINOPOISK_AUTH_TIMEOUT).

Обычно этот скрипт не нужен: тесты сами проверяют cookies и
запускают вход, если они протухли.
"""

import sys

from utils.auth import DEFAULT_BASE_URL, auth_cookies_path, interactive_login


def main() -> int:
    cookies = interactive_login(DEFAULT_BASE_URL)
    if not cookies:
        print("Не удалось сохранить cookies авторизации.")
        return 1

    print(f"Готово. Cookies записаны в {auth_cookies_path()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
