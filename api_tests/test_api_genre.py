"""Кейс KP_API_02: фильтрация фильмов по жанру."""

import allure
import pytest
import requests

from config import API_GENRE

GENRE_PARAMS = (
    pytest.param(API_GENRE, id="genre-criminals"),
    pytest.param("комедия", id="genre-comedy"),
    pytest.param("фантастика", id="genre-scifi"),
)


@allure.feature("API: Фильмы")
@allure.story("KP_API_02. Фильтрация по жанру")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("KP_API_02. Фильмы выбранного жанра: {genre}")
@pytest.mark.parametrize("genre", GENRE_PARAMS)
def test_api_get_movies_by_genre(
    genre: str,
    api_base_url: str,
    api_key: str,
) -> None:
    """
    Фильтрация по жанру: проверяется, что каждый фильм в выдаче
    содержит запрошенный жанр (точное совпадение названия).
    """
    headers = {
        "X-API-KEY": api_key,
        "Accept": "application/json",
    }
    params = {"genres.name": genre}

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

    with allure.step(f"Проверяем жанр «{genre}» у каждого фильма"):
        needle = genre.strip().casefold()

        for index, movie in enumerate(data["docs"]):
            assert isinstance(movie, dict), (
                f"docs[{index}] должен быть объектом"
            )
            assert isinstance(movie.get("id"), int) and movie["id"] > 0, (
                f"docs[{index}]: id должен быть целым больше 0, "
                f"получено {movie.get('id')!r}"
            )
            assert isinstance(movie.get("genres"), list), (
                f"docs[{index}]: genres должен быть списком"
            )
            assert movie["genres"], (
                f"docs[{index}]: список жанров пуст"
            )

            genre_names = [
                item.get("name")
                for item in movie["genres"]
                if isinstance(item, dict)
            ]
            has_genre = any(
                isinstance(name, str) and name.strip().casefold() == needle
                for name in genre_names
            )

            assert has_genre, (
                f"Фильм id={movie['id']} не содержит жанр «{genre}». "
                f"Жанры: {genre_names}"
            )
