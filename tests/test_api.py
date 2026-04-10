from datetime import date

from weather_history_api import main
from weather_history_api.clients import UpstreamPayloadError
from weather_history_api.models import DayWeather
from weather_history_api.service import InvalidDateRangeError


class FakeService:
    def __init__(self, *, days=None, error=None):
        self._days = days or []
        self._error = error

    def get_history(self, latitude, longitude, start_date, end_date):
        if self._error is not None:
            raise self._error
        return self._days


def test_weather_history_endpoint_returns_normalized_payload(monkeypatch):
    monkeypatch.setattr(
        main,
        "_service",
        FakeService(
        days=[
            DayWeather(
                date=date(2024, 1, 1),
                temperature_max=3.2,
                temperature_min=-1.4,
                precipitation_sum=0.5,
            )
        ]
        ),
    )

    with main.app.test_client() as client:
        response = client.get(
            "/weather-history?latitude=59.93&longitude=30.31&start_date=2024-01-01&end_date=2024-01-01"
        )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["location"] == {"latitude": 59.93, "longitude": 30.31}
    assert payload["range"] == {
        "start_date": "2024-01-01",
        "end_date": "2024-01-01",
    }
    assert payload["days"] == [
        {
            "date": "2024-01-01",
            "temperature_max": 3.2,
            "temperature_min": -1.4,
            "precipitation_sum": 0.5,
        }
    ]
    assert payload["source"] == "open-meteo"


def test_weather_history_endpoint_rejects_invalid_date_range(monkeypatch):
    monkeypatch.setattr(
        main,
        "_service",
        FakeService(
            error=InvalidDateRangeError(
                "start_date must be earlier than or equal to end_date."
            )
        ),
    )

    with main.app.test_client() as client:
        response = client.get(
            "/weather-history?latitude=59.93&longitude=30.31&start_date=2024-01-03&end_date=2024-01-01"
        )

    assert response.status_code == 400
    assert response.get_json() == {
        "detail": "start_date must be earlier than or equal to end_date."
    }


def test_weather_history_endpoint_surfaces_upstream_payload_errors(monkeypatch):
    monkeypatch.setattr(
        main,
        "_service",
        FakeService(
            error=UpstreamPayloadError("Open-Meteo returned an empty daily payload.")
        ),
    )

    with main.app.test_client() as client:
        response = client.get(
            "/weather-history?latitude=59.93&longitude=30.31&start_date=2024-01-01&end_date=2024-01-01"
        )

    assert response.status_code == 502
    assert response.get_json() == {
        "detail": "Open-Meteo returned an empty daily payload."
    }
