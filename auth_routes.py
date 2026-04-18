import re
import bcrypt
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    set_access_cookies,
    unset_jwt_cookies,
)
from extensions import db
from models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _bad(msg, code):
    return jsonify({"error": msg}), code


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not EMAIL_RE.match(email):
        return _bad("Invalid email address", 400)
    if len(password) < 8:
        return _bad("Password must be at least 8 characters", 400)

    if User.query.filter_by(email=email).first():
        return _bad("Email already registered", 409)

    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user = User(email=email, password_hash=pw_hash)
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    resp = jsonify({"message": "Registered successfully", "email": user.email, "id": user.id})
    set_access_cookies(resp, token)
    return resp, 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        return _bad("Invalid credentials", 401)

    token = create_access_token(identity=str(user.id))
    resp = jsonify({"message": "Logged in", "email": user.email, "id": user.id})
    set_access_cookies(resp, token)
    return resp, 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    resp = jsonify({"message": "Logged out"})
    unset_jwt_cookies(resp)
    return resp, 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return _bad("User not found", 401)
    return jsonify(user.to_dict()), 200
