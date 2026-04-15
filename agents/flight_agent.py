"""
Flight Agent - SerpAPI Google Flights
Real flight data from Google Flights.
Same SERPAPI_KEY as hotels — no extra key needed!
"""
import requests, os, re
from datetime import datetime

SERPAPI_BASE = "https://serpapi.com/search"

# Fallback IATA codes if user doesn't select airport
CITY_TO_IATA = {
    "new york": "JFK", "nyc": "JFK", "new york city": "JFK",
    "los angeles": "LAX", "la": "LAX", "chicago": "ORD",
    "atlanta": "ATL", "dallas": "DFW", "miami": "MIA",
    "san francisco": "SFO", "seattle": "SEA", "boston": "BOS",
    "las vegas": "LAS", "orlando": "MCO", "houston": "IAH",
    "london": "LHR", "paris": "CDG", "frankfurt": "FRA",
    "amsterdam": "AMS", "rome": "FCO", "madrid": "MAD",
    "barcelona": "BCN", "berlin": "BER", "vienna": "VIE",
    "zurich": "ZRH", "lisbon": "LIS", "athens": "ATH",
    "brussels": "BRU", "stockholm": "ARN", "oslo": "OSL",
    "dubai": "DXB", "abu dhabi": "AUH", "doha": "DOH",
    "riyadh": "RUH", "istanbul": "IST",
    "delhi": "DEL", "new delhi": "DEL", "mumbai": "BOM",
    "bangalore": "BLR", "bengaluru": "BLR",
    "hyderabad": "HYD", "chennai": "MAA", "kolkata": "CCU",
    "kochi": "COK", "pune": "PNQ", "ahmedabad": "AMD",
    "goa": "GOI", "india": "DEL",
    "tokyo": "NRT", "osaka": "KIX", "seoul": "ICN",
    "beijing": "PEK", "shanghai": "PVG",
    "singapore": "SIN", "bangkok": "BKK",
    "hong kong": "HKG", "taipei": "TPE",
    "kuala lumpur": "KUL", "jakarta": "CGK",
    "bali": "DPS", "denpasar": "DPS", "manila": "MNL",
    "sydney": "SYD", "melbourne": "MEL", "brisbane": "BNE",
    "auckland": "AKL", "toronto": "YYZ", "vancouver": "YVR",
    "montreal": "YUL", "mexico city": "MEX", "cancun": "CUN",
    "cairo": "CAI", "nairobi": "NBO",
    "johannesburg": "JNB", "cape town": "CPT",
    "casablanca": "CMN", "lagos": "LOS",
    "moscow": "SVO", "amsterdam": "AMS",
    "sao paulo": "GRU", "rio de janeiro": "GIG",
    "antalya": "AYT", "hurghada": "HRG",
}


