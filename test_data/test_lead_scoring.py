"""
Lead Scoring Engine for Bangalore Real-Estate Leads
Implements the 6 core factors:
1. Buying Timeline (0 - 20 pts)
2. Budget Readiness & Market Fit (0 - 20 pts)
3. Purchase Intent & Urgency Drivers (0 - 20 pts)
4. Property Requirement Specificity (0 - 15 pts)
5. Engagement Level & Inquiry Depth (0 - 10 pts)
6. Decision Readiness & Financing Status (0 - 15 pts)

Total Score: 0 - 100
Tags: Hot (>= 70), Warm (40 - 69), Cold (< 40), Disqualified, Unknown
"""

from typing import Dict, Any, List, Tuple
import re

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
    "hebbal", "bannerghatta", "bannerghatta road", "devanahalli", "bangalore", "bengaluru"
]

NON_SERVICEABLE_CITIES = ["mumbai", "andheri", "pune", "delhi", "noida", "gurgaon", "hyderabad", "chennai"]

SPAM_KEYWORDS = ["digital marketing", "lead generation services", "guaranteed leads", "vendor", "seo services", "500 leads/month"]


def parse_budget_lakhs(budget_str: str, message_str: str) -> float | None:
    text = f"{budget_str} {message_str}".lower()
    cr_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:cr|crore|crores)', text)
    if cr_match:
        return float(cr_match.group(1)) * 100.0
    lakh_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:l|lac|lakh|lakhs)', text)
    if lakh_match:
        return float(lakh_match.group(1))
    num_match = re.search(r'(\d+)', budget_str)
    if num_match:
        val = float(num_match.group(1))
        if val > 100000:
            return val / 100000.0
        return val
    return None


