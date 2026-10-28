"""Кейс KP_API_03: фильтрация фильмов по году выпуска."""

import allure
import pytest
import requests

from config import API_YEAR, API_YEAR_LIMIT


@pytest.mark.smoke
@allure.feature("API: Фильмы")
@allure.story("KP_API_03. Фильтрация по году")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("KP_API_03. Фильмы за {year} год")
def test_api_get_movies_by_year(
    api_base_url: str,
    api_key: str,
) -> None:
    """
    Фильтрация по году: проверяются ограничение выдачи и то, что
    год каждого фильма совпадает с запрошенным.
    """
    year = API_YEAR
    limit = API_YEAR_LIMIT
    allure.dynamic.parameter("year", year)
    allure.dynamic.parameter("limit", limit)

    headers = {
        "X-API-KEY": api_key,
        "Accept": "application/json",
    }
    params = {
        "year": year,
        "type": "movie",
        "limit": limit,
    }

    response = requests.get(
        f"{api_base_url}/v1.5/movie",
        params=params,
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

    with allure.step("Проверяем непустой массив фильмов"):
        assert "docs" in data, "Поле 'docs' отсутствует"
        assert isinstance(data["docs"], list), (
            "Поле 'docs' должно быть списком"
        )
        assert data["docs"], "Список фильмов пуст"

    with allure.step("Проверяем, что выдача не превышает limit"):
        assert len(data["docs"]) <= limit, (
            f"Результатов больше limit: {len(data['docs'])} > {limit}"
        )

    with allure.step("Проверяем год выпуска у каждого фильма"):
        for index, movie in enumerate(data["docs"]):
            assert isinstance(movie, dict), (
                f"docs[{index}] должен быть объектом"
            )
            assert isinstance(movie.get("id"), int) and movie["id"] > 0, (
                f"docs[{index}]: id должен быть целым больше 0, "
                f"получено {movie.get('id')!r}"
            )
            assert movie.get("year") == year, (
                f"Фильм id={movie.get('id')}: ожидался год {year}, "
                f"получен {movie.get('year')!r}"
            )
            assert movie.get("type") == "movie", (
                f"Объект id={movie.get('id')} не является фильмом: "
                f"type={movie.get('type')!r}"
            )
