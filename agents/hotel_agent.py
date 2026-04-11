"""
Hotel Agent - Booking.com via RapidAPI
Host: booking-com15.p.rapidapi.com
Key: RAPIDAPI_KEY in .env / Railway Variables
"""
import requests, os, math

HOTEL_HOST = "booking-com15.p.rapidapi.com"

class HotelAgent:
    def __init__(self):
        pass

    def _headers(self):
        key = os.getenv("RAPIDAPI_KEY", "")
        return {
            "x-rapidapi-key": key,
            "x-rapidapi-host": HOTEL_HOST
        }

    def search_hotels(self, destination, checkin, checkout, travelers, budget):
        rooms = max(1, math.ceil(travelers / 2))
        key = os.getenv("RAPIDAPI_KEY", "")

        print(f"Hotel search: dest={destination}, key_set={'YES' if key else 'NO'}, key_len={len(key)}")

        if not key:
            print("No RapidAPI key — using mock hotels")
            return self._mock(destination, checkin, checkout, travelers, budget, rooms)

        try:
            dest_id, city_name, country_name = self._dest_id(destination)
            print(f"Hotel dest resolved: city={city_name}, country={country_name}, id={dest_id}")

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
                hotels = self._parse(data, destination, checkin, checkout,
                                     rooms, city_name, country_name)
                if hotels:
                    print(f"Returning {len(hotels)} LIVE hotels")
                    return {"success": True, "hotels": hotels,
                            "source": "live", "rooms": rooms}
                print("No hotels parsed from API response — falling back to mock")
            elif r.status_code == 403:
                print("Hotel API 403 — RapidAPI key invalid or not subscribed to Booking.com API")
            elif r.status_code == 429:
                print("Hotel API 429 — Rate limit exceeded")
            else:
                print(f"Hotel API error {r.status_code}: {r.text[:200]}")

        except Exception as e:
            print(f"Hotel search exception: {e}")

        return self._mock(destination, checkin, checkout, travelers, budget, rooms)

    def _dest_id(self, destination):
        """Search for Booking.com dest_id and return (dest_id, city, country)."""
        try:
            url = f"https://{HOTEL_HOST}/api/v1/hotels/searchDestination"
            r = requests.get(url, headers=self._headers(),
                             params={"query": destination}, timeout=10)
            print(f"Dest search status: {r.status_code}")

            if r.status_code == 200:
                results = r.json().get("data", [])
                print(f"Dest results: {[(x.get('city_name','?'), x.get('country','?'), x.get('dest_type','?')) for x in results[:4]]}")

                dest_lower = destination.lower().strip()

                # Priority 1: city-type match
                for res in results[:6]:
                    if res.get("dest_type") == "city":
                        city = res.get("city_name") or res.get("label") or destination
                        country = res.get("country") or ""
                        dest_id = str(res.get("dest_id", ""))
                        if dest_id:
                            print(f"Matched city: {city}, {country}")
                            return dest_id, city, country

                # Priority 2: any result with matching name
                for res in results[:6]:
                    city = (res.get("city_name") or res.get("label") or "").lower()
                    if dest_lower in city or city in dest_lower:
                        dest_id = str(res.get("dest_id", ""))
                        city_name = res.get("city_name") or res.get("label") or destination
                        country = res.get("country") or ""
                        if dest_id:
                            return dest_id, city_name, country

                # Fallback: first result
                if results:
                    first = results[0]
                    dest_id = str(first.get("dest_id", "-2092174"))
                    city = first.get("city_name") or first.get("label") or destination
                    country = first.get("country") or ""
                    return dest_id, city, country

        except Exception as e:
            print(f"Dest search error: {e}")

        return "-2092174", destination, ""

    def _parse(self, data, destination, checkin, checkout, rooms,
               city_name, country_name):
        hotels = []
        try:
            raw = (data.get("data", {}).get("hotels") or
                   data.get("hotels") or [])
            print(f"Raw hotels from API: {len(raw)}")

            # Print first hotel structure for debugging
            if raw:
                prop0 = raw[0].get("property", raw[0])
                print(f"Sample hotel: name={prop0.get('name')}, "
                      f"city={prop0.get('wishlistName') or prop0.get('city')}, "
                      f"score={prop0.get('reviewScore')}, "
                      f"price={prop0.get('priceBreakdown',{}).get('grossPrice',{})}")

            unrelated = self._get_unrelated_keywords(destination)

            for h in raw[:8]:
                try:
                    prop = h.get("property", h)
                    hotel_name = prop.get("name", "Unknown Hotel")

                    # Skip unrelated region results
                    if any(k in hotel_name.lower() for k in unrelated):
                        print(f"Skipping mismatched: {hotel_name}")
                        continue

                    # Price
                    price_obj = (prop.get("priceBreakdown", {}).get("grossPrice") or
                                prop.get("price") or {})
                    price = float(price_obj.get("value") or price_obj.get("amount") or 0)
                    if price <= 0:
                        print(f"Skipping {hotel_name}: no price")
                        continue

                    # Location — try multiple fields
                    hotel_city = (
                        prop.get("wishlistName") or
                        prop.get("countryCode") and city_name or
                        city_name or destination
                    )
                    location_str = f"{city_name}, {country_name}" if country_name else city_name or destination

                    # Amenities
                    amenities_raw = prop.get("amenities") or []
                    if amenities_raw and isinstance(amenities_raw[0], dict):
                        amenities = [a.get("name","") for a in amenities_raw[:5] if a.get("name")]
                    elif amenities_raw and isinstance(amenities_raw[0], str):
                        amenities = amenities_raw[:5]
                    else:
                        amenities = ["Free WiFi", "24hr Reception"]

                    # Rating
                    try:
                        rating = float(prop.get("reviewScore") or 7.0)
                    except:
                        rating = 7.0

                    # Stars
                    try:
                        stars = int(float(prop.get("propertyClass") or 3))
                    except:
                        stars = 3

                    hotels.append({
                        "name": hotel_name,
                        "rating": round(rating, 1),
                        "review_count": int(prop.get("reviewCount") or prop.get("reviewNr") or 0),
                        "price_per_night_per_room": round(price, 2),
                        "rooms": rooms,
                        "stars": min(5, max(1, stars)),
                        "amenities": amenities if amenities else ["Free WiFi"],
                        "location": location_str,
                        "checkin": checkin,
                        "checkout": checkout,
                        "source": "live"
                    })
                except Exception as e:
                    print(f"Hotel row parse error: {e}")
                    continue

        except Exception as e:
            print(f"Hotel parse error: {e}")

        print(f"Parsed {len(hotels)} valid hotels")
        return hotels[:3]

    def _get_unrelated_keywords(self, destination: str) -> list:
        dest_lower = destination.lower()
        us_places = ["florida","texas","california","georgia","alabama",
                     "miami","orlando","spring hill","weeki","dallas","phoenix"]
        if not any(us in dest_lower for us in ["usa","united states","florida","texas","georgia"]):
            return us_places
        return []

    def _mock(self, destination, checkin, checkout, travelers, budget, rooms):
        """Realistic mock data — clearly labeled as estimated."""
        nightly = min((budget * 0.35) / max(rooms, 1), 400)
        # Use destination as city name for mock
        city = destination.split(",")[0].strip()
        return {
            "success": True, "rooms": rooms, "source": "simulated",
            "hotels": [
                {
                    "name": f"The Grand {city} Hotel",
                    "stars": 5, "rating": 9.1, "review_count": 2840,
                    "price_per_night_per_room": round(nightly * 1.1, 2),
                    "amenities": ["Free WiFi","Pool","Spa","Restaurant","Airport Shuttle"],
                    "rooms": rooms, "location": f"{city} City Center",
                    "checkin": checkin, "checkout": checkout, "source": "simulated"
                },
                {
                    "name": f"{city} Boutique Hotel",
                    "stars": 4, "rating": 8.6, "review_count": 1420,
                    "price_per_night_per_room": round(nightly * 0.65, 2),
                    "amenities": ["Free WiFi","Breakfast Included","Gym","Bar"],
                    "rooms": rooms, "location": f"Downtown {city}",
                    "checkin": checkin, "checkout": checkout, "source": "simulated"
                },
                {
                    "name": f"{city} Budget Inn",
                    "stars": 3, "rating": 7.8, "review_count": 890,
                    "price_per_night_per_room": round(nightly * 0.38, 2),
                    "amenities": ["Free WiFi","24hr Reception"],
                    "rooms": rooms, "location": f"Near Transit, {city}",
                    "checkin": checkin, "checkout": checkout, "source": "simulated"
                },
            ]
        }

    def total_cost(self, hotel, nights):
        return round(hotel["price_per_night_per_room"] * hotel["rooms"] * nights, 2)

    def recommend(self, hotels, nights, budget):
        if not hotels: return 0
        hotel_budget = budget * 0.40
        within = [(i, self.total_cost(h, nights), h["rating"])
                  for i, h in enumerate(hotels)
                  if self.total_cost(h, nights) <= hotel_budget]
        if within:
            within.sort(key=lambda x: x[2], reverse=True)
            return within[0][0]
        # Fallback: cheapest
        cheapest = min(range(len(hotels)),
                       key=lambda i: self.total_cost(hotels[i], nights))
        return cheapest

    def format_for_display(self, data, nights, budget=0):
        if not data.get("hotels"):
            return "❌ No hotels found."
        hotels = data["hotels"]
        rooms = data.get("rooms", 1)
        src = "*(live data)*" if data.get("source") == "live" else "*(estimated data — verify on Booking.com)*"
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
                f"  • Location: 📍 {h['location']}\n"
                f"  • ${h['price_per_night_per_room']:,.2f}/night × {rooms} room(s) × {nights} nights\n"
                f"  • **Total: ${total:,.2f}**{pct}\n"
                f"  • Amenities: {amenities}\n"
            )
        bh = hotels[best]
        bt = self.total_cost(bh, nights)
        hotel_budget = budget * 0.40
        reason = ("best rated within budget" if bt <= hotel_budget else "cheapest available")
        lines.append(
            f"\n✅ **Recommended Hotel:** {bh['name']} "
            f"({'⭐'*int(bh.get('stars',3))}) — "
            f"**${bt:,.2f}** total for {nights} nights *({reason})*"
        )
        return "\n".join(lines)
