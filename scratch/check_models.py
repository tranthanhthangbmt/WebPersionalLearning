import google.generativeai as genai
import os

def get_all_api_keys():
    try:
        key_path = os.path.join(os.getcwd(), 'GeminiKey', 'geminiKey.txt')
        if os.path.exists(key_path):
            with open(key_path, 'r') as f:
                return [line.strip() for line in f.readlines() if line.strip()]
    except Exception as e:
        print(f"Error reading Gemini API Keys: {e}")
    return []

keys = get_all_api_keys()
if not keys:
    print("No keys found.")
    exit()

key = keys[0]
genai.configure(api_key=key)

print("Checking available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")
