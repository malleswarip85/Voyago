"""
Flight Booking Agent
Uses Skyscanner API via RapidAPI to search and book flights.
"""

import requests
import os
from datetime import datetime


RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

SKYSCANNER_HOST = "skyscanner89.p.rapidapi.com"


class FlightAgent:
    def __init__(self):
        self.headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": SKYSCANNER_HOST
        }

    def search_flights(self, origin: str, destination: str, date: str, travelers: int) -> dict:
        """Search for flights using Skyscanner API."""
        try:
            # Search for airport/city codes first
            origin_code = self._get_airport_code(origin)
            dest_code = self._get_airport_code(destination)

            url = "https://skyscanner89.p.rapidapi.com/flights/search-one-way"
            params = {
                "origin": origin_code,
                "destination": dest_code,
                "date": date,
                "adults": str(travelers),
                "currency": "USD",
                "countryCode": "US",
                "market": "en-US"
            }

            response = requests.get(url, headers=self.headers, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                return self._parse_flight_results(data, origin, destination, date, travelers)
            else:
                return self._mock_flights(origin, destination, date, travelers)

        except Exception as e:
            print(f"Flight search error: {e}")
            return self._mock_flights(origin, destination, date, travelers)

    def _get_airport_code(self, city: str) -> str:
        """Get IATA airport code for a city."""
        # Common city to IATA mapping
        city_codes = {
            "new york": "JFK", "nyc": "JFK", "london": "LHR", "paris": "CDG",
            "dubai": "DXB", "tokyo": "NRT", "los angeles": "LAX", "la": "LAX",
            "chicago": "ORD", "miami": "MIA", "singapore": "SIN", "sydney": "SYD",
            "toronto": "YYZ", "amsterdam": "AMS", "frankfurt": "FRA", "rome": "FCO",
            "barcelona": "BCN", "madrid": "MAD", "bangkok": "BKK", "hong kong": "HKG",
            "mumbai": "BOM", "delhi": "DEL", "beijing": "PEK", "shanghai": "PVG",
            "san francisco": "SFO", "seattle": "SEA", "boston": "BOS", "dallas": "DFW",
            "atlanta": "ATL", "denver": "DEN", "las vegas": "LAS", "orlando": "MCO",
            "cancun": "CUN", "mexico city": "MEX", "cairo": "CAI", "istanbul": "IST",
            "moscow": "SVO", "berlin": "BER", "vienna": "VIE", "zurich": "ZRH",
            "cape town": "CPT", "johannesburg": "JNB", "nairobi": "NBO",
            "kuala lumpur": "KUL", "jakarta": "CGK", "manila": "MNL",
            "seoul": "ICN", "osaka": "KIX", "taipei": "TPE",
        }
        return city_codes.get(city.lower(), city.upper()[:3])

    def _parse_flight_results(self, data: dict, origin: str, destination: str, date: str, travelers: int) -> dict:
        """Parse API response into clean flight results."""
        try:
            itineraries = data.get("data", {}).get("itineraries", [])
            flights = []
            for item in itineraries[:3]:
                legs = item.get("legs", [])
                price = item.get("price", {}).get("raw", 0)
                if legs:
                    leg = legs[0]
                    flights.append({
                        "airline": leg.get("carriers", {}).get("marketing", [{}])[0].get("name", "Unknown Airline"),
                        "departure": leg.get("departure", date + "T08:00:00"),
                        "arrival": leg.get("arrival", date + "T14:00:00"),
                        "duration": leg.get("durationInMinutes", 360),
                        "stops": len(leg.get("stopCount", 0)),
                        "price_per_person": round(price, 2),
                        "total_price": round(price * travelers, 2),
                        "currency": "USD"
                    })
            if flights:
                return {"success": True, "flights": flights, "source": "live"}
        except Exception:
            pass
        return self._mock_flights(origin, destination, date, travelers)

    def _mock_flights(self, origin: str, destination: str, date: str, travelers: int) -> dict:
        """Return realistic mock flight data as fallback."""
        airlines = [
            {"name": "Emirates", "code": "EK", "base": 450},
            {"name": "Qatar Airways", "code": "QR", "base": 520},
            {"name": "United Airlines", "code": "UA", "base": 380},
        ]
        flights = []
        for i, airline in enumerate(airlines):
            price = airline["base"] + (i * 30)
            flights.append({
                "airline": airline["name"],
                "flight_number": f"{airline['code']}{200 + i * 11}",
                "departure": f"{date}T{7 + i * 3:02d}:00:00",
                "arrival": f"{date}T{13 + i * 3:02d}:30:00",
                "duration": 390 + i * 20,
                "stops": i,
                "stop_city": "Dubai" if i == 1 else None,
                "price_per_person": price,
                "total_price": price * travelers,
                "currency": "USD",
                "origin": origin,
                "destination": destination
            })
        return {"success": True, "flights": flights, "source": "simulated"}

    def format_for_display(self, flight_data: dict) -> str:
        """Format flight results for chat display."""
        if not flight_data.get("success"):
            return "❌ Could not find flights for your route."

        flights = flight_data.get("flights", [])
        source_note = " *(live data)*" if flight_data.get("source") == "live" else " *(sample data)*"

        lines = [f"✈️ **Available Flights**{source_note}\n"]
        for i, f in enumerate(flights, 1):
            duration_h = f['duration'] // 60
            duration_m = f['duration'] % 60
            stops = "Non-stop" if f.get('stops', 0) == 0 else f"{f.get('stops')} stop(s)"
            lines.append(
                f"**Option {i}: {f['airline']}**\n"
                f"  • Departure: {f['departure']}\n"
                f"  • Duration: {duration_h}h {duration_m}m | {stops}\n"
                f"  • Price per person: ${f['price_per_person']:,.2f}\n"
                f"  • **Total: ${f['total_price']:,.2f}**\n"
            )
        return "\n".join(lines)
