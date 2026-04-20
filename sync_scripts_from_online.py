import os
import json
import urllib.request
import urllib.error

# Config
REPO_URL = "https://tranthanhthangbmt.github.io/ThuongMaiDienTu_3TC"
TREE_FILE = "user_data/thanhthangbmt/trees/e69bf65f.json"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_VIDEO_DIR = os.path.join(BASE_DIR, "DB", "Video")

def sync_scripts():
    # Load Tree
    tree_path = os.path.join(BASE_DIR, TREE_FILE)
    if not os.path.exists(tree_path):
        print(f"Error: Tree file not found at {tree_path}")
        return

    with open(tree_path, 'r', encoding='utf-8') as f:
        tree = json.load(f)

    nodes = tree.get("nodes", {})
    count_success = 0
    count_skipped = 0
    
    # Iterate through macro/micro nodes
    for node_id, node_data in nodes.items():
        if not node_id.startswith("Chuong_"):
            continue
            
        print(f"\nProcessing {node_id}...")
        
        # Local paths
        node_dir = os.path.join(DB_VIDEO_DIR, node_id)
        os.makedirs(node_dir, exist_ok=True)
        local_script = os.path.join(node_dir, "script.txt")
        local_video_link = os.path.join(node_dir, "videoLink.txt")
        
        # Remote URLs
        remote_script_url = f"{REPO_URL}/Video/{node_id}/script.txt"
        remote_video_url = f"{REPO_URL}/Video/{node_id}/videoLink.txt"
        
        # Fetch script.txt
        if not os.path.exists(local_script):
            try:
                print(f"Fetching {remote_script_url}...")
                req = urllib.request.Request(remote_script_url, headers={'User-Agent': 'Mozilla/5.0'})
                response = urllib.request.urlopen(req, timeout=5)
                content = response.read().decode('utf-8')
                
                with open(local_script, 'w', encoding='utf-8') as f:
                    f.write(content)
                print("✅ Downloaded script.txt")
                count_success += 1
            except urllib.error.HTTPError as e:
                print(f"❌ HTTP Error {e.code}: Not found online.")
            except Exception as e:
                print(f"❌ Error: {e}")
        else:
            print("⏩ script.txt already exists. Skipping.")
            count_skipped += 1
            
        # Fetch videoLink.txt (optional but useful)
        if not os.path.exists(local_video_link):
            try:
                print(f"Fetching {remote_video_url}...")
                req = urllib.request.Request(remote_video_url, headers={'User-Agent': 'Mozilla/5.0'})
                response = urllib.request.urlopen(req, timeout=5)
                content = response.read().decode('utf-8')
                
                with open(local_video_link, 'w', encoding='utf-8') as f:
                    f.write(content)
                print("✅ Downloaded videoLink.txt")
            except urllib.error.HTTPError:
                pass # Ignore if missing
            except Exception as e:
                pass


    print(f"\n🎉 Sync completed! {count_success} new scripts downloaded. {count_skipped} skipped because they already exist locally.")

if __name__ == "__main__":
    sync_scripts()
