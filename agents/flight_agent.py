"""
Flight Agent - SerpAPI Google Flights
Fetches real flights from Google Flights.
Returns up to 5 best options sorted by price.
"""
import requests, os, re
from datetime import datetime

SERPAPI_BASE = "https://serpapi.com/search"

# City/country → IATA code
CITY_TO_IATA = {
    "new york":"JFK","nyc":"JFK","los angeles":"LAX","la":"LAX",
    "chicago":"ORD","atlanta":"ATL","dallas":"DFW","miami":"MIA",
    "san francisco":"SFO","seattle":"SEA","boston":"BOS",
    "las vegas":"LAS","orlando":"MCO","houston":"IAH",
    "washington":"IAD","denver":"DEN","phoenix":"PHX",
    "minneapolis":"MSP","detroit":"DTW","charlotte":"CLT",
    "portland":"PDX","nashville":"BNA","mobile":"MOB",
    "london":"LHR","paris":"CDG","frankfurt":"FRA",
    "amsterdam":"AMS","rome":"FCO","madrid":"MAD",
    "barcelona":"BCN","berlin":"BER","vienna":"VIE",
    "zurich":"ZRH","lisbon":"LIS","athens":"ATH",
    "brussels":"BRU","stockholm":"ARN","oslo":"OSL",
    "dubai":"DXB","abu dhabi":"AUH","doha":"DOH","riyadh":"RUH",
    "istanbul":"IST","cairo":"CAI","tel aviv":"TLV",
    "delhi":"DEL","new delhi":"DEL","mumbai":"BOM",
    "bangalore":"BLR","bengaluru":"BLR","hyderabad":"HYD",
    "chennai":"MAA","kolkata":"CCU","kochi":"COK",
    "pune":"PNQ","ahmedabad":"AMD","goa":"GOI",
    "india":"DEL","japan":"NRT","tokyo":"NRT","osaka":"KIX",
    "seoul":"ICN","beijing":"PEK","shanghai":"PVG",
    "singapore":"SIN","bangkok":"BKK","hong kong":"HKG",
    "taipei":"TPE","kuala lumpur":"KUL","jakarta":"CGK",
    "bali":"DPS","denpasar":"DPS","manila":"MNL",
    "sydney":"SYD","melbourne":"MEL","auckland":"AKL",
    "toronto":"YYZ","vancouver":"YVR","montreal":"YUL",
    "mexico city":"MEX","cancun":"CUN",
    "sao paulo":"GRU","rio de janeiro":"GIG",
    "johannesburg":"JNB","cape town":"CPT","nairobi":"NBO",
}


