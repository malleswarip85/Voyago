"""
Flight Agent - Duffel API v2
Fixes: country→city mapping, price validation, duration sanity check
"""
import requests, os, re
from datetime import datetime

DUFFEL_TOKEN = os.getenv("DUFFEL_API_KEY")
DUFFEL_BASE = "https://api.duffel.com"

# Country name → default major city airport
COUNTRY_TO_CITY = {
    "india": "DEL", "china": "PEK", "japan": "NRT", "usa": "JFK",
    "united states": "JFK", "uk": "LHR", "united kingdom": "LHR",
    "france": "CDG", "germany": "FRA", "italy": "FCO", "spain": "MAD",
    "australia": "SYD", "canada": "YYZ", "brazil": "GRU", "mexico": "MEX",
    "thailand": "BKK", "singapore": "SIN", "malaysia": "KUL",
    "indonesia": "CGK", "philippines": "MNL", "south korea": "ICN",
    "korea": "ICN", "vietnam": "SGN", "turkey": "IST", "egypt": "CAI",
    "south africa": "JNB", "nigeria": "LOS", "kenya": "NBO",
    "uae": "DXB", "united arab emirates": "DXB", "qatar": "DOH",
    "saudi arabia": "RUH", "pakistan": "KHI", "bangladesh": "DAC",
    "sri lanka": "CMB", "nepal": "KTM", "russia": "SVO",
    "netherlands": "AMS", "switzerland": "ZRH", "portugal": "LIS",
    "greece": "ATH", "sweden": "ARN", "norway": "OSL", "denmark": "CPH",
    "new zealand": "AKL", "argentina": "EZE", "colombia": "BOG",
    "peru": "LIM", "chile": "SCL", "iran": "IKA", "iraq": "BGW",
    "israel": "TLV", "jordan": "AMM", "morocco": "CMN", "ghana": "ACC",
}

IATA_CODES = {
    "new york": "JFK", "nyc": "JFK", "new york city": "JFK",
    "london": "LHR", "paris": "CDG", "dubai": "DXB",
    "tokyo": "NRT", "los angeles": "LAX", "la": "LAX",
    "chicago": "ORD", "miami": "MIA", "singapore": "SIN",
    "sydney": "SYD", "toronto": "YYZ", "amsterdam": "AMS",
    "frankfurt": "FRA", "rome": "FCO", "barcelona": "BCN",
    "madrid": "MAD", "bangkok": "BKK", "hong kong": "HKG",
    "mumbai": "BOM", "delhi": "DEL", "new delhi": "DEL",
    "beijing": "PEK", "shanghai": "PVG", "san francisco": "SFO",
    "seattle": "SEA", "boston": "BOS", "dallas": "DFW",
    "atlanta": "ATL", "denver": "DEN", "las vegas": "LAS",
    "orlando": "MCO", "cancun": "CUN", "mexico city": "MEX",
    "cairo": "CAI", "istanbul": "IST", "berlin": "BER",
    "vienna": "VIE", "zurich": "ZRH", "cape town": "CPT",
    "kuala lumpur": "KUL", "jakarta": "CGK", "manila": "MNL",
    "seoul": "ICN", "osaka": "KIX", "taipei": "TPE",
    "bali": "DPS", "denpasar": "DPS", "doha": "DOH",
    "abu dhabi": "AUH", "houston": "IAH", "phoenix": "PHX",
    "lisbon": "LIS", "athens": "ATH", "brussels": "BRU",
    "johannesburg": "JNB", "nairobi": "NBO", "lagos": "LOS",
    "karachi": "KHI", "lahore": "LHE", "colombo": "CMB",
    "kathmandu": "KTM", "dhaka": "DAC", "hyderabad": "HYD",
    "bangalore": "BLR", "bengaluru": "BLR", "chennai": "MAA",
    "kolkata": "CCU", "ahmedabad": "AMD", "pune": "PNQ",
    "ho chi minh": "SGN", "hanoi": "HAN", "riyadh": "RUH",
    "jeddah": "JED", "tel aviv": "TLV", "amman": "AMM",
    "casablanca": "CMN", "accra": "ACC", "addis ababa": "ADD",
    "stockholm": "ARN", "oslo": "OSL", "copenhagen": "CPH",
    "auckland": "AKL", "buenos aires": "EZE", "bogota": "BOG",
    "lima": "LIM", "santiago": "SCL", "moscow": "SVO",
}

