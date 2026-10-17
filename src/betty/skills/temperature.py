import openmeteo_requests
import requests_cache
from retry_requests import retry


def get_temperature():
    cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    response = openmeteo.weather_api(
        "https://api.open-meteo.com/v1/forecast",
        {
            "latitude": -29.1253,
            "longitude": -56.5531,
            "current": "temperature_2m",
            "forecast_days": 1,
        },
    )[0]

    current = response.Current()
    return current.Variables(0).Value()
