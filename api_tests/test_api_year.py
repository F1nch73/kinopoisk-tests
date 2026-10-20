import allure
import requests


@allure.feature("API: Фильмы")
@allure.story("Фильтрация по году")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Получение фильмов за указанный год")
def test_api_get_movies_by_year(
    api_base_url: str,
    api_key: str,
) -> None:
    """Проверяет получение фильмов за указанный год."""
    year = 2021
    allure.dynamic.parameter("year", year)
    headers = {
        "X-API-KEY": api_key,
        "Accept": "application/json",
    }
    params = {
        "year": year,
        "type": "movie",
        "limit": 10,
    }

    response = requests.get(
        f"{api_base_url}/v1.5/movie",
        params=params,
        headers=headers,
        timeout=15,
    )

    assert response.status_code == 200, (
        f"Ожидался 200, получен {response.status_code}"
    )

    data = response.json()

    assert isinstance(data, dict), "Ответ должен быть JSON-объектом"
    assert "docs" in data, "Поле 'docs' отсутствует"
    assert isinstance(data["docs"], list), (
        "Поле 'docs' должно быть списком"
    )
    assert data["docs"], "Список фильмов пуст"
    assert len(data["docs"]) <= params["limit"], (
        "Количество результатов превышает limit"
    )

    for movie in data["docs"]:
        assert isinstance(movie, dict), (
            "Каждый результат должен быть объектом"
        )
        assert "year" in movie, "У фильма отсутствует поле 'year'"

        assert movie["year"] == year, (
            f"Фильм {movie.get('id')}: ожидался год {year}, "
            f"получен {movie['year']}"
        )
        assert movie.get("type") == "movie", (
            f"Объект {movie.get('id')} не является фильмом"
        )