# Route-aware minimum price validation only
# Duration check removed — Duffel returns segment durations not total
MIN_INTL_PRICE_PP = 80    # baseline min price/person

# Long-haul destination keywords → minimum price per person only
LONG_HAUL_RULES = [
    # (destination keywords, min_price_per_person)
    (["india","delhi","mumbai","bangalore","chennai","hyderabad","kolkata",
      "ahmedabad","pune","jaipur"], 400),
    (["singapore","bangkok","kuala lumpur","jakarta","manila",
      "ho chi minh","hanoi","yangon"], 350),
    (["tokyo","osaka","seoul","beijing","shanghai","hong kong",
      "taipei","guangzhou"], 450),
    (["sydney","melbourne","auckland","brisbane","perth"], 600),
    (["london","paris","amsterdam","frankfurt","rome","madrid",
      "barcelona","berlin","vienna","zurich","lisbon","athens",
      "brussels","stockholm","oslo","copenhagen"], 250),
    (["dubai","abu dhabi","doha","riyadh","jeddah","kuwait"], 350),
    (["cairo","nairobi","johannesburg","cape town","lagos",
      "accra","addis ababa","casablanca"], 400),
    (["moscow","istanbul"], 250),
    (["toronto","montreal","vancouver"], 120),
    (["cancun","mexico city","bogota","lima","santiago",
      "buenos aires","sao paulo"], 150),
]


