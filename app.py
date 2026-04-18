"""
Voyago - Flask Application
Multi-Agent AI Travel Planning System
"""
from flask import Flask, render_template, request, jsonify, session, send_file
from flask_cors import CORS
from extensions import db, jwt
from dotenv import load_dotenv
import os, uuid, json

load_dotenv()

from agents.orchestrator import AgentOrchestrator

app = Flask(__name__)

# SECRET_KEY must be stable across restarts — never use random fallback in production
secret = os.getenv("SECRET_KEY")
if not secret:
    print("WARNING: SECRET_KEY not set! Sessions will break on restart.")
    secret = "voyago-default-secret-key-change-this"
app.secret_key = secret

# Session config — needed for Railway (HTTPS)
app.config["SESSION_COOKIE_SECURE"] = os.getenv("RAILWAY_ENVIRONMENT") is not None
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# JWT config
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "voyago-jwt-secret-change-this-in-prod!!")
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_COOKIE_SECURE"] = os.getenv("RAILWAY_ENVIRONMENT") is not None
app.config["JWT_COOKIE_SAMESITE"] = "Lax"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False  # tokens don't expire (simplicity for MVP)

# Database config
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///voyago.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
jwt.init_app(app)

CORS(app)

# In-memory session store
sessions = {}

def get_orc(session_id: str) -> AgentOrchestrator:
    if session_id not in sessions:
        sessions[session_id] = AgentOrchestrator()
    return sessions[session_id]

def get_session_id() -> str:
    """Get or create a stable session ID."""
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
        session.permanent = True
    return session["session_id"]

@app.route("/")
def index():
    get_session_id()  # ensure session created on page load
    return render_template("index.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        msg = data.get("message", "").strip()
        if not msg:
            return jsonify({"error": "Empty"}), 400

        sid = get_session_id()
        orc = get_orc(sid)
        result = orc.process_message(msg)

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
        return jsonify({
            "success": False,
            "message": f"Something went wrong: {str(e)}",
            "stage": "error"
        }), 500

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

from auth_routes import auth_bp
app.register_blueprint(auth_bp)

with app.app_context():
    from models import User  # noqa: F401 — ensures model is registered before create_all
    db.create_all()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
