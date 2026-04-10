"""
Agent Orchestrator - v3
- Collects all traveler details at once via structured form
- Fixes gender extraction bug
- Budget validation with suggestions
- Nonstop logic fixed
"""

import google.generativeai as genai
import os
import json
import re
from datetime import datetime, timedelta

from agents.requirement_checker import RequirementCheckerAgent
from agents.flight_agent import FlightAgent
from agents.hotel_agent import HotelAgent
from agents.climate_agent import ClimateAgent
from agents.planning_agent import PlanningAgent


class TravelerProfile:
    def __init__(self, first_name=None, last_name=None, age=None, gender=None):
        self.first_name = first_name
        self.last_name = last_name
        self.age = age
        self.gender = gender

    def is_complete(self):
        return all([self.first_name, self.last_name, self.age, self.gender])

    def to_dict(self):
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "age": self.age,
            "gender": self.gender
        }


class TripRequirements:
    def __init__(self):
        self.origin = None
        self.destination = None
        self.checkin = None
        self.checkout = None
        self.nights = None
        self.budget = None
        self.nonstop_preferred = None
        self.travelers = []

    def traveler_count(self):
        return len(self.travelers)

    def to_dict(self):
        d = {
            "origin": self.origin,
            "destination": self.destination,
            "checkin": self.checkin,
            "checkout": self.checkout,
            "nights": self.nights,
            "budget": self.budget,
            "nonstop_preferred": self.nonstop_preferred,
            "traveler_count": self.traveler_count(),
            "travelers": [t.to_dict() for t in self.travelers]
        }
        return d

    def missing_fields(self):
        missing = []
        if not self.origin: missing.append("origin_city")
        if not self.destination: missing.append("destination_city")
        if not self.checkin: missing.append("checkin_date")
        if not self.checkout: missing.append("checkout_date")
        if not self.budget: missing.append("budget")
        if self.nonstop_preferred is None: missing.append("nonstop_preference")
        if self.traveler_count() == 0: missing.append("traveler_count")
        else:
            for i, t in enumerate(self.travelers):
                if not t.is_complete():
                    missing.append(f"traveler_profiles")
                    break
        return missing


