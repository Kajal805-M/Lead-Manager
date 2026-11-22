"""
Metamorphic Testing Battery (154 transforms).
Evaluates model robustness without gold human labels:
1. Invariance transforms (noise/formatting): score change must be <= 3 points.
2. Monotonic positive transforms (budget boost/loan sanction/ready to book): score must never decrease.
"""

from typing import List, Dict, Any
from evals.handwritten import HANDWRITTEN_LEADS

INVARIANCE_TRANSFORMS = [
    ("invariance_greeting", lambda m: f"Hello Team, {m}"),
    ("invariance_signoff", lambda m: f"{m}\n\nWarm regards,\nRaghav Sharma"),
    ("invariance_lowercase", lambda m: m.lower()),
    ("invariance_whitespace", lambda m: m.replace(". ", ".   ")),
    ("invariance_prefix_hi", lambda m: f"Dear Sir/Madam, {m}"),
    ("invariance_filler_typo", lambda m: m.replace("please", "pleae").replace("Please", "Pleae") if "please" in m.lower() else f"Kindly note: {m}"),
    ("invariance_phone_suffix", lambda m: f"{m} You can reach me at +91 98765 43210."),
]

MONOTONIC_TRANSFORMS = [
    ("monotonic_budget_boost", lambda m: f"{m} Actually my budget is flexible and I can increase it by another 30 Lakhs."),
    ("monotonic_loan_sanctioned", lambda m: f"{m} In addition, my home loan has been officially sanctioned by HDFC Bank."),
    ("monotonic_immediate_timeline", lambda m: f"{m} Need to move urgently within 7 days."),
    ("monotonic_site_visit", lambda m: f"{m} Can we schedule an immediate site inspection tomorrow at 11 AM?"),
    ("monotonic_ready_to_book", lambda m: f"{m} I am ready with the token cheque to book on the spot."),
    ("monotonic_own_funds", lambda m: f"{m} I have 100% own liquid funds ready for payment without loan dependency."),
    ("monotonic_joint_ready", lambda m: f"{m} My spouse and I have reviewed the brochure and are both ready to finalize."),
]

def build_metamorphic_transforms() -> List[Dict[str, Any]]:
    transforms: List[Dict[str, Any]] = []
    # 11 baseline leads x 14 transforms = 154 total transforms
    base_leads = HANDWRITTEN_LEADS[:11]
    
    count = 1
    for lead in base_leads:
        base_id = lead["id"]
        base_msg = lead["message"]

        # 7 Invariance transforms
        for name, fn in INVARIANCE_TRANSFORMS:
            t_msg = fn(base_msg)
            transforms.append({
                "id": f"META{count:03d}",
                "base_lead_id": base_id,
                "transform_type": "invariance",
                "transform_name": name,
                "base_message": base_msg,
                "transformed_message": t_msg,
                "max_score_diff": 3,
                "description": "Invariance test: score difference must be <= 3 points under cosmetic noise."
            })
            count += 1

        # 7 Monotonic transforms
        for name, fn in MONOTONIC_TRANSFORMS:
            t_msg = fn(base_msg)
            transforms.append({
                "id": f"META{count:03d}",
                "base_lead_id": base_id,
                "transform_type": "monotonic",
                "transform_name": name,
                "base_message": base_msg,
                "transformed_message": t_msg,
                "allow_score_decrease": False,
                "description": "Monotonic test: score must not decrease when lead qualifications improve."
            })
            count += 1

    return transforms

METAMORPHIC_TRANSFORMS = build_metamorphic_transforms()
