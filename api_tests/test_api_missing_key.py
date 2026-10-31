"""Кейс KP_API_07: запрос без API-ключа."""

import allure
import requests

from config import API_SEARCH_LIMIT


@allure.feature("API: Обработка ошибок")
@allure.story("KP_API_07. Запрос без API-ключа")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("KP_API_07. Запрос без API-ключа возвращает 401")
def test_api_missing_api_key(api_base_url: str) -> None:
    """
    Запрос без заголовка X-API-KEY: сервер должен вернуть
    401 Unauthorized.
    """
    limit = API_SEARCH_LIMIT
    allure.dynamic.parameter("limit", limit)

    response = requests.get(
        f"{api_base_url}/v1.5/movie",
        params={"limit": limit},
        timeout=10,
    )

    with allure.step("Проверяем статус-код"):
        assert response.status_code == 401, (
            "Ожидался статус 401 без API-ключа, "
            f"получен {response.status_code}"
        )

    with allure.step("Проверяем тело ответа"):
        body = response.json()
        assert isinstance(body, dict), "Тело ответа не является JSON-объектом"
        assert "message" in body, (
            "В теле ответа отсутствует поле 'message'"
        )
        allure.attach(
            response.text[:500],
            name="Тело ответа (JSON)",
        )
