"""
Lead Scoring Engine for Bangalore Real Estate Inbound Leads.
Implements 6-factor deterministic scoring with explainable breakdowns.

Factors:
1. Buying Timeline (0 - 20 pts)
2. Budget Readiness & Market Fit (0 - 20 pts)
3. Purchase Intent & Urgency Drivers (0 - 20 pts)
4. Property Requirement Specificity (0 - 15 pts)
5. Engagement Level & Inquiry Depth (0 - 10 pts)
6. Decision Readiness & Financing Status (0 - 15 pts)

Total Score: 0 - 100
Classification:
- Hot Leads: Score >= 70 (Cadence: Immediate to 24h)
- Warm Leads: Score 40 - 69 (Cadence: 48 - 72h)
- Cold Leads: Score < 40 (Cadence: 14 - 30d automated nurture)
"""

import re
from typing import Dict, Any, List, Tuple

MARKET_PRICE_BENCHMARKS = {
    ("whitefield", "2bhk"): (80, 130),
    ("whitefield", "3bhk"): (130, 220),
    ("whitefield", "villa"): (200, 500),
    ("sarjapur road", "2bhk"): (75, 120),
    ("sarjapur road", "3bhk"): (120, 200),
    ("sarjapur road", "4bhk"): (200, 500),
    ("sarjapur", "2bhk"): (75, 120),
    ("sarjapur", "3bhk"): (120, 200),
    ("sarjapur", "4bhk"): (200, 500),
    ("electronic city", "1bhk"): (40, 65),
    ("electronic city", "2bhk"): (55, 85),
    ("electronic city", "3bhk"): (85, 140),
    ("hebbal", "2bhk"): (100, 160),
    ("hebbal", "3bhk"): (160, 300),
    ("bannerghatta road", "2bhk"): (70, 110),
    ("bannerghatta road", "3bhk"): (110, 180),
    ("bannerghatta", "2bhk"): (70, 110),
    ("devanahalli", "plot"): (40, 75),
    ("devanahalli", "residential plot"): (40, 75),
}

SERVICEABLE_AREAS = [
    "whitefield", "sarjapur", "sarjapur road", "electronic city", "e city", 
    "hebbal", "bannerghatta", "bannerghatta road", "devanahalli", 
    "kanakapura", "kanakapura road", "bellandur", "marathahalli", 
    "indiranagar", "koramangala", "yelahanka", "thanisandra", "varthur", "panathur"
]

def parse_budget_lakhs(budget_str: str, message_str: str) -> float | None:
    combined = f"{budget_str or ''} {message_str or ''}".lower()
    
    # Check Crore
    cr_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:cr|crore|crores)', combined)
    if cr_match:
        return float(cr_match.group(1)) * 100.0
        
    # Check Lakhs
    l_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:l|lac|lacs|lakh|lakhs)', combined)
    if l_match:
        return float(l_match.group(1))
        
    # Pure numbers (e.g. 85, 95, 120, 160)
    num_match = re.search(r'\b(\d{2,3})\b', budget_str or "")
    if num_match:
        val = float(num_match.group(1))
        if 20 <= val <= 500:
            return val
            
    return None

