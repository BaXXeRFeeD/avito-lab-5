from datetime import date
import json

import httpx
import pytest

from weather_history_api.clients import OpenMeteoArchiveClient, UpstreamPayloadError


def test_open_meteo_client_maps_valid_archive_payload():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/archive"
        assert request.url.params["latitude"] == "59.93"
        assert request.url.params["longitude"] == "30.31"
        return httpx.Response(
            200,
            content=json.dumps(
                {
                    "daily": {
                        "time": ["2024-01-01", "2024-01-02"],
                        "temperature_2m_max": [1.2, 0.4],
                        "temperature_2m_min": [-3.0, -4.1],
                        "precipitation_sum": [0.0, 1.1],
                    }
                }
            ),
            headers={"Content-Type": "application/json"},
        )

    with httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url="https://archive-api.open-meteo.com",
    ) as http_client:
        client = OpenMeteoArchiveClient(http_client=http_client)
        days = client.fetch_history(59.93, 30.31, date(2024, 1, 1), date(2024, 1, 2))

    assert len(days) == 2
    assert days[0].date.isoformat() == "2024-01-01"
    assert days[1].precipitation_sum == 1.1


def test_open_meteo_client_rejects_mismatched_daily_columns():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=json.dumps(
                {
                    "daily": {
                        "time": ["2024-01-01", "2024-01-02"],
                        "temperature_2m_max": [1.2],
                        "temperature_2m_min": [-3.0, -4.1],
                        "precipitation_sum": [0.0, 1.1],
                    }
                }
            ),
            headers={"Content-Type": "application/json"},
        )

    with httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url="https://archive-api.open-meteo.com",
    ) as http_client:
        client = OpenMeteoArchiveClient(http_client=http_client)

        with pytest.raises(UpstreamPayloadError) as exc_info:
            client.fetch_history(
                59.93,
                30.31,
                date(2024, 1, 1),
                date(2024, 1, 2),
            )

    assert "mismatched lengths" in str(exc_info.value)


def test_open_meteo_client_rejects_non_object_root_payload():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=json.dumps(
                [
                    {
                        "daily": {
                            "time": ["2024-01-01"],
                            "temperature_2m_max": [1.2],
                            "temperature_2m_min": [-3.0],
                            "precipitation_sum": [0.0],
                        }
                    }
                ]
            ),
            headers={"Content-Type": "application/json"},
        )

    with httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url="https://archive-api.open-meteo.com",
    ) as http_client:
        client = OpenMeteoArchiveClient(http_client=http_client)

        with pytest.raises(UpstreamPayloadError) as exc_info:
            client.fetch_history(
                59.93,
                30.31,
                date(2024, 1, 1),
                date(2024, 1, 1),
            )

    assert "JSON object" in str(exc_info.value)


def test_open_meteo_client_rejects_non_string_dates():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=json.dumps(
                {
                    "daily": {
                        "time": [123],
                        "temperature_2m_max": [1.2],
                        "temperature_2m_min": [-3.0],
                        "precipitation_sum": [0.0],
                    }
                }
            ),
            headers={"Content-Type": "application/json"},
        )

    with httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url="https://archive-api.open-meteo.com",
    ) as http_client:
        client = OpenMeteoArchiveClient(http_client=http_client)

        with pytest.raises(UpstreamPayloadError) as exc_info:
            client.fetch_history(
                59.93,
                30.31,
                date(2024, 1, 1),
                date(2024, 1, 1),
            )

    assert "invalid format" in str(exc_info.value)
