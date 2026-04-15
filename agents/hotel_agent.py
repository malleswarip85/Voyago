"""
Hotel Agent - SerpAPI Google Hotels
Searches hotels near the destination airport city.
Recommends based on budget, rating and trip itinerary match.
"""
import requests, os, math
from datetime import datetime

SERPAPI_BASE = "https://serpapi.com/search"

# Airport code → city name for precise hotel search
AIRPORT_CITIES = {
    # India
    "DEL": "New Delhi", "BOM": "Mumbai", "BLR": "Bangalore",
    "HYD": "Hyderabad", "MAA": "Chennai", "CCU": "Kolkata",
    "COK": "Kochi", "PNQ": "Pune", "AMD": "Ahmedabad", "GOI": "Goa",
    # USA
    "JFK": "New York", "LAX": "Los Angeles", "ORD": "Chicago",
    "ATL": "Atlanta", "DFW": "Dallas", "MIA": "Miami",
    "SFO": "San Francisco", "SEA": "Seattle", "BOS": "Boston",
    "LAS": "Las Vegas", "MCO": "Orlando", "IAH": "Houston",
    # Europe
    "LHR": "London", "LGW": "London", "CDG": "Paris", "ORY": "Paris",
    "FRA": "Frankfurt", "MUC": "Munich", "BER": "Berlin",
    "FCO": "Rome", "MXP": "Milan", "VCE": "Venice",
    "MAD": "Madrid", "BCN": "Barcelona", "AMS": "Amsterdam",
    "LIS": "Lisbon", "ATH": "Athens", "VIE": "Vienna",
    "ZRH": "Zurich", "BRU": "Brussels", "ARN": "Stockholm",
    # Asia
    "NRT": "Tokyo", "HND": "Tokyo", "KIX": "Osaka",
    "ICN": "Seoul", "GMP": "Seoul", "PEK": "Beijing",
    "PKX": "Beijing", "PVG": "Shanghai", "SHA": "Shanghai",
    "SIN": "Singapore", "BKK": "Bangkok", "DMK": "Bangkok",
    "HKT": "Phuket", "KUL": "Kuala Lumpur", "CGK": "Jakarta",
    "DPS": "Bali", "MNL": "Manila", "HKG": "Hong Kong",
    "TPE": "Taipei", "CAN": "Guangzhou",
    # Middle East
    "DXB": "Dubai", "DWC": "Dubai", "AUH": "Abu Dhabi",
    "DOH": "Doha", "RUH": "Riyadh",
    # Others
    "SYD": "Sydney", "MEL": "Melbourne", "BNE": "Brisbane",
    "YYZ": "Toronto", "YVR": "Vancouver", "YUL": "Montreal",
    "GRU": "São Paulo", "GIG": "Rio de Janeiro",
    "JNB": "Johannesburg", "CPT": "Cape Town",
    "CAI": "Cairo", "IST": "Istanbul", "AYT": "Antalya",
    "NBO": "Nairobi", "CMN": "Casablanca",
}


