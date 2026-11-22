"""
Compare gemini-3.5-flash-lite and gemma-4-31b-it on test leads from leads_dataset.json.
Workflow:
1. Send lead to Model -> Extract structured JSON (summary, intent, requirements, objections, actions, suggested response).
2. Feed into Backend 6-Factor Deterministic Scoring Logic.
3. Compare accuracy, latency, and extraction quality against expected results.
"""

import os
import json
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from test_lead_scoring import evaluate_lead

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(timeout=25000)
)

# Load test leads
with open("leads_dataset.json", "r", encoding="utf-8") as f:
    data = json.load(f)

all_leads = data["leads"]

# Select 5 diverse benchmark leads representing all tiers and tricky edge cases
# L01: Hot (Relocation + Loan Sanctioned)
# L03: Warm (Passive brochure + Loan needed)
# L05: Cold (One-word "price?")
# L07: Warm (Tricky: Urgent + Cash, but unrealistic budget)
# L09: Hot (Hinglish message + School deadline)
# L14: Hot (Near booking + Competitor negotiation)
test_lead_ids = ["L01", "L03", "L05", "L07", "L09", "L14"]
selected_leads = [l for l in all_leads if l["id"] in test_lead_ids]

EXTRACTION_SYSTEM_PROMPT = """You are an expert AI Real Estate Analyst for Bangalore real estate.
Analyze the customer lead inquiry and extract structured details. Return ONLY valid JSON matching this schema:
{
  "lead_summary": "1-2 sentence concise summary of who the buyer is and what they want",
  "customer_intent": "Brief description of their buying intention and purpose",
  "key_requirements": "Extracted property type, BHK, and specific locality",
  "objections": ["List of customer concerns, objections, or friction points (empty array if none)"],
  "recommended_next_action": "Actionable next step for the sales representative",
  "suggested_customer_response": "Polite, professional response to send to the customer on WhatsApp/SMS"
}
"""

models_to_test = ["gemini-3.5-flash-lite", "gemma-4-31b-it"]

print("=" * 90)
print("       COMPARISON TEST: gemini-3.5-flash-lite VS gemma-4-31b-it ON TEST LEADS")
print("=" * 90)

overall_results = {}

for model_name in models_to_test:
    print(f"\n==========================================================================")
    print(f"🚀 RUNNING BENCHMARK WITH MODEL: [{model_name}]")
    print(f"==========================================================================")
    
    model_results = []
    total_time = 0
    successful_extractions = 0
    correct_classifications = 0

    for lead in selected_leads:
        lid = lead["id"]
        name = lead["name"]
        exp_tag = lead["expected"]["tag"]
        exp_range = lead["expected"]["score_range"]
        
        prompt = f"""Customer Inquiry:
Name: {lead.get('name', '')}
Location: {lead.get('location', '')}
Requirement: {lead.get('property_requirement', '')}
Budget: {lead.get('budget', '')}
Timeline: {lead.get('timeline', '')}
Message: "{lead.get('message', '')}"
"""
        print(f"Testing {lid} ({name[:16]})...", end=" ", flush=True)
        t0 = time.time()
        
        extracted_data = None
        err_msg = None
        
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=EXTRACTION_SYSTEM_PROMPT,
                    response_mime_type="application/json"
                )
            )
            dur = round(time.time() - t0, 2)
            total_time += dur
            raw_text = response.text.strip()
            extracted_data = json.loads(raw_text)
            successful_extractions += 1
            print(f"✅ Extracted ({dur}s)", end=" ")
        except Exception as e:
            dur = round(time.time() - t0, 2)
            total_time += dur
            err_msg = str(e).split("\n")[0][:40]
            print(f"❌ Failed ({dur}s, {err_msg})", end=" ")

        # Now run backend deterministic scoring on the lead
        score_res = evaluate_lead(lead)
        act_tag = score_res["tag"]
        act_score = score_res["total_score"]
        
        is_tag_match = (act_tag == exp_tag)
        is_score_match = (exp_range[0] <= act_score <= exp_range[1])
        
        if is_tag_match and is_score_match:
            correct_classifications += 1
            print(f"-> Tag: {act_tag} (Score: {act_score}) [PASS]")
        else:
            print(f"-> Tag: {act_tag} (Score: {act_score}) [Diff: Exp={exp_tag} {exp_range}]")

        model_results.append({
            "id": lid,
            "name": name,
            "latency": dur,
            "extracted": extracted_data,
            "error": err_msg,
            "score": act_score,
            "tag": act_tag,
            "exp_tag": exp_tag,
            "exp_range": exp_range
        })

    overall_results[model_name] = {
        "results": model_results,
        "avg_latency": round(total_time / len(selected_leads), 2) if selected_leads else 0,
        "success_rate": f"{successful_extractions}/{len(selected_leads)}",
        "tag_accuracy": f"{correct_classifications}/{len(selected_leads)}"
    }

print("\n" + "=" * 90)
print("                             FINAL COMPARISON SUMMARY")
print("=" * 90)
print(f"{'Metric':<32} | {'gemini-3.5-flash-lite':<25} | {'gemma-4-31b-it':<25}")
print("-" * 90)

flash_res = overall_results["gemini-3.5-flash-lite"]
gemma_res = overall_results["gemma-4-31b-it"]

print(f"{'Extraction Success Rate':<32} | {flash_res['success_rate']:<25} | {gemma_res['success_rate']:<25}")
print(f"{'Avg Latency Per Lead':<32} | {str(flash_res['avg_latency']) + 's':<25} | {str(gemma_res['avg_latency']) + 's':<25}")
print(f"{'Tag & Score Accuracy':<32} | {flash_res['tag_accuracy']:<25} | {gemma_res['tag_accuracy']:<25}")
print("-" * 90)

# Show detailed side-by-side extraction for a tricky lead (L09 Hinglish or L01)
sample_lead_id = "L09"
print(f"\n🔍 Detailed Extraction Quality Sample (Lead {sample_lead_id}: Mohammed Faizal - Hinglish Message):")
print("-" * 90)
for m in models_to_test:
    entry = next((e for e in overall_results[m]["results"] if e["id"] == sample_lead_id), None)
    if entry and entry["extracted"]:
        ex = entry["extracted"]
        print(f"Model: [{m}] (Latency: {entry['latency']}s)")
        print(f"  • Summary   : {ex.get('lead_summary')}")
        print(f"  • Intent    : {ex.get('customer_intent')}")
        print(f"  • Objections: {ex.get('objections')}")
        print(f"  • Next Step : {ex.get('recommended_next_action')}")
        print(f"  • Response  : {ex.get('suggested_customer_response')}")
        print()
    else:
        print(f"Model: [{m}] -> Failed to extract ({entry.get('error')})\n")

print("=" * 90 + "\n")
