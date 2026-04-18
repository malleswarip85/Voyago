"""
Flight Agent - SerpAPI Google Flights
Fetches real flights from Google Flights via SerpAPI.
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
    "phuket":"HKT","chiang mai":"CNX","ho chi minh":"SGN",
    "hanoi":"HAN","colombo":"CMB","kathmandu":"KTM",
    "karachi":"KHI","lahore":"LHE","dhaka":"DAC",
    "milan":"MXP","venice":"VCE","munich":"MUC",
    "budapest":"BUD","prague":"PRG","warsaw":"WAW",
    "copenhagen":"CPH","helsinki":"HEL",
    "oslo":"OSL","stockholm":"ARN","zurich":"ZRH","brussels":"BRU",
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
        serpapi_key = os.getenv("SERPAPI_KEY", "")
        print(f"Flight search: {origin} → {destination} on {date} for {travelers} traveler(s)")

        origin_iata = self._get_iata(origin)
        dest_iata = self._get_iata(destination)
        print(f"IATA codes: {origin_iata} → {dest_iata}")

        if not serpapi_key:
            print("No SERPAPI_KEY — using mock data")
            return self._mock(origin, destination, date, travelers, nonstop,
                              origin_iata, dest_iata)

        # Base params — type=2 is one-way in SerpAPI Google Flights
        base_params = {
            "engine": "google_flights",
            "departure_id": origin_iata,
            "arrival_id": dest_iata,
            "outbound_date": date,
            "type": "2",          # 2 = one-way
            "travel_class": "1",  # 1 = economy
            "adults": str(travelers),
            "currency": "USD",
            "hl": "en",
            "gl": "us",
            "api_key": serpapi_key,
        }

        # Search strategies — try different sorts to get variety
        strategies = [
            {"sort_by": "2", "label": "cheapest"},
            {"sort_by": "1", "label": "best"},
            {"sort_by": "5", "label": "fastest"},
        ]
        if nonstop:
            strategies = [
                {"stops": "1", "sort_by": "2", "label": "nonstop cheapest"},
                {"stops": "1", "sort_by": "1", "label": "nonstop best"},
                {"sort_by": "2", "label": "any stops"},
            ]

        all_flights = []
        seen = set()

        for strategy in strategies:
            if len(all_flights) >= 5:
                break
            try:
                params = {**base_params, **strategy}
                label = params.pop("label", "")

                r = requests.get(SERPAPI_BASE, params=params, timeout=30)
                print(f"  SerpAPI [{label}] → HTTP {r.status_code}")

                if r.status_code != 200:
                    print(f"  Error body: {r.text[:300]}")
                    continue

                data = r.json()
                if "error" in data:
                    print(f"  SerpAPI error: {data['error']}")
                    continue

                new = self._parse(data, origin, destination, origin_iata,
                                  dest_iata, date, travelers, seen)
                for f in new:
                    uid = f"{f['airline']}_{f['flight_number']}_{f['departure']}"
                    if uid not in seen:
                        all_flights.append(f)
                        seen.add(uid)

                print(f"  [{label}] parsed {len(new)} flights, total={len(all_flights)}")

            except Exception as e:
                print(f"  Strategy [{label}] exception: {e}")
                continue

        if all_flights:
            all_flights.sort(key=lambda f: f["total_price"])
            print(f"Returning {min(len(all_flights), 5)} live flights")
            return {"success": True, "flights": all_flights[:5], "source": "live"}

        print("All strategies failed — falling back to mock data")
        return self._mock(origin, destination, date, travelers, nonstop,
                          origin_iata, dest_iata)

    def _parse(self, data, origin, destination, origin_iata, dest_iata,
               date, travelers, seen):
        flights = []
        raw = data.get("best_flights", []) + data.get("other_flights", [])
        print(f"  Raw results from API: {len(raw)}")

        for result in raw[:20]:
            try:
                legs = result.get("flights", [])
                if not legs:
                    continue

                # SerpAPI Google Flights: `price` is per-person price
                price_per_person = float(result.get("price", 0))
                if price_per_person <= 0:
                    continue

                total_price = round(price_per_person * travelers, 2)
                total_duration = int(result.get("total_duration", 0))
                stops = len(result.get("layovers", []))

                first_leg = legs[0]
                last_leg = legs[-1]

                airline = first_leg.get("airline", "Unknown Airline")
                flight_num = first_leg.get("flight_number", "")
                airline_logo = first_leg.get("airline_logo", "")

                uid = f"{airline}_{flight_num}_{first_leg.get('departure_airport', {}).get('time', '')}"
                if uid in seen:
                    continue

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

                # Duration fallback
                duration_mins = total_duration
                if duration_mins == 0 and dep_time and arr_time:
                    try:
                        d1 = datetime.strptime(dep_time[:16], "%Y-%m-%d %H:%M")
                        d2 = datetime.strptime(arr_time[:16], "%Y-%m-%d %H:%M")
                        diff = (d2 - d1).total_seconds() / 60
                        if diff > 0:
                            duration_mins = int(diff)
                    except Exception:
                        pass

                airplane = first_leg.get("airplane", "")

                layovers = result.get("layovers", [])
                layover_info = ""
                if layovers:
                    cities = [lv.get("name", "").split(" Airport")[0].split(" International")[0]
                              for lv in layovers[:2]]
                    layover_info = " via " + ", ".join(c for c in cities if c)

                print(f"  ✈ {airline} {flight_num} | {dep_code}→{arr_code} | "
                      f"{duration_mins//60}h{duration_mins%60:02d}m | "
                      f"${price_per_person}/pp × {travelers} = ${total_price} | "
                      f"{stops} stop(s)")

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
                    "price_per_person": round(price_per_person, 2),
                    "total_price": total_price,
                    "currency": "USD",
                    "origin": origin,
                    "destination": destination,
                    "source": "live",
                })

            except Exception as e:
                print(f"  Parse error: {e}")
                continue

        return flights

    def _mock(self, origin, destination, date, travelers, nonstop,
              origin_iata="ORD", dest_iata="DEL"):
        dest_l = destination.lower()
        if any(k in dest_l for k in ["india","delhi","mumbai","bangalore","hyderabad","chennai","kolkata"]):
            base, dur = 680, 1380
        elif any(k in dest_l for k in ["london","paris","amsterdam","rome","madrid","berlin","zurich"]):
            base, dur = 510, 540
        elif any(k in dest_l for k in ["tokyo","singapore","bangkok","dubai","seoul","hong kong"]):
            base, dur = 790, 900
        elif any(k in dest_l for k in ["sydney","melbourne","auckland","perth"]):
            base, dur = 980, 1200
        elif any(k in dest_l for k in ["cancun","mexico","caribbean","bali","phuket"]):
            base, dur = 420, 480
        else:
            base, dur = 380, 300

        carriers = [
            ("Emirates",       "EK231"),
            ("United Airlines","UA972"),
            ("Air India",      "AI102"),
            ("Qatar Airways",  "QR572"),
            ("British Airways","BA117"),
        ]
        flights = []
        for i, (airline, fn) in enumerate(carriers[:5]):
            if nonstop and i > 0:
                continue
            ppp = base + i * 40
            total = ppp * travelers
            arr_h = (7 + i * 2 + dur // 60) % 24
            flights.append({
                "airline": airline,
                "flight_number": fn,
                "airline_logo": "",
                "departure": f"{date} {7 + i * 2:02d}:00",
                "arrival": f"{date} {arr_h:02d}:{dur % 60:02d}",
                "dep_airport": f"{origin} ({origin_iata})",
                "arr_airport": f"{destination} ({dest_iata})",
                "dep_code": origin_iata,
                "arr_code": dest_iata,
                "duration": dur + i * 30,
                "stops": 0 if i == 0 else 1,
                "layover_info": "" if i == 0 else " via connecting city",
                "airplane": "Boeing 777",
                "price_per_person": float(ppp),
                "total_price": float(total),
                "currency": "USD",
                "origin": origin,
                "destination": destination,
                "source": "simulated",
            })
        return {"success": True, "flights": flights, "source": "simulated"}

    def recommend(self, flights, budget, nonstop):
        if not flights:
            return 0
        scored = []
        for i, f in enumerate(flights):
            s = 0
            if f["total_price"] <= budget * 0.4:
                s += 50
            elif f["total_price"] <= budget * 0.55:
                s += 25
            if nonstop and f["stops"] == 0:
                s += 30
            elif f["stops"] == 0:
                s += 10
            s += max(0, 20 - int(f["total_price"] / 100))
            scored.append((i, s))
        return max(scored, key=lambda x: x[1])[0]

    def format_for_display(self, data, budget=0, nonstop=False):
        if not data.get("flights"):
            return "❌ No flights found for this route."

        flights = data["flights"]
        is_live = data.get("source") == "live"
        source_txt = "✓ Live data — Google Flights" if is_live else "~ Estimated prices — verify on Google Flights"
        best_idx = self.recommend(flights, budget, nonstop)

        bf = flights[best_idx]
        dur = bf.get("duration", 0)
        bh, bm = dur // 60, dur % 60
        best_dur = f"{bh}h {bm:02d}m" if bh > 0 else "N/A"
        best_stops = "Non-stop" if bf["stops"] == 0 else f"{bf['stops']} stop(s)"
        summary = (f"{bf['airline']} {bf['flight_number']} — "
                   f"${bf['total_price']:,.0f} total | {best_dur} | {best_stops}")

        cards = []
        for i, f in enumerate(flights):
            dur = f.get("duration", 0)
            fh, fm = dur // 60, dur % 60
            dur_str = f"{fh}h {fm:02d}m" if fh > 0 else "N/A"
            is_best = (i == best_idx)
            is_nonstop = f["stops"] == 0
            pct_txt = f" · {f['total_price']/budget*100:.0f}% of budget" if budget else ""
            layover = f.get("layover_info", "")
            airplane = f.get("airplane", "")
            footer_note = f.get("source", "")

            # Extract HH:MM from datetime string
            dep_time = f.get("departure", "")
            arr_time = f.get("arrival", "")
            dep_hm = dep_time.split(" ")[-1][:5] if " " in dep_time else dep_time[:5]
            arr_hm = arr_time.split(" ")[-1][:5] if " " in arr_time else arr_time[:5]

            dep_code = f.get("dep_code", "")
            arr_code = f.get("arr_code", "")
            origin_city = (f.get("origin") or "")[:12]
            dest_city = (f.get("destination") or "")[:12]

            stop_badge = (
                '<span style="background:rgba(34,197,94,0.12);color:#16a34a;border:1px solid rgba(34,197,94,0.2);'
                'border-radius:12px;padding:2px 7px;font-size:9.5px;font-weight:600;white-space:nowrap;">✈ Non-stop</span>'
                if is_nonstop else
                f'<span style="background:rgba(249,115,22,0.1);color:#c2410c;border:1px solid rgba(249,115,22,0.2);'
                f'border-radius:12px;padding:2px 7px;font-size:9.5px;font-weight:600;white-space:nowrap;">'
                f'🔀 {f["stops"]} stop</span>'
            )
            best_badge = (
                '<span style="background:rgba(217,119,6,0.12);color:#92400e;border:1px solid rgba(217,119,6,0.25);'
                'border-radius:12px;padding:2px 7px;font-size:9.5px;font-weight:700;white-space:nowrap;margin-left:3px;">'
                '🏆 Best Pick</span>'
                if is_best else ""
            )

            border_style = "border-color:#d97706;" if is_best else ""
            header_bg = "background:rgba(255,251,235,0.9);" if is_best else "background:rgba(240,253,250,0.6);"
            live_dot = '<span style="color:#16a34a;font-size:9px;">●</span> Live' if footer_note == "live" else "~ Est."

            cards.append(f"""