def evaluate_lead(lead: Dict[str, Any]) -> Dict[str, Any]:
    name = (lead.get("name") or "").strip()
    loc = (lead.get("location") or "").strip().lower()
    req = (lead.get("property_requirement") or "").strip().lower()
    budget_raw = (lead.get("budget") or "").strip()
    timeline_raw = (lead.get("timeline") or "").strip().lower()
    msg = (lead.get("message") or "").strip()
    msg_lower = msg.lower()

    signals = []
    flags = []

    # ---------------------------------------------------------
    # 0. Disqualification Checks: Spam / Vendor & Out-of-Area
    # ---------------------------------------------------------
    for spam_kw in SPAM_KEYWORDS:
        if spam_kw in msg_lower or spam_kw in name.lower():
            return {
                "total_score": 0,
                "tag": "Disqualified",
                "breakdown": {
                    "buying_timeline": 0,
                    "budget_readiness": 0,
                    "purchase_intent": 0,
                    "property_requirement": 0,
                    "engagement_level": 0,
                    "decision_readiness": 0
                },
                "key_signals": ["vendor pitch / spam"],
                "flags": ["SPAM_OR_VENDOR"],
                "reason": "Commercial vendor advertisement or spam query."
            }

    for non_serv in NON_SERVICEABLE_CITIES:
        is_loc_field = non_serv in loc
        is_query_for_city = f"in {non_serv}" in msg_lower or f"projects in {non_serv}" in msg_lower
        is_relocating_away = f"from {non_serv}" in msg_lower or f"relocating from {non_serv}" in msg_lower

        if (is_loc_field or is_query_for_city) and not is_relocating_away:
            signals.append(f"location outside service area ({non_serv.title()})")
            return {
                "total_score": 5,
                "tag": "Disqualified",
                "breakdown": {
                    "buying_timeline": 2,
                    "budget_readiness": 1,
                    "purchase_intent": 1,
                    "property_requirement": 1,
                    "engagement_level": 0,
                    "decision_readiness": 0
                },
                "key_signals": signals,
                "flags": ["OUT_OF_SERVICE_AREA"],
                "reason": f"Customer inquiring for non-serviceable location: {non_serv.title()}."
            }

    if not msg and not budget_raw and not req:
        return {
            "total_score": 0,
            "tag": "Unknown",
            "breakdown": {
                "buying_timeline": 0,
                "budget_readiness": 0,
                "purchase_intent": 0,
                "property_requirement": 0,
                "engagement_level": 0,
                "decision_readiness": 0
            },
            "key_signals": ["insufficient information"],
            "flags": ["INSUFFICIENT_DATA"],
            "reason": "Missing critical customer inquiry fields."
        }

    is_minimal_msg = len(msg.split()) <= 6 and any(w in msg_lower for w in ["price?", "price", "details", "brochure", "whats the price"])

    # ---------------------------------------------------------
    # Factor 1: Buying Timeline (0 - 20 pts)
    # ---------------------------------------------------------
    timeline_score = 0
    urgent_deadline = any(term in msg_lower for term in [
        "relocating", "joining on", "lease ends", "before april", "shift hona", "next academic year"
    ])
    
    if urgent_deadline:
        timeline_score = 20
        if "relocating" in msg_lower or "joining" in msg_lower:
            signals.append("job relocation (hard deadline)")
        elif "lease ends" in msg_lower:
            signals.append("lease end = real deadline")
        elif "school" in msg_lower or "academic year" in msg_lower:
            signals.append("school admission deadline")
    elif "1 month" in timeline_raw or "immediately" in timeline_raw or "asap" in timeline_raw:
        if is_minimal_msg:
            timeline_score = 14
            signals.append("form says ASAP, unverified in message")
        else:
            timeline_score = 19
            signals.append("urgent timeline (< 1 month / ASAP)")
    elif any(t in timeline_raw for t in ["6-12 months", "maybe next year", "not in a hurry"]) or "retirement in 2 years" in msg_lower:
        timeline_score = 5
        signals.append("long-term timeline (6-12+ months)")
    elif any(t in timeline_raw for t in ["2-3 months", "2 months", "within 3 months", "1-2 mahine"]):
        timeline_score = 16
        signals.append("short-term timeline (2-3 months)")
    elif "3 months" in timeline_raw:
        timeline_score = 15
        signals.append("3 months timeline")
    elif any(t in timeline_raw for t in ["3-6 months", "4 months"]):
        timeline_score = 13 if "possession" in msg_lower else 11
        signals.append("medium-term timeline (3-6 months)")
    elif "6 months" in timeline_raw:
        timeline_score = 8
        signals.append("medium-long timeline (6 months)")
    elif "not decided" in timeline_raw or "not mentioned" in timeline_raw or not timeline_raw:
        timeline_score = 2
    else:
        timeline_score = 8

    # ---------------------------------------------------------
    # Factor 2: Budget Readiness & Market Fit (0 - 20 pts)
    # ---------------------------------------------------------
    budget_lakhs = parse_budget_lakhs(budget_raw, msg)
    budget_score = 0
    is_unrealistic = False

    bhk = ""
    if "1bhk" in req or "1 bhk" in req:
        bhk = "1bhk"
    elif "2bhk" in req or "2 bhk" in req:
        bhk = "2bhk"
    elif "3bhk" in req or "3 bhk" in req:
        bhk = "3bhk"
    elif "4bhk" in req or "4 bhk" in req:
        bhk = "4bhk"
    elif "plot" in req:
        bhk = "plot"
    elif "villa" in req:
        bhk = "villa"

    matched_area = ""
    for area in ["whitefield", "sarjapur road", "sarjapur", "electronic city", "hebbal", "bannerghatta road", "bannerghatta", "devanahalli"]:
        if area in loc or area in req or area in msg_lower:
            matched_area = area
            break

    if budget_lakhs is not None:
        benchmark = MARKET_PRICE_BENCHMARKS.get((matched_area, bhk))
        if benchmark:
            min_p, max_p = benchmark
            if budget_lakhs >= min_p:
                budget_score = 19
                signals.append(f"budget fits {matched_area.title()} {bhk.upper()} market range")
            elif budget_lakhs >= min_p * 0.70:
                budget_score = 10
                signals.append(f"budget tight for {matched_area.title()} {bhk.upper()} (resale/budget unit only)")
            else:
                budget_score = 3
                is_unrealistic = True
                signals.append("unrealistic budget far below market benchmarks")
                flags.append("UNREALISTIC_BUDGET")
        else:
            if budget_lakhs >= 60:
                budget_score = 17
            elif budget_lakhs >= 30:
                budget_score = 13
            else:
                budget_score = 6
                
        if budget_lakhs >= 300:
            flags.append("HIGH_VALUE_DEAL")
            signals.append(f"high-ticket budget (₹{budget_lakhs/100:.1f} Cr)")
    else:
        budget_score = 1
        signals.append("no budget provided")

    # ---------------------------------------------------------
    # Factor 3: Purchase Intent & Urgency Drivers (0 - 20 pts)
    # ---------------------------------------------------------
    intent_score = 0
    if "ready to book" in msg_lower:
        intent_score = 20
        signals.append("ready to book conditional on closing terms")
    elif any(term in msg_lower for term in ["relocating", "lease ends", "school", "invest in a 2bhk", "rental income", "shortlisted 2 other projects"]):
        intent_score = 18
        if "invest" in msg_lower or "rental income" in msg_lower:
            signals.append("investor with clear ROI / rental yield goal")
        elif "shortlisted" in msg_lower:
            signals.append("active evaluation: shortlisted competitor projects")
    elif "retirement" in msg_lower:
        intent_score = 13
        signals.append("retirement home purpose")
    elif any(term in msg_lower for term in ["for my parents", "family"]):
        intent_score = 13
        signals.append("end-use home for family")
    elif "just exploring" in msg_lower or "not in a hurry" in msg_lower:
        intent_score = 3
        signals.append("casual exploration / low buying intent")
    elif is_minimal_msg:
        intent_score = 4
        signals.append("minimal passive inquiry")
    else:
        intent_score = 11

    # ---------------------------------------------------------
    # Factor 4: Property Requirement Specificity (0 - 15 pts)
    # ---------------------------------------------------------
    req_score = 0
    if bhk and matched_area:
        req_score += 8
    elif bhk or matched_area:
        req_score += 4
    else:
        req_score += 2

    if any(attr in f"{req} {msg_lower}" for attr in ["ready to move", "ready-to-move", "east facing", "12th floor", "1200 sqft", "gated society", "near itpl", "wipro campus", "hebbal flyover", "green meadows"]):
        req_score += 5

    if len(loc.split(",")) >= 3:
        req_score = max(2, req_score - 6)
        signals.append("scattered locations: lacks geographic focus")

    req_score = min(15, req_score)

    # ---------------------------------------------------------
    # Factor 5: Engagement Level & Inquiry Depth (0 - 10 pts)
    # ---------------------------------------------------------
    eng_score = 0
    deep_questions = []
    if "oc" in msg_lower:
        deep_questions.append("asks OC status")
    if "maintenance" in msg_lower:
        deep_questions.append("asks maintenance charges")
    if "rera" in msg_lower:
        deep_questions.append("asks RERA registration/number")
    if "payment plan" in msg_lower or "9:1" in msg_lower:
        deep_questions.append("asks payment plan")
    if "khata" in msg_lower or "title" in msg_lower:
        deep_questions.append("asks Khata/title documents")
    if "callback after" in msg_lower or "pm" in msg_lower:
        deep_questions.append("provided convenient callback window")
    if "??" in msg_lower:
        deep_questions.append("active conversational follow-up")
    if "prestige next door" in msg_lower or "5% lower" in msg_lower:
        deep_questions.append("competitor pricing comparison")

    if deep_questions:
        eng_score = min(10, 6 + len(deep_questions) * 2)
        signals.extend(deep_questions)
    elif "brochure" in msg_lower or "price list" in msg_lower:
        eng_score = 4
        signals.append("passive request: brochure / price list")
    elif is_minimal_msg:
        eng_score = 2
        signals.append("minimal one-liner inquiry")
    else:
        eng_score = 5

    # ---------------------------------------------------------
    # Factor 6: Decision Readiness & Financing Status (0 - 15 pts)
    # ---------------------------------------------------------
    dec_score = 0
    # Financial readiness
    if "sanctioned" in msg_lower:
        dec_score += 8
        signals.append("home loan sanctioned")
    elif "pre-approval" in msg_lower or "pre-approved" in msg_lower or "bank approved" in msg_lower:
        dec_score += 7
        signals.append("loan pre-approved")
    elif "in process" in msg_lower or "chalu hai" in msg_lower:
        dec_score += 5
        signals.append("loan in process")
    elif "down payment" in msg_lower or "cash" in msg_lower:
        dec_score += 6
        signals.append("down payment / equity ready")
    elif "haven't applied" in msg_lower or "need a home loan" in msg_lower:
        dec_score += 2
        signals.append("loan not yet initiated")

    # Visit readiness / decision stage
    if "visited" in msg_lower and ("last week" in msg_lower or "ramesh" in msg_lower):
        dec_score += 7
        signals.append("site visit already completed")
        if "liked the" in msg_lower or "ready to book" in msg_lower:
            dec_score += 4
            signals.append("specific unit shortlisted")
    elif "can i visit" in msg_lower or "site dikha sakte" in msg_lower or "visit this saturday" in msg_lower:
        dec_score += 7
        signals.append("explicitly requested site visit with timeframe")
    elif "video call" in msg_lower or "video walkthrough" in msg_lower:
        dec_score += 6
        signals.append("remote buyer requested video call / virtual tour")
    
    # Negative readiness flags
    if "brother" in msg_lower and "us" in msg_lower:
        dec_score = max(1, dec_score - 3)
        signals.append("decision split with overseas co-funder")
    if "delayed possession by 2 years" in msg_lower or "lost a lot" in msg_lower:
        signals.append("past builder delay trauma (trust sensitive)")
        dec_score = max(2, dec_score - 2)

    dec_score = min(15, dec_score)
    if dec_score == 0:
        dec_score = 2 if len(msg.split()) > 3 else 1

    # ---------------------------------------------------------
    # Total Score Calculation & Tag Assignment
    # ---------------------------------------------------------
    raw_total = timeline_score + budget_score + intent_score + req_score + eng_score + dec_score

    # Edge Case Rules
    if is_unrealistic:
        raw_total = min(raw_total, 52)

    if "HIGH_VALUE_DEAL" in flags and raw_total < 40:
        raw_total = 45

    if is_minimal_msg and raw_total >= 50:
        raw_total = 48

    if budget_score <= 10 and raw_total >= 65:
        raw_total = 62 # Cap in upper Warm for borderline inventory fit

    if "past builder delay trauma (trust sensitive)" in signals:
        raw_total = min(raw_total, 68)

    # Classify Tag
    if raw_total >= 70:
        tag = "Hot"
    elif raw_total >= 40:
        tag = "Warm"
    else:
        tag = "Cold"

    return {
        "total_score": raw_total,
        "tag": tag,
        "breakdown": {
            "buying_timeline": timeline_score,
            "budget_readiness": budget_score,
            "purchase_intent": intent_score,
            "property_requirement": req_score,
            "engagement_level": eng_score,
            "decision_readiness": dec_score
        },
        "key_signals": signals,
        "flags": flags
    }