class FlightAgent:

    def _get_iata(self, place: str) -> str:
        if re.match(r'^[A-Z]{3}$', place.strip()):
            return place.strip()
        clean = place.lower().strip()
        if clean in CITY_TO_IATA:
            return CITY_TO_IATA[clean]
        for key, code in CITY_TO_IATA.items():
            if key in clean or clean in key:
                return code
        return clean[:3].upper()

    def search_flights(self, origin: str, destination: str, date: str,
                       travelers: int, nonstop: bool = False) -> dict:
        key = os.getenv("SERPAPI_KEY", "")
        print(f"Flight search: {origin} → {destination} on {date}")

        origin_iata = self._get_iata(origin)
        dest_iata = self._get_iata(destination)
        print(f"Google Flights: {origin_iata} → {dest_iata}")

        if not key:
            print("No SERPAPI_KEY — using mock")
            return self._mock(origin, destination, date, travelers, nonstop,
                              origin_iata, dest_iata)

        # Build base params
        base_params = {
            "engine": "google_flights",
            "departure_id": origin_iata,
            "arrival_id": dest_iata,
            "outbound_date": date,
            "type": "2",          # one-way
            "travel_class": "1",  # economy
            "adults": str(travelers),
            "currency": "USD",
            "hl": "en",
            "gl": "us",
            "api_key": key,
        }

        # Try multiple strategies to get real flights
        strategies = [
            {"sort_by": "2", "label": "cheapest"},           # price
            {"sort_by": "1", "label": "best"},               # best
            {"sort_by": "5", "label": "shortest duration"},  # duration
        ]
        if nonstop:
            strategies = [{"stops": "1", "sort_by": "2", "label": "nonstop cheap"},
                          {"sort_by": "2", "label": "any stops"}]

        all_flights = []
        seen_airlines = set()

        for strategy in strategies:
            if len(all_flights) >= 5:
                break
            try:
                params = dict(base_params)
                params.update(strategy)
                label = params.pop("label", "")

                r = requests.get(SERPAPI_BASE, params=params, timeout=25)
                print(f"Google Flights [{label}] status: {r.status_code}")

                if r.status_code != 200:
                    continue

                data = r.json()
                new_flights = self._parse(
                    data, origin, destination, origin_iata, dest_iata,
                    date, travelers, seen_airlines
                )

                for f in new_flights:
                    key_str = f"{f['airline']}_{f['flight_number']}"
                    if key_str not in seen_airlines:
                        all_flights.append(f)
                        seen_airlines.add(key_str)

                print(f"[{label}] found {len(new_flights)} new flights, total={len(all_flights)}")

            except Exception as e:
                print(f"Flight strategy error [{label}]: {e}")
                continue

        if all_flights:
            # Sort by price
            all_flights.sort(key=lambda f: f["total_price"])
            print(f"Returning {len(all_flights)} real flights")
            return {"success": True, "flights": all_flights[:5], "source": "live"}

        print("All strategies failed — using mock")
        return self._mock(origin, destination, date, travelers, nonstop,
                         origin_iata, dest_iata)

    def _parse(self, data, origin, destination, origin_iata, dest_iata,
               date, travelers, seen_airlines):
        flights = []
        all_results = data.get("best_flights", []) + data.get("other_flights", [])
        print(f"  Raw results: {len(all_results)}")

        for result in all_results[:20]:
            try:
                flight_legs = result.get("flights", [])
                if not flight_legs:
                    continue

                price = float(result.get("price", 0))
                if price <= 0:
                    continue

                total_duration = int(result.get("total_duration", 0))
                stops = len(result.get("layovers", []))

                first_leg = flight_legs[0]
                last_leg = flight_legs[-1]

                airline = first_leg.get("airline", "Unknown")
                flight_num = first_leg.get("flight_number", "")
                airline_logo = first_leg.get("airline_logo", "")

                # Skip if already seen this exact flight
                key_str = f"{airline}_{flight_num}"
                if key_str in seen_airlines:
                    continue

                # Airports
                dep_airport = first_leg.get("departure_airport", {})
                arr_airport = last_leg.get("arrival_airport", {})
                dep_time = dep_airport.get("time", f"{date} 08:00")
                arr_time = arr_airport.get("time", f"{date} 20:00")
                dep_name = dep_airport.get("name", origin)
                dep_code = dep_airport.get("id", origin_iata)
                arr_name = arr_airport.get("name", destination)
                arr_code = arr_airport.get("id", dest_iata)

                dep_display = f"{dep_name} ({dep_code})" if dep_code and dep_code not in dep_name else dep_name
                arr_display = f"{arr_name} ({arr_code})" if arr_code and arr_code not in arr_name else arr_name

                # Duration
                duration_mins = total_duration if total_duration > 0 else 0
                if duration_mins == 0 and dep_time and arr_time:
                    try:
                        fmt = "%Y-%m-%d %H:%M"
                        d1 = datetime.strptime(dep_time, fmt)
                        d2 = datetime.strptime(arr_time, fmt)
                        diff = (d2 - d1).total_seconds() / 60
                        if diff > 0:
                            duration_mins = int(diff)
                    except:
                        pass

                # Airplane
                airplane = first_leg.get("airplane", "")

                # Layovers info
                layovers = result.get("layovers", [])
                layover_info = ""
                if layovers:
                    layover_cities = [lv.get("name","").split(" Airport")[0].split(" International")[0]
                                     for lv in layovers[:2]]
                    layover_info = " via " + ", ".join(layover_cities)

                print(f"  ✈ {airline} {flight_num} | {dep_code}→{arr_code} | "
                      f"{duration_mins//60}h | ${price} | {stops} stop(s)")

                flights.append({
                    "airline": airline,
                    "flight_number": flight_num,
                    "airline_logo": airline_logo,
                    "departure": dep_time,
                    "arrival": arr_time,
                    "dep_airport": dep_display,
                    "arr_airport": arr_display,
                    "dep_code": dep_code,
                    "arr_code": arr_code,
                    "duration": duration_mins,
                    "stops": stops,
                    "layover_info": layover_info,
                    "airplane": airplane,
                    "price_per_person": round(price / max(travelers, 1), 2),
                    "total_price": round(price, 2),
                    "currency": "USD",
                    "origin": origin,
                    "destination": destination,
                    "source": "live"
                })

            except Exception as e:
                print(f"  Parse error: {e}")
                continue

        return flights

    def _mock(self, origin, destination, date, travelers, nonstop,
              origin_iata="ORD", dest_iata="DEL"):
        dest_l = destination.lower()
        if any(k in dest_l for k in ["india","delhi","mumbai","bangalore","hyderabad","chennai"]):
            base, dur = 650, 1380   # ~23h
        elif any(k in dest_l for k in ["london","paris","amsterdam","rome","madrid","berlin"]):
            base, dur = 480, 540    # ~9h
        elif any(k in dest_l for k in ["tokyo","singapore","bangkok","dubai","seoul"]):
            base, dur = 750, 900    # ~15h
        elif any(k in dest_l for k in ["sydney","melbourne","auckland"]):
            base, dur = 950, 1200   # ~20h
        else:
            base, dur = 350, 300    # ~5h

        airlines = [
            ("Air India", "AI102"), ("United Airlines", "UA972"),
            ("Emirates", "EK231"), ("Qatar Airways", "QR572"),
            ("British Airways", "BA117"),
        ]
        flights = []
        for i, (airline, fn) in enumerate(airlines[:5]):
            if nonstop and i > 0: continue
            price = (base + i * 35) * travelers
            arr_h = (7 + i*2 + dur//60) % 24
            flights.append({
                "airline": airline, "flight_number": fn,
                "airline_logo": "",
                "departure": f"{date} {7+i*2:02d}:00",
                "arrival": f"{date} {arr_h:02d}:{dur%60:02d}",
                "dep_airport": f"{origin} ({origin_iata})",
                "arr_airport": f"{destination} ({dest_iata})",
                "dep_code": origin_iata, "arr_code": dest_iata,
                "duration": dur + i*30,
                "stops": 0 if i==0 else 1,
                "layover_info": "" if i==0 else " via connecting city",
                "airplane": "Boeing 777",
                "price_per_person": base + i*35,
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
            dur = f.get("duration", 0)
            h = dur // 60 if dur > 0 else 0
            dur_str = f"{h}h" if h > 0 else "N/A"
            stop_txt = "🟢 Non-stop" if f["stops"] == 0 else f"🔴 {f['stops']} stop(s)"
            badge = " 🏆 **BEST PICK**" if i == best else ""
            pct = f" *({f['total_price']/budget*100:.0f}% of budget)*" if budget else ""
            airplane = f" · {f['airplane']}" if f.get("airplane") else ""
            layover = f.get("layover_info", "")

            lines.append(
                f"**Option {i+1}: {f['airline']} {f['flight_number']}**{badge}\n"
                f"  • 🛫 **{f.get('dep_airport', f['origin'])}**\n"
                f"  • 🛬 **{f.get('arr_airport', f['destination'])}**\n"
                f"  • Departure: `{f['departure']}` → Arrival: `{f['arrival']}`\n"
                f"  • Duration: **{dur_str}** | {stop_txt}{layover}{airplane}\n"
                f"  • Per person: **${f['price_per_person']:,.2f}** | "
                f"Total: **${f['total_price']:,.2f} {f.get('currency','USD')}**{pct}\n"
            )

        bf = flights[best]
        dur = bf.get("duration", 0)
        h = dur // 60 if dur > 0 else 0
        dur_str = f"{h}h" if h > 0 else ""
        stop_label = "Non-stop" if bf["stops"] == 0 else f"{bf['stops']} stop(s)"
        lines.append(
            f"\n✅ **Recommended Flight:** {bf['airline']} {bf['flight_number']} — "
            f"**${bf['total_price']:,.2f}** total | {dur_str} | {stop_label}"
        )
        return "\n".join(lines)