class FlightAgent:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {DUFFEL_TOKEN or ''}",
            "Duffel-Version": "v2",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Accept-Encoding": "gzip"
        }

    def _resolve_iata(self, place: str) -> str:
        """
        Convert city/country name to IATA code.
        Handles: city names, country names, already-valid IATA codes.
        """
        clean = re.sub(r'[,.\-]\s*\w{2,3}$', '', place.strip()).lower()

        # Already an IATA code (3 uppercase letters)
        if re.match(r'^[A-Z]{3}$', place.strip()):
            return place.strip()

        # Direct city match
        if clean in IATA_CODES:
            return IATA_CODES[clean]

        # Country match → return default major airport
        if clean in COUNTRY_TO_CITY:
            iata = COUNTRY_TO_CITY[clean]
            print(f"Country '{clean}' → using major airport {iata}")
            return iata

        # Try Duffel places API
        return self._search_airport(place)

    def _search_airport(self, city: str) -> str:
        """Search Duffel for airport IATA — prefers city airports over regional."""
        clean = re.sub(r'[,.\-]\s*\w{2,3}$', '', city.strip())
        # If it's a country name, resolve to major city first
        clean_lower = clean.lower()
        if clean_lower in COUNTRY_TO_CITY:
            return COUNTRY_TO_CITY[clean_lower]

        try:
            url = f"{DUFFEL_BASE}/places/suggestions"
            r = requests.get(url, headers=self.headers,
                           params={"query": clean}, timeout=10)
            print(f"Duffel airport search [{clean}] status: {r.status_code}")
            if r.status_code == 200:
                places = r.json().get("data", [])
                # Prefer city type over airport (gets main hub, not regional)
                for p in places:
                    if p.get("type") == "city":
                        iata = p.get("iata_city_code") or p.get("iata_code", "")
                        if iata:
                            print(f"Found city: {p.get('name')} ({iata})")
                            return iata
                # Then try airports
                for p in places:
                    if p.get("type") == "airport":
                        iata = p.get("iata_code", "")
                        if iata:
                            print(f"Found airport: {p.get('name')} ({iata})")
                            return iata
                # Last fallback
                if places:
                    iata = (places[0].get("iata_city_code") or
                            places[0].get("iata_code", ""))
                    if iata:
                        return iata
        except Exception as e:
            print(f"Airport search error: {e}")

        # Final fallback
        return clean_lower.upper()[:3]

    def search_flights(self, origin: str, destination: str, date: str,
                       travelers: int, nonstop: bool = False) -> dict:
        if not DUFFEL_TOKEN:
            print("No Duffel API key — using mock flights")
            return self._mock(origin, destination, date, travelers, nonstop)

        origin_iata = self._resolve_iata(origin)
        dest_iata = self._resolve_iata(destination)

        print(f"Duffel search: {origin_iata} → {dest_iata} on {date}")

        if origin_iata == dest_iata:
            print("Origin and destination are the same — using mock")
            return self._mock(origin, destination, date, travelers, nonstop)

        try:
            payload = {
                "data": {
                    "slices": [{
                        "origin": origin_iata,
                        "destination": dest_iata,
                        "departure_date": date
                    }],
                    "passengers": [{"type": "adult"} for _ in range(travelers)],
                    "cabin_class": "economy"
                }
            }
            url = f"{DUFFEL_BASE}/air/offer_requests"
            r = requests.post(url, headers=self.headers,
                            json=payload, timeout=30)
            print(f"Duffel offer_request status: {r.status_code}")

            if r.status_code not in (200, 201):
                print(f"Duffel error: {r.text[:300]}")
                return self._mock(origin, destination, date, travelers, nonstop)

            offer_request_id = r.json().get("data", {}).get("id")
            if not offer_request_id:
                return self._mock(origin, destination, date, travelers, nonstop)

            return self._get_offers(
                offer_request_id, origin, destination, date, travelers, nonstop
            )

        except Exception as e:
            print(f"Duffel flight search error: {e}")
            return self._mock(origin, destination, date, travelers, nonstop)

    def _get_offers(self, offer_request_id, origin, destination,
                    date, travelers, nonstop):
        try:
            url = f"{DUFFEL_BASE}/air/offers"
            params = {
                "offer_request_id": offer_request_id,
                "sort": "total_amount",
                "limit": "20",
                "max_connections": "0" if nonstop else "2"
            }
            r = requests.get(url, headers=self.headers,
                           params=params, timeout=20)
            print(f"Duffel offers status: {r.status_code}")

            if r.status_code == 200:
                offers = r.json().get("data", [])
                print(f"Duffel returned {len(offers)} offers")
                flights = self._parse_offers(
                    offers, origin, destination, date, travelers, nonstop
                )
                if flights:
                    return {"success": True, "flights": flights, "source": "live"}
                print("All offers filtered out — using mock")
        except Exception as e:
            print(f"Duffel get_offers error: {e}")

        return self._mock(origin, destination, date, travelers, nonstop)

    def _parse_offers(self, offers, origin, destination, date, travelers, nonstop):
        flights = []
        seen_airlines = set()

        for offer in offers[:20]:
            try:
                slices = offer.get("slices", [])
                if not slices:
                    continue
                sl = slices[0]
                segments = sl.get("segments", [])
                if not segments:
                    continue

                stops = len(segments) - 1
                if nonstop and stops > 0:
                    continue

                # Duffel total_amount = total for ALL passengers
                total_amount = float(offer.get("total_amount", 0))
                currency = offer.get("total_currency", "USD")
                if total_amount <= 0:
                    continue

                price_per_person = round(total_amount / max(travelers, 1), 2)

                # Times & duration
                dep = segments[0].get("departing_at", f"{date}T08:00:00")
                arr = segments[-1].get("arriving_at", f"{date}T14:00:00")
                duration_str = sl.get("duration", "")
                duration_mins = self._parse_duration(duration_str, dep, arr)

                # Airline info
                first_seg = segments[0]
                airline_name = (
                    first_seg.get("operating_carrier", {}).get("name") or
                    first_seg.get("marketing_carrier", {}).get("name") or
                    "Unknown Airline"
                )
                airline_iata = (
                    first_seg.get("marketing_carrier", {}).get("iata_code") or
                    first_seg.get("operating_carrier", {}).get("iata_code") or "XX"
                )
                flight_num = f"{airline_iata}{first_seg.get('marketing_carrier_flight_number', '000')}"

                # ── Price validation only (duration unreliable for connecting flights) ──
                min_price = self._get_route_minimums(destination)

                if price_per_person < min_price:
                    print(f"Rejected {airline_name}: ${price_per_person}/person < min ${min_price} for {destination}")
                    continue

                if airline_name in seen_airlines:
                    continue
                seen_airlines.add(airline_name)

                flights.append({
                    "airline": airline_name,
                    "flight_number": flight_num,
                    "departure": dep,
                    "arrival": arr,
                    "duration": duration_mins,
                    "stops": stops,
                    "price_per_person": price_per_person,
                    "total_price": round(total_amount, 2),
                    "currency": currency,
                    "origin": origin,
                    "destination": destination,
                    "offer_id": offer.get("id", ""),
                    "source": "live"
                })

                if len(flights) >= 3:
                    break

            except Exception as e:
                print(f"Offer parse error: {e}")
                continue

        return flights

    def _get_route_minimums(self, destination: str):
        """Return min_price_per_person for a destination."""
        dest_lower = destination.lower()
        for keywords, min_price in LONG_HAUL_RULES:
            if any(k in dest_lower for k in keywords):
                return min_price
        return MIN_INTL_PRICE_PP

    def _parse_duration(self, iso_dur, dep, arr):
        if iso_dur:
            try:
                h = int(re.search(r'(\d+)H', iso_dur).group(1)) if 'H' in iso_dur else 0
                m = int(re.search(r'(\d+)M', iso_dur).group(1)) if 'M' in iso_dur else 0
                return h * 60 + m
            except: pass
        try:
            fmt = "%Y-%m-%dT%H:%M:%S"
            dep_dt = datetime.strptime(dep[:19], fmt)
            arr_dt = datetime.strptime(arr[:19], fmt)
            mins = int((arr_dt - dep_dt).total_seconds() / 60)
            return mins if mins > 0 else 360
        except:
            return 360

    def _mock(self, origin, destination, date, travelers, nonstop):
        options = [
            {"name": "Emirates", "code": "EK", "base": 850, "stops": 1},
            {"name": "Qatar Airways", "code": "QR", "base": 780, "stops": 1},
            {"name": "Air India", "code": "AI", "base": 920, "stops": 0},
            {"name": "British Airways", "code": "BA", "base": 1050, "stops": 1},
            {"name": "Singapore Airlines", "code": "SQ", "base": 980, "stops": 1},
        ]
        flights = []
        for i, a in enumerate(options):
            if nonstop and a["stops"] > 0:
                continue
            price_pp = a["base"] + i * 20
            flights.append({
                "airline": a["name"],
                "flight_number": f"{a['code']}{201+i}",
                "departure": f"{date}T{8+i*2:02d}:00:00",
                "arrival": f"{date}T{23+i:02d}:30:00",
                "duration": 900 + i * 30,
                "stops": a["stops"],
                "price_per_person": price_pp,
                "total_price": round(price_pp * travelers, 2),
                "currency": "USD",
                "origin": origin,
                "destination": destination,
                "source": "simulated"
            })
        return {"success": True, "flights": flights[:3], "source": "simulated"}

    def recommend(self, flights, budget, nonstop):
        if not flights: return 0
        scored = []
        for i, f in enumerate(flights):
            s = 0
            if f["total_price"] <= budget * 0.4: s += 50
            elif f["total_price"] <= budget * 0.55: s += 25
            if nonstop and f["stops"] == 0: s += 30
            elif f["stops"] == 0: s += 10
            s += max(0, 20 - int(f["total_price"] / 100))
            scored.append((i, s))
        return max(scored, key=lambda x: x[1])[0]

    def format_for_display(self, data, budget=0, nonstop=False):
        if not data.get("flights"):
            return "❌ No flights found."
        flights = data["flights"]
        src = "*(live data)*" if data.get("source") == "live" else "*(sample data)*"
        best = self.recommend(flights, budget, nonstop)
        lines = [f"### ✈️ Available Flights {src}\n"]
        for i, f in enumerate(flights):
            h, m = divmod(f["duration"], 60)
            stop_txt = "🟢 Non-stop" if f["stops"] == 0 else f"🔴 {f['stops']} stop(s)"
            badge = " 🏆 **BEST PICK**" if i == best else ""
            pct = f" *({f['total_price']/budget*100:.0f}% of budget)*" if budget else ""
            dep_fmt = str(f["departure"])[:16].replace("T", " ")
            arr_fmt = str(f["arrival"])[:16].replace("T", " ")
            lines.append(
                f"**Option {i+1}: {f['airline']} {f['flight_number']}**{badge}\n"
                f"  • Departure: `{dep_fmt}` → Arrival: `{arr_fmt}`\n"
                f"  • Duration: {h}h {m}m | {stop_txt}\n"
                f"  • Per person: **${f['price_per_person']:,.2f}** | "
                f"Total: **${f['total_price']:,.2f} {f['currency']}**{pct}\n"
            )
        bf = flights[best]
        stop_label = "Non-stop" if bf["stops"] == 0 else f"{bf['stops']} stop(s)"
        lines.append(
            f"\n✅ **Recommended Flight:** {bf['airline']} {bf['flight_number']} — "
            f"**${bf['total_price']:,.2f}** total ({stop_label})"
        )
        return "\n".join(lines)
