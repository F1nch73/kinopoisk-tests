import allure
import requests


@allure.feature("API: Обработка ошибок")
@allure.story("Несуществующий ID фильма")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Запрос фильма с несуществующим ID возвращает 4xx")
def test_api_get_film_with_invalid_id(
    api_base_url: str,
    api_key: str,
) -> None:
    """
    API-тест: Запрос информации о фильме с несуществующим ID.

    Ожидается клиентская ошибка 4xx.
    """
    invalid_film_id = 999_999_999
    allure.dynamic.parameter("invalid_film_id", invalid_film_id)
    url = f"{api_base_url}/v1.5/movie/{invalid_film_id}"
    headers = {
        "X-API-KEY": api_key,
        "accept": "application/json",
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=10,
    )

    assert 400 <= response.status_code < 500, (
        f"Ожидался статус 4xx, получен {response.status_code}"
    )


@allure.feature("API: Обработка ошибок")
@allure.story("Невалидный API-ключ")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Запрос с невалидным API-ключом возвращает 401/403")
def test_api_invalid_api_key(api_base_url: str) -> None:
    """
    API-тест: Запрос с невалидным API-ключом.

    Ожидается отказ в авторизации.
    """
    film_id = 300
    allure.dynamic.parameter("film_id", film_id)
    url = f"{api_base_url}/v1.5/movie/{film_id}"
    headers = {
        "X-API-KEY": "invalid_key_for_test",
        "accept": "application/json",
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=10,
    )

    assert response.status_code in (401, 403), (
        "Ожидался статус 401 или 403, "
        f"получен {response.status_code}"
    )
