from datetime import date
from dataclasses import dataclass


@dataclass(slots=True)
class DayWeather:
    date: date
    temperature_max: float | None
    temperature_min: float | None
    precipitation_sum: float | None


@dataclass(slots=True)
class LocationInfo:
    latitude: float
    longitude: float


@dataclass(slots=True)
class DateRangeInfo:
    start_date: date
    end_date: date


@dataclass(slots=True)
class WeatherHistoryResponse:
    location: LocationInfo
    range: DateRangeInfo
    days: list[DayWeather]
    source: str
