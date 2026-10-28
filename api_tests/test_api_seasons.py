"""Кейс KP_API_06: получение сезонов сериала."""

import allure
import requests

from config import API_SEASONS_LIMIT, API_SERIES_ID


@allure.feature("API: Сериалы")
@allure.story("KP_API_06. Сезоны сериала")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("KP_API_06. Сезоны сериала по ID")
def test_api_get_series_seasons(
    api_base_url: str,
    api_key: str,
) -> None:
    """
    Сезоны сериала: проверяются структура ответа, пагинация,
    корректность номеров сезонов и эпизодов и их сортировка.
    """
    series_id = API_SERIES_ID
    limit = API_SEASONS_LIMIT
    allure.dynamic.parameter("series_id", series_id)
    allure.dynamic.parameter("limit", limit)

    headers = {
        "X-API-KEY": api_key,
        "Accept": "application/json",
    }
    params = {
        "movieId": series_id,
        "limit": limit,
        "selectFields": [
            "movieId",
            "number",
            "episodes",
        ],
        "sortField": "number",
        "sortType": "1",
    }

    response = requests.get(
        f"{api_base_url}/v1.5/season",
        params=params,
        headers=headers,
        timeout=15,
    )

    with allure.step("Проверяем статус-код"):
        assert response.status_code == 200, (
            f"Ожидался статус 200, получен {response.status_code}"
        )

    data = response.json()

    with allure.step("Проверяем структуру ответа"):
        assert isinstance(data, dict), "Ответ должен быть JSON-объектом"
        for field in ("docs", "limit", "hasNext", "hasPrev"):
            assert field in data, (
                f"В ответе отсутствует поле '{field}'"
            )

    seasons = data["docs"]

    with allure.step("Проверяем массив сезонов"):
        assert isinstance(seasons, list), "Поле 'docs' должно быть списком"
        assert seasons, f"Для сериала с ID {series_id} не найдены сезоны"
        assert len(seasons) <= limit, (
            f"Количество сезонов превышает limit: "
            f"{len(seasons)} > {limit}"
        )

    with allure.step("Проверяем пагинацию"):
        assert data["limit"] == limit, (
            f"Ожидался limit={limit}, получен {data['limit']}"
        )
        assert isinstance(data["hasNext"], bool), (
            "Поле 'hasNext' должно быть логическим значением"
        )
        assert data["hasPrev"] is False, (
            "У первой страницы не должно быть предыдущей страницы"
        )

        if data["hasNext"]:
            assert isinstance(data.get("next"), str), (
                "При hasNext=true поле 'next' должно быть строкой"
            )
            assert data["next"].strip(), (
                "При hasNext=true курсор 'next' не должен быть пустым"
            )

    with allure.step("Проверяем поля и номера сезонов"):
        season_numbers: list[int] = []

        for index, season in enumerate(seasons):
            assert isinstance(season, dict), (
                f"Сезон docs[{index}] должен быть объектом"
            )
            for field in ("movieId", "number", "episodes"):
                assert field in season, (
                    f"В сезоне docs[{index}] отсутствует поле '{field}'"
                )

            assert season["movieId"] == series_id, (
                f"Сезон docs[{index}] относится к другому сериалу: "
                f"ожидался movieId={series_id}, "
                f"получен {season['movieId']}"
            )

            number = season["number"]
            assert isinstance(number, int) and not isinstance(number, bool), (
                f"Сезон docs[{index}]: number должен быть целым числом, "
                f"получено {number!r}"
            )
            assert number >= 0, (
                f"Сезон docs[{index}]: number не должен быть "
                f"отрицательным ({number})"
            )
            assert isinstance(season["episodes"], list), (
                f"Сезон docs[{index}]: episodes должен быть списком"
            )

            season_numbers.append(number)

    with allure.step("Проверяем сортировку сезонов по номеру"):
        assert season_numbers == sorted(season_numbers), (
            "Сезоны не отсортированы по возрастанию номера: "
            f"{season_numbers}"
        )

    with allure.step("Проверяем номера эпизодов"):
        for season_index, season in enumerate(seasons):
            for episode_index, episode in enumerate(season["episodes"]):
                label = (
                    f"Сезон [{season_index}], эпизод [{episode_index}]"
                )
                assert isinstance(episode, dict), (
                    f"{label}: эпизод должен быть объектом"
                )
                assert "number" in episode, (
                    f"{label}: отсутствует поле 'number'"
                )

                number = episode["number"]
                is_valid_number = isinstance(number, int) and not isinstance(
                    number, bool
                )
                assert is_valid_number, (
                    f"{label}: number должен быть целым числом, "
                    f"получено {number!r}"
                )
                assert number >= 0, (
                    f"{label}: number не должен быть отрицательным "
                    f"({number})"
                )
