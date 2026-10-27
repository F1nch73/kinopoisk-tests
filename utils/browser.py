"""Настройки браузера Chrome для тестов."""

import os

from selenium import webdriver


def is_headless() -> bool:
    """Возвращает True, если включён headless-режим."""
    return os.getenv("HEADLESS", "").lower() in {"1", "true", "yes"}


def build_chrome_options(
    headless: bool | None = None,
) -> webdriver.ChromeOptions:
    """
    Создаёт опции Chrome.

    Если headless не задан, режим берётся из переменной окружения HEADLESS.
    """
    options = webdriver.ChromeOptions()
    if headless is None:
        headless = is_headless()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    return options
