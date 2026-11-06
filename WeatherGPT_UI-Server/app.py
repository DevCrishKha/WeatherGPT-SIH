# Copyright (c) 2026 [Dev Crish Kha]. All rights reserved.
#
# This source code and all associated materials are proprietary and
# confidential to [Dev Crish Kha]. Unauthorized copying, modification,
# distribution, publication, sublicensing, or use of this code, in whole
# or in part, is strictly prohibited without prior written permission
# from the copyright holder.

"""
WeatherGPT -- Flask backend
===========================

Responsibilities:
  * Serve the chat UI (templates/index.html)
  * Keep a per-user, per-conversation message history on disk
    (data/conversations/<user_id>.json) so a returning, logged-in user
    sees their previous chats.
  * Expose a small JSON API the frontend talks to (/api/...)
  * Call your weather agent (agent_module.handle_message) for every user
    message and store its markdown reply. The agent itself returns text
    only now -- images and geojson arrive out of band, from your tools,
    through /get_tool_images and /get_tool_geojson below, and are relayed
    to the browser over Socket.IO.

Swap-in points for your real system are marked with "REPLACE ME".
"""

import os
import json
import uuid
import base64
from functools import wraps
from datetime import datetime, timezone

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_session import Session
from flask_socketio import SocketIO, join_room

import agent_module  # REPLACE ME: point this at your real agent module