def score_lead(lead_data: Dict[str, Any]) -> Dict[str, Any]:
    timeline_str = (lead_data.get("timeline") or "").lower()
    msg = (lead_data.get("message") or "").lower()
    req = (lead_data.get("property_requirement") or lead_data.get("requirement") or "").lower()
    loc = (lead_data.get("location") or "").lower()
    budget_raw = str(lead_data.get("budget") or "")
    
    signals: List[str] = []
    flags: List[str] = []
    
    # -------------------------------------------------------------
    # Factor 1: Timeline (Max 20)
    # -------------------------------------------------------------
    t_score = 0
    if any(k in timeline_str or k in msg for k in ["within 1 month", "immediate", "urgent", "ready to move", "asap", "this month"]):
        t_score = 20
        signals.append("Immediate buying urgency (< 1 month)")
    elif any(k in timeline_str or k in msg for k in ["2-3 months", "2 to 3 months", "next month", "3 months"]):
        t_score = 15
        signals.append("Near-term buying timeline (2-3 months)")
    elif any(k in timeline_str or k in msg for k in ["3-6 months", "3 to 6 months"]):
        t_score = 10
        signals.append("Mid-term buying window (3-6 months)")
    elif any(k in timeline_str or k in msg for k in ["6-12 months", "6 to 12 months", "next year"]):
        t_score = 5
        signals.append("Longer buying horizon (6-12 months)")
    else:
        t_score = 3
        signals.append("Timeline casual or unstated")
        
    # -------------------------------------------------------------
    # Factor 2: Budget Readiness & Market Fit (Max 20)
    # -------------------------------------------------------------
    b_score = 0
    budget_lakhs = parse_budget_lakhs(budget_raw, msg)
    
    if budget_lakhs is not None:
        # Check against market benchmark
        matched_benchmark = None
        for (m_loc, m_req), (low, high) in MARKET_PRICE_BENCHMARKS.items():
            if m_loc in loc and any(part in req for part in m_req.split()):
                matched_benchmark = (low, high)
                break
                
        if matched_benchmark:
            low, high = matched_benchmark
            if budget_lakhs >= low * 0.9:
                b_score = 20 if budget_lakhs <= high * 1.3 else 18
                signals.append(f"Budget ₹{budget_raw} aligns with {loc} market benchmark")
            else:
                b_score = 5
                flags.append("UNREALISTIC_BUDGET")
                signals.append(f"Budget ₹{budget_raw} is below typical {loc} baseline")
        else:
            b_score = 16 if budget_lakhs >= 60 else 10
            signals.append(f"Stated budget ₹{budget_raw}")
    else:
        b_score = 3
        signals.append("Budget not disclosed")
        
    # -------------------------------------------------------------
    # Factor 3: Purchase Intent & Urgency Drivers (Max 20)
    # -------------------------------------------------------------
    i_score = 0
    intent_drivers = 0
    if any(k in msg for k in ["relocat", "transfer", "joining", "job", "office"]):
        intent_drivers += 1
        signals.append("Relocation / employment driver identified")
    if any(k in msg for k in ["rent", "lease", "leaving rent", "moving out"]):
        intent_drivers += 1
        signals.append("Rental lease expiration driver")
    if any(k in msg for k in ["ready to register", "cheque", "token", "loan sanctioned", "pre-approved", "approved loan"]):
        intent_drivers += 1
        signals.append("Financing / down payment readiness detected")
    if any(k in msg for k in ["visit", "inspect", "walkthrough", "see unit", "saturday", "sunday", "tomorrow"]):
        intent_drivers += 1
        signals.append("Active site visit requested")
        
    if intent_drivers >= 3:
        i_score = 20
    elif intent_drivers == 2:
        i_score = 16
    elif intent_drivers == 1:
        i_score = 12
    else:
        i_score = 6 if len(msg.split()) > 6 else 2

    # -------------------------------------------------------------
    # Factor 4: Property Specificity (Max 15)
    # -------------------------------------------------------------
    r_score = 0
    req_pts = 0
    if any(bhk in req for bhk in ["1bhk", "2bhk", "3bhk", "4bhk", "villa", "penthouse", "plot"]):
        req_pts += 5
    if any(m in req or m in msg for m in ["ready to move", "rtm", "under construction", "gated community"]):
        req_pts += 4
    if any(a in loc for a in SERVICEABLE_AREAS):
        req_pts += 6
        signals.append(f"Location '{loc}' in active serviceable territory")
    else:
        req_pts += 2
        flags.append("UNVERIFIED_LOCATION")
        
    r_score = min(15, req_pts)

    # -------------------------------------------------------------
    # Factor 5: Engagement Level & Inquiry Depth (Max 10)
    # -------------------------------------------------------------
    word_count = len(msg.split())
    if word_count >= 25:
        e_score = 10
    elif word_count >= 15:
        e_score = 8
    elif word_count >= 6:
        e_score = 6
    else:
        e_score = 2

    # -------------------------------------------------------------
    # Factor 6: Decision Readiness & Financing (Max 15)
    # -------------------------------------------------------------
    d_score = 0
    if any(k in msg for k in ["sanction", "hdfc", "sbi", "icici", "pre-approved", "loan approved", "ready funds", "cash ready"]):
        d_score = 15
        signals.append("Verified financing readiness (pre-sanctioned / ready capital)")
    elif any(k in msg for k in ["loan", "bank", "downpayment", "down payment", "funding"]):
        d_score = 10
        signals.append("Financing plan in progress")
    else:
        d_score = 5

    total_score = min(100, max(10, t_score + b_score + i_score + r_score + e_score + d_score))

    # Priority Classification
    if total_score >= 70:
        priority = "Hot"
        urgency_label = "Call within 15 min" if t_score >= 18 else "Call within 24 hours"
    elif total_score >= 40:
        priority = "Warm"
        urgency_label = "Cadence 48-72h"
    else:
        priority = "Cold"
        urgency_label = "Automated nurture (14-30d)"

    return {
        "score": total_score,
        "priority": priority,
        "urgency_label": urgency_label,
        "breakdown": {
            "timeline": {"label": "Buying Timeline", "score": t_score, "max": 20},
            "budget": {"label": "Budget Readiness", "score": b_score, "max": 20},
            "intent": {"label": "Purchase Intent", "score": i_score, "max": 20},
            "requirement": {"label": "Property Specificity", "score": r_score, "max": 15},
            "engagement": {"label": "Inquiry Depth", "score": e_score, "max": 10},
            "readiness": {"label": "Decision Readiness", "score": d_score, "max": 15}
        },
        "signals": signals,
        "flags": flags
    }
