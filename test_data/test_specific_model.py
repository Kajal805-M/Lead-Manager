"""
Test gemini-3.8-flash-lite and compare with gemini-3.5-flash-lite
"""

import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Error: GEMINI_API_KEY not found in .env")
    exit(1)

client = genai.Client(api_key=api_key)

models_to_test = [
    "gemini-3.8-flash-lite",
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite"
]

test_prompt = """You are an AI Lead Analyst. Return ONLY valid JSON:
Lead: "3BHK in Whitefield for 1.5 Cr, moving next month for job at ITPL. Can we visit Saturday?"
Format: {"lead_summary": "string", "priority": "Hot", "budget_lakhs": 150}"""

print("=" * 70)
print("       TESTING GEMINI-3.8-FLASH-LITE vs CANDIDATES")
print("=" * 70)

for model_name in models_to_test:
    print(f"\n🔍 Testing [{model_name}]...")
    start_time = time.time()
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=test_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        latency = round(time.time() - start_time, 2)
        print(f"   ✅ Status: SUCCESS ({latency}s)")
        print(f"   📄 Response: {response.text.strip()}")
    except Exception as e:
        latency = round(time.time() - start_time, 2)
        err = str(e).split("\n")[0]
        print(f"   ❌ Status: FAILED ({latency}s)")
        print(f"   ⚠️ Reason: {err}")

print("\n" + "=" * 70 + "\n")
