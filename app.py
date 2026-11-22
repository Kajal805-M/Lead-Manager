"""
Lead Manager - Real Estate Sales Copilot Flask Application.
Serves the interactive frontend and exposes RESTful API endpoints for:
- Lead CRUD and Firestore / Local JSON synchronization
- 6-Factor Deterministic Bangalore Real Estate Lead Scoring
- Google Gemini AI-driven Sales Copilot (English & Hinglish)
- Follow-Up Hub Assistant and automated message drafting
"""

import os
import io
import csv
import json
import logging
from typing import Dict, Any, List
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, Response
from dotenv import load_dotenv

# Try importing flask_cors safely
try:
    from flask_cors import CORS
except ImportError:
    CORS = None

# Local modules
from scoring_engine import score_lead, parse_budget_lakhs
from gemini_service import gemini_service
from firebase_service import (
    get_all_leads,
    get_lead_by_id,
    save_lead,
    save_leads_batch,
    update_lead,
    seed_benchmark_leads,
    is_firebase_connected
)

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MOCKUP_DIR = os.path.join(BASE_DIR, "mockup")

app = Flask(
    __name__,
    static_folder=MOCKUP_DIR,
    static_url_path="",
    template_folder=MOCKUP_DIR
)

if CORS:
    CORS(app)

logger = logging.getLogger("LeadApp")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Ensure initial data exists on startup
@app.before_request
def ensure_database_seeded():
    # Only run once if empty
    if not getattr(app, "_db_initialized", False):
        try:
            leads = get_all_leads()
            if not leads or len(leads) == 0:
                logger.info("Initializing leads database with 18 benchmark records...")
                seed_benchmark_leads(force=False)
            app._db_initialized = True
        except Exception as e:
            logger.warning(f"Database seed check notice: {e}")
            app._db_initialized = True

@app.route("/")
def index():
    """Serves the main single-page application dashboard."""
    return send_from_directory(MOCKUP_DIR, "index.html")

@app.route("/api/status", methods=["GET"])
def api_status():
    """Health check and live service connection status."""
    leads = [l for l in get_all_leads() if isinstance(l, dict)]
    return jsonify({
        "status": "online",
        "app_name": "Lead Manager - Real Estate Sales Copilot",
        "firebase_connected": is_firebase_connected(),
        "gemini_connected": gemini_service.is_connected(),
        "active_gemini_model": gemini_service.active_model,
        "total_leads": len(leads),
        "hot_leads": len([l for l in leads if str(l.get("priority", "")).lower() == "hot"]),
        "warm_leads": len([l for l in leads if str(l.get("priority", "")).lower() == "warm"]),
        "cold_leads": len([l for l in leads if str(l.get("priority", "")).lower() == "cold"])
    })

@app.route("/api/leads", methods=["GET"])
def api_get_leads():
    """
    List all leads with optional query filters:
    - priority: Hot / Warm / Cold / all
    - locality: string filter
    - search: keyword search in name, requirement, notes, message
    - sort: score_desc (default), score_asc, newest
    """
    leads = [l for l in get_all_leads() if isinstance(l, dict)]
    priority = request.args.get("priority", "").strip()
    locality = request.args.get("locality", "").strip()
    search = request.args.get("search", "").strip().lower()
    sort_by = request.args.get("sort", "score_desc").strip()

    filtered = list(leads)

    if priority and priority.lower() != "all":
        filtered = [l for l in filtered if str(l.get("priority", "")).lower() == priority.lower()]

    if locality and locality.lower() != "all":
        filtered = [l for l in filtered if locality.lower() in str(l.get("location", "")).lower()]

    if search:
        filtered = [
            l for l in filtered if (
                search in str(l.get("name", "")).lower() or
                search in str(l.get("location", "")).lower() or
                search in str(l.get("property_requirement", "")).lower() or
                search in str(l.get("message", "")).lower() or
                search in str(l.get("phone", "")).lower()
            )
        ]

    # Sorting
    if sort_by == "score_desc":
        filtered.sort(key=lambda x: int(x.get("score", 0)), reverse=True)
    elif sort_by == "score_asc":
        filtered.sort(key=lambda x: int(x.get("score", 0)))
    elif sort_by == "newest":
        filtered.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)

    return jsonify({
        "success": True,
        "count": len(filtered),
        "leads": filtered
    })

