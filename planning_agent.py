"""
Planning Agent
Uses Gemini AI to generate a full travel itinerary based on
flights, hotels, weather, and budget data.
"""

import google.generativeai as genai
import os
import json


class PlanningAgent:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def generate_itinerary(
        self,
        requirements: dict,
        flight_data: dict,
        hotel_data: dict,
        weather_data: dict
    ) -> str:
        """Generate a complete travel itinerary using Gemini AI."""

        # Build context for the AI
        flight_summary = self._summarize_flights(flight_data)
        hotel_summary = self._summarize_hotels(hotel_data, requirements.get("nights", 1))
        weather_summary = self._summarize_weather(weather_data)

        prompt = f"""
You are an expert travel planner. Create a detailed, exciting travel itinerary based on the following information:

**TRIP DETAILS:**
- Destination: {requirements.get('destination')}
- Origin: {requirements.get('origin', 'Not specified')}
- Check-in: {requirements.get('checkin')}
- Check-out: {requirements.get('checkout')}
- Duration: {requirements.get('nights')} nights
- Travelers: {requirements.get('travelers')} person(s)
- Total Budget: ${requirements.get('budget'):,.2f} USD

**FLIGHT OPTIONS:**
{flight_summary}

**HOTEL OPTIONS:**
{hotel_summary}

**WEATHER FORECAST:**
{weather_summary}

Please create a comprehensive itinerary that includes:

1. **RECOMMENDED FLIGHT & HOTEL** (best value for budget)
2. **BUDGET BREAKDOWN** (flights + hotel + food + activities = total)
3. **DAY-BY-DAY ITINERARY** for all {requirements.get('nights')} nights:
   - Morning, Afternoon, Evening activities
   - Recommended restaurants/food for each day
   - Must-see attractions and hidden gems
   - Weather-appropriate suggestions
4. **PACKING SUGGESTIONS** based on weather
5. **TRAVEL TIPS** specific to {requirements.get('destination')}
6. **ESTIMATED SAVINGS** from the ${requirements.get('budget'):,.2f} budget

Make it enthusiastic, practical, and personalized. Use emojis to make it visually engaging.
Format with clear headers and bullet points.
"""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return self._fallback_itinerary(requirements, flight_data, hotel_data, weather_data)

    def _summarize_flights(self, flight_data: dict) -> str:
        if not flight_data or not flight_data.get("flights"):
            return "No flight data available"
        flights = flight_data["flights"]
        lines = []
        for i, f in enumerate(flights[:3], 1):
            lines.append(f"Option {i}: {f.get('airline', 'Unknown')} - ${f.get('total_price', 0):,.2f} total")
        return "\n".join(lines)

    def _summarize_hotels(self, hotel_data: dict, nights: int) -> str:
        if not hotel_data or not hotel_data.get("hotels"):
            return "No hotel data available"
        hotels = hotel_data["hotels"]
        lines = []
        for i, h in enumerate(hotels[:3], 1):
            total = h.get("price_per_night", 0) * nights
            lines.append(f"Option {i}: {h.get('name', 'Unknown')} - ${h.get('price_per_night', 0):,.2f}/night (${total:,.2f} total)")
        return "\n".join(lines)

    def _summarize_weather(self, weather_data: dict) -> str:
        if not weather_data:
            return "No weather data available"
        current = weather_data.get("current", {})
        return (
            f"Current: {current.get('condition', 'Unknown')}, "
            f"{current.get('temp_c', '?')}°C / {current.get('temp_f', '?')}°F, "
            f"Humidity: {current.get('humidity', '?')}%"
        )

    def _fallback_itinerary(self, requirements: dict, flight_data: dict, hotel_data: dict, weather_data: dict) -> str:
        """Simple fallback if Gemini API fails."""
        dest = requirements.get("destination", "your destination")
        nights = requirements.get("nights", 1)
        budget = requirements.get("budget", 0)

        return f"""
## 🗺️ Your {dest} Travel Plan

### ✈️ Flight Recommendation
Best value flight selected from available options above.

### 🏨 Hotel Recommendation  
Best rated hotel within budget selected from options above.

### 📅 Day-by-Day Plan

**Day 1 — Arrival**
- 🌅 Morning: Arrive, check in to hotel, freshen up
- 🍽️ Afternoon: Explore nearby restaurants, local lunch
- 🌆 Evening: Stroll around city center, dinner at a local restaurant

**Days 2 to {nights - 1} — Exploration**
- 🏛️ Visit major attractions and landmarks
- 🛍️ Shopping at local markets
- 🍜 Try authentic local cuisine

**Day {nights} — Departure**
- 🌅 Morning: Final breakfast, last-minute shopping
- 🧳 Check out and head to airport

### 💰 Budget Estimate
- Total Budget: ${budget:,.2f}
- Estimated spend: flights + hotels + food + activities

### 💡 Travel Tips
- Carry local currency for small purchases
- Book attractions in advance to avoid queues
- Check visa requirements before traveling
"""
