"""
Agent Orchestrator
Central hub that coordinates all agents:
- RequirementCheckerAgent
- FlightAgent
- HotelAgent
- ClimateAgent
- PlanningAgent
"""

import google.generativeai as genai
import os
import json
import re

from agents.requirement_checker import RequirementCheckerAgent
from agents.flight_agent import FlightAgent
from agents.hotel_agent import HotelAgent
from agents.climate_agent import ClimateAgent
from agents.planning_agent import PlanningAgent


class AgentOrchestrator:
    def __init__(self):
        # Initialize all agents
        self.requirement_checker = RequirementCheckerAgent()
        self.flight_agent = FlightAgent()
        self.hotel_agent = HotelAgent()
        self.climate_agent = ClimateAgent()
        self.planning_agent = PlanningAgent()

        # Initialize Gemini for conversation management
        api_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        self.gemini = genai.GenerativeModel("gemini-1.5-flash")

        # Session state
        self.conversation_history = []
        self.collected_info = {}
        self.stage = "greeting"  # greeting → collecting → planning → done

    def reset(self):
        """Reset session for a new conversation."""
        self.conversation_history = []
        self.collected_info = {}
        self.stage = "greeting"

    def process_message(self, user_message: str) -> dict:
        """
        Main entry point. Process a user message and return a response.
        Returns: {message, stage, data}
        """
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Extract any travel info from the message using Gemini
        extracted = self._extract_travel_info(user_message)
        self.collected_info.update({k: v for k, v in extracted.items() if v})

        # Check current requirements
        check_result = self.requirement_checker.check(self.collected_info)

        if not check_result["valid"]:
            # Still missing info — ask for it naturally
            response_message = self._generate_collection_response(
                user_message, check_result, extracted
            )
            self.stage = "collecting"
            self.conversation_history.append({
                "role": "assistant",
                "content": response_message
            })
            return {
                "message": response_message,
                "stage": self.stage,
                "collected": self.collected_info,
                "missing": check_result["missing"]
            }

        # All info collected — run all agents
        self.stage = "planning"
        requirements = check_result["data"]

        # Step 1: Confirm requirements
        yield_msg = f"✅ Perfect! I have everything I need. Let me now search for the best options for your trip to **{requirements['destination']}**!\n\n🔍 Searching flights, hotels, and checking weather..."

        # Step 2: Run agents in parallel (sequential for simplicity)
        flight_data = self.flight_agent.search_flights(
            requirements.get("origin", "New York"),
            requirements["destination"],
            requirements["checkin"],
            requirements["travelers"]
        )

        hotel_data = self.hotel_agent.search_hotels(
            requirements["destination"],
            requirements["checkin"],
            requirements["checkout"],
            requirements["travelers"],
            requirements["budget"]
        )

        weather_data = self.climate_agent.get_weather(
            requirements["destination"],
            requirements["checkin"]
        )

        # Step 3: Generate full itinerary
        itinerary = self.planning_agent.generate_itinerary(
            requirements, flight_data, hotel_data, weather_data
        )

        # Step 4: Format full response
        flight_display = self.flight_agent.format_for_display(flight_data)
        hotel_display = self.hotel_agent.format_for_display(hotel_data, requirements["nights"])
        weather_display = self.climate_agent.format_for_display(weather_data)

        full_response = f"""{yield_msg}

---

{flight_display}

---

{hotel_display}

---

{weather_display}

---

## 📋 Your Complete Travel Itinerary

{itinerary}

---
*💬 Feel free to ask me to adjust the plan, explore different options, or plan another trip!*
"""

        self.stage = "done"
        self.conversation_history.append({
            "role": "assistant",
            "content": full_response
        })

        return {
            "message": full_response,
            "stage": self.stage,
            "collected": requirements,
            "missing": []
        }

    def _extract_travel_info(self, message: str) -> dict:
        """Use Gemini to extract travel information from user message."""
        prompt = f"""
Extract travel information from this message. Return ONLY a valid JSON object with these keys:
- travelers (integer or null)
- destination (string or null)
- origin (string or null)
- checkin (string in YYYY-MM-DD format or null)
- checkout (string in YYYY-MM-DD format or null)
- budget (number in USD or null)

Message: "{message}"

Previously collected info: {json.dumps(self.collected_info)}

Return only the JSON, no explanation. If a field is not mentioned, use null.
Example: {{"travelers": 2, "destination": "Paris", "origin": null, "checkin": "2025-06-01", "checkout": "2025-06-07", "budget": 3000}}
"""
        try:
            response = self.gemini.generate_content(prompt)
            text = response.text.strip()
            # Clean up response
            text = re.sub(r"```json|```", "", text).strip()
            extracted = json.loads(text)
            return extracted
        except Exception as e:
            print(f"Extraction error: {e}")
            return {}

    def _generate_collection_response(self, user_message: str, check_result: dict, extracted: dict) -> str:
        """Generate a natural conversational response to collect missing info."""

        missing = check_result.get("missing", [])
        already_have = {k: v for k, v in self.collected_info.items() if v}

        history_text = "\n".join([
            f"{m['role'].upper()}: {m['content']}"
            for m in self.conversation_history[-6:]
        ])

        prompt = f"""
You are a friendly, enthusiastic travel agent assistant named "TravelAI". 

Conversation so far:
{history_text}

Information already collected: {json.dumps(already_have)}
Information still needed: {missing}

Generate a natural, warm, conversational response that:
1. Acknowledges what the user just said
2. Confirms information you've already collected (briefly)
3. Asks for the FIRST missing piece of information in a friendly way
4. Keeps the response concise (2-3 sentences max)
5. Uses relevant travel emojis

Do NOT ask for multiple pieces of info at once. Focus on just the first missing item.
"""
        try:
            response = self.gemini.generate_content(prompt)
            return response.text
        except Exception:
            if missing:
                return f"Thanks for that! I still need a few more details. Could you tell me your **{missing[0]}**? 😊"
            return "Let me gather a bit more information to plan your perfect trip!"