@app.route("/api/leads/<lead_id>", methods=["GET"])
def api_get_lead(lead_id):
    """Retrieve full lead dossier by ID."""
    lead = get_lead_by_id(lead_id)
    if not lead:
        return jsonify({"success": False, "error": f"Lead '{lead_id}' not found."}), 404
    return jsonify({"success": True, "lead": lead})

@app.route("/api/leads", methods=["POST"])
def api_create_lead():
    """
    Intake new lead, run 6-factor deterministic scoring,
    extract Gemini AI intelligence, and save to database.
    """
    data = request.get_json(force=True, silent=True)
    if not data or not data.get("name"):
        return jsonify({"success": False, "error": "Lead 'name' is required."}), 400

    phone = str(data.get("phone", "")).strip()
    if not phone:
        return jsonify({"success": False, "error": "Lead 'phone' (contact number) is mandatory."}), 400
    data["phone"] = phone

    # 1. Deterministic scoring
    scoring_result = score_lead(data)
    data["score"] = scoring_result.get("score", 50)
    data["priority"] = scoring_result.get("priority", "Warm")
    data["score_breakdown"] = scoring_result.get("breakdown", {})
    data["breakdown"] = scoring_result.get("breakdown", {})
    data["urgency_label"] = scoring_result.get("urgency_label", "Call within 15 min" if data["priority"] == "Hot" else "Follow up in 48h")
    data["scoring_reason"] = ", ".join(scoring_result.get("signals", []))

    # 2. Extract Gemini AI intelligence (summary, objections, intent, next action)
    if not data.get("ai_analysis") or not data["ai_analysis"].get("summary"):
        ai_intel = gemini_service.extract_lead_intelligence(data)
        data["ai_analysis"] = ai_intel

    # 3. Setup follow-up action based on priority
    if not data.get("followup"):
        p = data.get("priority", "Warm").upper()
        if p == "HOT":
            data["followup"] = {
                "status": "due",
                "cadence": "Every 24 hours",
                "due": "Today by 2:30 PM",
                "scheduled": "Today by 2:30 PM",
                "time_badge": "2:30 PM",
                "window": "Immediate / Morning",
                "goal": "Call within 24h: Confirm site visit & address loan/OC docs."
            }
        elif p == "WARM":
            data["followup"] = {
                "status": "due",
                "cadence": "Every 48 hours",
                "due": "Today by 5:00 PM",
                "scheduled": "Today by 5:00 PM",
                "time_badge": "5:00 PM",
                "window": "After 4:00 PM",
                "goal": "Share all-inclusive cost sheet with registration breakdown."
            }
        else:
            data["followup"] = {
                "status": "scheduled",
                "cadence": "Every 14 days",
                "due": "In 14 Days",
                "scheduled": "In 14 Days",
                "time_badge": "Next Wk",
                "window": "Anytime",
                "goal": "Send monthly micro-market newsletter & re-qualify."
            }

    # 4. Initialize chat history if absent
    if not data.get("chat_history"):
        data["chat_history"] = [
            {
                "sender": "assistant",
                "text": f"I have analyzed **{data['name']}** ({data['priority']} Lead, Score: {data['score']}/100). Ask me anything about their inquiry, requirements, objections, or strategy in English or Hinglish!"
            }
        ]

    # 5. Save to Firestore / Local DB
    saved = save_lead(data)
    return jsonify({"success": True, "lead": saved}), 201

