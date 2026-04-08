"""
Hotel Booking Agent
Uses Booking.com API via RapidAPI to search hotels.
"""

import requests
import os


RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
BOOKING_HOST = "booking-com15.p.rapidapi.com"


class HotelAgent:
    def __init__(self):
        self.headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": BOOKING_HOST
        }

    def search_hotels(self, destination: str, checkin: str, checkout: str, travelers: int, budget: float) -> dict:
        """Search hotels via Booking.com RapidAPI."""
        try:
            # Step 1: Get destination ID
            dest_id = self._get_destination_id(destination)

            # Step 2: Search hotels
            url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchHotels"
            params = {
                "dest_id": dest_id,
                "search_type": "city",
                "arrival_date": checkin,
                "departure_date": checkout,
                "adults": str(travelers),
                "room_qty": "1",
                "page_number": "1",
                "currency_code": "USD",
                "languagecode": "en-us"
            }

            response = requests.get(url, headers=self.headers, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                return self._parse_hotel_results(data, destination, checkin, checkout, travelers, budget)
            else:
                return self._mock_hotels(destination, checkin, checkout, travelers, budget)

        except Exception as e:
            print(f"Hotel search error: {e}")
            return self._mock_hotels(destination, checkin, checkout, travelers, budget)

    def _get_destination_id(self, destination: str) -> str:
        """Search for destination ID."""
        try:
            url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchDestination"
            params = {"query": destination}
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                results = data.get("data", [])
                if results:
                    return str(results[0].get("dest_id", "-2092174"))
        except Exception:
            pass
        return "-2092174"  # Default to Paris

    def _parse_hotel_results(self, data: dict, destination: str, checkin: str, checkout: str, travelers: int, budget: float) -> dict:
        """Parse API response into clean hotel results."""
        try:
            hotels_raw = data.get("data", {}).get("hotels", [])
            hotels = []
            for h in hotels_raw[:3]:
                prop = h.get("property", {})
                price_info = prop.get("priceBreakdown", {}).get("grossPrice", {})
                price = float(price_info.get("value", 0))
                hotels.append({
                    "name": prop.get("name", "Unknown Hotel"),
                    "rating": prop.get("reviewScore", 8.0),
                    "review_count": prop.get("reviewCount", 100),
                    "price_per_night": round(price, 2),
                    "stars": prop.get("propertyClass", 3),
                    "location": destination,
                    "checkin": checkin,
                    "checkout": checkout,
                })
            if hotels:
                return {"success": True, "hotels": hotels, "source": "live"}
        except Exception:
            pass
        return self._mock_hotels(destination, checkin, checkout, travelers, budget)

    def _mock_hotels(self, destination: str, checkin: str, checkout: str, travelers: int, budget: float) -> dict:
        """Return realistic mock hotel data."""
        nightly_budget = budget / 3  # rough estimate for hotel portion
        hotels = [
            {
                "name": f"Grand {destination} Hotel",
                "stars": 5,
                "rating": 9.2,
                "review_count": 2847,
                "price_per_night": min(nightly_budget * 0.9, 350),
                "amenities": ["Free WiFi", "Pool", "Spa", "Restaurant", "Airport Shuttle"],
                "location": f"City Center, {destination}",
                "checkin": checkin,
                "checkout": checkout,
            },
            {
                "name": f"{destination} Boutique Inn",
                "stars": 4,
                "rating": 8.7,
                "review_count": 1203,
                "price_per_night": min(nightly_budget * 0.6, 200),
                "amenities": ["Free WiFi", "Breakfast Included", "Gym", "Bar"],
                "location": f"Downtown, {destination}",
                "checkin": checkin,
                "checkout": checkout,
            },
            {
                "name": f"{destination} Budget Comfort",
                "stars": 3,
                "rating": 7.9,
                "review_count": 856,
                "price_per_night": min(nightly_budget * 0.35, 100),
                "amenities": ["Free WiFi", "24hr Reception", "Breakfast Available"],
                "location": f"Near Airport, {destination}",
                "checkin": checkin,
                "checkout": checkout,
            },
        ]
        return {"success": True, "hotels": hotels, "source": "simulated"}

    def format_for_display(self, hotel_data: dict, nights: int) -> str:
        """Format hotel results for chat display."""
        if not hotel_data.get("success"):
            return "❌ Could not find hotels for your destination."

        hotels = hotel_data.get("hotels", [])
        source_note = " *(live data)*" if hotel_data.get("source") == "live" else " *(sample data)*"

        lines = [f"🏨 **Available Hotels**{source_note}\n"]
        for i, h in enumerate(hotels, 1):
            stars = "⭐" * int(h.get("stars", 3))
            total = h["price_per_night"] * nights
            amenities = ", ".join(h.get("amenities", [])[:3])
            lines.append(
                f"**Option {i}: {h['name']}** {stars}\n"
                f"  • Rating: {h['rating']}/10 ({h.get('review_count', 0):,} reviews)\n"
                f"  • Location: {h['location']}\n"
                f"  • Price: ${h['price_per_night']:,.2f}/night\n"
                f"  • **Total ({nights} nights): ${total:,.2f}**\n"
                f"  • Amenities: {amenities}\n"
            )
        return "\n".join(lines)
