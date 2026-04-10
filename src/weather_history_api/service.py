from datetime import date

from weather_history_api.clients import OpenMeteoArchiveClient
from weather_history_api.models import DayWeather


class InvalidDateRangeError(Exception):
    """Raised when the requested date range is invalid."""


class WeatherHistoryService:
    def __init__(self, client: OpenMeteoArchiveClient | None = None) -> None:
        self._client = client or OpenMeteoArchiveClient()

    def get_history(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
    ) -> list[DayWeather]:
        if start_date > end_date:
            raise InvalidDateRangeError("start_date must be earlier than or equal to end_date.")

        return self._client.fetch_history(latitude, longitude, start_date, end_date)

