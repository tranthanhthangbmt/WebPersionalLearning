import os
import requests
import json
import time

key_file = r'i:\MY_CODE\WebPersionalLearning\GeminiKey\geminiKey.txt'

with open(key_file, 'r') as f:
    keys = [line.strip() for line in f if line.strip()]

working_keys = []

for key in keys:
    print(f"Testing key: {key[:10]}...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={key}"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": "Hello"}]}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            print(" -> WORKING!")
            working_keys.append(key)
        else:
            print(f" -> FAILED: {response.status_code} - {response.text[:100]}")
    except Exception as e:
        print(f" -> ERROR: {e}")
        
    time.sleep(0.5) # prevent rapid requests

print(f"\nFound {len(working_keys)} working keys out of {len(keys)}.")
