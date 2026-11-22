"""
Deterministic Lead Scoring Calculator implementing GUIDELINES.md.
Maps structured lead facts to ground-truth scores, factor breakdowns, signals, flags, and tags.
"""

from typing import Dict, Any, List, Optional, Tuple

VALID_BANGALORE_LOCATIONS = {
    "whitefield", "sarjapur", "sarjapur road", "electronic city", "e-city", "ecity",
    "hebbal", "bannerghatta", "bannerghatta road", "devanahalli",
    "kanakapura", "kanakapura road", "bellandur", "marathahalli",
    "indiranagar", "koramangala", "yelahanka", "thanisandra", "varthur", "panathur",
    "kadugodi", "budigere cross", "bagalur", "mysore road", "tumkur road",
    "btm layout", "domlur", "cv raman nagar", "kr puram", "jp nagar", "jayanagar",
    "rajajinagar", "malleshwaram", "bangalore", "bengaluru"
}

MARKET_PRICE_BENCHMARKS: Dict[Tuple[str, str], Tuple[float, float]] = {
    ("whitefield", "2bhk"): (80.0, 130.0),
    ("whitefield", "3bhk"): (130.0, 220.0),
    ("whitefield", "4bhk"): (220.0, 450.0),
    ("whitefield", "villa"): (250.0, 600.0),
    ("sarjapur road", "2bhk"): (75.0, 120.0),
    ("sarjapur road", "3bhk"): (120.0, 200.0),
    ("sarjapur road", "4bhk"): (200.0, 450.0),
    ("sarjapur", "2bhk"): (75.0, 120.0),
    ("sarjapur", "3bhk"): (120.0, 200.0),
    ("sarjapur", "villa"): (200.0, 500.0),
    ("electronic city", "1bhk"): (40.0, 65.0),
    ("electronic city", "2bhk"): (55.0, 85.0),
    ("electronic city", "3bhk"): (85.0, 140.0),
    ("hebbal", "2bhk"): (100.0, 160.0),
    ("hebbal", "3bhk"): (160.0, 300.0),
    ("bannerghatta road", "2bhk"): (70.0, 110.0),
    ("bannerghatta road", "3bhk"): (110.0, 180.0),
    ("bannerghatta", "2bhk"): (70.0, 110.0),
    ("bannerghatta", "3bhk"): (110.0, 180.0),
    ("devanahalli", "plot"): (40.0, 85.0),
    ("devanahalli", "villa"): (150.0, 350.0),
}


def is_serviceable_location(loc: Optional[str]) -> bool:
    if not loc:
        return True  # Location unspecified is not disqualified, just low specificity
    loc_clean = loc.strip().lower()
    return any(area in loc_clean for area in VALID_BANGALORE_LOCATIONS)


