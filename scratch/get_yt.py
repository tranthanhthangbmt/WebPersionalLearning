import requests
import re

url = 'https://olm.vn/chu-de/tap-hop-356926'
r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
text = r.text

print("video_url:")
m = re.findall(r'video_url:\s*"(https://www\.youtube\.com/[^"]+)"', text)
print(m)

print("src embed:")
m2 = re.findall(r'src="(https://www\.youtube\.com/embed/[^"]+)"', text)
print(m2)

print("any youtube watch link in HTML context:")
for link in re.findall(r'.{0,30}https://www\.youtube\.com/watch\?v=.{0,30}', text):
    print(link.strip())
