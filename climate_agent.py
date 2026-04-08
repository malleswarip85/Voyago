"""
Climate Check Agent
Uses WeatherAPI via RapidAPI to get weather forecasts.
"""

import requests
import os


RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
WEATHER_HOST = "weatherapi-com.p.rapidapi.com"


class ClimateAgent:
    def __init__(self):
        self.headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": WEATHER_HOST
        }

    def get_weather(self, destination: str, checkin: str) -> dict:
        """Get weather forecast for destination."""
        try:
            url = "https://weatherapi-com.p.rapidapi.com/forecast.json"
            params = {
                "q": destination,
                "days": "7",
                "aqi": "no",
                "alerts": "no"
            }

            response = requests.get(url, headers=self.headers, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return self._parse_weather(data, destination)
            else:
                return self._mock_weather(destination)

        except Exception as e:
            print(f"Weather fetch error: {e}")
            return self._mock_weather(destination)

    def _parse_weather(self, data: dict, destination: str) -> dict:
        """Parse WeatherAPI response."""
        try:
            current = data.get("current", {})
            location = data.get("location", {})
            forecast_days = data.get("forecast", {}).get("forecastday", [])

            daily_forecasts = []
            for day in forecast_days:
                day_data = day.get("day", {})
                daily_forecasts.append({
                    "date": day.get("date"),
                    "max_temp_c": day_data.get("maxtemp_c"),
                    "min_temp_c": day_data.get("mintemp_c"),
                    "max_temp_f": day_data.get("maxtemp_f"),
                    "min_temp_f": day_data.get("mintemp_f"),
                    "condition": day_data.get("condition", {}).get("text", ""),
                    "rain_chance": day_data.get("daily_chance_of_rain", 0),
                    "humidity": day_data.get("avghumidity", 0),
                })

            return {
                "success": True,
                "destination": location.get("name", destination),
                "country": location.get("country", ""),
                "current": {
                    "temp_c": current.get("temp_c"),
                    "temp_f": current.get("temp_f"),
                    "condition": current.get("condition", {}).get("text", ""),
                    "humidity": current.get("humidity"),
                    "wind_kph": current.get("wind_kph"),
                    "is_raining": "rain" in current.get("condition", {}).get("text", "").lower()
                },
                "forecast": daily_forecasts,
                "source": "live"
            }
        except Exception:
            return self._mock_weather(destination)

    def _mock_weather(self, destination: str) -> dict:
        """Fallback mock weather data."""
        return {
            "success": True,
            "destination": destination,
            "country": "",
            "current": {
                "temp_c": 24,
                "temp_f": 75,
                "condition": "Partly Cloudy",
                "humidity": 65,
                "wind_kph": 15,
                "is_raining": False
            },
            "forecast": [
                {"date": "Day 1", "max_temp_c": 26, "min_temp_c": 18, "max_temp_f": 79, "min_temp_f": 64,
                 "condition": "Sunny", "rain_chance": 5, "humidity": 60},
                {"date": "Day 2", "max_temp_c": 24, "min_temp_c": 17, "max_temp_f": 75, "min_temp_f": 63,
                 "condition": "Partly Cloudy", "rain_chance": 20, "humidity": 65},
                {"date": "Day 3", "max_temp_c": 22, "min_temp_c": 16, "max_temp_f": 72, "min_temp_f": 61,
                 "condition": "Light Rain", "rain_chance": 60, "humidity": 75},
            ],
            "source": "simulated"
        }

    def format_for_display(self, weather_data: dict) -> str:
        """Format weather for chat display."""
        if not weather_data.get("success"):
            return "❌ Could not retrieve weather data."

        current = weather_data["current"]
        forecast = weather_data.get("forecast", [])
        source_note = " *(live)*" if weather_data.get("source") == "live" else " *(sample)*"
        dest = weather_data.get("destination", "")
        country = weather_data.get("country", "")
        location_str = f"{dest}, {country}" if country else dest

        rain_warning = "🌧️ **Rain expected during your trip — pack an umbrella!**\n" if current.get("is_raining") else ""

        lines = [
            f"🌤️ **Weather in {location_str}**{source_note}\n",
            f"**Current Conditions:**",
            f"  • Temperature: {current['temp_c']}°C / {current['temp_f']}°F",
            f"  • Condition: {current['condition']}",
            f"  • Humidity: {current['humidity']}%",
            f"  • Wind: {current['wind_kph']} km/h\n",
            rain_warning,
            "**Forecast:**"
        ]

        for day in forecast[:3]:
            rain_emoji = "🌧️" if day["rain_chance"] > 50 else "🌤️"
            lines.append(
                f"  {rain_emoji} {day['date']}: {day['condition']} | "
                f"{day['max_temp_c']}°C/{day['min_temp_c']}°C | "
                f"Rain: {day['rain_chance']}%"
            )

        return "\n".join(lines)
