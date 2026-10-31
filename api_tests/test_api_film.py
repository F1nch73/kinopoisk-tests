"""Кейс KP_API_05: получение карточки фильма по ID."""

import allure
import pytest
import requests

from config import API_FILM_ID

# Поля, которые обязаны присутствовать в карточке фильма.
FILM_FIELDS = (
    "id",
    "name",
    "alternativeName",
    "type",
    "year",
    "genres",
)

# ID фильмов для параметризованной проверки: основной из кейса
# и два дополнительных, чтобы покрыть разные типы карточек.
KNOWN_FILM_IDS = (
    pytest.param(API_FILM_ID, id=f"film-{API_FILM_ID}"),
    pytest.param(409424, id="film-409424"),
    pytest.param(4370148, id="film-4370148"),
)


@pytest.mark.smoke
@allure.feature("API: Фильмы")
@allure.story("KP_API_05. Карточка фильма по ID")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("KP_API_05. Карточка фильма по ID: {film_id}")
@pytest.mark.parametrize("film_id", KNOWN_FILM_IDS)
def test_api_get_film_by_id(
    film_id: int,
    api_base_url: str,
    api_key: str,
) -> None:
    """
    Карточка фильма: ID в ответе совпадает с запрошенным,
    присутствуют обязательные поля, есть хотя бы одно название.
    """
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

    with allure.step("Проверяем статус-код"):
        assert response.status_code == 200, (
            f"Ожидался 200, получен {response.status_code}"
        )

    data = response.json()

    with allure.step("Проверяем, что ответ — JSON-объект"):
        assert isinstance(data, dict), "Ответ должен быть JSON-объектом"

    with allure.step("Проверяем, что ID совпадает с ID в запросе"):
        assert isinstance(data.get("id"), int), (
            f"Поле 'id' должно быть числом, получено {data.get('id')!r}"
        )
        assert data["id"] == film_id, (
            f"Ожидался ID {film_id}, получен {data['id']}"
        )

    with allure.step("Проверяем обязательные поля карточки"):
        for field in FILM_FIELDS:
            assert field in data, (
                f"Поле '{field}' отсутствует в карточке фильма"
            )

        assert data["id"] > 0, "ID фильма должен быть больше 0"
        assert isinstance(data["type"], str) and data["type"].strip(), (
            "Поле 'type' должно быть непустой строкой"
        )
        assert isinstance(data["genres"], list), (
            "Поле 'genres' должно быть списком"
        )

    with allure.step("Проверяем, что есть хотя бы одно название"):
        titles = (data.get("name"), data.get("alternativeName"))
        has_title = any(
            isinstance(title, str) and title.strip()
            for title in titles
        )
        allure.attach(
            f"name={data.get('name')!r}, "
            f"alternativeName={data.get('alternativeName')!r}",
            name="Названия фильма",
        )
        assert has_title, (
            "В карточке должно быть хотя бы одно непустое название "
            f"(name или alternativeName), получено: {titles}"
        )
