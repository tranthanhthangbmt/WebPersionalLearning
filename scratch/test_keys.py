import os
import requests
import json
import time

key_file = r'i:\MY_CODE\WebPersionalLearning\GeminiKey\geminiKey.txt'
out_file = r'D:\MY_CODE\Antigravity_SDK1\antigravity-sdk-python-main\working_keys.txt'

with open(key_file, 'r') as f:
    keys = [line.strip() for line in f if line.strip()]

working_keys = []

for key in keys:
    print(f"Testing key: {key[:10]}...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={key}"
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
        
    time.sleep(1) # prevent rapid requests

print(f"\nFound {len(working_keys)} working keys out of {len(keys)}.")

if working_keys:
    try:
        with open(out_file, 'w') as f:
            for k in working_keys:
                f.write(k + '\n')
        print(f"Saved working keys to {out_file}")
    except Exception as e:
        print(f"Could not save to {out_file}: {e}")
