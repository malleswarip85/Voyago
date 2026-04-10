"""
Voyago - Flask Application
Multi-Agent AI Travel Planning System
"""
from flask import Flask, render_template, request, jsonify, session, send_file
from flask_cors import CORS
from dotenv import load_dotenv
import os, uuid, json

load_dotenv()

from agents.orchestrator import AgentOrchestrator

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", os.urandom(24).hex())
CORS(app)

sessions = {}
last_plan = {}  # store last plan data for PDF generation

def get_orc(session_id):
    if session_id not in sessions:
        sessions[session_id] = AgentOrchestrator()
    return sessions[session_id]

@app.route("/")
def index():
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return render_template("index.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        msg = data.get("message", "").strip()
        if not msg:
            return jsonify({"error": "Empty"}), 400

        sid = session.get("session_id", str(uuid.uuid4()))
        orc = get_orc(sid)
        result = orc.process_message(msg)

        # Store plan data for PDF if done
        if result.get("stage") == "done":
            last_plan[sid] = orc.last_plan_data if hasattr(orc, 'last_plan_data') else {}

        return jsonify({
            "success": True,
            "message": result["message"],
            "stage": result["stage"],
            "collected": result.get("collected", {}),
            "missing": result.get("missing", []),
            "pdf_ready": result.get("pdf_path") is not None,
            "pdf_path": result.get("pdf_path", "")
        })
    except Exception as e:
        import traceback
        print(f"Chat error: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Error: {str(e)}", "stage": "error"}), 500

@app.route("/api/download-pdf")
def download_pdf():
    try:
        sid = session.get("session_id")
        orc = sessions.get(sid)
        if orc and hasattr(orc, 'pdf_path') and orc.pdf_path and os.path.exists(orc.pdf_path):
            return send_file(orc.pdf_path, as_attachment=True,
                           download_name="voyago_itinerary.pdf",
                           mimetype="application/pdf")
        return jsonify({"error": "PDF not ready"}), 404
    except Exception as e:
        print(f"PDF download error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/reset", methods=["POST"])
def reset():
    sid = session.get("session_id")
    if sid and sid in sessions:
        sessions[sid].reset()
    return jsonify({"success": True})

@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "Voyago Travel AI"})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