def compute_gold_score(facts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes deterministic gold score and tag from a dictionary of gold facts.
    Gold fields per GUIDELINES.md:
      - is_spam (bool)
      - primary_location (str | None)
      - property_type (str | None)
      - budget_lakhs (float | None)
      - timeline_months (int | None)
      - has_reason (bool)
      - loan_status (str: sanctioned, pre_approved, in_process, none, own_funds, unknown)
      - visit_or_call_requested (bool)
      - already_visited (bool)
      - ready_to_book (bool)
      - decision_maker (str: sole, joint_present, needs_others, unknown)
      - n_questions (int)
      - concrete_details_count (int)
    """
    is_spam = bool(facts.get("is_spam", False))
    loc = facts.get("primary_location")
    prop_type = (facts.get("property_type") or "").strip().lower()
    budget = facts.get("budget_lakhs")
    timeline = facts.get("timeline_months")
    has_reason = bool(facts.get("has_reason", False))
    loan_status = str(facts.get("loan_status", "unknown")).lower()
    visit_or_call = bool(facts.get("visit_or_call_requested", False))
    already_visited = bool(facts.get("already_visited", False))
    ready_to_book = bool(facts.get("ready_to_book", False))
    decision_maker = str(facts.get("decision_maker", "unknown")).lower()
    n_questions = int(facts.get("n_questions", 0))

    signals: List[str] = []
    flags: List[str] = []

    # 1. Spam check
    if is_spam:
        flags.append("SPAM_SENDER")
        return {
            "score": 0,
            "tag": "Disqualified",
            "breakdown": {
                "timeline": 0, "budget": 0, "intent": 0,
                "requirement": 0, "engagement": 0, "readiness": 0
            },
            "signals": ["Spam or vendor inquiry, not an authentic buyer"],
            "flags": flags
        }

    # 2. Serviceability check (out of area)
    if loc and not is_serviceable_location(loc):
        flags.append("OUT_OF_SERVICE_AREA")
        return {
            "score": 15,
            "tag": "Disqualified",
            "breakdown": {
                "timeline": 0, "budget": 0, "intent": 0,
                "requirement": 0, "engagement": 0, "readiness": 0
            },
            "signals": [f"Location '{loc}' is outside Bangalore serviceable micro-markets"],
            "flags": flags
        }

    # -------------------------------------------------------------------------
    # Factor 1: Timeline (0 - 20)
    # -------------------------------------------------------------------------
    t_score = 3
    if timeline is not None:
        if timeline <= 1:
            t_score = 20
            signals.append("Immediate buying timeline (within 1 month)")
        elif timeline <= 3:
            t_score = 15
            signals.append("Near-term buying timeline (2-3 months)")
        elif timeline <= 6:
            t_score = 10
            signals.append("Mid-term buying timeline (3-6 months)")
        elif timeline <= 12:
            t_score = 5
            signals.append("Long-term horizon (6-12 months)")
        else:
            t_score = 3
            signals.append("Long horizon (>12 months)")
    else:
        signals.append("Timeline unspecified")

    # -------------------------------------------------------------------------
    # Factor 2: Budget Readiness & Benchmark Alignment (0 - 20)
    # -------------------------------------------------------------------------
    b_score = 3
    if budget is not None and budget > 0:
        matched_bench: Optional[Tuple[float, float]] = None
        if loc:
            loc_l = loc.lower()
            for (b_loc, b_req), (low, high) in MARKET_PRICE_BENCHMARKS.items():
                if b_loc in loc_l and (b_req in prop_type or prop_type in b_req):
                    matched_bench = (low, high)
                    break

        if matched_bench:
            low, high = matched_bench
            if budget >= low * 0.85:
                b_score = 20 if budget <= high * 1.5 else 18
                signals.append(f"Budget ₹{budget:.0f}L is realistic for {loc} {prop_type}")
            else:
                b_score = 5
                flags.append("UNREALISTIC_BUDGET")
                signals.append(f"Budget ₹{budget:.0f}L is below {loc} benchmark (₹{low:.0f}-{high:.0f}L)")
        else:
            if budget >= 75:
                b_score = 18
                signals.append(f"Disclosed strong budget of ₹{budget:.0f}L")
            elif budget >= 45:
                b_score = 14
                signals.append(f"Disclosed standard budget of ₹{budget:.0f}L")
            else:
                b_score = 8
                signals.append(f"Disclosed entry budget of ₹{budget:.0f}L")
    else:
        signals.append("Budget not stated")

    # -------------------------------------------------------------------------
    # Factor 3: Purchase Intent & Urgency Drivers (0 - 20)
    # -------------------------------------------------------------------------
    intent_drivers = 0
    if has_reason:
        intent_drivers += 1
        signals.append("Identified concrete purchase trigger (job/lease/family)")
    if visit_or_call:
        intent_drivers += 1
        signals.append("Direct visit or callback requested")
    if already_visited or ready_to_book:
        intent_drivers += 1
        signals.append("High commitment: visited or ready to book")
    if timeline is not None and timeline <= 1:
        intent_drivers += 1

    if intent_drivers >= 3:
        i_score = 20
    elif intent_drivers == 2:
        i_score = 16
    elif intent_drivers == 1:
        i_score = 12
    else:
        i_score = 4

    # -------------------------------------------------------------------------
    # Factor 4: Requirement Specificity (0 - 15)
    # -------------------------------------------------------------------------
    r_pts = 0
    if prop_type:
        r_pts += 5
    if loc and is_serviceable_location(loc):
        r_pts += 6
    else:
        r_pts += 2
    if facts.get("ready_to_move") or "rtm" in str(facts):
        r_pts += 4
    else:
        r_pts += 2
    r_score = min(15, r_pts)

    # -------------------------------------------------------------------------
    # Factor 5: Engagement Level & Inquiry Depth (0 - 10)
    # -------------------------------------------------------------------------
    if n_questions >= 2:
        e_score = 10
        signals.append(f"High engagement with {n_questions} questions asked")
    elif n_questions == 1:
        e_score = 8
    elif facts.get("concrete_details_count", 0) >= 4:
        e_score = 7
    else:
        e_score = 4

    # -------------------------------------------------------------------------
    # Factor 6: Decision Readiness & Financing (0 - 15)
    # -------------------------------------------------------------------------
    if loan_status in ("sanctioned", "own_funds"):
        d_score = 15
        signals.append(f"Immediate capital readiness: {loan_status}")
    elif loan_status == "pre_approved":
        d_score = 13
        signals.append("Pre-approved loan in place")
    elif loan_status == "in_process":
        d_score = 10
        signals.append("Loan currently in process")
    elif loan_status == "none":
        d_score = 6
        signals.append("Self-financing or loan not yet initiated")
    else:
        d_score = 5
        signals.append("Financing status unknown")

    if decision_maker == "needs_others":
        d_score = max(3, d_score - 3)
        flags.append("DEPENDENT_DECISION_MAKER")
        signals.append("Buyer needs approval from outside decision maker")

    # Final score aggregation
    total_score = min(100, max(10, t_score + b_score + i_score + r_score + e_score + d_score))

    # Tag assignment per GUIDELINES.md:
    # Hot: 70+
    # Warm: 40-69
    # Cold: < 40
    # Disqualified: spam or out of area
    if total_score >= 70:
        tag = "Hot"
    elif total_score >= 40:
        tag = "Warm"
    else:
        tag = "Cold"

    return {
        "score": total_score,
        "tag": tag,
        "breakdown": {
            "timeline": t_score,
            "budget": b_score,
            "intent": i_score,
            "requirement": r_score,
            "engagement": e_score,
            "readiness": d_score
        },
        "signals": signals,
        "flags": flags
    }
