import os
import json
import uuid

def add_script_resources():
    tree_path = "user_data/thanhthangbmt/trees/e69bf65f.json"
    repo_url = "https://tranthanhthangbmt.github.io/ThuongMaiDienTu_3TC"
    
    if not os.path.exists(tree_path):
        print(f"File not found: {tree_path}")
        return
        
    with open(tree_path, 'r', encoding='utf-8') as f:
        tree = json.load(f)

    nodes = tree.get("nodes", {})
    added_count = 0
    
    for node_id, node_data in nodes.items():
        if not node_id.startswith("Chuong_"):
            continue
            
        resources = node_data.get("resources", [])
        
        # 1. Add Online Script URL
        online_url = f"{repo_url}/Video/{node_id}/script.txt"
        has_online = any(r.get("url") == online_url for r in resources)
        if not has_online:
            resources.append({
                "id": f"res_online_{uuid.uuid4().hex[:8]}",
                "url": online_url,
                "title": "📄 Kịch bản bài giảng (Online)",
                "type": "document",
                "icon": "📄"
            })
            added_count += 1
            
        # 2. Add Local File URL (for editing easily as requested)
        local_path = os.path.abspath(os.path.join("DB", "Video", node_id, "script.txt")).replace('\\', '/')
        local_url = f"vscode://file/{local_path}" # Use vscode URL scheme to open nicely in their IDE, or just file://
        has_local = any(r.get("title") == "✏️ Chỉnh sửa Kịch bản (Local)" for r in resources)
        
        if os.path.exists(os.path.join("DB", "Video", node_id, "script.txt")) and not has_local:
            resources.append({
                "id": f"res_local_{uuid.uuid4().hex[:8]}",
                "url": local_url,
                "title": "✏️ Chỉnh sửa Kịch bản (Local)",
                "type": "link", # Opens in external application usually
                "icon": "✏️"
            })
            added_count += 1
            
        node_data["resources"] = resources
        
    with open(tree_path, 'w', encoding='utf-8') as f:
        json.dump(tree, f, ensure_ascii=False, indent=4)
        
    print(f"Successfully added {added_count} script resources to nodes!")

if __name__ == "__main__":
    add_script_resources()
