from __future__ import annotations

from datetime import date

import httpx

from weather_history_api.models import DayWeather


class UpstreamWeatherError(Exception):
    """Raised when the weather provider is unavailable or returns an error."""


class UpstreamPayloadError(Exception):
    """Raised when the weather provider returns an invalid payload."""


class OpenMeteoArchiveClient:
    def __init__(
        self,
        base_url: str = "https://archive-api.open-meteo.com",
        http_client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._http_client = http_client

    def fetch_history(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
    ) -> list[DayWeather]:
        if self._http_client is not None:
            return self._fetch_with_client(
                self._http_client,
                latitude,
                longitude,
                start_date,
                end_date,
            )

        with httpx.Client(base_url=self._base_url, timeout=10.0) as client:
            return self._fetch_with_client(
                client,
                latitude,
                longitude,
                start_date,
                end_date,
            )

    def _fetch_with_client(
        self,
        client: httpx.Client,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
    ) -> list[DayWeather]:
        try:
            response = client.get(
                "/v1/archive",
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "daily": (
                        "temperature_2m_max,"
                        "temperature_2m_min,"
                        "precipitation_sum"
                    ),
                    "timezone": "UTC",
                },
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise UpstreamWeatherError(
                "Failed to fetch weather history from Open-Meteo."
            ) from exc

        return self._map_days(response.json())

    def _map_days(self, payload: object) -> list[DayWeather]:
        if not isinstance(payload, dict):
            raise UpstreamPayloadError(
                "Open-Meteo payload must be a JSON object."
            )

        daily = payload.get("daily")
        if not isinstance(daily, dict):
            raise UpstreamPayloadError("Open-Meteo payload does not contain daily data.")

        required_keys = [
            "time",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
        ]
        columns: dict[str, list] = {}
        for key in required_keys:
            value = daily.get(key)
            if not isinstance(value, list):
                raise UpstreamPayloadError(
                    f"Open-Meteo payload is missing list field '{key}'."
                )
            columns[key] = value

        lengths = {len(value) for value in columns.values()}
        if len(lengths) != 1:
            raise UpstreamPayloadError(
                "Open-Meteo daily payload contains columns with mismatched lengths."
            )

        if not columns["time"]:
            raise UpstreamPayloadError("Open-Meteo returned an empty daily payload.")

        days: list[DayWeather] = []
        for index, raw_date in enumerate(columns["time"]):
            try:
                parsed_date = date.fromisoformat(raw_date)
            except (TypeError, ValueError) as exc:
                raise UpstreamPayloadError(
                    "Open-Meteo returned a date with an invalid format."
                ) from exc

            days.append(
                DayWeather(
                    date=parsed_date,
                    temperature_max=columns["temperature_2m_max"][index],
                    temperature_min=columns["temperature_2m_min"][index],
                    precipitation_sum=columns["precipitation_sum"][index],
                )
            )
        return days

