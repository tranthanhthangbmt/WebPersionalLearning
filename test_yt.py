import requests
import re

def test():
    url = 'https://olm.vn/chu-de/bai-hoc-duong-doi-dau-tien-phan-1-470515'
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    matches = re.finditer(r'youtube', r.text.lower())
    for m in matches:
        start = max(0, m.start() - 50)
        end = min(len(r.text), m.end() + 100)
        print("MATCH:", r.text[start:end])

if __name__ == '__main__':
    test()
