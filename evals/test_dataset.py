"""
Unit Test Suite for Dataset Integrity.
Run with: python -m unittest evals.test_dataset
"""

import os
import json
import unittest
from typing import List, Dict, Any

from evals.handwritten import HANDWRITTEN_LEADS
from evals.generator import generate_leads
from evals.attacks import ATTACK_LEADS
from evals.chat_set import CHAT_TEST_SET
from evals.metamorphic import METAMORPHIC_TRANSFORMS
from evals.build import build_all, DATA_DIR

GOLD_FIELDS = {
    "is_spam": bool,
    "primary_location": (str, type(None)),
    "property_type": (str, type(None)),
    "budget_lakhs": (int, float, type(None)),
    "timeline_months": (int, type(None)),
    "has_reason": bool,
    "loan_status": str,
    "visit_or_call_requested": bool,
    "already_visited": bool,
    "ready_to_book": bool,
    "decision_maker": str,
    "n_questions": int,
    "concrete_details_count": int,
}

VALID_LOAN_STATUSES = {"sanctioned", "pre_approved", "in_process", "none", "own_funds", "unknown"}
VALID_DECISION_MAKERS = {"sole", "joint_present", "needs_others", "unknown"}


class TestDatasetIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure build runs first
        cls.stats = build_all()

    def test_unique_lead_ids(self):
        """All benchmark leads must have unique IDs."""
        all_leads = HANDWRITTEN_LEADS + generate_leads(seed=42, count=70)
        ids = [l["id"] for l in all_leads]
        self.assertEqual(len(ids), len(set(ids)), "Duplicate lead IDs found in dataset!")

    def test_evidence_phrases_exist_in_message(self):
        """Every single evidence phrase must be an exact substring of the lead's message."""
        all_leads = HANDWRITTEN_LEADS + generate_leads(seed=42, count=70)
        for lead in all_leads:
            msg = lead["message"]
            for field, phrase in lead.get("evidence_phrases", {}).items():
                self.assertIn(
                    phrase,
                    msg,
                    f"Evidence phrase '{phrase}' for field '{field}' not found in lead {lead['id']} message: '{msg}'"
                )

    def test_all_gold_fields_present_and_typed(self):
        """All 12 gold fields must exist with valid types and allowed enum values."""
        all_leads = HANDWRITTEN_LEADS + generate_leads(seed=42, count=70)
        for lead in all_leads:
            gold = lead["gold"]
            for field, expected_type in GOLD_FIELDS.items():
                self.assertIn(field, gold, f"Missing field '{field}' in lead {lead['id']} gold facts")
                val = gold[field]
                self.assertTrue(
                    isinstance(val, expected_type),
                    f"Field '{field}' in lead {lead['id']} has wrong type {type(val)}, expected {expected_type}"
                )

            # Enum checks
            self.assertIn(gold["loan_status"], VALID_LOAN_STATUSES)
            self.assertIn(gold["decision_maker"], VALID_DECISION_MAKERS)

    def test_dataset_sizes(self):
        """Verify exact sizes specified in Evel_example/README.md."""
        self.assertEqual(len(HANDWRITTEN_LEADS), 29, "Handwritten leads count must be 29")
        synthetic = generate_leads(seed=42, count=70)
        self.assertEqual(len(synthetic), 70, "Synthetic leads count must be 70")
        self.assertEqual(len(ATTACK_LEADS), 15, "Attack leads count must be 15")
        self.assertEqual(len(CHAT_TEST_SET), 37, "Chat test pairs count must be 37")
        self.assertEqual(len(METAMORPHIC_TRANSFORMS), 154, "Metamorphic transforms count must be 154")

    def test_split_sizes_and_files(self):
        """Check dev and heldout file creation and split ratio (~75% / ~25%)."""
        dev_file = os.path.join(DATA_DIR, "dev.jsonl")
        heldout_file = os.path.join(DATA_DIR, "heldout.jsonl")

        self.assertTrue(os.path.exists(dev_file), "dev.jsonl missing")
        self.assertTrue(os.path.exists(heldout_file), "heldout.jsonl missing")

        with open(dev_file, "r", encoding="utf-8") as f:
            dev_leads = [json.loads(line) for line in f]
        with open(heldout_file, "r", encoding="utf-8") as f:
            heldout_leads = [json.loads(line) for line in f]

        self.assertEqual(len(dev_leads) + len(heldout_leads), 99)
        self.assertGreaterEqual(len(dev_leads), 70)
        self.assertLessEqual(len(dev_leads), 78)
        self.assertGreaterEqual(len(heldout_leads), 21)
        self.assertLessEqual(len(heldout_leads), 29)

    def test_languages_covered(self):
        """Verify English and Hinglish messages are both covered."""
        languages = {l.get("language") for l in HANDWRITTEN_LEADS}
        self.assertIn("en", languages)
        self.assertIn("hinglish", languages)

    def test_build_determinism(self):
        """Rebuilding must produce identical files."""
        dev_file = os.path.join(DATA_DIR, "dev.jsonl")
        with open(dev_file, "r", encoding="utf-8") as f:
            content1 = f.read()

        # Re-run build
        build_all()

        with open(dev_file, "r", encoding="utf-8") as f:
            content2 = f.read()

        self.assertEqual(content1, content2, "Dataset build is not deterministic!")


if __name__ == "__main__":
    unittest.main()
