import allure
import requests


@allure.feature("API: Поиск")
@allure.story("Поиск фильмов по названию")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Поиск фильма по названию")
def test_api_search_film_by_name(
    api_base_url: str,
    api_key: str,
) -> None:
    """Проверяет поиск фильма по названию."""
    query = "Дюна"
    allure.dynamic.parameter("query", query)
    headers = {
        "X-API-KEY": api_key,
        "Accept": "application/json",
    }
    params = {
        "query": query,
        "limit": 10,
        "page": 1,
    }

    response = requests.get(
        f"{api_base_url}/v1.5/movie/search",
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
    assert data["docs"], "Список результатов поиска пуст"

    found = False

    for movie in data["docs"]:
        assert isinstance(movie, dict), (
            "Каждый результат должен быть объектом"
        )
        assert "id" in movie, "У результата отсутствует поле 'id'"

        titles = [
            movie.get("name"),
            movie.get("alternativeName"),
            movie.get("enName"),
        ]
        titles.extend(
            item.get("name")
            for item in (movie.get("names") or [])
            if isinstance(item, dict)
        )

        title_matches = any(
            isinstance(title, str)
            and query.casefold() in title.casefold()
            for title in titles
        )

        if movie.get("type") == "movie" and title_matches:
            found = True

    assert found, (
        f"Фильм с названием, содержащим '{query}', не найден"
    )
