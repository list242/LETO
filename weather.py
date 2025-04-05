import requests
from datetime import datetime

API_KEY = "fe3a34ae13d5505cef253dbe9a43d515"
LAT = 55.7760
LON = 37.4166

def get_weather_for_date(target_date: str):
    """
    Возвращает прогноз на указанную дату (в формате YYYY-MM-DD)
    """
    url = (
        f"https://api.openweathermap.org/data/2.5/forecast?lat={LAT}&lon={LON}"
        f"&appid={API_KEY}&units=metric&lang=ru"
    )
    try:
        response = requests.get(url)
        data = response.json()

        for entry in data["list"]:
            dt = datetime.fromtimestamp(entry["dt"])
            if dt.date().isoformat() == target_date:
                temp = round(entry["main"]["temp"])
                wind = round(entry["wind"]["speed"])
                rain = entry.get("rain", {}).get("3h", 0) > 0

                return {
                    "temp": temp,
                    "wind": wind,
                    "rain": rain
                }

    except Exception as e:
        print(f"Ошибка при получении погоды: {e}")

    return {
        "temp": "—",
        "wind": "—",
        "rain": False
    }
