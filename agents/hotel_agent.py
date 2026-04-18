"""
Hotel Agent - SerpAPI Google Hotels
Fetches top 10 ranked, affordable real hotels from Google Hotels.
Searches by specific city, sorted by rating then price.
"""
import requests, os, math
from datetime import datetime

SERPAPI_BASE = "https://serpapi.com/search"

# Airport code → city
AIRPORT_CITIES = {
    "DEL":"New Delhi","BOM":"Mumbai","BLR":"Bangalore","HYD":"Hyderabad",
    "MAA":"Chennai","CCU":"Kolkata","COK":"Kochi","PNQ":"Pune",
    "AMD":"Ahmedabad","GOI":"Goa",
    "JFK":"New York","LAX":"Los Angeles","ORD":"Chicago","ATL":"Atlanta",
    "DFW":"Dallas","MIA":"Miami","SFO":"San Francisco","SEA":"Seattle",
    "BOS":"Boston","LAS":"Las Vegas","MCO":"Orlando","IAH":"Houston",
    "LHR":"London","LGW":"London","CDG":"Paris","ORY":"Paris",
    "FRA":"Frankfurt","MUC":"Munich","BER":"Berlin","FCO":"Rome",
    "MXP":"Milan","VCE":"Venice","MAD":"Madrid","BCN":"Barcelona",
    "AMS":"Amsterdam","LIS":"Lisbon","ATH":"Athens","VIE":"Vienna",
    "ZRH":"Zurich","BRU":"Brussels","ARN":"Stockholm",
    "NRT":"Tokyo","HND":"Tokyo","KIX":"Osaka","ICN":"Seoul",
    "GMP":"Seoul","PEK":"Beijing","PVG":"Shanghai","SIN":"Singapore",
    "BKK":"Bangkok","DMK":"Bangkok","HKT":"Phuket","KUL":"Kuala Lumpur",
    "CGK":"Jakarta","DPS":"Bali","MNL":"Manila","HKG":"Hong Kong",
    "TPE":"Taipei","DXB":"Dubai","AUH":"Abu Dhabi","DOH":"Doha",
    "SYD":"Sydney","MEL":"Melbourne","BNE":"Brisbane",
    "YYZ":"Toronto","YVR":"Vancouver","YUL":"Montreal",
    "GRU":"Sao Paulo","GIG":"Rio de Janeiro",
    "JNB":"Johannesburg","CPT":"Cape Town",
    "CAI":"Cairo","IST":"Istanbul","AYT":"Antalya",
    "NBO":"Nairobi","CMN":"Casablanca","MOB":"Mobile",
}

# Country → major city for hotel search
COUNTRY_CITIES = {
    "india":"New Delhi","china":"Beijing","japan":"Tokyo",
    "france":"Paris","italy":"Rome","spain":"Madrid",
    "germany":"Berlin","australia":"Sydney","canada":"Toronto",
    "brazil":"Sao Paulo","mexico":"Mexico City","thailand":"Bangkok",
    "indonesia":"Jakarta","malaysia":"Kuala Lumpur",
    "south korea":"Seoul","egypt":"Cairo","turkey":"Istanbul",
    "south africa":"Johannesburg","portugal":"Lisbon",
    "greece":"Athens","netherlands":"Amsterdam",
    "uae":"Dubai","united arab emirates":"Dubai",
    "uk":"London","united kingdom":"London",
    "usa":"New York","united states":"New York",
}


