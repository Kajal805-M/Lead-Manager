"""
Dataset Build Script for Lead Evaluation Framework.
Compiles handwritten and synthetic leads, applies deterministic dev/heldout split,
and writes out evals/data/*.jsonl files.
"""

import os
import json
import random
from typing import List, Dict, Any

from evals.handwritten import HANDWRITTEN_LEADS
from evals.generator import generate_leads
from evals.attacks import ATTACK_LEADS
from evals.chat_set import CHAT_TEST_SET
from evals.metamorphic import METAMORPHIC_TRANSFORMS
from evals.rules import compute_gold_score

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def write_jsonl(filepath: str, records: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def build_all(seed: int = 1337) -> Dict[str, int]:
    # 1. Collect all leads (29 handwritten + 70 synthetic = 99)
    all_leads: List[Dict[str, Any]] = []

    for item in HANDWRITTEN_LEADS:
        lead = dict(item)
        gold_score_info = compute_gold_score(lead["gold"])
        lead["gold"]["expected_score"] = gold_score_info["score"]
        lead["gold"]["expected_tag"] = gold_score_info["tag"]
        all_leads.append(lead)

    synthetic_leads = generate_leads(seed=42, count=70)
    for item in synthetic_leads:
        lead = dict(item)
        gold_score_info = compute_gold_score(lead["gold"])
        lead["gold"]["expected_score"] = gold_score_info["score"]
        lead["gold"]["expected_tag"] = gold_score_info["tag"]
        all_leads.append(lead)

    # 2. Deterministic Train/Dev vs Heldout Split (~75% / ~25%)
    # Stratified shuffle by expected tag to ensure balanced representation
    rng = random.Random(seed)
    by_tag: Dict[str, List[Dict[str, Any]]] = {}
    for lead in all_leads:
        tag = lead["gold"]["expected_tag"]
        by_tag.setdefault(tag, []).append(lead)

    dev_set: List[Dict[str, Any]] = []
    heldout_set: List[Dict[str, Any]] = []

    for tag, leads_group in sorted(by_tag.items()):
        shuffled = list(leads_group)
        rng.shuffle(shuffled)
        n_heldout = max(1, round(len(shuffled) * 0.25))
        heldout_set.extend(shuffled[:n_heldout])
        dev_set.extend(shuffled[n_heldout:])

    # Sort deterministically by id
    dev_set.sort(key=lambda x: x["id"])
    heldout_set.sort(key=lambda x: x["id"])

    # 3. Write data files
    write_jsonl(os.path.join(DATA_DIR, "dev.jsonl"), dev_set)
    write_jsonl(os.path.join(DATA_DIR, "heldout.jsonl"), heldout_set)
    write_jsonl(os.path.join(DATA_DIR, "attacks.jsonl"), ATTACK_LEADS)
    write_jsonl(os.path.join(DATA_DIR, "chat.jsonl"), CHAT_TEST_SET)
    write_jsonl(os.path.join(DATA_DIR, "metamorphic.jsonl"), METAMORPHIC_TRANSFORMS)

    stats = {
        "dev": len(dev_set),
        "heldout": len(heldout_set),
        "total_benchmark": len(all_leads),
        "attacks": len(ATTACK_LEADS),
        "chat": len(CHAT_TEST_SET),
        "metamorphic": len(METAMORPHIC_TRANSFORMS),
    }

    print("=" * 60)
    print("AI Evaluation Dataset Build Complete")
    print("=" * 60)
    print(f"Dev Leads:        {stats['dev']}")
    print(f"Heldout Leads:    {stats['heldout']}")
    print(f"Total Leads:      {stats['total_benchmark']}")
    print(f"Attack Leads:     {stats['attacks']}")
    print(f"Chat Test Pairs:  {stats['chat']}")
    print(f"Metamorphic Sets: {stats['metamorphic']}")
    print(f"Output Directory: {DATA_DIR}")
    print("=" * 60)

    return stats


if __name__ == "__main__":
    build_all()
