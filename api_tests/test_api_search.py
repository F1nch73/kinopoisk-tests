"""Кейс KP_API_01: поиск фильма по названию."""

import allure
import pytest
import requests

from config import API_SEARCH_LIMIT, API_SEARCH_PAGE, API_SEARCH_QUERY

# Поля, которые обязаны присутствовать у каждого результата поиска.
RESULT_FIELDS = (
    "id",
    "name",
    "alternativeName",
    "type",
    "year",
    "genres",
)

# Поля пагинации: должны быть целыми неотрицательными числами.
PAGINATION_FIELDS = ("total", "limit", "page", "pages")


@pytest.mark.smoke
@allure.feature("API: Поиск")
@allure.story("KP_API_01. Поиск фильма по названию")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("KP_API_01. Поиск фильма по названию")
def test_api_search_film_by_name(
    api_base_url: str,
    api_key: str,
) -> None:
    """
    Поиск по названию: проверяются структура ответа, пагинация,
    обязательные поля результатов и наличие искомого названия.
    """
    query = API_SEARCH_QUERY
    allure.dynamic.parameter("query", query)
    allure.dynamic.parameter("limit", API_SEARCH_LIMIT)
    allure.dynamic.parameter("page", API_SEARCH_PAGE)

    headers = {
        "X-API-KEY": api_key,
        "Accept": "application/json",
    }
    params = {
        "query": query,
        "limit": API_SEARCH_LIMIT,
        "page": API_SEARCH_PAGE,
    }

    response = requests.get(
        f"{api_base_url}/v1.5/movie/search",
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

    with allure.step("Проверяем непустой массив docs"):
        assert "docs" in data, "Поле 'docs' отсутствует"
        assert isinstance(data["docs"], list), (
            "Поле 'docs' должно быть списком"
        )
        assert data["docs"], "Список результатов поиска пуст"

    with allure.step("Проверяем пагинацию"):
        for field in PAGINATION_FIELDS:
            assert field in data, f"В ответе отсутствует поле '{field}'"
            value = data[field]
            assert isinstance(value, int) and not isinstance(value, bool), (
                f"Поле '{field}' должно быть целым числом, "
                f"получено {value!r}"
            )
            assert value >= 0, (
                f"Поле '{field}' не может быть отрицательным: {value}"
            )

        assert data["page"] == API_SEARCH_PAGE, (
            f"Ожидалась страница {API_SEARCH_PAGE}, "
            f"получена {data['page']}"
        )
        assert data["limit"] == API_SEARCH_LIMIT, (
            f"Ожидался limit={API_SEARCH_LIMIT}, "
            f"получен {data['limit']}"
        )
        assert len(data["docs"]) <= API_SEARCH_LIMIT, (
            f"Результатов больше limit: {len(data['docs'])} > "
            f"{API_SEARCH_LIMIT}"
        )
        assert data["total"] >= len(data["docs"]), (
            f"total={data['total']} меньше количества "
            f"результатов {len(data['docs'])}"
        )

    with allure.step("Проверяем обязательные поля результатов"):
        for index, movie in enumerate(data["docs"]):
            assert isinstance(movie, dict), (
                f"docs[{index}] должен быть объектом"
            )
            for field in RESULT_FIELDS:
                assert field in movie, (
                    f"docs[{index}]: отсутствует поле '{field}'"
                )

            assert isinstance(movie["id"], int) and movie["id"] > 0, (
                f"docs[{index}]: id должен быть целым больше 0, "
                f"получено {movie['id']!r}"
            )
            assert isinstance(movie["type"], str) and movie["type"].strip(), (
                f"docs[{index}]: type должен быть непустой строкой"
            )
            assert isinstance(movie["genres"], list), (
                f"docs[{index}]: genres должен быть списком"
            )

    with allure.step(f"Проверяем, что найден фильм «{query}»"):
        found_movie = _find_movie_by_title(data["docs"], query)
        assert found_movie is not None, (
            f"В результатах нет названия, содержащего «{query}»"
        )
        allure.attach(
            f"id={found_movie['id']}, name={found_movie.get('name')!r}",
            name="Найденный фильм",
        )
        assert isinstance(found_movie["id"], int) and found_movie["id"] > 0, (
            "У найденного фильма некорректный id: "
            f"{found_movie['id']!r}"
        )


def _find_movie_by_title(
    movies: list[dict],
    query: str,
) -> dict | None:
    """
    Возвращает первый фильм, в названии которого есть запрос.

    Проверяются name, alternativeName, enName и массив names,
    сравнение регистронезависимое.
    """
    needle = query.strip().casefold()

    for movie in movies:
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

        if any(
            isinstance(title, str) and needle in title.casefold()
            for title in titles
        ):
            return movie

    return None
