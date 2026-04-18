"""
Climate Agent - OpenWeatherMap v1
Uses OpenWeatherMap free API (api.openweathermap.org)
Key stored as OPENWEATHER_API_KEY in .env
Free tier: 1000 calls/day, 5-day forecast
"""
import requests, os
from datetime import datetime, timedelta

OWM_KEY = os.getenv("OPENWEATHER_API_KEY", "")
OWM_BASE = "https://api.openweathermap.org/data/2.5"

class ClimateAgent:
    def __init__(self):
        pass

    def get_weather(self, destination, checkin, checkout=None):
        days = 5  # OWM free tier gives 5-day forecast
        if checkin and checkout:
            try:
                days = min(5, max(1, (
                    datetime.strptime(checkout, "%Y-%m-%d") -
                    datetime.strptime(checkin, "%Y-%m-%d")
                ).days + 1))
            except: pass

        key = os.getenv("OPENWEATHER_API_KEY", "")
        if not key:
            print("No OpenWeatherMap key — using mock weather")
            return self._mock(destination, checkin, checkout, days)

        # Check if checkin is within next 5 days (OWM free limit)
        today = datetime.now().date()
        try:
            checkin_date = datetime.strptime(checkin, "%Y-%m-%d").date()
            days_until_trip = (checkin_date - today).days
        except:
            days_until_trip = 0

        # OWM free forecast only covers next 5 days
        # If trip is further away, use mock with realistic seasonal data
        if days_until_trip > 5:
            print(f"Trip is {days_until_trip} days away — OWM free tier only covers 5 days, using seasonal estimate")
            return self._seasonal_mock(destination, checkin, checkout, days)

        try:
            url = f"{OWM_BASE}/forecast"
            params = {
                "q": destination,
                "appid": key,
                "units": "metric",
                "cnt": "40"  # max 5 days × 8 intervals
            }
            r = requests.get(url, params=params, timeout=10)
            print(f"OpenWeatherMap status: {r.status_code}")

            if r.status_code == 200:
                data = r.json()
                return self._parse(data, destination, checkin, checkout)
            elif r.status_code == 401:
                print("Invalid OpenWeatherMap API key")
            elif r.status_code == 404:
                print(f"City not found: {destination}")
            else:
                print(f"OWM error: {r.text[:200]}")

        except Exception as e:
            print(f"Weather error: {e}")

        return self._mock(destination, checkin, checkout, days)

    def _parse(self, data, destination, checkin, checkout):
        """Parse OWM 3-hour forecast — filter to trip dates only."""
        try:
            city_info = data.get("city", {})
            dest_name = city_info.get("name", destination)
            country = city_info.get("country", "")
            items = data.get("list", [])

            # Parse trip date range
            try:
                checkin_dt = datetime.strptime(checkin, "%Y-%m-%d").date()
                checkout_dt = datetime.strptime(checkout, "%Y-%m-%d").date() if checkout else None
            except:
                checkin_dt = None
                checkout_dt = None

            # Group by day
            days_dict = {}
            for item in items:
                dt_txt = item.get("dt_txt", "")
                day_key = dt_txt[:10] if dt_txt else ""
                if not day_key:
                    continue
                # Filter: only include dates within trip range
                if checkin_dt:
                    try:
                        item_date = datetime.strptime(day_key, "%Y-%m-%d").date()
                        if item_date < checkin_dt:
                            continue  # skip dates before trip
                        if checkout_dt and item_date > checkout_dt:
                            continue  # skip dates after trip
                    except:
                        pass
                if day_key not in days_dict:
                    days_dict[day_key] = []
                days_dict[day_key].append(item)

            daily = []
            for date_str, slots in sorted(days_dict.items()):
                try:
                    dt = datetime.strptime(date_str, "%Y-%m-%d")
                    temps = [s["main"]["temp"] for s in slots if s.get("main")]
                    humidities = [s["main"].get("humidity", 65) for s in slots if s.get("main")]
                    rain_chances = [int(s.get("pop", 0) * 100) for s in slots]
                    winds = [s.get("wind", {}).get("speed", 0) * 3.6 for s in slots]

                    midday = next((s for s in slots if "12:00" in s.get("dt_txt", "")), slots[len(slots)//2])
                    condition = midday.get("weather", [{}])[0].get("description", "Clear").title()
                    weather_id = midday.get("weather", [{}])[0].get("id", 800)

                    max_c = round(max(temps), 1) if temps else 25
                    min_c = round(min(temps), 1) if temps else 18

                    daily.append({
                        "date": date_str,
                        "day_name": dt.strftime("%A, %b %d"),
                        "max_temp_c": max_c,
                        "min_temp_c": min_c,
                        "max_temp_f": round(max_c * 9/5 + 32, 1),
                        "min_temp_f": round(min_c * 9/5 + 32, 1),
                        "condition": condition,
                        "weather_id": weather_id,
                        "rain_chance": max(rain_chances) if rain_chances else 0,
                        "humidity": int(sum(humidities)/len(humidities)) if humidities else 65,
                        "uv_index": self._uv_from_id(weather_id),
                        "wind_kph": round(sum(winds)/len(winds), 1) if winds else 15,
                    })
                except Exception as e:
                    print(f"Day parse error {date_str}: {e}")

            if not daily:
                print("No matching forecast dates for trip — using seasonal mock")
                return self._seasonal_mock(destination, checkin, checkout,
                                          (checkout_dt - checkin_dt).days + 1 if checkout_dt and checkin_dt else 5)

            # Current = first item overall (not filtered)
            all_items = data.get("list", [])
            cur = all_items[0] if all_items else {}
            cur_main = cur.get("main", {})
            cur_temp = cur_main.get("temp", 25)
            cur_w = cur.get("weather", [{}])[0]

            return {
                "success": True,
                "destination": dest_name,
                "country": country,
                "checkin": checkin,
                "checkout": checkout,
                "current": {
                    "temp_c": round(cur_temp, 1),
                    "temp_f": round(cur_temp * 9/5 + 32, 1),
                    "condition": cur_w.get("description", "Clear").title(),
                    "humidity": cur_main.get("humidity", 65),
                    "wind_kph": round(cur.get("wind", {}).get("speed", 4) * 3.6, 1),
                    "is_raining": "rain" in cur_w.get("description", "").lower()
                },
                "forecast": daily,
                "source": "live"
            }
        except Exception as e:
            print(f"OWM parse error: {e}")
            return self._seasonal_mock(destination, checkin, checkout, 5)

    def _seasonal_mock(self, destination, checkin, checkout, days):
        """Generate realistic seasonal weather based on destination and travel month."""
        try:
            month = datetime.strptime(checkin, "%Y-%m-%d").month
        except:
            month = 6

        dest_lower = destination.lower()

        # Seasonal temperature profiles by region
        if any(c in dest_lower for c in ["paris","london","berlin","amsterdam","rome","barcelona","madrid"]):
            # Europe
            temps = {1:(4,0), 2:(5,1), 3:(10,4), 4:(15,8), 5:(19,12), 6:(23,15),
                     7:(25,17), 8:(25,17), 9:(21,13), 10:(15,9), 11:(9,4), 12:(5,1)}
            rain_high = [6,7,8,9,10,11]
        elif any(c in dest_lower for c in ["singapore","bangkok","kuala lumpur","jakarta","bali"]):
            # Southeast Asia (tropical)
            temps = {m: (31, 24) for m in range(1,13)}
            rain_high = [1,2,3,11,12]
        elif any(c in dest_lower for c in ["dubai","abu dhabi","doha","cairo"]):
            # Middle East
            temps = {1:(24,14), 2:(26,15), 3:(30,18), 4:(35,22), 5:(40,27),
                     6:(41,29), 7:(42,30), 8:(42,30), 9:(39,26), 10:(34,22),
                     11:(29,18), 12:(25,15)}
            rain_high = [1,2,12]
        elif any(c in dest_lower for c in ["tokyo","osaka","seoul","beijing","shanghai"]):
            # East Asia
            temps = {1:(10,2), 2:(11,2), 3:(14,5), 4:(19,11), 5:(23,16), 6:(26,20),
                     7:(30,24), 8:(31,25), 9:(27,21), 10:(22,15), 11:(17,9), 12:(12,4)}
            rain_high = [6,7,8,9]
        elif any(c in dest_lower for c in ["new york","chicago","boston","atlanta","miami"]):
            # North America
            temps = {1:(4,-2), 2:(6,-1), 3:(11,3), 4:(17,8), 5:(22,13), 6:(27,18),
                     7:(29,21), 8:(28,20), 9:(24,16), 10:(18,10), 11:(12,5), 12:(6,0)}
            rain_high = [3,4,5,7,8]
        elif any(c in dest_lower for c in ["sydney","melbourne","auckland"]):
            # Southern hemisphere (seasons flipped)
            temps = {1:(26,18), 2:(26,18), 3:(24,16), 4:(21,13), 5:(18,10),
                     6:(15,8), 7:(14,7), 8:(15,8), 9:(17,10), 10:(20,13),
                     11:(22,15), 12:(24,17)}
            rain_high = [6,7,8]
        else:
            # Generic temperate
            temps = {1:(15,8), 2:(16,9), 3:(18,11), 4:(22,14), 5:(25,17),
                     6:(28,20), 7:(30,22), 8:(30,22), 9:(27,19), 10:(23,15),
                     11:(19,12), 12:(16,9)}
            rain_high = [4,5,6]

        max_c, min_c = temps.get(month, (25, 18))
        is_rainy = month in rain_high

        conditions_dry = ["Sunny", "Partly Cloudy", "Clear Sky", "Sunny", "Light Breeze"]
        conditions_wet = ["Partly Cloudy", "Light Rain", "Cloudy", "Showers", "Partly Cloudy"]
        conditions = conditions_wet if is_rainy else conditions_dry

        base = datetime.strptime(checkin, "%Y-%m-%d") if checkin else datetime.now()
        forecast = []
        for i in range(min(days, 7)):
            dt = base + timedelta(days=i)
            cond = conditions[i % len(conditions)]
            day_max = max_c + (i % 3 - 1)  # slight variation
            day_min = min_c + (i % 2)
            rain_chance = 55 if "Rain" in cond or "Shower" in cond else (20 if is_rainy else 8)
            forecast.append({
                "date": dt.strftime("%Y-%m-%d"),
                "day_name": dt.strftime("%A, %b %d"),
                "max_temp_c": day_max, "min_temp_c": day_min,
                "max_temp_f": round(day_max * 9/5 + 32, 1),
                "min_temp_f": round(day_min * 9/5 + 32, 1),
                "condition": cond,
                "rain_chance": rain_chance,
                "humidity": 75 if is_rainy else 55,
                "uv_index": 8 if max_c > 28 else 5,
                "wind_kph": 18
            })

        return {
            "success": True, "destination": destination, "country": "",
            "checkin": checkin, "checkout": checkout,
            "current": {
                "temp_c": max_c, "temp_f": round(max_c * 9/5 + 32, 1),
                "condition": conditions[0],
                "humidity": 75 if is_rainy else 55,
                "wind_kph": 18, "is_raining": is_rainy
            },
            "forecast": forecast,
            "source": "seasonal_estimate"
        }

    def _uv_from_id(self, weather_id: int) -> int:
        """Estimate UV index from OWM weather condition ID."""
        if weather_id >= 800: return 8  # Clear/sunny
        if weather_id >= 700: return 3  # Atmosphere
        if weather_id >= 600: return 2  # Snow
        if weather_id >= 500: return 2  # Rain
        if weather_id >= 300: return 3  # Drizzle
        if weather_id >= 200: return 2  # Thunderstorm
        return 5

    def _mock(self, destination, checkin, checkout, days):
        base = datetime.strptime(checkin, "%Y-%m-%d") if checkin else datetime.now()
        conditions = ["Sunny","Partly Cloudy","Cloudy","Light Rain",
                      "Sunny","Clear","Partly Cloudy","Thunderstorm"]
        forecast = []
        for i in range(min(days, 8)):
            dt = base + timedelta(days=i)
            cond = conditions[i % len(conditions)]
            forecast.append({
                "date": dt.strftime("%Y-%m-%d"),
                "day_name": dt.strftime("%A, %b %d"),
                "max_temp_c": 27-i%3, "min_temp_c": 19,
                "max_temp_f": 81-i%3*2, "min_temp_f": 66,
                "condition": cond,
                "rain_chance": 65 if "Rain" in cond or "Thunder" in cond else 10,
                "humidity": 70, "uv_index": 7, "wind_kph": 14
            })
        return {
            "success": True, "destination": destination, "country": "",
            "checkin": checkin, "checkout": checkout,
            "current": {"temp_c": 25, "temp_f": 77, "condition": "Partly Cloudy",
                        "humidity": 68, "wind_kph": 14, "is_raining": False},
            "forecast": forecast, "source": "simulated"
        }

    def format_for_display(self, data):
        if not data.get("success"): return "❌ Weather unavailable."
        cur = data["current"]
        fc = data.get("forecast", [])
        dest = data.get("destination", "")
        country = data.get("country", "")
        src = ("*(live data)*" if data.get("source") == "live"
               else "*(seasonal estimate — live data available closer to trip)*"
               if data.get("source") == "seasonal_estimate"
               else "*(sample data)*")
        loc = f"{dest}, {country}" if country else dest
        icons = {
            "sunny": "☀️", "clear": "☀️", "partly": "⛅",
            "cloud": "☁️", "overcast": "☁️", "rain": "🌧️",
            "shower": "🌦️", "thunder": "⛈️", "storm": "⛈️",
            "snow": "❄️", "fog": "🌫️", "mist": "🌫️", "haze": "🌫️"
        }
        lines = [
            f"### 🌤️ Weather for {loc} {src}",
            f"**Trip:** {data.get('checkin','')} → {data.get('checkout','')}\n",
            f"**Now:** {cur['condition']} | 🌡️ {cur['temp_c']}°C / {cur['temp_f']}°F "
            f"| 💧 {cur['humidity']}% | 💨 {cur['wind_kph']} km/h\n",
            "**📅 Day-by-Day Forecast:**\n"
        ]
        any_rain = False
        any_hot = False
        for d in fc:
            cond_lower = d["condition"].lower()
            icon = next((v for k, v in icons.items() if k in cond_lower), "🌤️")
            if d["rain_chance"] > 50: any_rain = True
            if d.get("max_temp_c", 0) > 30: any_hot = True
            uv_note = " ⚠️ High UV!" if d.get("uv_index", 0) >= 8 else ""
            lines.append(
                f"  {icon} **{d['day_name']}**: {d['condition']}\n"
                f"     🌡️ {d['max_temp_c']}°C / {d['min_temp_c']}°C  |  "
                f"🌧️ Rain: {d['rain_chance']}%  |  "
                f"💧 {d['humidity']}%  |  "
                f"🌬️ {d['wind_kph']} km/h{uv_note}\n"
            )
        packing = []
        if any_rain: packing.append("🌂 Umbrella/raincoat")
        if any_hot: packing.append("🧴 Sunscreen SPF50+")
        if any(d.get("uv_index", 0) >= 8 for d in fc): packing.append("🕶️ Sunglasses")
        if packing:
            lines.append("\n**🎒 Weather packing tips:** " + " | ".join(packing))
        return "\n".join(lines)
