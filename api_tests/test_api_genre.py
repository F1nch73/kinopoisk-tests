import allure
import pytest
import requests


GENRE_PARAMS = (
    pytest.param("криминал", id="genre-criminals"),
    pytest.param("комедия", id="genre-comedy"),
    pytest.param("фантастика", id="genre-scifi"),
)


@allure.feature("API: Фильмы")
@allure.story("Фильтрация по жанру")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Получение фильмов выбранного жанра: {genre}")
@pytest.mark.parametrize("genre", GENRE_PARAMS)
def test_api_get_movies_by_genre(
    genre: str,
    api_base_url: str,
    api_key: str,
) -> None:
    """Проверяет получение фильмов выбранного жанра."""
    headers = {
        "X-API-KEY": api_key,
        "Accept": "application/json",
    }
    params = {
        "genres.name": genre,
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
        assert "genres" in movie, (
            f"У фильма {movie.get('id')} отсутствует поле 'genres'"
        )
        assert isinstance(movie["genres"], list), (
            "Поле 'genres' должно быть списком"
        )

        genre_names = [
            item.get("name")
            for item in movie["genres"]
            if isinstance(item, dict)
        ]

        assert genre in genre_names, (
            f"Фильм {movie.get('id')}: жанр '{genre}' "
            f"отсутствует в списке {genre_names}"
        )
        assert movie.get("type") == "movie", (
            f"Объект {movie.get('id')} не является фильмом"
        )