@app.route("/api/leads/batch", methods=["POST"])
def api_batch_import_leads():
    """
    Batch import multiple leads (e.g. from CSV upload).
    Scores all leads, handles duplicates and commits in batch.
    """
    body = request.get_json(force=True, silent=True)
    if not body or "leads" not in body or not isinstance(body["leads"], list):
        return jsonify({"success": False, "error": "Invalid payload. Expected { 'leads': [...] }."}), 400

    leads_to_process = body["leads"]
    skip_duplicates = body.get("skip_duplicates", True)

    existing_leads = get_all_leads()
    existing_phone_map = {}
    existing_name_map = {}
    for el in existing_leads:
        p_clean = "".join(filter(str.isdigit, str(el.get("phone", ""))))
        if len(p_clean) >= 10:
            existing_phone_map[p_clean[-10:]] = el
        name_clean = str(el.get("name", "")).strip().lower()
        if name_clean:
            existing_name_map[name_clean] = el

    processed = []
    skipped_duplicates = 0
    seen_in_batch = set()

    for item in leads_to_process:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        if not name:
            continue

        raw_phone = str(item.get("phone", "")).strip()
        p_clean = "".join(filter(str.isdigit, raw_phone))
        phone_key = p_clean[-10:] if len(p_clean) >= 10 else ""
        name_key = name.lower()

        # Duplicate checking
        dup_key = f"{name_key}|{phone_key}"
        if dup_key in seen_in_batch:
            skipped_duplicates += 1
            continue
        seen_in_batch.add(dup_key)

        if skip_duplicates:
            if (phone_key and phone_key in existing_phone_map) or (name_key and name_key in existing_name_map):
                skipped_duplicates += 1
                continue

        # Score and qualify
        scoring = score_lead(item)
        item["score"] = scoring.get("score", 50)
        item["priority"] = scoring.get("priority", "Warm")
        item["score_breakdown"] = scoring.get("breakdown", {})
        item["breakdown"] = scoring.get("breakdown", {})
        item["urgency_label"] = scoring.get("urgency_label", "Call within 15 min" if item["priority"] == "Hot" else "Follow up in 48h")
        item["scoring_reason"] = ", ".join(scoring.get("signals", []))

        if not item.get("ai_analysis"):
            item["ai_analysis"] = gemini_service.extract_lead_intelligence(item)

        if not item.get("chat_history"):
            item["chat_history"] = [
                {
                    "sender": "assistant",
                    "text": f"I have analyzed **{item['name']}** ({item['priority']} Lead, Score: {item['score']}/100). Ask me anything about their inquiry, requirements, objections, or strategy in English or Hinglish!"
                }
            ]

        if not item.get("followup"):
            p = item["priority"].upper()
            item["followup"] = {
                "status": "due" if p in ["HOT", "WARM"] else "scheduled",
                "cadence": "Every 24 hours" if p == "HOT" else "Every 48 hours",
                "due": "Today by 4:00 PM" if p in ["HOT", "WARM"] else "In 14 Days",
                "scheduled": "Today by 4:00 PM" if p in ["HOT", "WARM"] else "In 14 Days",
                "time_badge": "4:00 PM" if p in ["HOT", "WARM"] else "Next Wk",
                "window": "Afternoon",
                "goal": "Initiate qualification and schedule property inspection."
            }
        processed.append(item)

    saved_count = save_leads_batch(processed) if processed else 0
    return jsonify({
        "success": True,
        "imported_count": saved_count,
        "skipped_duplicates": skipped_duplicates,
        "leads": processed
    })