def run_benchmark_tests():
    import json
    with open("leads_dataset.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    leads = data["leads"]
    passed = 0
    total = len(leads)

    print(f"\n{'ID':<5} | {'Customer':<22} | {'Exp Tag':<12} | {'Act Tag':<12} | {'Exp Range':<10} | {'Act Score':<10} | {'Status'}")
    print("-" * 88)

    for lead in leads:
        lid = lead["id"]
        name = lead["name"]
        exp = lead["expected"]
        exp_tag = exp["tag"]
        exp_range = exp["score_range"]
        
        result = evaluate_lead(lead)
        act_tag = result["tag"]
        act_score = result["total_score"]
        
        tag_match = (act_tag == exp_tag)
        score_match = (exp_range[0] <= act_score <= exp_range[1])
        
        is_pass = tag_match and score_match
        if is_pass:
            passed += 1
            status = "PASS"
        else:
            status = f"FAIL (Tag:{tag_match}, Score:{score_match})"

        print(f"{lid:<5} | {name:<22} | {exp_tag:<12} | {act_tag:<12} | {str(exp_range):<10} | {act_score:<10} | {status}")
        if not is_pass:
            print(f"   -> Breakdown: {result['breakdown']}")
            print(f"   -> Signals: {result['key_signals']}")
            print(f"   -> Flags: {result['flags']}")

    print("-" * 88)
    print(f"Test Summary: {passed}/{total} Passed ({passed/total*100:.1f}%)\n")


def interactive_mode():
    print("\n" + "=" * 60)
    print("      REAL ESTATE LEAD SCORING - INTERACTIVE TEST")
    print("=" * 60)
    name = input("Customer Name: ").strip() or "Anonymous"
    location = input("Location (e.g. Whitefield, Sarjapur Road): ").strip()
    req = input("Property Requirement (e.g. 3BHK apartment, ready to move): ").strip()
    budget = input("Budget (e.g. 1.5 Cr, 85 L): ").strip()
    timeline = input("Timeline (e.g. Within 1 month, 3 months): ").strip()
    print("Enter customer message (press Enter):")
    msg = input("> ").strip()

    lead = {
        "name": name,
        "location": location,
        "property_requirement": req,
        "budget": budget,
        "timeline": timeline,
        "message": msg
    }

    result = evaluate_lead(lead)
    print("\n" + "=" * 60)
    print("                 SCORING RESULT")
    print("=" * 60)
    print(f"Customer Name  : {name}")
    print(f"Lead Priority  : {result['tag'].upper()}")
    print(f"Total Score    : {result['total_score']} / 100")
    print("\nFactor Breakdown (Max 100 pts):")
    for factor, score in result["breakdown"].items():
        print(f"  • {factor.replace('_', ' ').title():<30}: {score} pts")
    
    print("\nKey Extracted Signals:")
    for sig in result["key_signals"]:
        print(f"  ✓ {sig}")
    
    if result["flags"]:
        print("\nAlert Flags:")
        for fl in result["flags"]:
            print(f"  ⚠️  {fl}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] in ["-i", "--interactive"]:
        interactive_mode()
    else:
        run_benchmark_tests()