class FlightAgent:

    def _key(self):
        return os.getenv("SERPAPI_KEY", "")

    def _get_iata(self, place: str) -> str:
        """Convert city/country name to IATA code."""
        # Already an IATA code
        if re.match(r'^[A-Z]{3}$', place.strip()):
            return place.strip()
        clean = place.lower().strip()
        # Direct match
        if clean in CITY_TO_IATA:
            return CITY_TO_IATA[clean]
        # Partial match
        for key, code in CITY_TO_IATA.items():
            if key in clean or clean in key:
                return code
        # Fallback: uppercase first 3 letters
        return clean[:3].upper()

    def search_flights(self, origin: str, destination: str, date: str,
                       travelers: int, nonstop: bool = False) -> dict:
        key = self._key()
        print(f"Flight search: {origin} → {destination} on {date}, serpapi_key={'SET' if key else 'NOT SET'}")

        if not key:
            return self._mock(origin, destination, date, travelers, nonstop)

        # Get IATA codes
        origin_iata = self._get_iata(origin)
        dest_iata = self._get_iata(destination)
        print(f"Google Flights: {origin_iata} → {dest_iata}")

        try:
            params = {
                "engine": "google_flights",
                "departure_id": origin_iata,
                "arrival_id": dest_iata,
                "outbound_date": date,
                "type": "2",           # one-way
                "travel_class": "1",   # economy
                "adults": str(travelers),
                "currency": "USD",
                "hl": "en",
                "gl": "us",
                "api_key": key,
                "sort_by": "2",        # sort by price
            }
            if nonstop:
                params["stops"] = "1"  # 1 = nonstop only

            r = requests.get(SERPAPI_BASE, params=params, timeout=25)
            print(f"Google Flights status: {r.status_code}")

            if r.status_code == 200:
                data = r.json()
                flights = self._parse(data, origin, destination,
                                      origin_iata, dest_iata,
                                      date, travelers, nonstop)
                if flights:
                    print(f"Google Flights returned {len(flights)} real flights")
                    return {"success": True, "flights": flights, "source": "live"}
                print("No flights parsed from Google Flights")
            else:
                print(f"Google Flights error {r.status_code}: {r.text[:200]}")

        except Exception as e:
            print(f"Google Flights exception: {e}")

        return self._mock(origin, destination, date, travelers, nonstop)

    def _parse(self, data, origin, destination, origin_iata, dest_iata,
               date, travelers, nonstop):
        flights = []
        seen = set()

        # SerpAPI returns best_flights and other_flights
        all_results = data.get("best_flights", []) + data.get("other_flights", [])
        print(f"Google Flights raw results: {len(all_results)}")

        if all_results:
            first = all_results[0]
            first_flight = first.get("flights", [{}])[0]
            print(f"Sample: airline={first_flight.get('airline')}, "
                  f"price={first.get('price')}, "
                  f"duration={first.get('total_duration')}")

        for result in all_results[:10]:
            try:
                flight_legs = result.get("flights", [])
                if not flight_legs:
                    continue

                price = float(result.get("price", 0))
                if price <= 0:
                    continue

                total_duration = int(result.get("total_duration", 0))
                stops = len(result.get("layovers", []))

                if nonstop and stops > 0:
                    continue

                # First and last leg
                first_leg = flight_legs[0]
                last_leg = flight_legs[-1]

                airline = first_leg.get("airline", "Unknown")
                flight_num = first_leg.get("flight_number", "")
                airline_logo = first_leg.get("airline_logo", "")

                # Departure / arrival times
                dep_airport = first_leg.get("departure_airport", {})
                arr_airport = last_leg.get("arrival_airport", {})
                dep_time = dep_airport.get("time", f"{date} 08:00")
                arr_time = arr_airport.get("time", f"{date} 20:00")
                dep_name = dep_airport.get("name", origin)
                arr_name = arr_airport.get("name", destination)

                # Airplane model
                airplane = first_leg.get("airplane", "")

                # Extensions (legroom, wifi etc)
                extensions = first_leg.get("extensions", [])
                features = [e for e in extensions[:3] if isinstance(e, str)]

                if airline in seen:
                    continue
                seen.add(airline)

                flights.append({
                    "airline": airline,
                    "flight_number": flight_num,
                    "airline_logo": airline_logo,
                    "departure": dep_time,
                    "arrival": arr_time,
                    "dep_airport": dep_name,
                    "arr_airport": arr_name,
                    "duration": total_duration,
                    "stops": stops,
                    "airplane": airplane,
                    "features": features,
                    "price_per_person": round(price / max(travelers, 1), 2),
                    "total_price": round(price, 2),
                    "currency": "USD",
                    "origin": origin,
                    "destination": destination,
                    "origin_iata": origin_iata,
                    "dest_iata": dest_iata,
                    "source": "live"
                })

                if len(flights) >= 3:
                    break

            except Exception as e:
                print(f"Flight parse error: {e}")
                continue

        return flights

    def _mock(self, origin, destination, date, travelers, nonstop):
        dest_l = destination.lower()
        if any(k in dest_l for k in ["india","delhi","mumbai","bangalore","hyderabad"]):
            base, dur = 650, 1020
        elif any(k in dest_l for k in ["london","paris","amsterdam","rome","madrid"]):
            base, dur = 480, 540
        elif any(k in dest_l for k in ["tokyo","singapore","bangkok","dubai"]):
            base, dur = 750, 900
        elif any(k in dest_l for k in ["sydney","melbourne","auckland"]):
            base, dur = 950, 1200
        else:
            base, dur = 350, 300

        airlines = [
            ("Air India", "AI102"), ("Emirates", "EK231"),
            ("British Airways", "BA117"), ("United Airlines", "UA972"),
            ("Qatar Airways", "QR572")
        ]
        flights = []
        for i, (airline, fn) in enumerate(airlines[:3]):
            if nonstop and i > 0: continue
            price = (base + i * 40) * travelers
            flights.append({
                "airline": airline, "flight_number": fn,
                "departure": f"{date} {7+i*2:02d}:00",
                "arrival": f"{date} {7+i*2+dur//60:02d}:{dur%60:02d}",
                "dep_airport": f"{origin} Airport",
                "arr_airport": f"{destination} Airport",
                "duration": dur + i * 30,
                "stops": 0 if i == 0 else 1,
                "airplane": "Boeing 777",
                "features": ["Free WiFi", "In-seat power"],
                "price_per_person": base + i * 40,
                "total_price": float(price),
                "currency": "USD",
                "origin": origin, "destination": destination,
                "source": "simulated"
            })
        return {"success": True, "flights": flights, "source": "simulated"}

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
            return "❌ No flights found for this route."
        flights = data["flights"]
        src = "*(live data — Google Flights)*" if data.get("source") == "live" \
              else "*(estimated — verify on Google Flights)*"
        best = self.recommend(flights, budget, nonstop)
        lines = [f"### ✈️ Available Flights {src}\n"]
        for i, f in enumerate(flights):
            h, m = divmod(f["duration"], 60)
            stop_txt = "🟢 Non-stop" if f["stops"] == 0 else f"🔴 {f['stops']} stop(s)"
            badge = " 🏆 **BEST PICK**" if i == best else ""
            pct = f" *({f['total_price']/budget*100:.0f}% of budget)*" if budget else ""
            airplane = f" · {f['airplane']}" if f.get("airplane") else ""
            lines.append(
                f"**Option {i+1}: {f['airline']} {f['flight_number']}**{badge}\n"
                f"  • 🛫 {f.get('dep_airport', f['origin'])} → "
                f"🛬 {f.get('arr_airport', f['destination'])}\n"
                f"  • Departure: `{f['departure']}` → Arrival: `{f['arrival']}`\n"
                f"  • Duration: **{h}h {m}m** | {stop_txt}{airplane}\n"
                f"  • Per person: **${f['price_per_person']:,.2f}** | "
                f"Total: **${f['total_price']:,.2f} {f['currency']}**{pct}\n"
            )
        bf = flights[best]
        h, m = divmod(bf["duration"], 60)
        stop_label = "Non-stop" if bf["stops"] == 0 else f"{bf['stops']} stop(s)"
        lines.append(
            f"\n✅ **Recommended Flight:** {bf['airline']} {bf['flight_number']} — "
            f"**${bf['total_price']:,.2f}** total | {h}h {m}m | {stop_label}"
        )
        return "\n".join(lines)
