"""Кейс KP_API_04: невалидный API-ключ."""

import allure
import requests

from config import API_FILM_ID, API_INVALID_KEY


@allure.feature("API: Обработка ошибок")
@allure.story("KP_API_04. Невалидный API-ключ")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("KP_API_04. Невалидный API-ключ возвращает 401")
def test_api_invalid_api_key(api_base_url: str) -> None:
    """
    Запрос с невалидным API-ключом: сервер должен отказать
    в авторизации со статусом 401.
    """
    film_id = API_FILM_ID
    allure.dynamic.parameter("film_id", film_id)

    headers = {
        "X-API-KEY": API_INVALID_KEY,
        "accept": "application/json",
    }

    response = requests.get(
        f"{api_base_url}/v1.5/movie/{film_id}",
        headers=headers,
        timeout=10,
    )

    with allure.step("Проверяем статус-код"):
        assert response.status_code == 401, (
            "Ожидался статус 401 при невалидном ключе, "
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
