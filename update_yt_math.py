import json
import re
import requests
import concurrent.futures
import time

def fetch_youtube_url(url):
    if not url.startswith('https://olm.vn/chu-de/'):
        return url
    
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}, timeout=10)
        if r.status_code == 200:
            m = re.search(r'video_url:\s*"(https://www\.youtube\.com/[^"]+)"', r.text)
            if m:
                yt_url = m.group(1)
                yt_embed = yt_url.replace("watch?v=", "embed/")
                return yt_embed
            
            m2 = re.search(r'src="(https://www\.youtube\.com/embed/[^"]+)"', r.text)
            if m2:
                return m2.group(1)
        else:
            print(f"Failed {url}: HTTP {r.status_code}")
    except Exception as e:
        print(f"Error {url}: {e}")
        
    return url

def update():
    filepath = r'DB/public_trees/f2c8d7e9.json'
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    urls_to_check = []
    for node in data.get('micro_nodes', []):
        urls_to_check.append((node, 'url', node.get('url', '')))
        for res in node.get('resources', []):
            urls_to_check.append((res, 'url', res.get('url', '')))
            
    print(f"Total URLs to check: {len(urls_to_check)}")
    
    def process_item(item):
        obj, key, url = item
        if url.startswith('https://olm.vn/chu-de/'):
            new_url = fetch_youtube_url(url)
            if new_url != url:
                obj[key] = new_url
                print(f"Updated: {url} -> {new_url}", flush=True)
                return 1
            time.sleep(0.5)
        return 0

    updated_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(process_item, urls_to_check)
        updated_count = sum(results)
        
    if updated_count > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Update complete! {updated_count} URLs were changed to YouTube embeds.")
    else:
        print("No URLs were updated.")

if __name__ == '__main__':
    update()
