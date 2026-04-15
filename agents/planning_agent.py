"""
Planning Agent - Enhanced
Generates very detailed day-by-day itinerary using Gemini AI.
Uses REAL data from flight/hotel/weather agents — no hallucination.
"""

import google.generativeai as genai
import os


class PlanningAgent:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash-lite")

    def generate_itinerary(self, requirements: dict, flight_data: dict, hotel_data: dict, weather_data: dict) -> str:
        dest = requirements.get("destination", "your destination")
        origin = requirements.get("origin", "your city")
        checkin = requirements.get("checkin", "")
        checkout = requirements.get("checkout", "")
        nights = requirements.get("nights", 1)
        budget = requirements.get("budget", 0)
        travelers = requirements.get("travelers", 1)
        nonstop = requirements.get("nonstop_preferred", False)
        profiles = requirements.get("travelers_profiles", [])

        # Build traveler string
        traveler_str = ""
        if profiles:
            traveler_str = "\n".join([
                f"  - {t.get('first_name','')} {t.get('last_name','')}, Age {t.get('age','?')}, {t.get('gender','?')}"
                for t in profiles
            ])
        else:
            traveler_str = f"  - {travelers} traveler(s)"

        # Best flight — use recommended one
        best_flight = "Not available"
        flight_cost = 0
        if flight_data.get("flights"):
            from agents.flight_agent import FlightAgent
            _fa = FlightAgent()
            best_flight_idx = _fa.recommend(flight_data["flights"], budget, nonstop)
            f = flight_data["flights"][best_flight_idx]
            flight_cost = f["total_price"]
            best_flight = (
                f"{f['airline']} {f['flight_number']} — "
                f"${f['total_price']:,.2f} total | "
                f"{'Non-stop' if f['stops']==0 else str(f['stops'])+' stop(s)'} | "
                f"${f['price_per_person']:,.2f}/person"
            )

        # Best hotel — use recommended one (not just first)
        best_hotel = "Not available"
        hotel_per_night = 0
        hotel_rooms = hotel_data.get("rooms", 1)
        hotel_search_city = hotel_data.get("search_city", dest)
        hotel_airport = hotel_data.get("airport_code", "")
        if hotel_data.get("hotels"):
            from agents.hotel_agent import HotelAgent
            _ha = HotelAgent()
            best_idx = _ha.recommend(hotel_data["hotels"], nights, budget)
            h = hotel_data["hotels"][best_idx]
            hotel_per_night = h.get("price_per_night_per_room") or h.get("price_per_night", 0)
            hotel_per_night_total = hotel_per_night * hotel_rooms
            hotel_cost = hotel_per_night_total * nights
            location_str = h.get("location", hotel_search_city)
            airport_str = f" | Near {hotel_airport} Airport" if hotel_airport else ""
            best_hotel = (
                f"{h['name']} — ${hotel_per_night_total:,.2f}/night "
                f"({hotel_rooms} room(s)) | Rating: {h['rating']}/10 | "
                f"Location: {location_str}{airport_str} | "
                f"Total: ${hotel_cost:,.2f}"
            )

        # Weather
        weather_str = "Not available"
        if weather_data.get("current"):
            c = weather_data["current"]
            weather_str = f"{c.get('condition','')}, {c.get('temp_c','?')}°C/{c.get('temp_f','?')}°F, Humidity {c.get('humidity','?')}%"

        forecast_str = ""
        for d in weather_data.get("forecast", [])[:3]:
            forecast_str += f"\n  - {d.get('date','')}: {d.get('condition','')} | {d.get('max_temp_c','?')}°C max | Rain: {d.get('rain_chance','?')}%"

        flight_cost = flight_data["flights"][0]["total_price"] if flight_data.get("flights") else 0
        if not hotel_data.get("hotels"):
            hotel_cost = 0
            hotel_rooms = 1
        remaining = budget - flight_cost - hotel_cost

        prompt = f"""
You are an expert luxury travel planner. Create an extremely detailed, practical, and exciting travel itinerary.

IMPORTANT: Use ONLY the real data provided below. Do NOT make up prices, airlines, hotels, or weather. Base your recommendations entirely on the actual data given.

═══════════════════════════════════════
TRIP DATA (USE THIS EXACTLY)
═══════════════════════════════════════
Destination: {dest}
Departing From: {origin}
Check-in: {checkin}
Check-out: {checkout}
Duration: {nights} nights
Total Budget: ${budget:,.2f} USD
Non-stop Preference: {"Yes" if nonstop else "No preference"}

TRAVELERS:
{traveler_str}

RECOMMENDED FLIGHT (real data):
{best_flight}

RECOMMENDED HOTEL (real data):
{best_hotel}
Hotel search area: {hotel_search_city}{f" (near {hotel_airport} airport)" if hotel_airport else ""}
NOTE: Suggest activities, restaurants and attractions near this hotel location.

WEATHER (real data):
Current: {weather_str}
Forecast:{forecast_str}

BUDGET BREAKDOWN:
- Flight Cost: ${flight_cost:,.2f}
- Hotel Cost ({nights} nights): ${hotel_cost:,.2f}
- Remaining for Food/Activities: ${max(0, remaining):,.2f}
═══════════════════════════════════════

Create the itinerary in this EXACT format:

## 💰 Budget Summary
Show exact breakdown using the numbers above. Calculate daily food/activity budget from remaining amount.

## ✈️ Flight & Hotel Confirmed
State the recommended flight and hotel from the real data above.

## 🗓️ Day-by-Day Itinerary

For EACH of the {nights} days, provide:

### Day [N] — [Date] — [Theme e.g. "Arrival & Exploration"]

**🌅 Morning (7:00 AM – 12:00 PM)**
- Specific activity with real location name
- Estimated cost: $X
- Travel tip

**☀️ Afternoon (12:00 PM – 6:00 PM)**  
- Specific restaurant recommendation with cuisine type
- Lunch estimated cost: $X per person
- Afternoon activity with real attraction name
- Estimated cost: $X

**🌙 Evening (6:00 PM – 10:00 PM)**
- Dinner restaurant recommendation
- Estimated cost: $X per person
- Evening activity or relaxation

**💸 Day [N] Total Estimate: $X**

[Repeat for all {nights} days]

## 🎒 Packing List
Based on the actual weather data: {weather_str}
List 10-15 specific items.

## 💡 Local Tips for {dest}
- 5 practical tips specific to this destination
- Best local transport options
- Currency/payment tips
- Safety tips
- Cultural etiquette

## 📊 Final Budget Tracker
| Category | Budgeted | Estimated Spend |
|----------|---------|-----------------|
| Flights | ${flight_cost:,.2f} | ${flight_cost:,.2f} |
| Hotel | ${hotel_cost:,.2f} | ${hotel_cost:,.2f} |
| Food ({nights} days) | $X | $X |
| Activities | $X | $X |
| Transport | $X | $X |
| Shopping/Misc | $X | $X |
| **TOTAL** | **${budget:,.2f}** | **$X** |

Be specific, practical and enthusiastic. Use real place names for {dest}. Make each day feel unique and exciting!
"""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Gemini error: {e}")
            return self._fallback(requirements, flight_cost, hotel_cost, remaining, nights, dest)

    def _fallback(self, req, flight_cost, hotel_cost, remaining, nights, dest):
        return f"""
## 💰 Budget Summary
- ✈️ Flights: ${flight_cost:,.2f}
- 🏨 Hotel ({nights} nights): ${hotel_cost:,.2f}
- 🍽️ Food & Activities: ${max(0,remaining):,.2f}
- **Total Budget: ${req.get('budget',0):,.2f}**

## 📅 Day-by-Day Plan

**Day 1 — Arrival**
- 🌅 Morning: Arrive, check in, freshen up
- ☀️ Afternoon: Explore local area, light lunch (~$15-20/person)
- 🌙 Evening: Welcome dinner at local restaurant (~$25-35/person)

**Days 2–{max(1, nights-1)} — Exploration**
- Visit top attractions and landmarks
- Try authentic local cuisine
- Shopping at local markets

**Day {nights} — Departure**
- Morning: Final breakfast, last-minute shopping
- Check out and head to airport

## 💡 Travel Tips
- Book attractions in advance
- Carry local currency for small vendors
- Keep copies of important documents
- Check visa requirements before travel
- Get travel insurance
"""