class HotelAgent:
    def __init__(self):
        pass

    def _key(self):
        return os.getenv("SERPAPI_KEY", "")

    def get_search_city(self, destination, destination_iata=None):
        """Get the best city name to search hotels in."""
        # If user selected a specific airport, use that city
        if destination_iata and destination_iata in AIRPORT_CITIES:
            city = AIRPORT_CITIES[destination_iata]
            print(f"Hotel search city from airport {destination_iata}: {city}")
            return city, destination_iata

        # Otherwise use destination name
        return destination, None

    def search_hotels(self, destination, checkin, checkout, travelers,
                      budget, destination_iata=None):
        rooms = max(1, math.ceil(travelers / 2))
        key = self._key()

        # Determine best city to search
        search_city, airport_code = self.get_search_city(destination, destination_iata)
        print(f"Hotel search: city={search_city}, airport={airport_code}, key={'SET' if key else 'NOT SET'}")

        if not key:
            print("No SerpAPI key — using mock")
            return self._mock(search_city, destination, checkin, checkout,
                            travelers, budget, rooms, airport_code)

        try:
            # Search hotels near the airport city
            query = f"hotels near {search_city} airport" if airport_code \
                    else f"hotels in {search_city}"

            params = {
                "engine": "google_hotels",
                "q": query,
                "check_in_date": checkin,
                "check_out_date": checkout,
                "adults": str(travelers),
                "rooms": str(rooms),
                "currency": "USD",
                "gl": "us",
                "hl": "en",
                "api_key": key,
                "sort_by": "3",  # lowest price first
            }

            r = requests.get(SERPAPI_BASE, params=params, timeout=20)
            print(f"SerpAPI status: {r.status_code}")

            if r.status_code == 200:
                data = r.json()
                hotels = self._parse(data, search_city, destination,
                                    checkin, checkout, rooms, budget, airport_code)
                if hotels:
                    print(f"SerpAPI returned {len(hotels)} live hotels in {search_city}")
                    return {
                        "success": True, "hotels": hotels,
                        "source": "live", "rooms": rooms,
                        "search_city": search_city,
                        "airport_code": airport_code
                    }
                print("No hotels parsed — using mock")
            else:
                print(f"SerpAPI error {r.status_code}: {r.text[:200]}")

        except Exception as e:
            print(f"SerpAPI exception: {e}")

        return self._mock(search_city, destination, checkin, checkout,
                         travelers, budget, rooms, airport_code)

    def _parse(self, data, search_city, destination, checkin,
               checkout, rooms, budget, airport_code):
        hotels = []
        try:
            raw = data.get("properties", [])
            print(f"SerpAPI raw hotels: {len(raw)}")

            nights = max(1, (
                datetime.strptime(checkout, "%Y-%m-%d") -
                datetime.strptime(checkin, "%Y-%m-%d")
            ).days)

            for h in raw[:8]:
                try:
                    name = h.get("name", "Unknown Hotel")

                    # Price extraction
                    price = self._extract_price(h, nights)
                    if price <= 10:
                        print(f"Skipping {name}: no valid price")
                        continue

                    # Rating (Google 1-5 → convert to 1-10)
                    try:
                        rating = float(h.get("overall_rating") or 0)
                        if 0 < rating <= 5:
                            rating = round(rating * 2, 1)
                        elif rating == 0:
                            rating = 7.0
                    except:
                        rating = 7.0

                    # Stars
                    try:
                        star_str = str(h.get("hotel_class", "3 out of 5 stars"))
                        stars = int(star_str[0]) if star_str[0].isdigit() else 3
                    except:
                        stars = 3

                    # Location — prefer neighborhood, then address
                    location = (
                        h.get("neighborhood") or
                        h.get("location") or
                        h.get("address") or
                        search_city
                    )
                    if not location or str(location) == "None":
                        location = search_city

                    # Distance from airport if available
                    dist_info = ""
                    if airport_code:
                        desc = h.get("description", "") or ""
                        if "airport" in desc.lower():
                            dist_info = " (near airport)"

                    # Amenities
                    amenities_raw = h.get("amenities", [])
                    amenities = [a for a in amenities_raw[:5]
                                if isinstance(a, str) and a] if amenities_raw else []
                    if not amenities:
                        amenities = ["Free WiFi", "24hr Reception"]

                    # Budget fit label
                    total = round(price * rooms * nights, 2)
                    budget_pct = (total / budget * 100) if budget else 0
                    if budget_pct <= 30:
                        budget_label = "💚 Budget-friendly"
                    elif budget_pct <= 45:
                        budget_label = "💛 Good value"
                    else:
                        budget_label = "💰 Premium"

                    hotels.append({
                        "name": name,
                        "rating": round(rating, 1),
                        "review_count": int(h.get("reviews") or 0),
                        "price_per_night_per_room": round(price, 2),
                        "rooms": rooms,
                        "stars": min(5, max(1, stars)),
                        "amenities": amenities,
                        "location": f"{location}{dist_info}",
                        "search_city": search_city,
                        "airport_code": airport_code or "",
                        "budget_label": budget_label,
                        "checkin": checkin,
                        "checkout": checkout,
                        "link": h.get("link", ""),
                        "source": "live"
                    })

                except Exception as e:
                    print(f"Hotel row error: {e}")
                    continue

        except Exception as e:
            print(f"SerpAPI parse error: {e}")

        # Sort: within budget first (by rating), then cheapest
        hotels.sort(key=lambda x: (
            x["price_per_night_per_room"] * rooms * nights > budget * 0.45,
            -x["rating"],
            x["price_per_night_per_room"]
        ))
        return hotels[:3]

    def _extract_price(self, h, nights):
        """Extract nightly price from SerpAPI hotel data."""
        # Try rate_per_night first
        rpn = h.get("rate_per_night", {})
        if isinstance(rpn, dict):
            for field in ["extracted_lowest", "extracted_before_taxes_fees"]:
                val = rpn.get(field)
                if val and float(val) > 10:
                    return float(val)
            # Try string fields
            for field in ["lowest", "before_taxes_fees"]:
                val = str(rpn.get(field, "0"))
                cleaned = ''.join(c for c in val if c.isdigit() or c == '.')
                if cleaned and float(cleaned) > 10:
                    return float(cleaned)

        # Try total_rate / nights
        tr = h.get("total_rate", {})
        if isinstance(tr, dict):
            for field in ["extracted_lowest", "extracted_before_taxes_fees"]:
                val = tr.get(field)
                if val and float(val) > 10:
                    return round(float(val) / max(nights, 1), 2)

        return 0

    def _mock(self, search_city, destination, checkin, checkout,
              travelers, budget, rooms, airport_code=None):
        nightly = min((budget * 0.35) / max(rooms, 1), 400)
        city = search_city or destination.split(",")[0].strip()
        airport_note = f" near {airport_code} Airport" if airport_code else ""
        return {
            "success": True, "rooms": rooms, "source": "simulated",
            "search_city": city, "airport_code": airport_code or "",
            "hotels": [
                {
                    "name": f"The Grand {city} Hotel",
                    "stars": 5, "rating": 9.1, "review_count": 2840,
                    "price_per_night_per_room": round(nightly * 1.1, 2),
                    "amenities": ["Free WiFi","Pool","Spa","Restaurant","Airport Shuttle"],
                    "rooms": rooms, "location": f"{city} City Center{airport_note}",
                    "search_city": city, "airport_code": airport_code or "",
                    "budget_label": "💛 Good value",
                    "checkin": checkin, "checkout": checkout, "source": "simulated"
                },
                {
                    "name": f"{city} Boutique Hotel",
                    "stars": 4, "rating": 8.6, "review_count": 1420,
                    "price_per_night_per_room": round(nightly * 0.65, 2),
                    "amenities": ["Free WiFi","Breakfast Included","Gym","Bar"],
                    "rooms": rooms, "location": f"Downtown {city}{airport_note}",
                    "search_city": city, "airport_code": airport_code or "",
                    "budget_label": "💚 Budget-friendly",
                    "checkin": checkin, "checkout": checkout, "source": "simulated"
                },
                {
                    "name": f"{city} Budget Inn",
                    "stars": 3, "rating": 7.8, "review_count": 890,
                    "price_per_night_per_room": round(nightly * 0.38, 2),
                    "amenities": ["Free WiFi","24hr Reception"],
                    "rooms": rooms, "location": f"Near Transit, {city}{airport_note}",
                    "search_city": city, "airport_code": airport_code or "",
                    "budget_label": "💚 Budget-friendly",
                    "checkin": checkin, "checkout": checkout, "source": "simulated"
                },
            ]
        }

    def total_cost(self, hotel, nights):
        return round(hotel["price_per_night_per_room"] * hotel["rooms"] * nights, 2)

    def recommend(self, hotels, nights, budget):
        """Recommend: cheapest within 45% of budget with highest rating."""
        if not hotels: return 0
        hotel_budget = budget * 0.45
        within = [(i, self.total_cost(h, nights), h["rating"])
                  for i, h in enumerate(hotels)
                  if self.total_cost(h, nights) <= hotel_budget]
        if within:
            within.sort(key=lambda x: x[2], reverse=True)  # highest rating first
            return within[0][0]
        # Fallback: cheapest
        return min(range(len(hotels)),
                   key=lambda i: self.total_cost(hotels[i], nights))

    def format_for_display(self, data, nights, budget=0):
        if not data.get("hotels"):
            return "❌ No hotels found."
        hotels = data["hotels"]
        rooms = data.get("rooms", 1)
        search_city = data.get("search_city", "")
        airport_code = data.get("airport_code", "")
        src = "*(live data — Google Hotels)*" if data.get("source") == "live" \
              else "*(estimated — verify on Booking.com)*"

        location_note = f"near **{airport_code}** airport in **{search_city}**" \
                        if airport_code else f"in **{search_city}**"

        best = self.recommend(hotels, nights, budget)
        lines = [
            f"### 🏨 Available Hotels {src}",
            f"*Searching {location_note} · {rooms} room(s) · {nights} nights*\n"
        ]

        for i, h in enumerate(hotels):
            stars = "⭐" * int(h.get("stars", 3))
            total = self.total_cost(h, nights)
            amenities = ", ".join(h.get("amenities", [])[:4])
            badge = " 🏆 **BEST PICK**" if i == best else ""
            pct = f" *({total/budget*100:.0f}% of budget)*" if budget else ""
            link = f" · [View]({h['link']})" if h.get("link") else ""
            budget_label = h.get("budget_label", "")

            lines.append(
                f"**Option {i+1}: {h['name']}** {stars}{badge} {budget_label}\n"
                f"  • Rating: **{h['rating']}/10** ({h.get('review_count',0):,} reviews)\n"
                f"  • 📍 {h['location']}{link}\n"
                f"  • ${h['price_per_night_per_room']:,.2f}/night × {rooms} room(s) × {nights} nights\n"
                f"  • **Total: ${total:,.2f}**{pct}\n"
                f"  • Amenities: {amenities}\n"
            )

        bh = hotels[best]
        bt = self.total_cost(bh, nights)
        reason = "best rated within budget" if bt <= budget * 0.45 else "cheapest available"
        lines.append(
            f"\n✅ **Recommended Hotel:** {bh['name']} "
            f"({'⭐'*int(bh.get('stars',3))}) — "
            f"**${bt:,.2f}** total for {nights} nights *({reason})*"
        )
        return "\n".join(lines)
