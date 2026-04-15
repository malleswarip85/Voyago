"""
Hotel Agent - SerpAPI Google Hotels
Uses SerpAPI to fetch real hotel data from Google Hotels
Free: 100 searches/month
"""
import requests, os, math
from datetime import datetime

SERPAPI_BASE = "https://serpapi.com/search"

class HotelAgent:
    def __init__(self):
        pass

    def _key(self):
        return os.getenv("SERPAPI_KEY", "")

    def search_hotels(self, destination, checkin, checkout, travelers, budget):
        rooms = max(1, math.ceil(travelers / 2))
        key = self._key()

        print(f"Hotel search: dest={destination}, serpapi_key={'SET' if key else 'NOT SET'}")

        if not key:
            print("No SerpAPI key — using mock")
            return self._mock(destination, checkin, checkout, travelers, budget, rooms)

        try:
            # Format dates for Google Hotels (YYYY-MM-DD)
            params = {
                "engine": "google_hotels",
                "q": f"hotels in {destination}",
                "check_in_date": checkin,
                "check_out_date": checkout,
                "adults": str(travelers),
                "rooms": str(rooms),
                "currency": "USD",
                "gl": "us",
                "hl": "en",
                "api_key": key,
                "sort_by": "3",  # 3 = lowest price
            }

            r = requests.get(SERPAPI_BASE, params=params, timeout=20)
            print(f"SerpAPI status: {r.status_code}")

            if r.status_code == 200:
                data = r.json()
                hotels = self._parse(data, destination, checkin, checkout, rooms)
                if hotels:
                    print(f"SerpAPI returned {len(hotels)} live hotels")
                    return {"success": True, "hotels": hotels,
                            "source": "live", "rooms": rooms}
                print("No hotels parsed from SerpAPI")
            else:
                print(f"SerpAPI error: {r.text[:200]}")

        except Exception as e:
            print(f"SerpAPI exception: {e}")

        return self._mock(destination, checkin, checkout, travelers, budget, rooms)

    def _parse(self, data, destination, checkin, checkout, rooms):
        hotels = []
        try:
            # SerpAPI returns properties in "properties" key
            raw = data.get("properties", [])
            print(f"SerpAPI raw hotels: {len(raw)}")

            if raw:
                # Debug first hotel structure
                print(f"Sample: name={raw[0].get('name')}, "
                      f"price={raw[0].get('rate_per_night')}, "
                      f"rating={raw[0].get('overall_rating')}, "
                      f"location={raw[0].get('location')}")

            nights = max(1, (
                datetime.strptime(checkout, "%Y-%m-%d") -
                datetime.strptime(checkin, "%Y-%m-%d")
            ).days)

            for h in raw[:6]:
                try:
                    name = h.get("name", "Unknown Hotel")

                    # Price — SerpAPI gives rate_per_night
                    price_raw = h.get("rate_per_night", {})
                    if isinstance(price_raw, dict):
                        price_str = price_raw.get("lowest") or price_raw.get("before_taxes_fees", "0")
                    else:
                        price_str = str(price_raw)

                    # Clean price string (remove $, commas)
                    price = float(''.join(c for c in str(price_str) if c.isdigit() or c == '.') or 0)
                    if price <= 0:
                        continue

                    # Rating
                    try:
                        rating = float(h.get("overall_rating") or 0)
                        # Google uses 1-5, convert to 1-10
                        if rating <= 5:
                            rating = round(rating * 2, 1)
                    except:
                        rating = 7.5

                    # Stars
                    try:
                        stars = int(h.get("hotel_class", "3").replace(" out of 5 stars","").replace(" star","").strip()[0])
                    except:
                        stars = 3

                    # Location
                    location = h.get("location", destination)
                    if not location or location == destination:
                        # Try to get neighborhood or address
                        location = h.get("neighborhood", "") or h.get("address", "") or destination

                    # Amenities
                    amenities_raw = h.get("amenities", [])
                    if isinstance(amenities_raw, list):
                        amenities = [a for a in amenities_raw[:5] if isinstance(a, str)]
                    else:
                        amenities = []
                    if not amenities:
                        amenities = ["Free WiFi", "24hr Reception"]

                    # Reviews
                    reviews = int(h.get("reviews", 0) or 0)

                    hotels.append({
                        "name": name,
                        "rating": round(rating, 1),
                        "review_count": reviews,
                        "price_per_night_per_room": round(price, 2),
                        "rooms": rooms,
                        "stars": min(5, max(1, stars)),
                        "amenities": amenities,
                        "location": location,
                        "checkin": checkin,
                        "checkout": checkout,
                        "source": "live",
                        "link": h.get("link", "")
                    })

                except Exception as e:
                    print(f"Hotel row error: {e}")
                    continue

        except Exception as e:
            print(f"SerpAPI parse error: {e}")

        # Sort by price
        hotels.sort(key=lambda x: x["price_per_night_per_room"])
        return hotels[:3]

    def _mock(self, destination, checkin, checkout, travelers, budget, rooms):
        nightly = min((budget * 0.35) / max(rooms, 1), 400)
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
        return min(range(len(hotels)),
                   key=lambda i: self.total_cost(hotels[i], nights))

    def format_for_display(self, data, nights, budget=0):
        if not data.get("hotels"):
            return "❌ No hotels found."
        hotels = data["hotels"]
        rooms = data.get("rooms", 1)
        src = "*(live data — Google Hotels)*" if data.get("source") == "live" \
              else "*(estimated — verify on Booking.com)*"
        best = self.recommend(hotels, nights, budget)
        lines = [f"### 🏨 Available Hotels {src}\n",
                 f"*Booking {rooms} room(s) for {nights} nights*\n"]
        for i, h in enumerate(hotels):
            stars = "⭐" * int(h.get("stars", 3))
            total = self.total_cost(h, nights)
            amenities = ", ".join(h.get("amenities", [])[:4])
            badge = " 🏆 **BEST PICK**" if i == best else ""
            pct = f" *({total/budget*100:.0f}% of budget)*" if budget else ""
            link = f" · [View]({h['link']})" if h.get("link") else ""
            lines.append(
                f"**Option {i+1}: {h['name']}** {stars}{badge}\n"
                f"  • Rating: **{h['rating']}/10** ({h.get('review_count',0):,} reviews)\n"
                f"  • 📍 Location: {h['location']}{link}\n"
                f"  • ${h['price_per_night_per_room']:,.2f}/night × {rooms} room(s) × {nights} nights\n"
                f"  • **Total: ${total:,.2f}**{pct}\n"
                f"  • Amenities: {amenities}\n"
            )
        bh = hotels[best]
        bt = self.total_cost(bh, nights)
        reason = "best rated within budget" if bt <= budget * 0.40 else "cheapest available"
        lines.append(
            f"\n✅ **Recommended Hotel:** {bh['name']} "
            f"({'⭐'*int(bh.get('stars',3))}) — "
            f"**${bt:,.2f}** total for {nights} nights *({reason})*"
        )
        return "\n".join(lines)
