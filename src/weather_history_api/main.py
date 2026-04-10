from datetime import date
from dataclasses import asdict

from flask import Flask, jsonify, request

from weather_history_api.clients import UpstreamPayloadError, UpstreamWeatherError
from weather_history_api.models import DateRangeInfo, LocationInfo, WeatherHistoryResponse
from weather_history_api.service import InvalidDateRangeError, WeatherHistoryService

app = Flask(__name__)

_service = WeatherHistoryService()


def _parse_float(name: str, lower: float, upper: float) -> float:
    raw_value = request.args.get(name)
    if raw_value is None:
        raise ValueError(f"Missing required query parameter '{name}'.")

    try:
        value = float(raw_value)
    except ValueError as exc:
        raise ValueError(f"Query parameter '{name}' must be a number.") from exc

    if not lower <= value <= upper:
        raise ValueError(
            f"Query parameter '{name}' must be between {lower} and {upper}."
        )
    return value


def _parse_date(name: str) -> date:
    raw_value = request.args.get(name)
    if raw_value is None:
        raise ValueError(f"Missing required query parameter '{name}'.")

    try:
        return date.fromisoformat(raw_value)
    except ValueError as exc:
        raise ValueError(
            f"Query parameter '{name}' must use YYYY-MM-DD format."
        ) from exc


def _serialize_response(response: WeatherHistoryResponse) -> dict:
    payload = asdict(response)
    payload["range"]["start_date"] = response.range.start_date.isoformat()
    payload["range"]["end_date"] = response.range.end_date.isoformat()
    payload["days"] = [
        {
            "date": day.date.isoformat(),
            "temperature_max": day.temperature_max,
            "temperature_min": day.temperature_min,
            "precipitation_sum": day.precipitation_sum,
        }
        for day in response.days
    ]
    return payload


@app.get("/weather-history")
def get_weather_history():
    try:
        latitude = _parse_float("latitude", -90, 90)
        longitude = _parse_float("longitude", -180, 180)
        start_date = _parse_date("start_date")
        end_date = _parse_date("end_date")
    except ValueError as exc:
        return jsonify({"detail": str(exc)}), 400

    try:
        days = _service.get_history(latitude, longitude, start_date, end_date)
    except InvalidDateRangeError as exc:
        return jsonify({"detail": str(exc)}), 400
    except (UpstreamWeatherError, UpstreamPayloadError) as exc:
        return jsonify({"detail": str(exc)}), 502

    response = WeatherHistoryResponse(
        location=LocationInfo(latitude=latitude, longitude=longitude),
        range=DateRangeInfo(start_date=start_date, end_date=end_date),
        days=days,
        source="open-meteo",
    )
    return jsonify(_serialize_response(response))


if __name__ == "__main__":
    app.run()
