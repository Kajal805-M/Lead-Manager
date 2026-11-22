"""
Fact-first Synthetic Lead Generator (Seeded).
Produces 70 deterministic synthetic leads with distractor numbers per GUIDELINES.md.
"""

import random
from typing import List, Dict, Any, Optional

LOCATIONS = [
    "Whitefield", "Sarjapur Road", "Electronic City", "Hebbal", "Bellandur",
    "Thanisandra", "Bannerghatta Road", "Devanahalli", "Marathahalli",
    "Kanakapura Road", "Yelahanka", "Varthur", "Panathur", "Kadugodi",
    "Indiranagar", "Koramangala"
]

PROPERTY_TYPES = ["1BHK", "2BHK", "3BHK", "4BHK", "villa", "plot"]

BUDGET_TEMPLATES = [
    (lambda b: f"{b:.0f} Lakhs", lambda b: float(b)),
    (lambda b: f"₹{b:.0f}L", lambda b: float(b)),
    (lambda b: f"{b/100:.2f} Cr" if b%100 else f"{b/100:.1f} Cr", lambda b: float(b)),
    (lambda b: f"₹{b/100:.2f} Crore" if b%100 else f"₹{b/100:.1f} Crore", lambda b: float(b)),
]

TIMELINE_SNIPPETS = [
    ("within 1 month", 1),
    ("immediately", 1),
    ("next week", 1),
    ("in 2 months", 2),
    ("within 3 months", 3),
    ("by 6 months", 6),
    ("next year", 12),
]

REASONS = [
    "relocating due to office transfer",
    "current rental lease ending shortly",
    "need bigger house after baby arrival",
    "near child's new school admission",
    "joining new tech firm in tech park"
]

LOAN_SNIPPETS = [
    ("loan is sanctioned by bank", "sanctioned"),
    ("pre-approved loan ready", "pre_approved"),
    ("home loan is currently in process", "in_process"),
    ("paying with own funds", "own_funds"),
    ("not applying for any loan", "none"),
]

VISIT_SNIPPETS = [
    "Can we arrange a site visit this weekend?",
    "Please schedule an in-person walkthrough soon.",
    "Could someone call me back today to discuss details?",
    "Can I visit tomorrow afternoon?"
]

DISTRACTORS = [
    "My current phone number is 9845012345.",
    "Looking for minimum 1350 sqft carpet area.",
    "Currently living on 4th floor.",
    "Expecting builder rate around ₹7200 per sqft.",
    "I have been working in IT for 14 years.",
    "Preferred unit number ending in 5 or 7."
]

SPAM_TEMPLATES = [
    "We provide top SEO rankings and Google Ads leads for your real estate business. Contact info@growleads.biz",
    "Hiring urgent! Senior Sales Executives required for leading builder with attractive commissions. Send resume.",
    "Earn 18% APY on USDT crypto liquidity pool backed by commercial assets. Click bit.ly/crypto-yield",
    "We supply bulk sanitaryware and premium tiles directly from factory at wholesale rates. Call 9988776655.",
    "Exclusive business loan and loan against property available at low interest 8.5%. Reply to connect."
]


