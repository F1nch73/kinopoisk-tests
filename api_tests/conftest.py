"""Автосбор HTTP-трафика API в Allure-отчёт."""
import json

import allure
import pytest
import requests

MAX_BODY_LENGTH = 20000


def _dump_json(payload) -> str:
    try:
        return json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    except TypeError:
        return str(payload)


def _truncate(body: str) -> str:
    if len(body) <= MAX_BODY_LENGTH:
        return body
    return f"{body[:MAX_BODY_LENGTH]}\n... обрезано (всего {len(body)} символов)"


def _safe_headers(headers):
    """Возвращает копию заголовков с маскированным API-ключом."""
    masked = dict(headers or {})
    for key in list(masked):
        if "api-key" in key.lower() or "authorization" in key.lower():
            masked[key] = "***"
    return masked


@pytest.fixture(autouse=True)
def attach_api_traffic_to_allure():
    """
    Перехватывает HTTP-запросы через requests.Session и крепит
    тело запроса и ответ к Allure-отчёту.

    Позволяет в любой момент увидеть запрос/ответ в отчёте
    без изменения кода самих тестов.
    """
    original_request = requests.Session.request

    def request(self, method, url, *args, **kwargs):
        request_headers = _safe_headers(kwargs.get("headers"))
        request_params = kwargs.get("params")
        request_json = kwargs.get("json")
        request_body = kwargs.get("data")
        request_timeout = kwargs.get("timeout")

        with allure.step(f"{method.upper()} {url}"):
            # Запрос
            request_info = {
                "method": method.upper(),
                "url": url,
                "params": request_params,
                "headers": request_headers,
                "body": _dump_json(request_json or request_body),
                "timeout": request_timeout,
            }
            allure.attach(
                _truncate(_dump_json(request_info)),
                "Запрос",
                attachment_type=allure.attachment_type.JSON,
            )

            response = original_request(self, method, url, *args, **kwargs)

            # Ответ
            response_info = {
                "status_code": response.status_code,
                "headers": _safe_headers(dict(response.headers)),
                "elapsed_ms": response.elapsed.total_seconds() * 1000,
            }
            allure.attach(
                _truncate(_dump_json(response_info)),
                "Ответ (метаданные)",
                attachment_type=allure.attachment_type.JSON,
            )
            allure.attach(
                _truncate(response.text),
                f"Ответ ({response.status_code})",
                attachment_type=allure.attachment_type.JSON,
            )

        return response

    requests.Session.request = request
    try:
        yield
    finally:
        requests.Session.request = original_request