class HotelAgent:
    def __init__(self):
        pass

    def _key(self):
        return os.getenv("SERPAPI_KEY", "")

    def _resolve_city(self, destination, destination_iata=None):
        """Resolve best city name for hotel search."""
        # Airport code takes priority
        if destination_iata and destination_iata in AIRPORT_CITIES:
            city = AIRPORT_CITIES[destination_iata]
            print(f"Hotel city from airport {destination_iata}: {city}")
            return city, destination_iata

        dest_lower = destination.lower().strip()

        # Country → major city
        if dest_lower in COUNTRY_CITIES:
            city = COUNTRY_CITIES[dest_lower]
            print(f"Country '{destination}' → using {city}")
            return city, None

        return destination, None

    def search_hotels(self, destination, checkin, checkout, travelers,
                      budget, destination_iata=None):
        rooms = max(1, math.ceil(travelers / 2))
        key = self._key()

        search_city, airport_code = self._resolve_city(destination, destination_iata)
        print(f"Hotel search: '{search_city}' airport={airport_code} key={'SET' if key else 'NOT SET'}")

        if not key:
            return self._mock(search_city, destination, checkin, checkout, travelers, budget, rooms, airport_code)

        # Try multiple search strategies to get real prices
        strategies = [
            # Strategy 1: Sort by highest rating
            {"sort_by": "8", "label": "top rated"},
            # Strategy 2: Sort by lowest price
            {"sort_by": "3", "label": "lowest price"},
        ]

        all_hotels = []
        for strategy in strategies:
            hotels = self._search_with_params(
                search_city, checkin, checkout, travelers, rooms,
                budget, airport_code, destination, strategy, key
            )
            # Merge unique hotels
            existing_names = {h["name"] for h in all_hotels}
            for h in hotels:
                if h["name"] not in existing_names:
                    all_hotels.append(h)
                    existing_names.add(h["name"])
            if len(all_hotels) >= 6:
                break

        if all_hotels:
            print(f"Total real hotels found: {len(all_hotels)}")
            # Sort: best rating first, then by price
            all_hotels.sort(key=lambda h: (-h["rating"], h["price_per_night_per_room"]))
            return {
                "success": True,
                "hotels": all_hotels[:10],
                "source": "live",
                "rooms": rooms,
                "search_city": search_city,
                "airport_code": airport_code or ""
            }

        print("No real hotels found — using mock")
        return self._mock(search_city, destination, checkin, checkout, travelers, budget, rooms, airport_code)

    def _search_with_params(self, search_city, checkin, checkout, travelers,
                            rooms, budget, airport_code, destination,
                            strategy, key):
        """Run one SerpAPI Google Hotels search."""
        try:
            query = f"hotels in {search_city}"
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
                "sort_by": strategy["sort_by"],
            }

            r = requests.get(SERPAPI_BASE, params=params, timeout=20)
            print(f"SerpAPI [{strategy['label']}] status: {r.status_code}")

            if r.status_code != 200:
                return []

            data = r.json()
            raw = data.get("properties", [])
            print(f"SerpAPI [{strategy['label']}] raw hotels: {len(raw)}")

            nights = max(1, (
                datetime.strptime(checkout, "%Y-%m-%d") -
                datetime.strptime(checkin, "%Y-%m-%d")
            ).days)

            hotels = []
            for h in raw[:15]:
                parsed = self._parse_hotel(h, search_city, airport_code,
                                           checkin, checkout, rooms, nights, budget)
                if parsed:
                    hotels.append(parsed)
                    if len(hotels) >= 8:
                        break

            return hotels

        except Exception as e:
            print(f"SerpAPI search error: {e}")
            return []

    def _parse_hotel(self, h, search_city, airport_code,
                     checkin, checkout, rooms, nights, budget):
        """Parse a single SerpAPI hotel result."""
        try:
            name = h.get("name", "")
            if not name:
                return None

            # Extract price
            price = self._extract_price(h, nights)
            if price <= 0:
                # Try to get any price from the property
                desc = str(h)
                import re
                prices = re.findall(r'\$(\d+)', desc)
                if prices:
                    price = float(min(prices, key=lambda x: int(x)))
                if price <= 0:
                    print(f"  No price for: {name}")
                    return None

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
                star_str = str(h.get("hotel_class", "3"))
                stars = int(''.join(filter(str.isdigit, star_str))[:1] or "3")
                stars = max(1, min(5, stars))
            except:
                stars = 3

            # Location
            location = (h.get("neighborhood") or
                       h.get("location") or
                       h.get("address") or
                       search_city)
            if str(location) == "None":
                location = search_city

            # Amenities
            amenities_raw = h.get("amenities", [])
            if amenities_raw and isinstance(amenities_raw[0], dict):
                amenities = [a.get("name","") for a in amenities_raw[:6] if a.get("name")]
            elif amenities_raw:
                amenities = [a for a in amenities_raw[:6] if isinstance(a, str)]
            else:
                amenities = ["Free WiFi", "24hr Reception"]

            # Budget label
            total = round(price * rooms * nights, 2)
            if budget:
                pct = total / budget * 100
                if pct <= 25: budget_label = "💚 Budget-friendly"
                elif pct <= 40: budget_label = "💛 Good value"
                else: budget_label = "💰 Premium"
            else:
                budget_label = ""

            print(f"  Hotel: {name[:40]} | ⭐{rating}/10 | ${price}/night")

            return {
                "name": name,
                "rating": round(rating, 1),
                "review_count": int(h.get("reviews") or 0),
                "price_per_night_per_room": round(price, 2),
                "rooms": rooms,
                "stars": stars,
                "amenities": amenities if amenities else ["Free WiFi"],
                "location": location,
                "search_city": search_city,
                "airport_code": airport_code or "",
                "budget_label": budget_label,
                "checkin": checkin,
                "checkout": checkout,
                "link": h.get("link", ""),
                "source": "live"
            }
        except Exception as e:
            print(f"  Parse error: {e}")
            return None

    def _extract_price(self, h, nights):
        """Extract nightly price — try all possible fields."""
        # rate_per_night
        rpn = h.get("rate_per_night", {})
        if isinstance(rpn, dict):
            for field in ["extracted_lowest","extracted_before_taxes_fees"]:
                val = rpn.get(field)
                if val is not None:
                    try:
                        f = float(val)
                        if f > 0: return f
                    except: pass
            for field in ["lowest","before_taxes_fees"]:
                val = str(rpn.get(field,""))
                cleaned = ''.join(c for c in val if c.isdigit() or c == '.')
                if cleaned:
                    try:
                        f = float(cleaned)
                        if f > 0: return f
                    except: pass

        # total_rate / nights
        tr = h.get("total_rate", {})
        if isinstance(tr, dict):
            for field in ["extracted_lowest","extracted_before_taxes_fees"]:
                val = tr.get(field)
                if val is not None:
                    try:
                        f = float(val)
                        if f > 0: return round(f / max(nights,1), 2)
                    except: pass
            for field in ["lowest","before_taxes_fees"]:
                val = str(tr.get(field,""))
                cleaned = ''.join(c for c in val if c.isdigit() or c == '.')
                if cleaned:
                    try:
                        f = float(cleaned)
                        if f > 0: return round(f / max(nights,1), 2)
                    except: pass

        # Top-level price fields
        for field in ["price","nightly_price","min_price","lowest_price"]:
            val = h.get(field)
            if val:
                try:
                    cleaned = ''.join(c for c in str(val) if c.isdigit() or c == '.')
                    f = float(cleaned)
                    if f > 0: return f
                except: pass

        return 0

    def _mock(self, search_city, destination, checkin, checkout,
              travelers, budget, rooms, airport_code=None):
        nightly = min((budget * 0.35) / max(rooms,1), 400)
        city = search_city or destination.split(",")[0].strip()
        note = f" near {airport_code} Airport" if airport_code else ""
        return {
            "success":True, "rooms":rooms, "source":"simulated",
            "search_city":city, "airport_code":airport_code or "",
            "hotels":[
                {"name":f"The Grand {city} Hotel","stars":5,"rating":9.2,
                 "review_count":3240,"price_per_night_per_room":round(nightly*1.1,2),
                 "amenities":["Free WiFi","Pool","Spa","Restaurant","Airport Shuttle"],
                 "rooms":rooms,"location":f"City Center, {city}{note}",
                 "search_city":city,"airport_code":airport_code or "",
                 "budget_label":"💛 Good value",
                 "checkin":checkin,"checkout":checkout,"source":"simulated"},
                {"name":f"{city} Boutique Hotel","stars":4,"rating":8.7,
                 "review_count":1580,"price_per_night_per_room":round(nightly*0.65,2),
                 "amenities":["Free WiFi","Breakfast Included","Gym","Bar"],
                 "rooms":rooms,"location":f"Downtown, {city}{note}",
                 "search_city":city,"airport_code":airport_code or "",
                 "budget_label":"💚 Budget-friendly",
                 "checkin":checkin,"checkout":checkout,"source":"simulated"},
                {"name":f"{city} Comfort Inn","stars":3,"rating":7.9,
                 "review_count":920,"price_per_night_per_room":round(nightly*0.4,2),
                 "amenities":["Free WiFi","24hr Reception","Parking"],
                 "rooms":rooms,"location":f"Near Transit, {city}{note}",
                 "search_city":city,"airport_code":airport_code or "",
                 "budget_label":"💚 Budget-friendly",
                 "checkin":checkin,"checkout":checkout,"source":"simulated"},
            ]
        }

    def total_cost(self, hotel, nights):
        return round(hotel["price_per_night_per_room"] * hotel["rooms"] * nights, 2)

    def recommend(self, hotels, nights, budget):
        """Best rated hotel within 45% of budget, else cheapest."""
        if not hotels: return 0
        hotel_budget = budget * 0.45
        within = [(i, self.total_cost(h, nights), h["rating"])
                  for i, h in enumerate(hotels)
                  if self.total_cost(h, nights) <= hotel_budget]
        if within:
            within.sort(key=lambda x: x[2], reverse=True)
            return within[0][0]
        return min(range(len(hotels)), key=lambda i: self.total_cost(hotels[i], nights))

    def format_for_display(self, data, nights, budget=0):
        if not data.get("hotels"):
            return "❌ No hotels found."

        hotels = data["hotels"]
        rooms = data.get("rooms", 1)
        search_city = data.get("search_city", "")
        airport_code = data.get("airport_code", "")
        is_live = data.get("source") == "live"
        source_txt = "✓ Live data — Google Hotels" if is_live else "~ Estimated — verify on Booking.com"
        location_note = f"near {airport_code} airport · {search_city}" if airport_code else search_city

        best_idx = self.recommend(hotels, nights, budget)
        bh = hotels[best_idx]
        bt = self.total_cost(bh, nights)
        reason = "best rated within budget" if bt <= budget * 0.45 else "most affordable"
        summary = (f"{bh['name']} ({'⭐' * int(bh.get('stars', 3))}) — "
                   f"${bt:,.0f} total · {nights} nights · {reason}")

        cards = []
        for i, h in enumerate(hotels):
            total = self.total_cost(h, nights)
            is_best = (i == best_idx)
            stars_str = "⭐" * int(h.get("stars", 3))
            rating = h.get("rating", 7.0)
            reviews = h.get("review_count", 0)
            amenities = h.get("amenities", [])[:4]
            amenity_pills = "".join(
                f'<span style="background:rgba(14,116,144,0.08);color:var(--sky-mid,#0e7490);'
                f'border-radius:10px;padding:2px 7px;font-size:10px;white-space:nowrap;">{a}</span>'
                for a in amenities
            )
            pct_txt = f" · {total/budget*100:.0f}% of budget" if budget else ""
            budget_label = h.get("budget_label", "")
            location = h.get("location", search_city)
            live_dot = '<span style="color:#16a34a;font-size:9px;">●</span> Live' if h.get("source") == "live" else "~ Est."

            link_html = ""
            if h.get("link"):
                link_html = (f'<a href="{h["link"]}" target="_blank" style="font-size:11px;font-weight:600;'
                             f'color:var(--sky-mid,#0e7490);text-decoration:none;padding:3px 8px;'
                             f'border:1px solid var(--border,rgba(14,116,144,0.15));border-radius:6px;">'
                             f'View Hotel →</a>')

            border_style = "border-color:#d97706;" if is_best else ""
            header_bg = "background:rgba(255,251,235,0.9);" if is_best else "background:rgba(240,253,250,0.6);"
            best_badge = (
                '<span style="background:rgba(217,119,6,0.12);color:#92400e;border:1px solid rgba(217,119,6,0.25);'
                'border-radius:12px;padding:2px 7px;font-size:9.5px;font-weight:700;margin-left:3px;">'
                '🏆 Best Pick</span>'
                if is_best else ""
            )

            # Rating color
            rating_color = "#16a34a" if rating >= 8 else ("#d97706" if rating >= 6.5 else "#dc2626")

            cards.append(f"""
<div style="background:var(--bg-white,#fff);border:1.5px solid var(--border,rgba(14,116,144,0.15));{border_style}border-radius:12px;overflow:hidden;box-shadow:var(--shadow-sm,0 2px 8px rgba(12,92,107,0.05));">
  <div style="display:flex;align-items:center;justify-content:space-between;padding:10px 14px;{header_bg}border-bottom:1px solid var(--border,rgba(14,116,144,0.08));">
    <div style="flex:1;min-width:0;">
      <div style="display:flex;align-items:center;gap:4px;flex-wrap:wrap;">
        <span style="font-size:12.5px;font-weight:700;color:var(--sky-deep,#0c5c6b);">{h['name']}</span>
        {best_badge}
      </div>
      <div style="font-size:11px;color:var(--text-muted,#a16207);margin-top:2px;">{stars_str} {budget_label}</div>
    </div>
    <div style="text-align:right;flex-shrink:0;margin-left:10px;">
      <div style="font-size:15px;font-weight:700;color:var(--sky-deep,#0c5c6b);">${total:,.0f}</div>
      <div style="font-size:10px;color:var(--text-muted,#a16207);">${h['price_per_night_per_room']:,.0f}/night{pct_txt}</div>
    </div>
  </div>
  <div style="padding:12px 14px;">
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
      <span style="background:{rating_color};color:white;font-size:11px;font-weight:700;padding:3px 8px;border-radius:8px;">{rating}/10</span>
      <span style="font-size:11px;color:var(--text-muted,#a16207);">{reviews:,} reviews</span>
      <span style="font-size:11px;color:var(--text-muted,#a16207);">📍 {location}</span>
    </div>
    <div style="display:flex;gap:5px;flex-wrap:wrap;margin-bottom:8px;">{amenity_pills}</div>
    <div style="font-size:10.5px;color:var(--text-muted,#a16207);">{rooms} room(s) × {nights} nights</div>
  </div>
  <div style="padding:8px 14px 10px;border-top:1px solid var(--border,rgba(14,116,144,0.08));display:flex;justify-content:space-between;align-items:center;">
    <span style="font-size:10.5px;color:var(--text-muted,#a16207);">{live_dot}</span>
    {link_html}
  </div>
</div>""")

        return (f'<div data-summary="{summary}" style="display:flex;flex-direction:column;gap:8px;">'
                f'<div style="font-size:10.5px;color:var(--text-muted,#a16207);margin-bottom:2px;">'
                f'{source_txt} · {rooms} room(s) · {location_note}</div>'
                + "".join(cards) +
                f'<div style="font-size:12px;font-weight:600;color:var(--sky-deep,#0c5c6b);padding:6px 2px 0;">'
                f'✅ Recommended: {summary}</div>'
                f'</div>')
