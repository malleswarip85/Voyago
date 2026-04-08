"""
Requirement Checker Agent
Validates and extracts travel requirements from user input:
- Number of travelers
- Travel dates
- Budget
- Origin and destination
"""

import re
from datetime import datetime


class RequirementCheckerAgent:
    def __init__(self):
        self.required_fields = ["travelers", "destination", "checkin", "checkout", "budget"]

    def check(self, user_data: dict) -> dict:
        """
        Validate and normalize user requirements.
        Returns a dict with 'valid', 'missing', 'data', and 'message'.
        """
        missing = []
        normalized = {}

        # Check travelers
        travelers = user_data.get("travelers")
        if not travelers:
            missing.append("number of travelers")
        else:
            try:
                normalized["travelers"] = int(travelers)
                if normalized["travelers"] < 1:
                    return self._error("Number of travelers must be at least 1.")
            except (ValueError, TypeError):
                return self._error("Please provide a valid number of travelers.")

        # Check destination
        destination = user_data.get("destination", "").strip()
        if not destination:
            missing.append("destination city")
        else:
            normalized["destination"] = destination

        # Check origin
        origin = user_data.get("origin", "").strip()
        normalized["origin"] = origin if origin else "Not specified"

        # Check check-in date
        checkin = user_data.get("checkin", "").strip()
        if not checkin:
            missing.append("check-in date")
        else:
            parsed = self._parse_date(checkin)
            if not parsed:
                return self._error(f"Invalid check-in date format: '{checkin}'. Use YYYY-MM-DD.")
            normalized["checkin"] = parsed

        # Check check-out date
        checkout = user_data.get("checkout", "").strip()
        if not checkout:
            missing.append("check-out date")
        else:
            parsed = self._parse_date(checkout)
            if not parsed:
                return self._error(f"Invalid check-out date format: '{checkout}'. Use YYYY-MM-DD.")
            normalized["checkout"] = parsed

        # Validate date order
        if "checkin" in normalized and "checkout" in normalized:
            if normalized["checkin"] >= normalized["checkout"]:
                return self._error("Check-out date must be after check-in date.")

        # Check budget
        budget = user_data.get("budget")
        if not budget:
            missing.append("budget (in USD)")
        else:
            try:
                normalized["budget"] = float(str(budget).replace(",", "").replace("$", ""))
                if normalized["budget"] <= 0:
                    return self._error("Budget must be a positive amount.")
            except (ValueError, TypeError):
                return self._error("Please provide a valid budget amount in USD.")

        if missing:
            return {
                "valid": False,
                "missing": missing,
                "data": normalized,
                "message": f"I still need the following information: {', '.join(missing)}. Could you please provide these details?"
            }

        # Calculate nights
        checkin_dt = datetime.strptime(normalized["checkin"], "%Y-%m-%d")
        checkout_dt = datetime.strptime(normalized["checkout"], "%Y-%m-%d")
        normalized["nights"] = (checkout_dt - checkin_dt).days

        return {
            "valid": True,
            "missing": [],
            "data": normalized,
            "message": f"✅ Requirements confirmed! Planning trip for {normalized['travelers']} traveler(s) to {normalized['destination']} from {normalized['checkin']} to {normalized['checkout']} ({normalized['nights']} nights) with a budget of ${normalized['budget']:,.2f}."
        }

    def _parse_date(self, date_str: str) -> str | None:
        """Try multiple date formats and return YYYY-MM-DD or None."""
        formats = ["%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y", "%B %d, %Y", "%b %d, %Y"]
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return None

    def _error(self, message: str) -> dict:
        return {
            "valid": False,
            "missing": [],
            "data": {},
            "message": f"⚠️ {message}"
        }
