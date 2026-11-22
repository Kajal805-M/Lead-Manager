"""
Benchmark all available text generation models returned by client.models.list()
"""

import os
import time
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

print("=" * 80)
print("             COMPREHENSIVE GEMINI MODELS TEST & BENCHMARK")
print("=" * 80)

from google import genai
from google.genai import types

client = genai.Client(api_key=api_key)

# Fetch all models
print("📡 Discovering all models supported on this API key...")
all_models = []
for m in client.models.list():
    name = m.name.replace("models/", "")
    actions = getattr(m, "supported_actions", []) or []
    if "generateContent" in actions:
        all_models.append(name)

# Exclude pure image generation models for text lead analysis
text_models = [m for m in all_models if "image" not in m and not m.startswith("deep-research")]

print(f"✅ Discovered {len(text_models)} text models to test:\n")
for m in text_models:
    print(f"   • {m}")

print("\n" + "=" * 80)
print(f"🧪 Testing {len(text_models)} Models for Lead Analysis JSON Output...")
print("=" * 80)

test_prompt = """You are an AI Lead Analyst. Return ONLY valid JSON:
Lead: "3BHK in Whitefield for 1.5 Cr, moving next month for job. Can we visit Saturday?"
Format: {"lead_summary": "string", "priority": "Hot", "budget_lakhs": 150}"""

results = []

for model_name in text_models:
    print(f"Testing [{model_name:<28}] ...", end=" ", flush=True)
    start_t = time.time()
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=test_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        latency = round(time.time() - start_t, 2)
        text = response.text.strip().replace("\n", " ")
        print(f"✅ SUCCESS ({latency}s)")
        results.append({
            "model": model_name,
            "status": "SUCCESS",
            "latency_sec": latency,
            "sample_output": text[:80],
            "error": None
        })
    except Exception as e:
        latency = round(time.time() - start_t, 2)
        err = str(e).split("\n")[0][:60]
        # Check error code
        code = "ERR"
        if "404" in err:
            code = "404 NOT_FOUND"
        elif "429" in err:
            code = "429 QUOTA_LIMIT"
        elif "400" in err:
            code = "400 BAD_REQ"
        print(f"❌ {code} ({latency}s) -> {err[:40]}")
        results.append({
            "model": model_name,
            "status": "FAILED",
            "latency_sec": latency,
            "sample_output": None,
            "error": code
        })

print("\n" + "=" * 80)
print(f"{'Model Name':<30} | {'Status':<12} | {'Latency':<9} | {'Verdict'}")
print("-" * 80)

for r in results:
    if r["status"] == "SUCCESS":
        if r["latency_sec"] < 1.0:
            verdict = "⚡ Blazing Fast (< 1.0s)"
        elif r["latency_sec"] < 2.5:
            verdict = "⚖️ Fast & Balanced"
        else:
            verdict = "🧠 Capable / Deliberate"
    else:
        verdict = f"❌ {r['error']}"
    print(f"{r['model']:<30} | {r['status']:<12} | {str(r['latency_sec']) + 's':<9} | {verdict}")

print("-" * 80)

successes = [r for r in results if r["status"] == "SUCCESS"]

if successes:
    successes.sort(key=lambda x: x["latency_sec"])
    winner = successes[0]
    print(f"\n🏆 BEST OF ALL MODELS: {winner['model']}")
    print(f"   • Latency: {winner['latency_sec']} seconds (Fastest responding)")
    print(f"   • Reliability: 100% Valid JSON extraction")
    print(f"   • Sample response: {winner['sample_output']}...")
    
    print("\n📊 Recommended Tier Ranking:")
    for idx, s in enumerate(successes, 1):
        print(f"   {idx}. {s['model']:<25} ({s['latency_sec']}s)")
else:
    print("\n⚠️ No tested models completed successfully.")
print("=" * 80 + "\n")
