import json
import re
import requests
import concurrent.futures

def fetch_youtube_url(url):
    if not url.startswith('https://olm.vn/chu-de/'):
        return url
    
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}, timeout=10)
        if r.status_code == 200:
            m = re.search(r'video_url:\s*"(https://www\.youtube\.com/watch\?v=[^"]+)"', r.text)
            if m:
                # Convert watch?v= format to embed format for better iframe compatibility if needed, 
                # but YouTube watch links are generally fine if the frontend handles them. 
                # The prompt asks for "đường link youtube gốc" which is watch?v=. We'll keep it as watch?v= or convert to embed.
                yt_url = m.group(1)
                # Convert to embed for iframe
                yt_embed = yt_url.replace("watch?v=", "embed/")
                return yt_embed
            
            # Sometimes it might be an embedded iframe directly
            m2 = re.search(r'src="(https://www\.youtube\.com/embed/[^"]+)"', r.text)
            if m2:
                return m2.group(1)
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        
    return url

def update():
    filepath = r'DB/public_trees/c4d5e6f7.json'
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    urls_to_check = []
    # Collect all URLs
    for node in data.get('micro_nodes', []):
        urls_to_check.append((node, 'url', node.get('url', '')))
        for res in node.get('resources', []):
            urls_to_check.append((res, 'url', res.get('url', '')))
            
    # Function to process one item
    def process_item(item):
        obj, key, url = item
        if url.startswith('https://olm.vn/chu-de/'):
            new_url = fetch_youtube_url(url)
            if new_url != url:
                obj[key] = new_url
                print(f"Updated: {new_url}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(process_item, urls_to_check)
        
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        
    print("Update complete!")

if __name__ == '__main__':
    update()
