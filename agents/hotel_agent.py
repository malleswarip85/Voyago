"""
Hotel Agent - Booking.com via RapidAPI
Host: booking-com15.p.rapidapi.com
Key: RAPIDAPI_KEY in .env
"""
import requests, os, math

HOTEL_HOST = "booking-com15.p.rapidapi.com"

class HotelAgent:
    def __init__(self):
        pass

    def _headers(self):
        return {
            "x-rapidapi-key": os.getenv("RAPIDAPI_KEY", ""),
            "x-rapidapi-host": HOTEL_HOST
        }

    def search_hotels(self, destination, checkin, checkout, travelers, budget):
        rooms = max(1, math.ceil(travelers / 2))
        key = os.getenv("RAPIDAPI_KEY", "")

        if not key:
            print("No RapidAPI key — using mock hotels")
            return self._mock(destination, checkin, checkout, travelers, budget, rooms)

        try:
            dest_id, location_name, country = self._dest_id(destination)
            print(f"Searching hotels in: {location_name}, {country} (dest_id={dest_id})")

            url = f"https://{HOTEL_HOST}/api/v1/hotels/searchHotels"
            params = {
                "dest_id": dest_id,
                "search_type": "city",
                "arrival_date": checkin,
                "departure_date": checkout,
                "adults": str(travelers),
                "room_qty": str(rooms),
                "page_number": "1",
                "currency_code": "USD",
                "languagecode": "en-us",
                "sort_by": "popularity"
            }
            r = requests.get(url, headers=self._headers(), params=params, timeout=15)
            print(f"Hotel API status: {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                hotels = self._parse(data, destination, checkin, checkout, rooms, location_name)
                if hotels:
                    return {"success": True, "hotels": hotels, "source": "live", "rooms": rooms}
                print("No valid hotels parsed — using mock")
        except Exception as e:
            print(f"Hotel API error: {e}")

        return self._mock(destination, checkin, checkout, travelers, budget, rooms)

    def _dest_id(self, destination):
        try:
            url = f"https://{HOTEL_HOST}/api/v1/hotels/searchDestination"
            r = requests.get(url, headers=self._headers(),
                           params={"query": destination}, timeout=10)
            print(f"Hotel dest search: {r.status_code}")
            if r.status_code == 200:
                results = r.json().get("data", [])
                print(f"Hotel dest results: {[(x.get('city_name',''),x.get('country',''),x.get('dest_id','')) for x in results[:3]]}")

                dest_lower = destination.lower().strip()

                # Try to find best matching result
                for result in results[:5]:
                    city = (result.get("city_name") or result.get("label") or "").lower()
                    country = (result.get("country") or "").lower()
                    dest_type = result.get("dest_type", "")

                    # Prefer city-type results that match our destination
                    if dest_type == "city" and (dest_lower in city or city in dest_lower):
                        dest_id = str(result.get("dest_id", ""))
                        if dest_id:
                            print(f"Matched city: {city}, {country} → dest_id={dest_id}")
                            return dest_id, city.title(), country.title()

                # Fallback: first result
                if results:
                    first = results[0]
                    dest_id = str(first.get("dest_id", "-2092174"))
                    city = first.get("city_name") or first.get("label") or destination
                    country = first.get("country") or ""
                    print(f"Using first result: {city} → dest_id={dest_id}")
                    return dest_id, city.title(), country.title()

        except Exception as e:
            print(f"Dest search error: {e}")
        return "-2092174", destination, ""

    def _parse(self, data, destination, checkin, checkout, rooms, location_name):
        hotels = []
        try:
            raw = (data.get("data", {}).get("hotels") or
                   data.get("hotels") or [])
            print(f"Found {len(raw)} hotels from API")
            for h in raw[:6]:
                prop = h.get("property", h)
                price_obj = (prop.get("priceBreakdown", {}).get("grossPrice") or
                            prop.get("price") or {})
                price = float(price_obj.get("value") or price_obj.get("amount") or 0)
                if price <= 0:
                    continue

                # Get actual hotel location from API
                hotel_city = (prop.get("wishlistName") or
                             prop.get("city") or
                             location_name or destination)

                # Get accurate name
                hotel_name = prop.get("name", "Unknown Hotel")

                # Skip if hotel name contains unrelated location keywords
                # (this catches cases where API returns wrong region)
                unrelated_keywords = self._get_unrelated_keywords(destination)
                name_lower = hotel_name.lower()
                if any(k in name_lower for k in unrelated_keywords):
                    print(f"Skipping potentially mismatched hotel: {hotel_name}")
                    continue

                amenities_raw = prop.get("amenities") or []
                if isinstance(amenities_raw, list) and amenities_raw and isinstance(amenities_raw[0], dict):
                    amenities = [a.get("name","") for a in amenities_raw[:5] if a.get("name")]
                elif isinstance(amenities_raw, list):
                    amenities = [a for a in amenities_raw[:5] if isinstance(a, str)]
                else:
                    amenities = []

                if not amenities:
                    amenities = ["Free WiFi", "24hr Reception"]

                rating = float(prop.get("reviewScore") or prop.get("reviewScoreWord") and 7.5 or 7.5)
                try:
                    rating = float(prop.get("reviewScore") or 7.5)
                except:
                    rating = 7.5

                hotels.append({
                    "name": hotel_name,
                    "rating": round(rating, 1),
                    "review_count": int(prop.get("reviewCount") or prop.get("reviewNr") or 0),
                    "price_per_night_per_room": round(price, 2),
                    "rooms": rooms,
                    "stars": int(prop.get("propertyClass") or 3),
                    "amenities": amenities,
                    "location": location_name or destination,
                    "checkin": checkin,
                    "checkout": checkout,
                    "source": "live"
                })
        except Exception as e:
            print(f"Hotel parse error: {e}")
        return hotels[:3]

    def _get_unrelated_keywords(self, destination: str) -> list:
        """Keywords that suggest wrong region results."""
        dest_lower = destination.lower()
        # If searching for non-US destination, filter US state/city names
        us_cities = ["florida","texas","california","georgia","alabama","chicago",
                     "miami","orlando","spring hill","weeki","atlanta","dallas"]
        if not any(us in dest_lower for us in ["usa","us","united states","florida","texas"]):
            return us_cities
        return []

    def _mock(self, destination, checkin, checkout, travelers, budget, rooms):
        nightly = (budget * 0.35) / max(rooms, 1)
        return {
            "success": True, "rooms": rooms, "source": "simulated",
            "hotels": [
                {"name": f"Grand {destination} Resort & Spa", "stars": 5,
                 "rating": 9.3, "review_count": 3241,
                 "price_per_night_per_room": round(min(nightly*1.1, 350), 2),
                 "amenities": ["Free WiFi","Pool","Spa","Restaurant","Airport Shuttle"],
                 "rooms": rooms, "location": f"City Center, {destination}",
                 "checkin": checkin, "checkout": checkout, "source": "simulated"},
                {"name": f"{destination} Boutique Hotel", "stars": 4,
                 "rating": 8.7, "review_count": 1587,
                 "price_per_night_per_room": round(min(nightly*0.7, 180), 2),
                 "amenities": ["Free WiFi","Breakfast Included","Gym","Bar"],
                 "rooms": rooms, "location": f"Downtown, {destination}",
                 "checkin": checkin, "checkout": checkout, "source": "simulated"},
                {"name": f"{destination} Budget Inn", "stars": 3,
                 "rating": 7.8, "review_count": 924,
                 "price_per_night_per_room": round(min(nightly*0.4, 90), 2),
                 "amenities": ["Free WiFi","24hr Reception"],
                 "rooms": rooms, "location": f"Near Transit, {destination}",
                 "checkin": checkin, "checkout": checkout, "source": "simulated"},
            ]
        }

    def total_cost(self, hotel, nights):
        return round(hotel["price_per_night_per_room"] * hotel["rooms"] * nights, 2)

    def recommend(self, hotels, nights, budget):
        """
        Recommend best hotel:
        Priority 1: Cheapest option within 40% of budget
        Priority 2: If multiple fit budget, pick highest rated
        Priority 3: If none fit budget, pick cheapest overall
        """
        if not hotels: return 0

        hotel_budget = budget * 0.40

        # Separate hotels into within-budget and over-budget
        within_budget = []
        over_budget = []
        for i, h in enumerate(hotels):
            total = self.total_cost(h, nights)
            if total <= hotel_budget:
                within_budget.append((i, total, h["rating"]))
            else:
                over_budget.append((i, total, h["rating"]))

        # If hotels within budget exist → pick highest rated among them
        if within_budget:
            # Sort by rating descending (cheapest is already priority via budget filter)
            within_budget.sort(key=lambda x: x[2], reverse=True)
            return within_budget[0][0]

        # No hotels within budget → pick cheapest overall
        all_hotels = [(i, self.total_cost(h, nights), h["rating"])
                      for i, h in enumerate(hotels)]
        all_hotels.sort(key=lambda x: x[1])  # sort by total price ascending
        return all_hotels[0][0]

    def format_for_display(self, data, nights, budget=0):
        if not data.get("hotels"):
            return "❌ No hotels found."
        hotels = data["hotels"]
        rooms = data.get("rooms", 1)
        src = "*(live data)*" if data.get("source") == "live" else "*(sample data)*"
        best = self.recommend(hotels, nights, budget)
        lines = [f"### 🏨 Available Hotels {src}\n",
                 f"*Booking {rooms} room(s) for {nights} nights*\n"]
        for i, h in enumerate(hotels):
            stars = "⭐" * int(h.get("stars", 3))
            total = self.total_cost(h, nights)
            amenities = ", ".join(h.get("amenities", [])[:4])
            badge = " 🏆 **BEST PICK**" if i == best else ""
            pct = f" *({total/budget*100:.0f}% of budget)*" if budget else ""
            lines.append(
                f"**Option {i+1}: {h['name']}** {stars}{badge}\n"
                f"  • Rating: **{h['rating']}/10** ({h.get('review_count',0):,} reviews)\n"
                f"  • Location: {h['location']}\n"
                f"  • ${h['price_per_night_per_room']:,.2f}/night × {rooms} room(s) × {nights} nights\n"
                f"  • **Total: ${total:,.2f}**{pct}\n"
                f"  • Amenities: {amenities}\n"
            )
        bh = hotels[best]
        bt = self.total_cost(bh, nights)
        hotel_budget = budget * 0.40
        reason = (f"best rated within budget (${hotel_budget:,.0f})"
                  if bt <= hotel_budget else "cheapest available option")
        lines.append(
            f"\n✅ **Recommended Hotel:** {bh['name']} "
            f"({'⭐'*int(bh.get('stars',3))}) — "
            f"**${bt:,.2f}** total for {nights} nights "
            f"*({reason})*"
        )
        return "\n".join(lines)