# ---------------------------------------------------------------------------
# App + session setup
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data", "conversations")
os.makedirs(DATA_DIR, exist_ok=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")

# -- exactly the session config you specified --
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_FILE_DIR"] = os.path.join(BASE_DIR, "flask_session")
app.config["PERMANENT_SESSION_LIFETIME"] = 60 * 60 * 24 * 30  # 30 days

Session(app)
socketio = SocketIO(app, manage_session=True, cors_allowed_origins="*")

# Optional shared secret for the two server-to-server routes below
# (/get_tool_images, /get_tool_geojson). Those calls come from your tools,
# not the browser, so there's no session cookie to check -- set this env
# var and have your tools send it as `X-Internal-Token` if you want anything
# more than network-level trust. Left unset, the check is skipped.
INTERNAL_TOOL_TOKEN = os.environ.get("INTERNAL_TOOL_TOKEN")


def _internal_token_ok() -> bool:
    if not INTERNAL_TOOL_TOKEN:
        return True
    return request.headers.get("X-Internal-Token") == INTERNAL_TOOL_TOKEN


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Conversation storage
#
# REPLACE ME: this JSON-file store exists so the app runs out of the box.
# Swap load_conversations/save_conversations for real database calls
# (e.g. Postgres) -- nothing else in the file needs to change, since every
# route only talks to these two functions.
# ---------------------------------------------------------------------------
def _user_file(user_id: str) -> str:
    safe_id = "".join(c for c in user_id if c.isalnum() or c in "-_") or "anon"
    return os.path.join(DATA_DIR, f"{safe_id}.json")


def load_conversations(user_id: str) -> dict:
    path = _user_file(user_id)
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_conversations(user_id: str, conversations: dict) -> None:
    with open(_user_file(user_id), "w", encoding="utf-8") as f:
        json.dump(conversations, f, ensure_ascii=False, indent=2)


def new_conversation_id() -> str:
    return uuid.uuid4().hex[:12]


# ---------------------------------------------------------------------------
# Auth guard
#
# REPLACE ME: this reads session['logged_in'] / session['user_id'] exactly as
# you described. The /login route below is a stand-in for your real login --
# swap its body for your actual auth check and keep setting those two keys.
# ---------------------------------------------------------------------------
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = (request.form.get("username") or "").strip()
    if not username:
        return render_template("login.html", error="Enter a username to continue.")

    session["logged_in"] = True
    session["user_id"] = username
    session.permanent = True
    return redirect(url_for("index"))


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Main page
# ---------------------------------------------------------------------------
@app.route("/")
@login_required
def index():
    return render_template("index.html", user_id=session["user_id"])


# ---------------------------------------------------------------------------
# Conversation list / CRUD API
# ---------------------------------------------------------------------------
@app.route("/api/conversations", methods=["GET"])
@login_required
def api_list_conversations():
    conversations = load_conversations(session["user_id"])
    items = sorted(
        (
            {"id": cid, "title": c["title"], "updated_at": c["updated_at"]}
            for cid, c in conversations.items()
        ),
        key=lambda c: c["updated_at"],
        reverse=True,
    )
    return jsonify(items)


@app.route("/api/conversations", methods=["POST"])
@login_required
def api_create_conversation():
    user_id = session["user_id"]
    conversations = load_conversations(user_id)
    cid = new_conversation_id()
    conversations[cid] = {
        "id": cid,
        "title": "New conversation",
        "messages": [],
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    save_conversations(user_id, conversations)
    return jsonify(conversations[cid])


@app.route("/api/conversations/<cid>", methods=["GET"])
@login_required
def api_get_conversation(cid):
    conversations = load_conversations(session["user_id"])
    conv = conversations.get(cid)
    if not conv:
        return jsonify({"error": "not found"}), 404
    return jsonify(conv)


@app.route("/api/conversations/<cid>", methods=["DELETE"])
@login_required
def api_delete_conversation(cid):
    user_id = session["user_id"]
    conversations = load_conversations(user_id)
    conversations.pop(cid, None)
    save_conversations(user_id, conversations)
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Chat endpoint -- calls your agent and stores history.
#
# The agent returns markdown text only. Any image or geojson it triggers your
# tools to produce arrives later, out of band, via /get_tool_images and
# /get_tool_geojson below -- this route no longer waits for or emits either.
# ---------------------------------------------------------------------------
@app.route("/api/chat", methods=["POST"])
@login_required
def api_chat():
    user_id = session["user_id"]
    payload = request.get_json(force=True, silent=True) or {}
    cid = payload.get("conversation_id")
    user_input = (payload.get("message") or "").strip()

    if not user_input:
        return jsonify({"error": "empty message"}), 400

    conversations = load_conversations(user_id)
    if not cid or cid not in conversations:
        cid = new_conversation_id()
        conversations[cid] = {
            "id": cid,
            "title": "New conversation",
            "messages": [],
            "html_blocks": [],          # <-- add
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }
    conv = conversations[cid]

    # 1) store the user's prompt exactly as typed
    # --- USER CONV & Socket-Room INFO to Agent/TOOLS Workflow ---
    user_conv_dict = {'user_id':session["user_id"], 'c_id':conv['id']}
    conv["messages"].append({"role": "user", "content": user_input})

    # 2) hand it to your agent -- REPLACE ME: call your real agent here.
    #    handle_message now returns plain markdown text, nothing else.
    markdown_reply = agent_module.main(user_input=user_input, history=conv["messages"], conv_dict=user_conv_dict)

    # 3) store the assistant's markdown reply
    conv["messages"].append({"role": "assistant", "content": markdown_reply})
    
    # ---
    #   CHECKING OUT HOW THE MSG LOOKS | THEN I'LL ADD IN THE SYSTEM INSTRUCTIONS 
    #   THAT THE TOOL CALLING IS NOT INCLUDED IN THE CHAT HISTORY AFTER COMPACTION
    # ---
    with open("chat-history.json", "w", encoding="utf-8") as f:
        json.dump(conv["messages"], f, indent=4, ensure_ascii=False, default=str)
        
    conv["updated_at"] = now_iso()
    if conv["title"] == "New conversation":
        conv["title"] = user_input[:40] + ("…" if len(user_input) > 40 else "")

    save_conversations(user_id, conversations)

    return jsonify({"conversation_id": cid, "title": conv["title"], "markdown": markdown_reply})

# ---------------------------------------------------------------------------
# Server-to-server: your tools post short-lived status text here while
# they're working (e.g. "Fetching weather data...", "Rendering chart...").
# This is NOT persisted anywhere -- it's purely a live, ephemeral push that
# replaces the "..." typing indicator in the browser until the real
# /api/chat response arrives and removes it for good.
#
# JSON body:
#   {
#     "user_id": "...",           required -- which user's room to emit to
#     "conversation_id": "...",   optional -- so the frontend can ignore a
#                                  status meant for a thread that isn't open
#     "message": "Fetching..."    required -- the status text to show
#   }
# ---------------------------------------------------------------------------
@app.route("/get_tool_status", methods=["POST"])
def get_tool_status():
    if not _internal_token_ok():
        return jsonify({"error": "unauthorized"}), 401

    payload = request.get_json(force=True, silent=True) or {}
    user_id = payload.get("user_id")
    message = payload.get("message")

    if not user_id or not message:
        return jsonify({"error": "user_id and message are required"}), 400

    socketio.emit(
        "tool_status",
        {"conversation_id": payload.get("conversation_id", ""), "message": message},
        room=user_id,
    )
    return jsonify({"ok": True})

# ---------------------------------------------------------------------------
# Server-to-server: your image-generation tool posts its rendered chart here.
#
# This is NOT called by the browser, so there's no session/cookie to read the
# user from -- the tool must tell us which user's socket room to push to
# (and ideally which conversation, so the frontend can ignore images meant
# for a thread that isn't currently open).
#
# multipart/form-data:
#   user_id           required -- which user's room to emit to
#   conversation_id   optional -- which conversation this image belongs to
#   image             required -- the image file itself (png/jpeg/...)
# ---------------------------------------------------------------------------
@app.route("/get_tool_image", methods=["POST"])
def get_tool_images():
    if not _internal_token_ok():
        return jsonify({"error": "unauthorized"}), 401

    # user_id = request.form.get("user_id") # How will the tool get the userid ?
    user_id = request.form.get("user_id")
    conversation_id = request.form.get("conversation_id", "")
    image_file = request.files.get("image")

    if not user_id or not image_file:
        return jsonify({"error": "user_id and image are required"}), 400

    mime = image_file.mimetype or "image/png"
    encoded = base64.b64encode(image_file.read()).decode("ascii")
    
    print("NOW SENFING IMAGE TO FRONTEND: ")

    socketio.emit(
        "weather_image",
        {"conversation_id": conversation_id, "image_base64": encoded, "mime": "image/png"},
        room=user_id,
    )
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Server-to-server: your geojson-producing tool posts here. Same shape of
# problem as /get_tool_images -- no session, so user_id must be supplied.
#
# JSON body:
#   {
#     "user_id": "...",           required -- which user's room to emit to
#     "conversation_id": "...",   optional
#     "geojson": {...},           required -- a Feature / FeatureCollection
#     "data": {...}               optional -- shown on hover over the overlay
#   }
# ---------------------------------------------------------------------------
@app.route("/get_tool_geojson", methods=["POST"])
def get_tool_geojson():
    if not _internal_token_ok():
        return jsonify({"error": "unauthorized"}), 401

    payload = request.get_json(force=True, silent=True) or {}
    user_id = payload.get("user_id")
    geojson = payload.get("geojson")

    if not user_id or not geojson:
        return jsonify({"error": "user_id and geojson are required"}), 400

    socketio.emit(
        "weather_geojson",
        {
            "conversation_id": payload.get("conversation_id", ""),
            "geojson": geojson,
            "data": payload.get("data"),
            "color": payload.get("color"),
        },
        room=user_id,
    )
    return jsonify({"ok": True})


@app.route("/get_tool_html", methods=["POST"])
def get_tool_html():
    if not _internal_token_ok():
        return jsonify({"error": "unauthorized"}), 401

    payload = request.get_json(force=True, silent=True) or {}
    user_id = payload.get("user_id")
    conversation_id = payload.get("conversation_id")
    html_content = payload.get("html")

    if not user_id or not html_content:
        return jsonify({"error": "user_id and html are required"}), 400

    # Persist onto the conversation so it survives a reload. The block
    # remembers which message it followed, so reopening replays it in the
    # same spot. conv["messages"] itself is never modified.
    if conversation_id:
        conversations = load_conversations(user_id)
        conv = conversations.get(conversation_id)
        if conv is not None:
            conv.setdefault("html_blocks", []).append({
                "id": uuid.uuid4().hex[:12],
                "after_message_index": len(conv["messages"]) - 1,
                "html": html_content,
                "ts": now_iso(),
            })
            conv["updated_at"] = now_iso()
            save_conversations(user_id, conversations)

    socketio.emit(
        "weather_html",
        {"conversation_id": conversation_id or "", "html": html_content},
        room=user_id,
    )
    print("conversation_id: ", conversation_id)
    return jsonify({"ok": True})

# ---------------------------------------------------------------------------
# Socket.IO -- each logged-in user gets a private room, keyed by user_id, so
# one user's images/geojsons never reach another user's browser.
# ---------------------------------------------------------------------------
@socketio.on("connect")
def on_connect():
    user_id = session.get("user_id")
    if user_id:
        join_room(user_id)


if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)