<div style="background:var(--bg-white,#fff);border:1.5px solid var(--border,rgba(14,116,144,0.15));{border_style}border-radius:12px;overflow:hidden;box-shadow:var(--shadow-sm,0 2px 8px rgba(12,92,107,0.05));">
  <div style="display:flex;align-items:center;justify-content:space-between;padding:10px 14px;{header_bg}border-bottom:1px solid var(--border,rgba(14,116,144,0.08));">
    <div style="display:flex;align-items:center;gap:5px;flex-wrap:wrap;">
      <span style="font-size:12.5px;font-weight:700;color:var(--sky-deep,#0c5c6b);">✈ {f['airline']} {f['flight_number']}</span>
      {stop_badge}{best_badge}
    </div>
    <div style="text-align:right;flex-shrink:0;margin-left:8px;">
      <div style="font-size:15px;font-weight:700;color:var(--sky-deep,#0c5c6b);">${f['total_price']:,.0f}</div>
      <div style="font-size:10px;color:var(--text-muted,#a16207);">${f['price_per_person']:,.0f}/person{pct_txt}</div>
    </div>
  </div>
  <div style="padding:14px 16px;display:flex;align-items:center;">
    <div style="text-align:center;min-width:54px;">
      <div style="font-size:18px;font-weight:700;color:var(--text-body,#1c1917);">{dep_hm}</div>
      <div style="font-size:12px;font-weight:700;color:var(--sky-mid,#0e7490);">{dep_code}</div>
      <div style="font-size:9.5px;color:var(--text-muted,#a16207);">{origin_city}</div>
    </div>
    <div style="flex:1;padding:0 14px;position:relative;">
      <div style="height:1.5px;background:rgba(14,116,144,0.2);width:100%;"></div>
      <div style="position:absolute;top:-8px;left:50%;transform:translateX(-50%);background:var(--bg-white,white);padding:0 6px;font-size:10px;color:var(--sky-mid,#0e7490);font-weight:600;white-space:nowrap;">{dur_str}</div>
      <div style="text-align:center;font-size:9px;color:var(--text-muted,#a16207);margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{layover}</div>
    </div>
    <div style="text-align:center;min-width:54px;">
      <div style="font-size:18px;font-weight:700;color:var(--text-body,#1c1917);">{arr_hm}</div>
      <div style="font-size:12px;font-weight:700;color:var(--sky-mid,#0e7490);">{arr_code}</div>
      <div style="font-size:9.5px;color:var(--text-muted,#a16207);">{dest_city}</div>
    </div>
  </div>
  <div style="padding:8px 14px 10px;border-top:1px solid var(--border,rgba(14,116,144,0.08));display:flex;justify-content:space-between;align-items:center;">
    <span style="font-size:10.5px;color:var(--text-muted,#a16207);">{live_dot}{(' · ' + airplane) if airplane else ''}</span>
    <a href="https://www.google.com/travel/flights" target="_blank" style="font-size:11px;font-weight:600;color:var(--sky-mid,#0e7490);text-decoration:none;padding:3px 8px;border:1px solid var(--border,rgba(14,116,144,0.15));border-radius:6px;">Search Google Flights →</a>
  </div>
</div>""")

        return (f'<div data-summary="{summary}" style="display:flex;flex-direction:column;gap:8px;">'
                f'<div style="font-size:10.5px;color:var(--text-muted,#a16207);margin-bottom:2px;">{source_txt}</div>'
                + "".join(cards) +
                f'<div style="font-size:12px;font-weight:600;color:var(--sky-deep,#0c5c6b);padding:6px 2px 0;">'
                f'✅ Recommended: {summary}</div>'
                f'</div>')