def generate_leads(seed: int = 42, count: int = 70) -> List[Dict[str, Any]]:
    rng = random.Random(seed)
    leads: List[Dict[str, Any]] = []

    for i in range(1, count + 1):
        lead_id = f"GEN{i:02d}"
        
        # ~8% spam leads
        if rng.random() < 0.08:
            spam_msg = rng.choice(SPAM_TEMPLATES)
            leads.append({
                "id": lead_id,
                "source": "synthetic",
                "language": "en",
                "message": spam_msg,
                "gold": {
                    "is_spam": True,
                    "primary_location": None,
                    "property_type": None,
                    "budget_lakhs": None,
                    "timeline_months": None,
                    "has_reason": False,
                    "loan_status": "unknown",
                    "visit_or_call_requested": False,
                    "already_visited": False,
                    "ready_to_book": False,
                    "decision_maker": "unknown",
                    "n_questions": 0,
                    "concrete_details_count": 0
                },
                "evidence_phrases": {},
                "ambiguous_fields": []
            })
            continue

        loc = rng.choice(LOCATIONS)
        prop = rng.choice(PROPERTY_TYPES)

        # Budget calculation
        if prop == "1BHK":
            base_budget = rng.choice([40.0, 50.0, 60.0])
        elif prop == "2BHK":
            base_budget = rng.choice([65.0, 75.0, 85.0, 95.0, 110.0])
        elif prop == "3BHK":
            base_budget = rng.choice([120.0, 140.0, 160.0, 180.0, 210.0])
        elif prop == "4BHK":
            base_budget = rng.choice([220.0, 250.0, 280.0, 320.0])
        elif prop == "villa":
            base_budget = rng.choice([250.0, 300.0, 350.0, 450.0])
        else: # plot
            base_budget = rng.choice([45.0, 60.0, 75.0, 90.0])

        b_tmpl, b_parser = rng.choice(BUDGET_TEMPLATES)
        budget_str = b_tmpl(base_budget)
        budget_val = b_parser(base_budget)

        # Timeline
        timeline_snip, timeline_months = rng.choice(TIMELINE_SNIPPETS)

        # Intent / Reason
        has_reason = rng.random() < 0.55
        reason_snip = rng.choice(REASONS) if has_reason else None

        # Financing
        has_loan_info = rng.random() < 0.70
        loan_snip, loan_status = rng.choice(LOAN_SNIPPETS) if has_loan_info else (None, "unknown")

        # Visit / callback request
        visit_requested = rng.random() < 0.50
        visit_snip = rng.choice(VISIT_SNIPPETS) if visit_requested else None

        # Commitment
        already_visited = False
        ready_to_book = False
        if rng.random() < 0.15:
            already_visited = True
        elif rng.random() < 0.10:
            ready_to_book = True

        # Decision maker
        dm_choice = rng.random()
        if dm_choice < 0.12:
            decision_maker = "joint_present"
            dm_snip = "My wife and I will attend together"
        elif dm_choice < 0.22:
            decision_maker = "needs_others"
            dm_snip = "Need to confirm with my father before deciding"
        else:
            decision_maker = "sole"
            dm_snip = None

        # Distractor numbers on 40% of leads
        has_distractor = rng.random() < 0.40
        distractor_snip = rng.choice(DISTRACTORS) if has_distractor else None

        # Build message clauses
        parts = [f"Hi, I am looking for a {prop} in {loc} with a budget of {budget_str}."]
        evidence_phrases: Dict[str, str] = {
            "primary_location": loc,
            "property_type": prop,
            "budget_lakhs": budget_str,
            "timeline_months": timeline_snip
        }

        parts.append(f"Planning to finalize {timeline_snip}.")

        if reason_snip:
            parts.append(f"The reason is {reason_snip}.")
            evidence_phrases["has_reason"] = reason_snip

        if loan_snip:
            parts.append(f"Regarding financing, {loan_snip}.")
            evidence_phrases["loan_status"] = loan_snip

        if already_visited:
            already_snip = "I visited the site previously"
            parts.append(f"{already_snip} and liked the layout.")
            evidence_phrases["already_visited"] = already_snip

        if ready_to_book:
            book_snip = "Ready to proceed with booking token"
            parts.append(f"{book_snip} if terms match.")
            evidence_phrases["ready_to_book"] = book_snip

        if dm_snip:
            parts.append(f"{dm_snip}.")
            evidence_phrases["decision_maker"] = dm_snip

        if distractor_snip:
            parts.append(distractor_snip)

        if visit_snip:
            parts.append(visit_snip)
            evidence_phrases["visit_or_call_requested"] = visit_snip

        full_message = " ".join(parts)
        n_questions = full_message.count("?")

        # Concrete details count: location, type, budget, timeline, loan known, has_reason
        concrete_count = 0
        if loc: concrete_count += 1
        if prop: concrete_count += 1
        if budget_val is not None: concrete_count += 1
        if timeline_months is not None: concrete_count += 1
        if loan_status != "unknown": concrete_count += 1
        if has_reason: concrete_count += 1

        leads.append({
            "id": lead_id,
            "source": "synthetic",
            "language": "en",
            "message": full_message,
            "gold": {
                "is_spam": False,
                "primary_location": loc,
                "property_type": prop,
                "budget_lakhs": budget_val,
                "timeline_months": timeline_months,
                "has_reason": has_reason,
                "loan_status": loan_status,
                "visit_or_call_requested": visit_requested,
                "already_visited": already_visited,
                "ready_to_book": ready_to_book,
                "decision_maker": decision_maker,
                "n_questions": n_questions,
                "concrete_details_count": concrete_count
            },
            "evidence_phrases": evidence_phrases,
            "ambiguous_fields": []
        })

    return leads
