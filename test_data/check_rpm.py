"""
Check rate limits (RPM / RPD / TPM) and inspect headers for:
- gemini-3.5-flash-lite
- gemma-4-31b-it (and gemini-4-31b-it)
"""

import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(timeout=15000)
)

print("=" * 75)
print("             CHECKING MODEL METADATA & RPM LIMITS")
print("=" * 75)

models_to_check = ["gemini-3.5-flash-lite", "gemma-4-31b-it"]

for model_name in models_to_check:
    print(f"\n🔍 Inspecting Model: [{model_name}]")
    try:
        m = client.models.get(model=model_name)
        print(f"   Name: {m.name}")
        print(f"   Display Name: {getattr(m, 'display_name', 'N/A')}")
        print(f"   Input Token Limit: {getattr(m, 'input_token_limit', 'N/A')}")
        print(f"   Output Token Limit: {getattr(m, 'output_token_limit', 'N/A')}")
        for attr in dir(m):
            if "rate" in attr.lower() or "quota" in attr.lower() or "limit" in attr.lower():
                val = getattr(m, attr)
                if not callable(val):
                    print(f"   {attr}: {val}")
    except Exception as e:
        print(f"   ❌ Could not get metadata: {e}")

# Next: Check HTTP response headers by making a lightweight request with httpx / requests
import requests

print("\n" + "=" * 75)
print("📡 Checking Live Response Headers for Rate Limits (x-ratelimit-*)...")
print("=" * 75)

for model_name in models_to_check:
    print(f"\nTesting live request to [{model_name}]...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": "Hi"}]}]
    }
    t0 = time.time()
    try:
        res = requests.post(url, json=payload, timeout=15)
        duration = round(time.time() - t0, 2)
        print(f"   Status Code: {res.status_code} ({duration}s)")
        
        # Look for rate limit headers
        rate_headers = {k: v for k, v in res.headers.items() if any(x in k.lower() for x in ["ratelimit", "rate-limit", "quota", "retry"])}
        if rate_headers:
            print("   Rate Limit Headers:")
            for k, v in rate_headers.items():
                print(f"     • {k}: {v}")
        else:
            print("   (No explicit x-ratelimit-* headers returned in standard response headers)")
            
        if res.status_code == 429:
            print(f"   429 Response Body: {res.text}")
    except Exception as e:
        print(f"   Request error: {e}")

print("\n" + "=" * 75 + "\n")
