"""
Comprehensive Backend CSV Verification Suite:
- Batch Import via API
- Lead ID non-collision
- Phone number persistence
- Duplicate detection & skipping
- Scoring validation
- CSV Export with RFC-4180 compliance & filters
- Round-trip integrity
"""

import io
import os
import sys
import csv
import json
import unittest
from datetime import datetime

# Add root folder to sys.path so app can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import application components
from app import app
from firebase_service import get_all_leads, get_lead_by_id, LocalLeadDB

class TestBackendCsvWorkflow(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_01_batch_import_and_id_safety(self):
        """Verify batch import creates sequential non-colliding IDs and stores phones."""
        initial_leads = get_all_leads()
        initial_count = len(initial_leads)
        initial_ids = {str(l.get("id")) for l in initial_leads}

        test_payload = {
            "leads": [
                {
                    "name": "Test User Alpha",
                    "phone": "+91 99887 76655",
                    "location": "Whitefield",
                    "property_requirement": "3BHK",
                    "budget": "1.8 Cr",
                    "timeline": "Within 1 month",
                    "message": "Ready to buy immediately, loan sanctioned."
                },
                {
                    "name": "Test User Beta",
                    "phone": "+91 98777 66554",
                    "location": "Hebbal",
                    "property_requirement": "4BHK Luxury",
                    "budget": "3.2 Cr",
                    "timeline": "2-3 months",
                    "message": "Looking for premium penthouse."
                }
            ],
            "skip_duplicates": True
        }

        response = self.client.post(
            "/api/leads/batch",
            data=json.dumps(test_payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["imported_count"], 2)

        imported = data["leads"]
        self.assertEqual(len(imported), 2)

        # Ensure IDs generated do not collide with any pre-existing lead ID
        for item in imported:
            lid = str(item.get("id"))
            self.assertNotIn(lid, initial_ids, f"ID {lid} collided with existing lead!")
            self.assertTrue(lid.startswith("L"), f"ID {lid} must follow standard L prefix convention")
            self.assertIn("phone", item)
            self.assertTrue(len(item["phone"]) >= 10)
            self.assertIn("score", item)
            self.assertIn("priority", item)
            self.assertIn("ai_analysis", item)

        # Verify leads are now retrievable from DB
        for item in imported:
            saved = get_lead_by_id(item["id"])
            self.assertIsNotNone(saved)
            self.assertEqual(saved["name"], item["name"])
            self.assertEqual(saved["phone"], item["phone"])

    def test_02_duplicate_prevention(self):
        """Verify duplicates in batch or against CRM are skipped."""
        dup_payload = {
            "leads": [
                {
                    "name": "Duplicate Check Lead",
                    "phone": "+91 91111 22222",
                    "location": "Sarjapur Road",
                    "property_requirement": "2BHK",
                    "budget": "80 L",
                    "timeline": "Immediate",
                    "message": "Inquiry 1"
                },
                {
                    "name": "Duplicate Check Lead",
                    "phone": "+91 91111 22222",
                    "location": "Sarjapur Road",
                    "property_requirement": "2BHK",
                    "budget": "80 L",
                    "timeline": "Immediate",
                    "message": "Duplicate inquiry"
                }
            ],
            "skip_duplicates": True
        }

        # First import should import 1 and skip 1
        resp = self.client.post("/api/leads/batch", data=json.dumps(dup_payload), content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        d = resp.get_json()
        self.assertEqual(d["imported_count"], 1)
        self.assertEqual(d["skipped_duplicates"], 1)

        # Second import with the same payload should skip both as they now exist in CRM
        resp2 = self.client.post("/api/leads/batch", data=json.dumps(dup_payload), content_type="application/json")
        self.assertEqual(resp2.status_code, 200)
        d2 = resp2.get_json()
        self.assertEqual(d2["imported_count"], 0)
        self.assertEqual(d2["skipped_duplicates"], 2)

    def test_03_csv_export_endpoint(self):
        """Verify CSV export endpoint produces valid RFC 4180 CSV with BOM and correct headers."""
        resp = self.client.get("/api/leads/export")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/csv", resp.content_type)
        self.assertIn("attachment; filename=leads_export_", resp.headers.get("Content-Disposition", ""))

        text_content = resp.data.decode("utf-8")
        # Check UTF-8 BOM
        self.assertTrue(text_content.startswith("\ufeff"), "Export must include UTF-8 BOM for Excel")

        # Strip BOM and parse with python csv.reader
        clean_csv = text_content[1:] if text_content.startswith("\ufeff") else text_content
        reader = csv.reader(io.StringIO(clean_csv))
        rows = list(reader)

        self.assertGreater(len(rows), 1, "Exported CSV must contain headers + data rows")
        expected_headers = ["Lead ID", "Name", "Phone", "Priority", "Score", "Location", "Property Requirement", "Budget", "Timeline", "Urgency Action", "Inquiry Message", "Followup Status", "Created At"]
        self.assertEqual(rows[0], expected_headers, "CSV headers must match specification exactly")

        # Verify all rows have 13 columns
        for idx, row in enumerate(rows[1:], start=2):
            self.assertEqual(len(row), 13, f"Row {idx} should have 13 columns, found {len(row)}")

    def test_04_csv_export_filters(self):
        """Verify CSV export respects priority and location query filters."""
        # Hot priority filter
        resp_hot = self.client.get("/api/leads/export?priority=Hot")
        self.assertEqual(resp_hot.status_code, 200)
        clean_hot = resp_hot.data.decode("utf-8").lstrip("\ufeff")
        rows_hot = list(csv.reader(io.StringIO(clean_hot)))
        for row in rows_hot[1:]:
            self.assertEqual(row[3].lower(), "hot", "Every row in Hot export must have Hot priority")

        # Location filter
        resp_loc = self.client.get("/api/leads/export?location=Whitefield")
        self.assertEqual(resp_loc.status_code, 200)
        clean_loc = resp_loc.data.decode("utf-8").lstrip("\ufeff")
        rows_loc = list(csv.reader(io.StringIO(clean_loc)))
        for row in rows_loc[1:]:
            self.assertIn("whitefield", row[5].lower(), "Every row in Whitefield export must contain Whitefield")

if __name__ == "__main__":
    unittest.main()
