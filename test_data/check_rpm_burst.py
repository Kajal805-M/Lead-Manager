"""
Burst test for gemini-3.5-flash-lite to test practical RPM throughput
"""

import os
import time
from dotenv import load_dotenv
import requests

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={api_key}"
payload = {"contents": [{"parts": [{"text": "Reply with '1'"}]}]}

print("Testing 5 consecutive requests to gemini-3.5-flash-lite...")
success_count = 0
start_all = time.time()

for i in range(5):
    t0 = time.time()
    try:
        r = requests.post(url, json=payload, timeout=10)
        dur = round(time.time() - t0, 2)
        if r.status_code == 200:
            success_count += 1
            print(f"  Req #{i+1}: 200 OK ({dur}s)")
        else:
            print(f"  Req #{i+1}: {r.status_code} ({dur}s) -> {r.text[:60]}")
    except Exception as e:
        print(f"  Req #{i+1}: Error: {e}")

total_time = round(time.time() - start_all, 2)
print(f"\nResult: {success_count}/5 Successful in {total_time}s.")
