import urllib.request, re
try:
    req = urllib.request.Request('https://vi.khanacademy.org/math/toan-lop-6-viet-nam/x6fc1a176abf8821a:so-tu-nhien-lop-6/x6fc1a176abf8821a:on-tap-ve-so-tu-nhien-lop-6/v/place-value-2', headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    html = urllib.request.urlopen(req).read().decode('utf-8')
    matches = re.findall(r'youtubeId.:.([^\"\}]+)', html)
    print('youtubeId:', set(matches))
    print('youtube count:', html.lower().count('youtube'))
except Exception as e:
    print('Error:', e)