class AgentOrchestrator:
    def __init__(self):
        self.requirement_checker = RequirementCheckerAgent()
        self.flight_agent = FlightAgent()
        self.hotel_agent = HotelAgent()
        self.climate_agent = ClimateAgent()
        self.planning_agent = PlanningAgent()

        api_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        self.gemini = genai.GenerativeModel("gemini-2.5-flash-lite")

        self.trip = TripRequirements()
        self.conversation_history = []
        self.stage = "greeting"
        self.last_asked = None
        self.budget_warning_sent = False
        self.awaiting_budget_confirm = False
        self.suggested_budget = None
        self.awaiting_days_confirm = False

    def reset(self):
        self.trip = TripRequirements()
        self.conversation_history = []
        self.stage = "greeting"
        self.last_asked = None
        self.budget_warning_sent = False
        self.awaiting_budget_confirm = False
        self.suggested_budget = None
        self.awaiting_days_confirm = False

    def process_message(self, user_message: str) -> dict:
        self.conversation_history.append({"role": "user", "content": user_message})
        msg = user_message.lower().strip()

        # ── Handle budget increase confirmation ──
        if self.awaiting_budget_confirm:
            if any(w in msg for w in ["yes", "ok", "okay", "sure", "agree", "fine", "accept", "yeah", "yep"]):
                self.trip.budget = self.suggested_budget
                self.awaiting_budget_confirm = False
                self.budget_warning_sent = True
            elif any(w in msg for w in ["no", "nope", "reduce", "less", "fewer", "days", "cut"]):
                self.awaiting_budget_confirm = False
                self.awaiting_days_confirm = True
                resp = self._budget_reduce_days_prompt()
                self.conversation_history.append({"role": "assistant", "content": resp})
                return {"message": resp, "stage": "collecting", "collected": self.trip.to_dict(), "missing": []}
            else:
                # Try to extract a custom budget
                b = self._extract_budget(msg)
                if b:
                    self.trip.budget = b
                    self.awaiting_budget_confirm = False
                    self.budget_warning_sent = True

        # ── Handle days reduction ──
        if self.awaiting_days_confirm:
            nights = self._extract_number(msg)
            if nights and self.trip.checkin:
                dt = datetime.strptime(self.trip.checkin, "%Y-%m-%d")
                self.trip.checkout = (dt + timedelta(days=nights)).strftime("%Y-%m-%d")
                self.trip.nights = nights
                self.awaiting_days_confirm = False

        # ── Extract from message ──
        self._smart_extract(msg, user_message)

        # ── Parse traveler form JSON if sent ──
        if "traveler_form:" in user_message:
            self._parse_traveler_form(user_message)

        print(f"Trip: {json.dumps(self.trip.to_dict(), indent=2)}")

        missing = self.trip.missing_fields()

        # ── All basic info collected — validate budget ──
        if not missing or missing == ["traveler_profiles"]:
            budget_check = self._validate_budget()
            if budget_check and not self.budget_warning_sent:
                self.awaiting_budget_confirm = True
                self.suggested_budget = budget_check["suggested"]
                resp = budget_check["message"]
                self.conversation_history.append({"role": "assistant", "content": resp})
                return {"message": resp, "stage": "collecting", "collected": self.trip.to_dict(), "missing": []}

        if missing:
            self.last_asked = missing[0]
            response = self._generate_question(missing[0])
            self.stage = "collecting"
            self.conversation_history.append({"role": "assistant", "content": response})
            return {"message": response, "stage": self.stage, "collected": self.trip.to_dict(), "missing": missing}

        # ── Check all travelers complete ──
        incomplete = [t for t in self.trip.travelers if not t.is_complete()]
        if incomplete:
            resp = self._traveler_form_prompt()
            self.conversation_history.append({"role": "assistant", "content": resp})
            return {"message": resp, "stage": "collecting", "collected": self.trip.to_dict(), "missing": ["traveler_profiles"]}

        # ── Run all agents ──
        return self._run_agents()

    def _validate_budget(self) -> dict | None:
        """Check if budget is sufficient for the trip duration."""
        if not all([self.trip.budget, self.trip.checkin, self.trip.checkout, self.trip.traveler_count()]):
            return None
        if self.budget_warning_sent:
            return None

        checkin_dt = datetime.strptime(self.trip.checkin, "%Y-%m-%d")
        checkout_dt = datetime.strptime(self.trip.checkout, "%Y-%m-%d")
        nights = (checkout_dt - checkin_dt).days
        travelers = self.trip.traveler_count()
        import math
        rooms = max(1, math.ceil(travelers / 2))

        # Minimum estimates (realistic)
        min_flight_pp = 300
        min_hotel_per_room_night = 60
        min_food_pp_day = 40

        min_total = (min_flight_pp * travelers) + (min_hotel_per_room_night * rooms * nights) + (min_food_pp_day * travelers * nights)

        if self.trip.budget < min_total:
            suggested_low = round(min_total / 100) * 100
            suggested_high = round(min_total * 1.3 / 100) * 100
            self.trip.nights = nights
            return {
                "suggested": suggested_low,
                "message": f"""⚠️ **Budget Alert!**

Your current budget of **${self.trip.budget:,.0f}** may not be enough for **{nights} nights** in **{self.trip.destination}** for **{travelers} traveler(s)**.

**Minimum estimated costs:**
- ✈️ Flights: ~${min_flight_pp * travelers:,.0f} (${min_flight_pp}/person)
- 🏨 Hotel ({nights} nights): ~${min_hotel_per_room_night * rooms * nights:,.0f} (${min_hotel_per_room_night}/room/night)
- 🍽️ Food & transport: ~${min_food_pp_day * travelers * nights:,.0f}
- **Minimum total: ~${min_total:,.0f}**

**Suggested budget range: ${suggested_low:,.0f} – ${suggested_high:,.0f}**

Would you like to:
1. ✅ **Increase budget to ${suggested_low:,.0f}** — type "Yes" or enter your new budget
2. 📅 **Reduce trip days** — type "No" and I'll suggest a shorter trip that fits your budget"""
            }
        self.trip.nights = nights
        return None

    def _budget_reduce_days_prompt(self) -> str:
        if not self.trip.budget or not self.trip.traveler_count():
            return "How many nights would you like instead?"

        travelers = self.trip.traveler_count()
        min_per_night = (60 + 40 * travelers)
        flight_cost = 300 * travelers
        available_for_stay = self.trip.budget - flight_cost
        max_nights = max(1, int(available_for_stay / min_per_night))

        return f"""📅 **Trip Duration Adjustment**

With your budget of **${self.trip.budget:,.0f}**, I recommend a maximum of **{max_nights} nights** in {self.trip.destination}.

This keeps your trip within budget:
- ✈️ Flights: ~${flight_cost:,.0f}
- 🏨 Hotel + Food ({max_nights} nights): ~${min_per_night * max_nights:,.0f}

How many nights would you like? (Maximum {max_nights} recommended)"""

    def _parse_traveler_form(self, message: str):
        """Parse traveler form JSON submitted from frontend."""
        try:
            match = re.search(r'traveler_form:(.*)', message, re.DOTALL)
            if match:
                data = json.loads(match.group(1).strip())
                travelers_data = data.get("travelers", [])
                self.trip.travelers = []
                for t in travelers_data:
                    profile = TravelerProfile(
                        first_name=t.get("first_name", "").strip().title(),
                        last_name=t.get("last_name", "").strip().title(),
                        age=int(t.get("age", 0)) if t.get("age") else None,
                        gender=t.get("gender", "").strip()
                    )
                    self.trip.travelers.append(profile)
                print(f"Parsed {len(self.trip.travelers)} travelers from form")
        except Exception as e:
            print(f"Form parse error: {e}")

    def _smart_extract(self, msg: str, original: str):
        la = self.last_asked or ""

        if la == "origin_city":
            self.trip.origin = self._clean_city(original)
            return
        if la == "destination_city":
            self.trip.destination = self._clean_city(original)
            return
        if la == "checkin_date":
            d = self._extract_date(msg)
            if d: self.trip.checkin = d
            return
        if la == "checkout_date":
            d = self._extract_date(msg)
            if d:
                self.trip.checkout = d
            else:
                nights = self._extract_nights(msg)
                if nights and self.trip.checkin:
                    dt = datetime.strptime(self.trip.checkin, "%Y-%m-%d")
                    self.trip.checkout = (dt + timedelta(days=nights)).strftime("%Y-%m-%d")
            return
        if la == "budget":
            b = self._extract_budget(msg)
            if b: self.trip.budget = b
            return
        if la == "nonstop_preference":
            self.trip.nonstop_preferred = any(w in msg for w in ["yes","yeah","yep","sure","nonstop","non-stop","direct","definitely","prefer","y"])
            return
        if la == "traveler_count":
            n = self._extract_number(msg)
            if n and 1 <= n <= 20:
                self.trip.travelers = [TravelerProfile() for _ in range(n)]
            return

        # General extraction from first message — extract ALL info at once
        msg_lower = msg.lower()

        # ── Destination ──
        if not self.trip.destination:
            dest_patterns = [
                r'(?:go to|going to|visit|travel to|trip to|fly to|heading to|need to for|for)\s+([A-Za-z][A-Za-z\s]+?)(?:\s+trip|\s+from|\s+for|\s+check|\.|,|$)',
                r'(?:to)\s+([A-Za-z][A-Za-z\s]+?)\s+(?:trip|vacation|holiday|travel)',
                r'^([A-Za-z][A-Za-z\s]+?)\s+(?:trip|vacation|holiday)',
            ]
            for pat in dest_patterns:
                m = re.search(pat, msg, re.IGNORECASE)
                if m:
                    dest = m.group(1).strip().title()
                    # Reject if it looks like a city we know as origin
                    if len(dest) > 1 and not re.match(r'^\d', dest):
                        self.trip.destination = dest
                        break

        # ── Origin ──
        if not self.trip.origin:
            origin_patterns = [
                r'from\s+([A-Za-z][A-Za-z\s]+?)(?:\s+check|\s+to|\s+on|\.|,|$)',
                r'departing\s+(?:from\s+)?([A-Za-z][A-Za-z\s]+?)(?:\s+to|\.|,|$)',
                r'leaving\s+(?:from\s+)?([A-Za-z][A-Za-z\s]+?)(?:\s+to|\.|,|$)',
            ]
            for pat in origin_patterns:
                m = re.search(pat, msg, re.IGNORECASE)
                if m:
                    origin = m.group(1).strip().title()
                    if len(origin) > 1 and not re.match(r'^\d', origin):
                        self.trip.origin = origin
                        break

        # ── Dates — extract ALL dates found, assign checkin/checkout in order ──
        if not self.trip.checkin or not self.trip.checkout:
            all_dates = re.findall(r'\d{4}-\d{2}-\d{2}', msg)
            if len(all_dates) >= 2:
                if not self.trip.checkin: self.trip.checkin = all_dates[0]
                if not self.trip.checkout: self.trip.checkout = all_dates[1]
            elif len(all_dates) == 1:
                if not self.trip.checkin: self.trip.checkin = all_dates[0]

        # ── Nights from message ──
        if self.trip.checkin and not self.trip.checkout:
            nights = self._extract_nights(msg)
            if nights:
                dt = datetime.strptime(self.trip.checkin, "%Y-%m-%d")
                self.trip.checkout = (dt + timedelta(days=nights)).strftime("%Y-%m-%d")

        # ── Budget — only with explicit markers ──
        if not self.trip.budget:
            b = self._extract_budget(msg)
            if b: self.trip.budget = b

        # ── Traveler count ──
        if self.trip.traveler_count() == 0:
            for pat in [r'(\d+)\s*(?:people|persons?|travelers?|adults?)', r'for\s+(\d+)\s+people', r'party\s+of\s+(\d+)']:
                m = re.search(pat, msg)
                if m:
                    n = int(m.group(1))
                    if 1 <= n <= 20:
                        self.trip.travelers = [TravelerProfile() for _ in range(n)]
                        break

    def _generate_question(self, field: str) -> str:
        d = self.trip.to_dict()
        confirms = []
        if d["destination"]: confirms.append(f"📍 **{d['destination']}**")
        if d["origin"]: confirms.append(f"🛫 **{d['origin']}**")
        if d["checkin"]: confirms.append(f"📅 **{d['checkin']}**")
        if d["checkout"]: confirms.append(f"to **{d['checkout']}**")
        if d["budget"]: confirms.append(f"💰 **${d['budget']:,.0f}**")
        if d["traveler_count"]: confirms.append(f"👥 **{d['traveler_count']} traveler(s)**")
        if d["nonstop_preferred"] is not None:
            confirms.append("✈️ **Non-stop**" if d["nonstop_preferred"] else "✈️ **Any flights**")
        conf = f"\n\n✅ *So far:* {' | '.join(confirms)}" if confirms else ""

        questions = {
            "origin_city": f"🛫 Which city will you be **departing from**?{conf}",
            "destination_city": f"🌍 Where would you like to **travel to**?{conf}",
            "checkin_date": f"📅 What is your **departure / check-in date**? *(e.g. 2025-08-01)*{conf}",
            "checkout_date": f"📅 What is your **return / check-out date**? *(e.g. 2025-08-07, or tell me the number of nights!)*{conf}",
            "budget": f"💰 What is your **total budget in USD** for this trip? *(flights + hotel + activities)*{conf}",
            "nonstop_preference": f"✈️ Do you prefer **non-stop flights only**? *(Yes / No)*\n\n> 💡 Non-stop flights save time but may cost more.{conf}",
            "traveler_count": f"👥 How many **travelers** will be on this trip?{conf}",
            "traveler_profiles": self._traveler_form_prompt(),
        }
        return questions.get(field, f"Could you provide your **{field}**?{conf}")

    def _traveler_form_prompt(self) -> str:
        count = self.trip.traveler_count()
        incomplete = [(i, t) for i, t in enumerate(self.trip.travelers) if not t.is_complete()]

        if not incomplete:
            return "All traveler details collected! ✅"

        form_fields = []
        for i, t in incomplete:
            form_fields.append({
                "index": i,
                "label": f"Traveler {i+1}",
                "first_name": t.first_name or "",
                "last_name": t.last_name or "",
                "age": t.age or "",
                "gender": t.gender or ""
            })

        form_json = json.dumps({"travelers_needed": form_fields})
        return f"""👥 **Traveler Details**

Please fill in the details for all {count} traveler(s) below:

TRAVELER_FORM:{form_json}"""

    def _run_agents(self) -> dict:
        self.stage = "planning"
        req = self.trip.to_dict()

        checker_data = {
            "travelers": req["traveler_count"],
            "destination": req["destination"],
            "origin": req["origin"],
            "checkin": req["checkin"],
            "checkout": req["checkout"],
            "budget": req["budget"]
        }
        check = self.requirement_checker.check(checker_data)
        validated = check["data"] if check["valid"] else checker_data

        # Always ensure nights is calculated
        if not validated.get("nights"):
            try:
                from datetime import datetime as _dt
                ci = _dt.strptime(validated["checkin"], "%Y-%m-%d")
                co = _dt.strptime(validated["checkout"], "%Y-%m-%d")
                validated["nights"] = (co - ci).days
            except Exception:
                validated["nights"] = self.trip.nights or 1

        # Ensure travelers count is set
        if not validated.get("travelers"):
            validated["travelers"] = req["traveler_count"]

        validated["nonstop_preferred"] = req.get("nonstop_preferred", False)
        validated["travelers_profiles"] = req["travelers"]
        nonstop = validated.get("nonstop_preferred", False)

        dest_log = validated.get('destination', '?')
        print(f"Running agents: {dest_log} | nights={validated.get('nights')} | travelers={validated.get('travelers')}")

        flight_data = self.flight_agent.search_flights(
            validated.get("origin", "New York"),
            validated["destination"],
            validated["checkin"],
            validated["travelers"],
            nonstop=nonstop
        )
        hotel_data = self.hotel_agent.search_hotels(
            validated["destination"],
            validated["checkin"],
            validated["checkout"],
            validated["travelers"],
            validated["budget"]
        )
        weather_data = self.climate_agent.get_weather(
            validated["destination"],
            validated["checkin"],
            validated["checkout"]
        )
        itinerary = self.planning_agent.generate_itinerary(
            validated, flight_data, hotel_data, weather_data
        )

        flight_display = self.flight_agent.format_for_display(flight_data, validated["budget"], nonstop)
        hotel_display = self.hotel_agent.format_for_display(hotel_data, validated["nights"], validated["budget"])
        weather_display = self.climate_agent.format_for_display(weather_data)

        traveler_names = ", ".join([
            t.get("first_name", "") + " " + t.get("last_name", "")
            for t in req["travelers"] if t.get("first_name")
        ])

        # Generate PDF
        self.pdf_path = None
        try:
            import sys, tempfile
            # Support both direct run and module import
            try:
                from agents.pdf_generator import generate_itinerary_pdf
            except ImportError:
                from pdf_generator import generate_itinerary_pdf
            pdf_path = os.path.join(tempfile.gettempdir(), f"voyago_itinerary_{id(self)}.pdf")
            generate_itinerary_pdf(validated, flight_data, hotel_data, weather_data, itinerary, pdf_path)
            self.pdf_path = pdf_path
            print(f"PDF generated: {pdf_path}")
        except Exception as e:
            import traceback
            print(f"PDF generation error: {e}")
            traceback.print_exc()

        pdf_note = "\n\n📄 **[Download Your PDF Itinerary](/api/download-pdf)** — Full day-by-day plan as PDF" if self.pdf_path else ""

        dest_name = validated.get("destination", "")
        traveler_str = traveler_names or (str(validated.get("travelers", 1)) + " traveler(s)")

        full_response = f"""✅ **All set!** Planning your trip to **{dest_name}** for **{traveler_str}**!

---

{flight_display}

---

{hotel_display}

---

{weather_display}

---

## 📋 Your Complete Day-by-Day Itinerary

{itinerary}{pdf_note}

---
*💬 Ask me to adjust the plan or start a new trip!*"""

        self.stage = "done"
        self.conversation_history.append({"role": "assistant", "content": full_response})
        return {"message": full_response, "stage": self.stage, "collected": req, "missing": [], "pdf_path": self.pdf_path}

    def _clean_city(self, text: str) -> str:
        text = re.sub(r'\b(i am|i\'m|we are|flying|departing|leaving|from|to|going|visiting|it is|its)\b', '', text, flags=re.IGNORECASE)
        return text.strip(" .,!?").title()

    def _extract_number(self, text: str):
        word_nums = {"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,"nine":9,"ten":10}
        for w, n in word_nums.items():
            if w in text: return n
        m = re.search(r'\d+', text)
        return int(m.group()) if m else None

    def _extract_date(self, text: str) -> str:
        m = re.search(r'(\d{4}-\d{2}-\d{2})', text)
        if m: return m.group(1)
        m = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', text)
        if m:
            try: return datetime.strptime(f"{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}", "%Y-%m-%d").strftime("%Y-%m-%d")
            except: pass
        months = {"january":"01","february":"02","march":"03","april":"04","may":"05","june":"06",
                  "july":"07","august":"08","september":"09","october":"10","november":"11","december":"12",
                  "jan":"01","feb":"02","mar":"03","apr":"04","jun":"06","jul":"07","aug":"08","sep":"09","oct":"10","nov":"11","dec":"12"}
        for mon, num in months.items():
            m = re.search(rf'{mon}\w*\s+(\d{{1,2}}),?\s*(\d{{4}})?', text)
            if m:
                day = m.group(1).zfill(2)
                year = m.group(2) if m.group(2) else str(datetime.now().year + 1)
                return f"{year}-{num}-{day}"
        return None

    def _extract_nights(self, text: str):
        m = re.search(r'(\d+)\s*(?:nights?|days?)', text)
        if m: return int(m.group(1))
        if "a week" in text or "one week" in text: return 7
        if "two weeks" in text: return 14
        return None

    def _extract_budget(self, text: str):
        """Extract budget amount, avoiding date years (2000-2099)."""
        text = text.strip()

        # Pattern 1: $3000 or $ 3,000
        m = re.search(r'\$\s*(\d[\d,]*)', text)
        if m:
            val = float(m.group(1).replace(",", ""))
            if val > 100: return val

        # Pattern 2: 3000$ (dollar sign after)
        m = re.search(r'(\d[\d,]*)\s*\$', text)
        if m:
            val = float(m.group(1).replace(",", ""))
            if val > 100: return val

        # Pattern 3: 3000 usd / 3000 dollars
        m = re.search(r'(\d[\d,]*)\s*(?:usd|dollars?)', text, re.IGNORECASE)
        if m:
            val = float(m.group(1).replace(",", ""))
            if val > 100: return val

        # Pattern 4: budget of 3000
        m = re.search(r'budget\s+(?:of\s+)?(\d[\d,]*)', text, re.IGNORECASE)
        if m:
            val = float(m.group(1).replace(",", ""))
            if val > 100: return val

        # Pattern 5: 3k / 5k
        m = re.search(r'\b(\d+(?:\.\d+)?)\s*k\b', text, re.IGNORECASE)
        if m:
            val = float(m.group(1)) * 1000
            if val > 100: return val

        # Pattern 6: bare number — only if message is JUST a number
        # e.g. user types "3000" as direct reply to budget question
        bare = text.strip().replace(",", "")
        if re.match(r'^\d+$', bare):
            val = float(bare)
            # Reject year-like (2000-2099) and unreasonably small/large
            if val > 100 and not (2000 <= val <= 2099):
                return val

        return None
