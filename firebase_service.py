"""
Firebase Firestore Service with Seamless Local DB Fallback.
Provides unified CRUD operations for Real Estate Lead records:
- Connects to Google Cloud Firestore using firebase-admin SDK if credentials exist.
- Seamlessly falls back to local JSON storage (local_leads.json) if credentials are absent or Firestore DB is not yet enabled.
- Automatically initializes and enriches the 18 benchmark leads from test_data/leads_dataset.json.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("LeadDatabase")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

_firebase_initialized = False
_firestore_db = None
_LOCAL_STORAGE_FILE = "local_leads.json"
_BENCHMARK_SEED_FILE = os.path.join("test_data", "leads_dataset.json")

def init_firebase() -> bool:
    """Attempt to initialize Firebase Admin SDK and Firestore client from env or local file."""
    global _firebase_initialized, _firestore_db
    if _firebase_initialized and _firestore_db is not None:
        return True

    cred = None

    # 1. Check if Service Account JSON is passed directly as environment variable (Ideal for Vercel/Cloud)
    env_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON") or os.getenv("FIREBASE_CREDENTIALS_JSON")
    if env_json:
        try:
            raw_str = env_json.strip()
            if raw_str.startswith("{"):
                cert_dict = json.loads(raw_str)
            else:
                import base64
                cert_dict = json.loads(base64.b64decode(raw_str).decode("utf-8"))
            from firebase_admin import credentials
            cred = credentials.Certificate(cert_dict)
            logger.info("Firebase credentials successfully parsed from environment variable JSON.")
        except Exception as json_err:
            logger.warning(f"Failed to parse Firebase JSON from environment: {json_err}")

    # 2. Check individual environment variables
    if cred is None:
        project_id = os.getenv("FIREBASE_PROJECT_ID")
        private_key = os.getenv("FIREBASE_PRIVATE_KEY")
        client_email = os.getenv("FIREBASE_CLIENT_EMAIL")
        if project_id and private_key and client_email:
            try:
                cert_dict = {
                    "type": "service_account",
                    "project_id": project_id,
                    "private_key": private_key.replace("\\n", "\n"),
                    "client_email": client_email,
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
                from firebase_admin import credentials
                cred = credentials.Certificate(cert_dict)
                logger.info("Firebase credentials successfully constructed from individual environment variables.")
            except Exception as ind_err:
                logger.warning(f"Failed to build Firebase credentials from individual env vars: {ind_err}")

    # 3. Check credentials file on disk
    if cred is None:
        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase_credentials.json")
        if not os.path.isabs(cred_path):
            current_dir = os.path.dirname(os.path.abspath(__file__))
            cred_path = os.path.join(current_dir, cred_path)

        if os.path.exists(cred_path):
            try:
                from firebase_admin import credentials
                cred = credentials.Certificate(cred_path)
                logger.info(f"Firebase credentials loaded from local file: {cred_path}")
            except Exception as file_err:
                logger.warning(f"Failed to load credentials from file '{cred_path}': {file_err}")

    if cred is None:
        logger.info("No Firebase credentials provided. Operating in seamless local JSON storage mode.")
        return False

    try:
        import firebase_admin
        from firebase_admin import firestore

        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        _firestore_db = firestore.client()
        # Test Firestore connectivity with a small check
        try:
            test_stream = _firestore_db.collection("leads").limit(1).stream()
            for _ in test_stream:
                break
            _firebase_initialized = True
            logger.info("Firebase Firestore connected & ready.")
            return True
        except Exception as conn_err:
            logger.warning(
                f"Firebase initialized, but Firestore database is not yet created in console: {conn_err}. "
                "Falling back to local storage until created."
            )
            _firebase_initialized = False
            return False
    except Exception as e:
        logger.warning(f"Failed to initialize Firebase Admin SDK: {e}. Falling back to local storage.")
        _firebase_initialized = False
        _firestore_db = None
        return False

# Attempt initialization
init_firebase()

def is_firebase_connected() -> bool:
    """Check if live Firebase Firestore connection is actively responsive."""
    return _firebase_initialized and _firestore_db is not None

class LocalLeadDB:
    """In-memory and file-backed JSON database for leads when Firestore is not in use."""
    _in_memory_leads: Optional[List[Dict[str, Any]]] = None

    @staticmethod
    def _get_path() -> str:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, _LOCAL_STORAGE_FILE)

    @classmethod
    def load_all(cls) -> List[Dict[str, Any]]:
        if cls._in_memory_leads is not None and len(cls._in_memory_leads) > 0:
            return list(cls._in_memory_leads)

        # 1. Check primary local path
        path = cls._get_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        cls._in_memory_leads = data
                        return list(data)
                    elif isinstance(data, dict) and "leads" in data:
                        cls._in_memory_leads = data["leads"]
                        return list(cls._in_memory_leads)
            except Exception as e:
                logger.error(f"Error reading local leads file: {e}")

        # 2. Check /tmp serverless path (e.g. Vercel)
        tmp_path = os.path.join("/tmp", _LOCAL_STORAGE_FILE) if os.path.exists("/tmp") else None
        if tmp_path and os.path.exists(tmp_path):
            try:
                with open(tmp_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        cls._in_memory_leads = data
                        return list(data)
            except Exception as e:
                logger.debug(f"Error reading /tmp local leads file: {e}")

        # 3. Seed from benchmark dataset if available
        seed_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), _BENCHMARK_SEED_FILE)
        if os.path.exists(seed_path):
            try:
                with open(seed_path, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                    if isinstance(raw_data, list):
                        enriched = cls._enrich_raw_leads(raw_data)
                        cls.save_all(enriched)
                        return enriched
            except Exception as e:
                logger.warning(f"Could not auto-seed from {seed_path}: {e}")

        return []

    @classmethod
    def _enrich_raw_leads(cls, raw_leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Ensures raw benchmark leads have scoring, contact, and followup structures."""
        from scoring_engine import score_lead
        enriched = []
        for idx, item in enumerate(raw_leads):
            lead = dict(item)
            lid = lead.get("id") or f"L{idx+1:02d}"
            lead["id"] = lid
            if "phone" not in lead:
                lead["phone"] = f"+91 98450 {10000 + idx}"
            if "email" not in lead:
                first = lead.get("name", "client").split()[0].lower()
                lead["email"] = f"{first}.leads@example.com"

            # Compute score
            scoring = score_lead(lead)
            lead["score"] = scoring.get("score", 50)
            lead["priority"] = scoring.get("priority", "Warm")
            lead["score_breakdown"] = scoring.get("breakdown", {})
            lead["scoring_reason"] = ", ".join(scoring.get("signals", []))

            # AI Analysis structure
            exp = lead.get("expected", {})
            lead["ai_analysis"] = {
                "summary": f"{lead.get('name')} looking for {lead.get('property_requirement')} in {lead.get('location')} (Budget: ₹{lead.get('budget')}).",
                "intent": "; ".join(exp.get("key_signals", ["Active buyer inquiry"])),
                "requirements": f"{lead.get('property_requirement')} in {lead.get('location')}",
                "objections": exp.get("objections", ["Budget / pricing fit"]),
                "next_action": exp.get("next_action", "Initiate contact to confirm property requirements"),
                "suggested_response": f"Hello {lead.get('name').split()[0]}, we have verified units in {lead.get('location')} fitting your criteria. Can we connect today?"
            }

            # Followup action
            if "followup" not in lead or not isinstance(lead["followup"], dict):
                priority_str = lead["priority"].upper()
                if priority_str == "HOT":
                    lead["followup"] = {
                        "status": "due",
                        "cadence": "Every 24 hours",
                        "due": "Today by 2:30 PM",
                        "scheduled": "Today by 2:30 PM",
                        "time_badge": "2:30 PM",
                        "window": "Immediate / Morning",
                        "goal": exp.get("next_action", "Call within 24h: Confirm site visit & share OC documents.")
                    }
                elif priority_str == "WARM":
                    lead["followup"] = {
                        "status": "due",
                        "cadence": "Every 48 hours",
                        "due": "Today by 5:00 PM",
                        "scheduled": "Today by 5:00 PM",
                        "time_badge": "5:00 PM",
                        "window": "After 4:00 PM",
                        "goal": exp.get("next_action", "Share all-inclusive cost sheet with registration breakdown.")
                    }
                else:
                    lead["followup"] = {
                        "status": "scheduled",
                        "cadence": "Every 14 days",
                        "due": "In 14 Days",
                        "scheduled": "In 14 Days",
                        "time_badge": "Next Wk",
                        "window": "Anytime",
                        "goal": exp.get("next_action", "Send monthly newsletter & re-qualify.")
                    }
            else:
                if "due" in lead["followup"] and "scheduled" not in lead["followup"]:
                    lead["followup"]["scheduled"] = lead["followup"]["due"]
                if "scheduled" in lead["followup"] and "due" not in lead["followup"]:
                    lead["followup"]["due"] = lead["followup"]["scheduled"]
                if "time_badge" not in lead["followup"]:
                    raw = str(lead["followup"].get("due", "4:00 PM")).replace("Today by ", "").replace("Today, ", "").strip()
                    lead["followup"]["time_badge"] = raw
            enriched.append(lead)
        return enriched

    @classmethod
    def save_all(cls, leads: List[Dict[str, Any]]) -> bool:
        cls._in_memory_leads = list(leads)
        path = cls._get_path()
        saved = False
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(leads, f, indent=2, ensure_ascii=False)
            saved = True
        except Exception as e:
            logger.debug(f"Could not save to primary path '{path}': {e}. Attempting /tmp fallback...")

        # If primary failed (e.g. read-only filesystem on Vercel), save to /tmp
        if not saved and os.path.exists("/tmp"):
            try:
                tmp_path = os.path.join("/tmp", _LOCAL_STORAGE_FILE)
                with open(tmp_path, "w", encoding="utf-8") as f:
                    json.dump(leads, f, indent=2, ensure_ascii=False)
                saved = True
            except Exception as tmp_err:
                logger.warning(f"Could not save to /tmp fallback: {tmp_err}")

        return saved or (cls._in_memory_leads is not None)