@app.route("/api/leads/export", methods=["GET"])
def api_export_leads_csv():
    """Export leads to a downloadable RFC 4180 CSV file."""
    priority_filter = request.args.get("priority", "").strip()
    location_filter = request.args.get("location", "").strip()

    all_leads = get_all_leads()
    filtered = all_leads

    if priority_filter and priority_filter.lower() != "all":
        filtered = [l for l in filtered if str(l.get("priority", "")).lower() == priority_filter.lower()]
    if location_filter and location_filter.lower() != "all":
        filtered = [l for l in filtered if location_filter.lower() in str(l.get("location", "")).lower()]

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    # Standard CRM CSV headers
    writer.writerow([
        "Lead ID",
        "Name",
        "Phone",
        "Priority",
        "Score",
        "Location",
        "Property Requirement",
        "Budget",
        "Timeline",
        "Urgency Action",
        "Inquiry Message",
        "Followup Status",
        "Created At"
    ])

    for l in filtered:
        writer.writerow([
            l.get("id", ""),
            l.get("name", ""),
            l.get("phone", ""),
            l.get("priority", "Warm"),
            l.get("score", ""),
            l.get("location", ""),
            l.get("property_requirement", ""),
            l.get("budget", ""),
            l.get("timeline", ""),
            l.get("urgency_label", ""),
            l.get("message", ""),
            l.get("followup", {}).get("status", "pending") if isinstance(l.get("followup"), dict) else "",
            l.get("created_at", "")
        ])

    csv_data = "\ufeff" + output.getvalue()
    filename = f"leads_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.route("/api/leads/<lead_id>/copilot", methods=["POST"])
def api_lead_copilot_chat(lead_id):
    """Grounded AI Copilot conversation for a specific lead."""
    body = request.get_json(force=True, silent=True) or {}
    query = body.get("query", "").strip()
    if not query:
        return jsonify({"success": False, "error": "Query cannot be empty."}), 400

    lead = get_lead_by_id(lead_id)
    if not lead:
        return jsonify({"success": False, "error": f"Lead '{lead_id}' not found."}), 404

    reply = gemini_service.chat_with_copilot(lead, query)
    return jsonify({"success": True, "reply": reply})

@app.route("/api/leads/<lead_id>/regenerate-reply", methods=["POST", "GET"])
def api_regenerate_reply(lead_id):
    """Regenerate an alternative suggested customer reply with varied tone/angle."""
    body = (request.get_json(force=True, silent=True) if request.is_json else None) or {}
    current_reply = body.get("current_reply") or request.args.get("current_reply", "")
    tone = body.get("tone") or request.args.get("tone", "")
    try:
        variation = int(body.get("variation") or request.args.get("variation", 1))
    except (ValueError, TypeError):
        variation = 1

    lead = get_lead_by_id(lead_id)
    if not lead:
        return jsonify({"success": False, "error": f"Lead '{lead_id}' not found."}), 404

    reply = gemini_service.regenerate_suggested_reply(lead, current_reply=current_reply, tone=tone, variation=variation)
    return jsonify({"success": True, "reply": reply})

@app.route("/api/leads/<lead_id>/followup/generate", methods=["POST"])
def api_generate_followup(lead_id):
    """Generate high-converting follow-up message copy (WhatsApp / SMS)."""
    body = request.get_json(force=True, silent=True) or {}
    channel = body.get("channel", "whatsapp").strip().lower()

    lead = get_lead_by_id(lead_id)
    if not lead:
        return jsonify({"success": False, "error": f"Lead '{lead_id}' not found."}), 404

    copy = gemini_service.generate_followup_copy(lead, channel=channel)
    return jsonify({"success": True, "copy": copy})

@app.route("/api/followup/chat", methods=["POST"])
def api_followup_hub_chat():
    """Follow-Up Hub pipeline AI assistant chat."""
    body = request.get_json(force=True, silent=True) or {}
    query = body.get("query", "").strip()
    if not query:
        return jsonify({"success": False, "error": "Query cannot be empty."}), 400

    all_leads = get_all_leads()
    due_leads = [l for l in all_leads if str(l.get("followup", {}).get("status", "")).lower() == "due"]
    reply = gemini_service.chat_with_followup_hub(query, due_leads)
    return jsonify({"success": True, "reply": reply})

@app.route("/api/leads/seed", methods=["POST"])
def api_seed_leads():
    """Seeds or resets the 18 benchmark leads."""
    force = request.args.get("force", "false").lower() == "true"
    count = seed_benchmark_leads(force=force)
    return jsonify({"success": True, "seeded_count": count})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "127.0.0.1")
    logger.info(f"Starting Lead Manager Server on http://{host}:{port}")
    debug_mode = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    app.run(host=host, port=port, debug=debug_mode)
