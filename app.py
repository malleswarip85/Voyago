"""
Travel Agent - Flask Application
Multi-Agent AI Travel Planning System
"""

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from dotenv import load_dotenv
import os
import uuid

load_dotenv()

from agents.orchestrator import AgentOrchestrator

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", os.urandom(24).hex())
CORS(app)

# Store orchestrator sessions in memory
sessions = {}


def get_orchestrator(session_id: str) -> AgentOrchestrator:
    """Get or create an orchestrator for this session."""
    if session_id not in sessions:
        sessions[session_id] = AgentOrchestrator()
    return sessions[session_id]


@app.route("/")
def index():
    """Main chat page."""
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    """Handle chat messages."""
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()

        if not user_message:
            return jsonify({"error": "Empty message"}), 400

        session_id = session.get("session_id", str(uuid.uuid4()))
        orchestrator = get_orchestrator(session_id)

        result = orchestrator.process_message(user_message)

        return jsonify({
            "success": True,
            "message": result["message"],
            "stage": result["stage"],
            "collected": result.get("collected", {}),
            "missing": result.get("missing", [])
        })

    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({
            "success": False,
            "message": "I encountered an error. Please try again! 😊",
            "stage": "error"
        }), 500


@app.route("/api/reset", methods=["POST"])
def reset():
    """Reset the conversation."""
    session_id = session.get("session_id")
    if session_id and session_id in sessions:
        sessions[session_id].reset()
    return jsonify({"success": True, "message": "Conversation reset!"})


@app.route("/health")
def health():
    """Health check endpoint for Railway."""
    return jsonify({"status": "ok", "service": "Travel Agent AI"})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV", "production") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)