def get_all_leads() -> List[Dict[str, Any]]:
    """Retrieve all leads from Firestore or Local DB."""
    if is_firebase_connected():
        try:
            coll = _firestore_db.collection("leads")
            docs = coll.stream()
            leads = []
            for doc in docs:
                d = doc.to_dict()
                if isinstance(d, dict):
                    if "id" not in d:
                        d["id"] = doc.id
                    leads.append(d)
            if leads:
                return leads
        except Exception as e:
            logger.warning(f"Firestore get_all_leads error: {e}. Falling back to local storage.")

    return LocalLeadDB.load_all()

def get_lead_by_id(lead_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single lead by its identifier."""
    if is_firebase_connected():
        try:
            doc_ref = _firestore_db.collection("leads").document(str(lead_id))
            doc = doc_ref.get()
            if doc.exists:
                d = doc.to_dict()
                d["id"] = doc.id
                return d
        except Exception as e:
            logger.warning(f"Firestore get_lead_by_id error: {e}")

    leads = LocalLeadDB.load_all()
    for l in leads:
        if isinstance(l, dict) and str(l.get("id", "")).strip().lower() == str(lead_id).strip().lower():
            return l
    return None

def _get_next_lead_id(existing_leads: List[Dict[str, Any]]) -> str:
    """Generate next sequential lead ID (e.g. L19, L20) avoiding collisions."""
    existing_nums = []
    for l in existing_leads:
        if isinstance(l, dict):
            lid = str(l.get("id", "")).strip()
            if lid.startswith("L") and lid[1:].isdigit():
                try:
                    existing_nums.append(int(lid[1:]))
                except ValueError:
                    pass
    next_num = max(existing_nums, default=0) + 1
    return f"L{next_num:02d}"

def save_lead(lead_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create or update a lead in Firestore and/or Local DB."""
    lead_id = str(lead_data.get("id", "")).strip()
    existing = get_all_leads()
    if not lead_id or lead_id == "None":
        lead_id = _get_next_lead_id(existing)
        lead_data["id"] = lead_id

    lead_data["updated_at"] = datetime.utcnow().isoformat()
    if "created_at" not in lead_data:
        lead_data["created_at"] = datetime.utcnow().isoformat()

    if is_firebase_connected():
        try:
            doc_ref = _firestore_db.collection("leads").document(lead_id)
            doc_ref.set(lead_data, merge=True)
            logger.info(f"Saved lead {lead_id} to Firestore.")
        except Exception as e:
            logger.warning(f"Firestore save_lead error: {e}. Saved to local DB.")

    # Mirror to local DB
    leads = LocalLeadDB.load_all()
    updated = False
    for i, l in enumerate(leads):
        if isinstance(l, dict) and str(l.get("id", "")).strip().lower() == lead_id.lower():
            leads[i] = lead_data
            updated = True
            break
    if not updated:
        leads.insert(0, lead_data)
    LocalLeadDB.save_all(leads)
    return lead_data

def save_leads_batch(leads_list: List[Dict[str, Any]]) -> int:
    """Batch save multiple leads safely avoiding ID collision."""
    if not leads_list:
        return 0

    existing_leads = get_all_leads()
    existing_nums = []
    for l in existing_leads:
        if isinstance(l, dict):
            lid = str(l.get("id", "")).strip()
            if lid.startswith("L") and lid[1:].isdigit():
                try:
                    existing_nums.append(int(lid[1:]))
                except ValueError:
                    pass
    next_num = max(existing_nums, default=0) + 1

    # Ensure all leads have unique IDs and timestamps
    for l in leads_list:
        if isinstance(l, dict):
            lid = str(l.get("id", "")).strip()
            if not lid or lid == "None":
                lid = f"L{next_num:02d}"
                next_num += 1
                l["id"] = lid
            if "created_at" not in l:
                l["created_at"] = datetime.utcnow().isoformat()
            l["updated_at"] = datetime.utcnow().isoformat()

    saved_count = 0
    if is_firebase_connected():
        try:
            batch = _firestore_db.batch()
            for l in leads_list:
                ref = _firestore_db.collection("leads").document(l["id"])
                batch.set(ref, l, merge=True)
                saved_count += 1
            batch.commit()
            logger.info(f"Committed batch of {saved_count} leads to Firestore.")
        except Exception as e:
            logger.warning(f"Firestore batch commit error: {e}")

    # Update local DB as well (preserve non-empty IDs)
    local_leads = {str(l.get("id")): l for l in LocalLeadDB.load_all() if isinstance(l, dict) and l.get("id")}
    for l in leads_list:
        if isinstance(l, dict) and l.get("id"):
            local_leads[str(l.get("id"))] = l
    all_combined = list(local_leads.values())
    LocalLeadDB.save_all(all_combined)
    return len(leads_list)

def update_lead(lead_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update specific fields on an existing lead."""
    lead = get_lead_by_id(lead_id)
    if not lead:
        return None
    lead.update(updates)
    lead["updated_at"] = datetime.utcnow().isoformat()
    return save_lead(lead)

def seed_benchmark_leads(force: bool = False) -> int:
    """Seed the 18 benchmark leads into the active database."""
    current_leads = LocalLeadDB.load_all()

    if is_firebase_connected():
        try:
            # Check if firestore collection has leads
            stream = _firestore_db.collection("leads").limit(1).stream()
            has_docs = False
            for _ in stream:
                has_docs = True
                break
            if not has_docs or force:
                logger.info("Syncing benchmark leads to Firestore collection 'leads'...")
                save_leads_batch(current_leads)
        except Exception as e:
            logger.warning(f"Error syncing leads to Firestore: {e}")

    if current_leads and not force:
        logger.info(f"Database already has {len(current_leads)} leads.")
        return len(current_leads)

    seed_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), _BENCHMARK_SEED_FILE)
    if not os.path.exists(seed_path):
        logger.warning(f"Seed benchmark file not found: {seed_path}")
        return 0

    try:
        with open(seed_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
            raw_leads = raw.get("leads", []) if isinstance(raw, dict) else raw
            enriched = LocalLeadDB._enrich_raw_leads(raw_leads)
            return save_leads_batch(enriched)
    except Exception as e:
        logger.error(f"Failed to seed benchmark leads: {e}")
        return 0
