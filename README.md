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
│   ├── test_ui_rating.py
│   ├── test_ui_playback.py
│   └── test_ui_watchlist.py
├── api_tests/            # API-тесты (requests)
│   ├── test_api_film.py
│   ├── test_api_search.py
│   ├── test_api_genre.py
│   ├── test_api_year.py
│   ├── test_api_seasons.py
│   └── test_api_invalid_key.py
├── pages/                # Page Object
│   ├── base_page.py
│   ├── main_page.py
│   ├── film_page.py
│   └── search_results_page.py
├── conftest.py           # Общие фикстуры (driver, API-клиент)
├── pytest.ini            # Конфигурация pytest
└── requirements.txt
```

## Установка

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/<username>/kinopoisk-tests.git
   cd kinopoisk-tests
   ```

2. Создайте виртуальное окружение и установите зависимости:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate        # Windows
   source .venv/bin/activate     # macOS / Linux
   pip install -r requirements.txt
   ```

3. Создайте файл `.env` в корне проекта:
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

### С фильтрами по тегу
```bash
pytest -m "smoke"
```

### Headless-режим (без открытия браузера)
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

## Переменные окружения

| Переменная | По умолчанию | Описание |
|---|---|---|
| `KINOPOISK_API_KEY` | — | Ключ API (обязательно) |
| `KINOPOISK_BASE_URL` | `https://www.kinopoisk.ru` | Адрес сайта для UI-тестов |
| `KINOPOISK_API_BASE_URL` | `https://api.poiskkino.dev` | Базовый URL API |
| `HEADLESS` | `0` | Запуск браузера в headless-режиме |

## Allure-отчёт

Каждый тест помечен Allure-метками (feature, story, severity, title). При падении UI-теста автоматически прикрепляются скриншот и URL страницы.

