import allure
import pytest
import requests


# Общие ID фильмов для параметризованных проверок.
KNOWN_FILM_IDS = (
    pytest.param(300, id="film-300"),
    pytest.param(409424, id="film-409424"),
    pytest.param(4370148, id="film-4370148"),
)


@pytest.mark.smoke
@allure.feature("API: Фильмы")
@allure.story("Получение карточки фильма по ID")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Получение карточки фильма по ID: {film_id}")
@pytest.mark.parametrize("film_id", KNOWN_FILM_IDS)
def test_api_get_film_by_id(
    film_id: int,
    api_base_url: str,
    api_key: str,
) -> None:
    """Проверяет получение фильма по ID."""
    allure.dynamic.parameter("film_id", film_id)
    headers = {
        "X-API-KEY": api_key,
        "Accept": "application/json",
    }

    response = requests.get(
        f"{api_base_url}/v1.5/movie/{film_id}",
        headers=headers,
        timeout=15,
    )

    assert response.status_code == 200, (
        f"Ожидался 200, получен {response.status_code}"
    )

    data = response.json()

    assert isinstance(data, dict), "Ответ должен быть JSON-объектом"

    required_fields = (
        "id",
        "name",
        "year",
        "type",
        "rating",
        "genres",
    )

    for field in required_fields:
        assert field in data, (
            f"Поле '{field}' отсутствует в карточке фильма"
        )

    assert data["id"] == film_id, (
        f"Ожидался ID {film_id}, получен {data['id']}"
    )
    assert isinstance(data["name"], str), (
        "Поле 'name' должно быть строкой"
    )
    assert data["name"].strip(), "Название фильма пустое"
    assert isinstance(data["year"], int), (
        "Поле 'year' должно быть целым числом"
    )
    assert isinstance(data["genres"], list), (
        "Поле 'genres' должно быть списком"
    )
    assert data["rating"] is None or isinstance(
        data["rating"], dict
    ), "Поле 'rating' должно быть объектом или null"
