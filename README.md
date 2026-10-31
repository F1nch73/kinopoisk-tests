# Kinopoisk Tests

Набор автотестов для [Кинопоиска](https://www.kinopoisk.ru): UI-тесты и API-тесты.

## Стек

- **Python 3.10+**
- **Selenium 4** — UI-автоматизация
- **pytest** — фреймворк для запуска тестов
- **Allure** — отчёты о тестах
- **requests** — HTTP-клиент для API-тестов
- **Page Object** — паттерн организации UI-тестов

## Структура

```
├── tests/                # UI-тесты (Selenium)
│   ├── test_ui_search.py
│   ├── test_ui_film_card.py
│   ├── test_ui_rating.py             # рейтинг фильма и оценка пользователя
│   ├── test_ui_actor.py              # страница актёра и фильмография
│   └── test_ui_watchlist_authorized.py # добавление в список и проверка раздела
├── api_tests/            # API-тесты (requests)
│   ├── test_api_film.py
│   ├── test_api_search.py
│   ├── test_api_genre.py
│   ├── test_api_year.py
│   ├── test_api_seasons.py
│   ├── test_api_invalid_key.py
│   └── test_api_missing_key.py
├── pages/                # Page Object
│   ├── base_page.py
│   ├── main_page.py
│   ├── film_page.py
│   ├── actor_page.py      # страница актёра /name/ с фильмографией
│   ├── search_results_page.py
│   ├── watchlist_page.py    # раздел «Моё кино» → «Буду смотреть»
│   └── user_ratings_page.py # раздел «Моё кино» → «Оценки»
├── utils/                # Вспомогательные модули
│   ├── auth.py           # cookies авторизованной сессии
│   └── browser.py        # опции браузера (headless-режим)
├── save_auth_cookies.py  # одноразовый захват cookies (запуск вручную)
├── config.py             # тестовые данные: ID фильмов, названия, оценка
├── conftest.py           # Общие фикстуры (driver, API-клиент)
├── pytest.ini            # Конфигурация pytest
├── .env.example          # образец файла окружения
└── requirements.txt
```

## Установка

1. Клонируйте репозиторий проекта и перейдите в его каталог:
   ```bash
   git clone <URL репозитория> kinopoisk_tests
   cd kinopoisk_tests
   ```

2. Создайте виртуальное окружение и установите зависимости:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate        # Windows
   source .venv/bin/activate     # macOS / Linux
   pip install -r requirements.txt
   ```

3. Создайте файл `.env` в корне проекта (образец — `.env.example`):
   ```env
   KINOPOISK_API_KEY=ваш_ключ_api
   ```

   Получить ключ можно на [kinopoisk.dev](https://kinopoisk.dev).

## Запуск

### Все тесты
```bash
pytest
```

### Только UI-тесты
```bash
pytest tests/
```

### Только API-тесты
```bash
pytest api_tests/
```

### Smoke-набор (по метке)
```bash
pytest -m smoke
```

В smoke-набор входят базовые проверки: получение карточки фильма и поиск
через API, поиск и открытие карточки фильма в UI. Остальные тесты запускаются
только полным прогоном.### Headless-режим (без открытия браузера)
```bash
set HEADLESS=1        # Windows
export HEADLESS=1     # macOS / Linux
pytest
```

### Генерация Allure-отчёта
```bash
pytest --alluredir=allure-results
allure serve allure-results
```

## Тесты с авторизацией

Часть функциональности Кинопоиска (например, «Буду смотреть») доступна
только авторизованному пользователю. Вход выполняется через Яндекс ID,
где регистрация возможна **только по номеру телефона**, поэтому
автотесты не создают аккаунты, а переиспользуют cookies реальной сессии.

### Автоматическое обновление cookies

Перед прогоном UI-тестов сессионная фикстура `prepare_auth` проверяет
cookies из `.auth/cookies.json`:

- cookies действуют — браузер не открывается, тесты идут сразу;
- файла нет или сессия истекла — открывается браузер, вы входите
  в аккаунт, cookies сохраняются, и прогон продолжается без
  перезапуска тестов;
- обновить нельзя (`HEADLESS=1` или `KINOPOISK_AUTO_LOGIN=0`) — тесты
  с авторизацией помечаются `skipped` с подсказкой.

Проверка выполняется один раз за прогон и только если в нём есть тесты,
которым нужна авторизация.

Принудительно переполучить cookies:

```bash
pytest tests/ --refresh-auth
```

Сохранить cookies без запуска тестов:

```bash
python save_auth_cookies.py
```

Файл `.auth/cookies.json` находится в `.gitignore` и не попадает
в репозиторий. Тесты, требующие авторизации, используют фикстуру
`authorized_driver`.

## Переменные окружения

| Переменная | По умолчанию | Описание |
|---|---|---|
| `KINOPOISK_API_KEY` | — | Ключ API (обязательно) |
| `KINOPOISK_BASE_URL` | `https://www.kinopoisk.ru` | Адрес сайта для UI-тестов |
| `KINOPOISK_API_BASE_URL` | `https://api.poiskkino.dev` | Базовый URL API |
| `HEADLESS` | `0` | Запуск браузера в headless-режиме |
| `KINOPOISK_AUTH_COOKIES` | `.auth/cookies.json` | Путь к файлу с cookies авторизации |
| `KINOPOISK_AUTO_LOGIN` | `1` | Разрешить открывать браузер для входа при протухших cookies |
| `KINOPOISK_AUTH_TIMEOUT` | `300` | Сколько секунд ждать входа в аккаунт |

## Allure-отчёт

Каждый тест помечен Allure-метками (feature, story, severity, title). При падении UI-теста автоматически прикрепляются скриншот и URL страницы.

## Лицензия

MIT
