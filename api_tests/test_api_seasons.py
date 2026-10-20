import allure
import requests


@allure.feature("API: Сериалы")
@allure.story("Получение сезонов сериала")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Получение сезонов сериала по ID")
def test_api_get_series_seasons(
    api_base_url: str,
    api_key: str,
) -> None:
    """Проверяет получение сезонов сериала по ID."""
    series_id = 685246
    limit = 10
    allure.dynamic.parameter("series_id", series_id)

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
        f"{api_base_url.rstrip('/')}/v1.5/season",
        params=params,
        headers=headers,
        timeout=15,
    )

    assert response.status_code == 200, (
        f"Ожидался статус 200, получен {response.status_code}"
    )

    data = response.json()

    assert isinstance(data, dict), (
        "Ответ должен быть JSON-объектом"
    )

    for field in ("docs", "limit", "hasNext", "hasPrev"):
        assert field in data, (
            f"В ответе отсутствует поле '{field}'"
        )

    seasons = data["docs"]

    assert isinstance(seasons, list), (
        "Поле 'docs' должно быть списком"
    )
    assert seasons, (
        f"Для сериала с ID {series_id} не найдены сезоны"
    )
    assert data["limit"] == limit, (
        f"Ожидался limit={limit}, получен {data['limit']}"
    )
    assert len(seasons) <= limit, (
        "Количество сезонов превышает запрошенный limit"
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

    season_numbers = []

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
        assert type(season["number"]) is int, (
            "Номер сезона должен быть целым числом"
        )
        assert season["number"] >= 0, (
            "Номер сезона не должен быть отрицательным"
        )
        assert isinstance(season["episodes"], list), (
            "Поле 'episodes' должно быть списком"
        )

        season_numbers.append(season["number"])

        for episode_index, episode in enumerate(season["episodes"]):
            assert isinstance(episode, dict), (
                f"Эпизод {episode_index} сезона {season['number']} "
                "должен быть объектом"
            )
            assert "number" in episode, (
                f"У эпизода {episode_index} сезона "
                f"{season['number']} отсутствует поле 'number'"
            )
            assert type(episode["number"]) is int, (
                "Номер эпизода должен быть целым числом"
            )
            assert episode["number"] >= 0, (
                "Номер эпизода не должен быть отрицательным"
            )

    assert season_numbers == sorted(season_numbers), (
        "Сезоны не отсортированы по возрастанию номера: "
        f"{season_numbers}"
    )
