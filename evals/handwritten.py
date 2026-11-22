"""
Handwritten Benchmark Leads (29 diverse real/tricky leads).
Written by hand with gold facts and verifiable evidence phrases per GUIDELINES.md.
"""

from typing import List, Dict, Any

HANDWRITTEN_LEADS: List[Dict[str, Any]] = [
    {
        "id": "HW01",
        "source": "handwritten",
        "language": "en",
        "message": "Hi, I am relocating to Bangalore next month for my new job at ITPL. Looking for a ready-to-move 3BHK in Whitefield within 1.5 Cr. My loan is sanctioned by HDFC. Can we visit this Saturday to finalize?",
        "gold": {
            "is_spam": False,
            "primary_location": "Whitefield",
            "property_type": "3BHK",
            "budget_lakhs": 150.0,
            "timeline_months": 1,
            "has_reason": True,
            "loan_status": "sanctioned",
            "visit_or_call_requested": True,
            "already_visited": False,
            "ready_to_book": False,
            "decision_maker": "sole",
            "n_questions": 1,
            "concrete_details_count": 6
        },
        "evidence_phrases": {
            "primary_location": "Whitefield",
            "property_type": "3BHK",
            "budget_lakhs": "1.5 Cr",
            "timeline_months": "next month",
            "has_reason": "relocating to Bangalore next month for my new job at ITPL",
            "loan_status": "loan is sanctioned",
            "visit_or_call_requested": "Can we visit this Saturday to finalize?"
        },
        "ambiguous_fields": []
    },
    {
        "id": "HW02",
        "source": "handwritten",
        "language": "en",
        "message": "Hello, our current rental lease is ending in 30 days. We urgently need a 3BHK flat on Sarjapur Road up to 1.4 Cr. We have a pre-approved loan from SBI. Please schedule an inspection call or site visit soon.",
        "gold": {
            "is_spam": False,
            "primary_location": "Sarjapur Road",
            "property_type": "3BHK",
            "budget_lakhs": 140.0,
            "timeline_months": 1,
            "has_reason": True,
            "loan_status": "pre_approved",
            "visit_or_call_requested": True,
            "already_visited": False,
            "ready_to_book": False,
            "decision_maker": "sole",
            "n_questions": 0,
            "concrete_details_count": 6
        },
        "evidence_phrases": {
            "primary_location": "Sarjapur Road",
            "property_type": "3BHK",
            "budget_lakhs": "1.4 Cr",
            "timeline_months": "30 days",
            "has_reason": "rental lease is ending in 30 days",
            "loan_status": "pre-approved loan",
            "visit_or_call_requested": "Please schedule an inspection call or site visit soon"
        },
        "ambiguous_fields": []
    },
    {
        "id": "HW03",
        "source": "handwritten",
        "language": "en",
        "message": "Looking for 2BHK apartment in Electronic City near Infosys campus. Budget around 70 Lakhs, planning to move within 3 months. Bank loan application is currently in process.",
        "gold": {
            "is_spam": False,
            "primary_location": "Electronic City",
            "property_type": "2BHK",
            "budget_lakhs": 70.0,
            "timeline_months": 3,
            "has_reason": False,
            "loan_status": "in_process",
            "visit_or_call_requested": False,
            "already_visited": False,
            "ready_to_book": False,
            "decision_maker": "sole",
            "n_questions": 0,
            "concrete_details_count": 5
        },
        "evidence_phrases": {
            "primary_location": "Electronic City",
            "property_type": "2BHK",
            "budget_lakhs": "70 Lakhs",
            "timeline_months": "within 3 months",
            "loan_status": "in process"
        },
        "ambiguous_fields": []
    },
    {
        "id": "HW04",
        "source": "handwritten",
        "language": "en",
        "message": "Hi, just casually checking 2BHK options in Bangalore. What are the starting prices in your projects?",
        "gold": {
            "is_spam": False,
            "primary_location": "Bangalore",
            "property_type": "2BHK",
            "budget_lakhs": None,
            "timeline_months": None,
            "has_reason": False,
            "loan_status": "unknown",
            "visit_or_call_requested": False,
            "already_visited": False,
            "ready_to_book": False,
            "decision_maker": "sole",
            "n_questions": 1,
            "concrete_details_count": 2
        },
        "evidence_phrases": {
            "primary_location": "Bangalore",
            "property_type": "2BHK"
        },
        "ambiguous_fields": []
    },
    {
        "id": "HW05",
        "source": "handwritten",
        "language": "en",
        "message": "We offer best SEO and digital marketing services for real estate builders. Generate 500 leads per week guaranteed. Contact sales@digiboost.example.com",
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
    },
    {
        "id": "HW06",
        "source": "handwritten",
        "language": "en",
        "message": "Looking for 2BHK near Hinjewadi IT park in Pune. Budget is 65 Lakhs, possession in 6 months.",
        "gold": {
            "is_spam": False,
            "primary_location": "Pune",
            "property_type": "2BHK",
            "budget_lakhs": 65.0,
            "timeline_months": 6,
            "has_reason": False,
            "loan_status": "unknown",
            "visit_or_call_requested": False,
            "already_visited": False,
            "ready_to_book": False,
            "decision_maker": "sole",
            "n_questions": 0,
            "concrete_details_count": 4
        },
        "evidence_phrases": {
            "primary_location": "Pune",
            "property_type": "2BHK",
            "budget_lakhs": "65 Lakhs",
            "timeline_months": "6 months"
        },
        "ambiguous_fields": []
    },
    {
        "id": "HW07",
        "source": "handwritten",
        "language": "hinglish",
        "message": "Namaste, mujhe Whitefield me 2BHK chahiye within 80 Lakhs. Next month company transfer ho raha hai. SBI se loan sanctioned hai. Kya Saturday ko visit arrange kar sakte ho?",
        "gold": {
            "is_spam": False,
            "primary_location": "Whitefield",
            "property_type": "2BHK",
            "budget_lakhs": 80.0,
            "timeline_months": 1,
            "has_reason": True,
            "loan_status": "sanctioned",
            "visit_or_call_requested": True,
            "already_visited": False,
            "ready_to_book": False,
            "decision_maker": "sole",
            "n_questions": 1,
            "concrete_details_count": 6
        },
        "evidence_phrases": {
            "primary_location": "Whitefield",
            "property_type": "2BHK",
            "budget_lakhs": "80 Lakhs",
            "timeline_months": "Next month",
            "has_reason": "company transfer ho raha hai",
            "loan_status": "loan sanctioned",
            "visit_or_call_requested": "Kya Saturday ko visit arrange kar sakte ho?"
        },
        "ambiguous_fields": []
    },
    {
        "id": "HW08",
        "source": "handwritten",
        "language": "hinglish",
        "message": "Bhai Sarjapur me 3BHK dekh rahe hain 1.2 Cr tak. Shift hone me 3 months lagenge. Mere parents ke saath aana hai, final decision father karenge. Can you share brochure?",
        "gold": {
            "is_spam": False,
            "primary_location": "Sarjapur",
            "property_type": "3BHK",
            "budget_lakhs": 120.0,
            "timeline_months": 3,
            "has_reason": False,
            "loan_status": "unknown",
            "visit_or_call_requested": False,
            "already_visited": False,
            "ready_to_book": False,
            "decision_maker": "needs_others",
            "n_questions": 1,
            "concrete_details_count": 4
        },
        "evidence_phrases": {
            "primary_location": "Sarjapur",
            "property_type": "3BHK",
            "budget_lakhs": "1.2 Cr",
            "timeline_months": "3 months",
            "decision_maker": "final decision father karenge"
        },
        "ambiguous_fields": []
    },
    {
        "id": "HW09",
        "source": "handwritten",
        "language": "en",
        "message": "Searching for a luxury 4BHK in Hebbal under 2.8 Cr. We have own funds ready without any bank loan. Ready to book immediately after doing one final walkthrough this Friday.",
        "gold": {
            "is_spam": False,
            "primary_location": "Hebbal",
            "property_type": "4BHK",
            "budget_lakhs": 280.0,
            "timeline_months": 1,
            "has_reason": False,
            "loan_status": "own_funds",
            "visit_or_call_requested": True,
            "already_visited": False,
            "ready_to_book": True,
            "decision_maker": "sole",
            "n_questions": 0,
            "concrete_details_count": 5
        },
        "evidence_phrases": {
            "primary_location": "Hebbal",
            "property_type": "4BHK",
            "budget_lakhs": "2.8 Cr",
            "timeline_months": "immediately",
            "loan_status": "own funds ready",
            "visit_or_call_requested": "walkthrough this Friday",
            "ready_to_book": "Ready to book immediately"
        },
        "ambiguous_fields": []
    },
    {
        "id": "HW10",
        "source": "handwritten",
        "language": "en",
        "message": "Enquiring about 3BHK on Bannerghatta Road under 1.1 Cr. Need to shift within 2 months because of baby birth in family. Paying from personal savings. Please call me back today.",
        "gold": {
            "is_spam": False,
            "primary_location": "Bannerghatta Road",
            "property_type": "3BHK",
            "budget_lakhs": 110.0,
            "timeline_months": 2,
            "has_reason": True,
            "loan_status": "own_funds",
            "visit_or_call_requested": True,
            "already_visited": False,
            "ready_to_book": False,
            "decision_maker": "sole",
            "n_questions": 0,
            "concrete_details_count": 6
        },
        "evidence_phrases": {
            "primary_location": "Bannerghatta Road",
            "property_type": "3BHK",
            "budget_lakhs": "1.1 Cr",
            "timeline_months": "within 2 months",
            "has_reason": "baby birth in family",
            "loan_status": "personal savings",
            "visit_or_call_requested": "Please call me back today"
        },
        "ambiguous_fields": []
    },
    {
        "id": "HW11",
        "source": "handwritten",
        "language": "en",
        "message": "Interested in your properties. Send brochure and complete price list on WhatsApp.",
        "gold": {
            "is_spam": False,
            "primary_location": None,
            "property_type": None,
            "budget_lakhs": None,
            "timeline_months": None,
            "has_reason": False,
            "loan_status": "unknown",
            "visit_or_call_requested": False,
            "already_visited": False,
            "ready_to_book": False,
            "decision_maker": "sole",
            "n_questions": 0,
            "concrete_details_count": 0
        },
        "evidence_phrases": {},
        "ambiguous_fields": []
    },
    {
        "id": "HW12",
        "source": "handwritten",
        "language": "en",
        "message": "Respected HR Manager, I have 5 years experience as real estate sales manager in Bengaluru. Please find my CV attached for current vacancies.",
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
    },
    {
        "id": "HW13",
        "source": "handwritten",
        "language": "en",
        "message": "Looking for residential plot in Devanahalli with budget between 50 to 60 Lakhs. Looking to purchase in next 6 months for pure long-term investment.",
        "gold": {
            "is_spam": False,
            "primary_location": "Devanahalli",
            "property_type": "plot",
            "budget_lakhs": 60.0,
            "timeline_months": 6,
            "has_reason": False,
            "loan_status": "unknown",
            "visit_or_call_requested": False,
            "already_visited": False,
            "ready_to_book": False,
            "decision_maker": "sole",
            "n_questions": 0,
            "concrete_details_count": 4
        },
        "evidence_phrases": {
            "primary_location": "Devanahalli",
            "property_type": "plot",
            "budget_lakhs": "60 Lakhs",
            "timeline_months": "6 months"
        },
        "ambiguous_fields": []
    },
    {
        "id": "HW14",
        "source": "handwritten",
        "language": "en",
        "message": "We already visited your Bellandur project last Sunday and liked Unit 402. Our budget is 1.8 Cr for this 3BHK. Pre-approved loan from ICICI. We are ready to book and give the token cheque tomorrow.",
        "gold": {
            "is_spam": False,
            "primary_location": "Bellandur",
            "property_type": "3BHK",
            "budget_lakhs": 180.0,
            "timeline_months": 1,
            "has_reason": False,
            "loan_status": "pre_approved",
            "visit_or_call_requested": False,
            "already_visited": True,
            "ready_to_book": True,
            "decision_maker": "sole",
            "n_questions": 0,
            "concrete_details_count": 5
        },
        "evidence_phrases": {
            "primary_location": "Bellandur",
            "property_type": "3BHK",
            "budget_lakhs": "1.8 Cr",
            "loan_status": "Pre-approved loan",
            "already_visited": "already visited your Bellandur project last Sunday",
            "ready_to_book": "ready to book and give the token cheque tomorrow"
        },
        "ambiguous_fields": []
    },
    {
        "id": "HW15",
        "source": "handwritten",
        "language": "en",
        "message": "Want 1BHK in Thanisandra around 25 Lakhs. Will consider buying next year when I have saved up.",
        "gold": {
            "is_spam": False,
            "primary_location": "Thanisandra",
            "property_type": "1BHK",
            "budget_lakhs": 25.0,
            "timeline_months": 12,
            "has_reason": False,
            "loan_status": "unknown",
            "visit_or_call_requested": False,
            "already_visited": False,
            "ready_to_book": False,
            "decision_maker": "sole",
            "n_questions": 0,
            "concrete_details_count": 4
        },
        "evidence_phrases": {
            "primary_location": "Thanisandra",
            "property_type": "1BHK",
            "budget_lakhs": "25 Lakhs",
            "timeline_months": "next year"
        },
        "ambiguous_fields": []
    },
    {
        "id": "HW16",
        "source": "handwritten",
        "language": "en",
        "message": "Need a 2BHK in Marathahalli around 95 Lakhs. Moving out as current lease ending end of next month. Pre-approved loan from HDFC ready. Can we schedule a site visit this Sunday morning?",
        "gold": {
            "is_spam": False,
            "primary_location": "Marathahalli",
            "property_type": "2BHK",
            "budget_lakhs": 95.0,
            "timeline_months": 1,
            "has_reason": True,
            "loan_status": "pre_approved",
            "visit_or_call_requested": True,
            "already_visited": False,
            "ready_to_book": False,
            "decision_maker": "sole",
            "n_questions": 1,
            "concrete_details_count": 6
        },
        "evidence_phrases": {
            "primary_location": "Marathahalli",
            "property_type": "2BHK",
            "budget_lakhs": "95 Lakhs",
            "timeline_months": "next month",
            "has_reason": "current lease ending end of next month",
            "loan_status": "Pre-approved loan",
            "visit_or_call_requested": "Can we schedule a site visit this Sunday morning?"
        },
        "ambiguous_fields": []
    },
    {
        "id": "HW17",
        "source": "handwritten",
        "language": "hinglish",
        "message": "Namashkar, hum Indiranagar me luxury villa dekh rahe hain. Hamara budget 4.5 Cr hai, payment full own funds se hoga without loan. Main aur meri wife dono ready hain spot booking ke liye, bas Saturday ko unit dekhna hai.",
        "gold": {
            "is_spam": False,
            "primary_location": "Indiranagar",
            "property_type": "villa",
            "budget_lakhs": 450.0,
            "timeline_months": 1,
            "has_reason": False,
            "loan_status": "own_funds",
            "visit_or_call_requested": True,
            "already_visited": False,
            "ready_to_book": True,
            "decision_maker": "joint_present",
            "n_questions": 0,
            "concrete_details_count": 5
        },
        "evidence_phrases": {
            "primary_location": "Indiranagar",
            "property_type": "villa",
            "budget_lakhs": "4.5 Cr",
            "loan_status": "own funds",
            "visit_or_call_requested": "Saturday ko unit dekhna hai",
            "ready_to_book": "ready hain spot booking ke liye",
            "decision_maker": "Main aur meri wife dono"
        },
        "ambiguous_fields": []
    },
    {
        "id": "HW18",
        "source": "handwritten",
        "language": "en",
        "message": "Earn guaranteed 15% monthly return on your real estate investments with decentralized crypto liquidity pools. Register at bit.example.com/yield",
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
    },
    {
        "id": "HW19",
        "source": "handwritten",
        "language": "en",
        "message": "Looking for flats in Whitefield, Sarjapur or Electronic City. Haven't decided on location yet, no fixed budget in mind right now.",
        "gold": {
            "is_spam": False,
            "primary_location": None,
            "property_type": None,
            "budget_lakhs": None,
            "timeline_months": None,
            "has_reason": False,
            "loan_status": "unknown",
            "visit_or_call_requested": False,
            "already_visited": False,
            "ready_to_book": False,
            "decision_maker": "sole",
            "n_questions": 0,
            "concrete_details_count": 0
        },
        "evidence_phrases": {},
        "ambiguous_fields": ["primary_location"]
    },
    {
        "id": "HW20",
        "source": "handwritten",
        "language": "en",
        "message": "Hi, exploring 3BHK flats on Kanakapura Road within 1.3 Cr. Moving in 3 months. My loan approval is in process with Axis Bank. Is Metro station reachable by walk from your property?",
        "gold": {
            "is_spam": False,
            "primary_location": "Kanakapura Road",
            "property_type": "3BHK",
            "budget_lakhs": 130.0,
            "timeline_months": 3,
            "has_reason": False,
            "loan_status": "in_process",
            "visit_or_call_requested": False,
            "already_visited": False,
            "ready_to_book": False,
            "decision_maker": "sole",
            "n_questions": 1,
            "concrete_details_count": 5
        },
        "evidence_phrases": {
            "primary_location": "Kanakapura Road",
            "property_type": "3BHK",
            "budget_lakhs": "1.3 Cr",
            "timeline_months": "3 months",
            "loan_status": "in process"
        },
        "ambiguous_fields": []
    },
    {
        "id": "HW21",
        "source": "handwritten",
        "language": "en",
        "message": "Looking for 2BHK in Kadugodi under 85 Lakhs. Shifted to Amazon campus this week, need urgent possession within 1 month. Loan pre-approved. Please call me back at 5 PM.",
        "gold": {
            "is_spam": False,
            "primary_location": "Kadugodi",
            "property_type": "2BHK",
            "budget_lakhs": 85.0,
            "timeline_months": 1,
            "has_reason": True,
            "loan_status": "pre_approved",
            "visit_or_call_requested": True,
            "already_visited": False,
            "ready_to_book": False,
            "decision_maker": "sole",
            "n_questions": 0,
            "concrete_details_count": 6
        },
        "evidence_phrases": {
            "primary_location": "Kadugodi",
            "property_type": "2BHK",
            "budget_lakhs": "85 Lakhs",
            "timeline_months": "within 1 month",
            "has_reason": "Shifted to Amazon campus this week",
            "loan_status": "Loan pre-approved",
            "visit_or_call_requested": "Please call me back at 5 PM"
        },
        "ambiguous_fields": []
    },
    {
        "id": "HW22",
        "source": "handwritten",
        "language": "en",
        "message": "I am 42 years old and lived at Flat 304 for 8 years. Now looking for 2BHK in Electronic City. My budget is 65 Lakhs and area should be 1250 sqft. Call on 9845012345.",
        "gold": {
            "is_spam": False,
            "primary_location": "Electronic City",
            "property_type": "2BHK",
            "budget_lakhs": 65.0,
            "timeline_months": None,
            "has_reason": False,
            "loan_status": "unknown",
            "visit_or_call_requested": True,
            "already_visited": False,
            "ready_to_book": False,
            "decision_maker": "sole",
            "n_questions": 0,
            "concrete_details_count": 3
        },
        "evidence_phrases": {
            "primary_location": "Electronic City",
            "property_type": "2BHK",
            "budget_lakhs": "65 Lakhs",
            "visit_or_call_requested": "Call on 9845012345"
        },
        "ambiguous_fields": []
    },
    {
        "id": "HW23",
        "source": "handwritten",
        "language": "hinglish",
        "message": "Hi, Wipro office ke paas Electronic City Phase 1 me 2BHK flat chahiye. Budget 65 Lakhs hai. Moving timeline 3 months hai. Bank loan apply kiya hua hai.",
        "gold": {
            "is_spam": False,
            "primary_location": "Electronic City",
            "property_type": "2BHK",
            "budget_lakhs": 65.0,
            "timeline_months": 3,
            "has_reason": False,
            "loan_status": "in_process",
            "visit_or_call_requested": False,
            "already_visited": False,
            "ready_to_book": False,
            "decision_maker": "sole",
            "n_questions": 0,
            "concrete_details_count": 5
        },
        "evidence_phrases": {
            "primary_location": "Electronic City",
            "property_type": "2BHK",
            "budget_lakhs": "65 Lakhs",
            "timeline_months": "3 months",
            "loan_status": "Bank loan apply kiya hua hai"
        },
        "ambiguous_fields": []
    },
    {
        "id": "HW24",
        "source": "handwritten",
        "language": "en",
        "message": "Looking for sea-facing 2BHK apartment in Andheri West, Mumbai. Ready to invest 2 Cr.",
        "gold": {
            "is_spam": False,
            "primary_location": "Mumbai",
            "property_type": "2BHK",
            "budget_lakhs": 200.0,
            "timeline_months": None,
            "has_reason": False,
            "loan_status": "unknown",
            "visit_or_call_requested": False,
            "already_visited": False,
            "ready_to_book": False,
            "decision_maker": "sole",
            "n_questions": 0,
            "concrete_details_count": 3
        },
        "evidence_phrases": {
            "primary_location": "Mumbai",
            "property_type": "2BHK",
            "budget_lakhs": "2 Cr"
        },
        "ambiguous_fields": []
    },
    {
        "id": "HW25",
        "source": "handwritten",
        "language": "en",
        "message": "Hi, looking for 3BHK in Yelahanka up to 1.6 Cr. My HDFC loan of 1.3 Cr is sanctioned and I have 30 Lakhs ready downpayment. Need to finalize within 1 month. Can I visit tomorrow morning?",
        "gold": {
            "is_spam": False,
            "primary_location": "Yelahanka",
            "property_type": "3BHK",
            "budget_lakhs": 160.0,
            "timeline_months": 1,
            "has_reason": False,
            "loan_status": "sanctioned",
            "visit_or_call_requested": True,
            "already_visited": False,
            "ready_to_book": False,
            "decision_maker": "sole",
            "n_questions": 1,
            "concrete_details_count": 5
        },
        "evidence_phrases": {
            "primary_location": "Yelahanka",
            "property_type": "3BHK",
            "budget_lakhs": "1.6 Cr",
            "timeline_months": "within 1 month",
            "loan_status": "loan of 1.3 Cr is sanctioned",
            "visit_or_call_requested": "Can I visit tomorrow morning?"
        },
        "ambiguous_fields": []
    },
    {
        "id": "HW26",
        "source": "handwritten",
        "language": "en",
        "message": "Hi, is this project still available?",
        "gold": {
            "is_spam": False,
            "primary_location": None,
            "property_type": None,
            "budget_lakhs": None,
            "timeline_months": None,
            "has_reason": False,
            "loan_status": "unknown",
            "visit_or_call_requested": False,
            "already_visited": False,
            "ready_to_book": False,
            "decision_maker": "sole",
            "n_questions": 1,
            "concrete_details_count": 0
        },
        "evidence_phrases": {},
        "ambiguous_fields": []
    },
    {
        "id": "HW27",
        "source": "handwritten",
        "language": "en",
        "message": "Relocating from Chennai in 4 months. Looking for 3BHK in JP Nagar with 1.5 Cr budget. What is the clubhouse size, when is the exact possession date, and is Cauvery water connected?",
        "gold": {
            "is_spam": False,
            "primary_location": "JP Nagar",
            "property_type": "3BHK",
            "budget_lakhs": 150.0,
            "timeline_months": 4,
            "has_reason": True,
            "loan_status": "unknown",
            "visit_or_call_requested": False,
            "already_visited": False,
            "ready_to_book": False,
            "decision_maker": "sole",
            "n_questions": 3,
            "concrete_details_count": 5
        },
        "evidence_phrases": {
            "primary_location": "JP Nagar",
            "property_type": "3BHK",
            "budget_lakhs": "1.5 Cr",
            "timeline_months": "4 months",
            "has_reason": "Relocating from Chennai in 4 months"
        },
        "ambiguous_fields": []
    },
    {
        "id": "HW28",
        "source": "handwritten",
        "language": "hinglish",
        "message": "Hello, Varthur me 3BHK flat dekh rahe hain around 1.35 Cr. Next week shifting karni hai. SBI loan sanction letter aa chuka hai. Kal site visit fix kar do please.",
        "gold": {
            "is_spam": False,
            "primary_location": "Varthur",
            "property_type": "3BHK",
            "budget_lakhs": 135.0,
            "timeline_months": 1,
            "has_reason": True,
            "loan_status": "sanctioned",
            "visit_or_call_requested": True,
            "already_visited": False,
            "ready_to_book": False,
            "decision_maker": "sole",
            "n_questions": 0,
            "concrete_details_count": 6
        },
        "evidence_phrases": {
            "primary_location": "Varthur",
            "property_type": "3BHK",
            "budget_lakhs": "1.35 Cr",
            "timeline_months": "Next week",
            "has_reason": "Next week shifting karni hai",
            "loan_status": "loan sanction letter",
            "visit_or_call_requested": "Kal site visit fix kar do please"
        },
        "ambiguous_fields": []
    },
    {
        "id": "HW29",
        "source": "handwritten",
        "language": "en",
        "message": "Partner with HDFC DSA Network: offer home loans to your real estate clients and earn 0.65% payout per disbursement. Contact 9876543210 for channel partner tie-up.",
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
    }
]
