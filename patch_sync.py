import re

def modify_resource_sync():
    with open('resource_sync.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    extracted_func = """
def _sync_extracted_node(node_id, node_info, res_list):
    '''Trích xuất tài nguyên từ các trường url và content/description của node.'''
    changed = False
    existing_urls = set(r.get('url', '').strip() for r in res_list)
    
    def add_res_if_new(url, title):
        nonlocal changed
        url = url.strip()
        if url and url not in existing_urls:
            from resource_manager import detect_resource_type
            import uuid
            from datetime import datetime
            rtype, icon, dname = detect_resource_type(url)
            res_list.append({
                "id": f"res_ext_{uuid.uuid4().hex[:8]}",
                "url": url,
                "title": title or dname,
                "type": rtype,
                "icon": icon,
                "added_at": "auto-sync"
            })
            existing_urls.add(url)
            changed = True

    # Check direct 'url' field
    if 'url' in node_info and isinstance(node_info['url'], str) and node_info['url'].strip():
        add_res_if_new(node_info['url'], f"Tài nguyên chính: {node_info.get('title', node_id)}")
        
    # Regex extract from content/description_md
    text_content = node_info.get('content', '') or ''
    desc_md = node_info.get('description_md', '') or ''
    combined_text = text_content + '\\n' + desc_md
    
    # Extract markdown links [Title](url)
    matches = re.findall(r'\[([^\]]+)\]\((https?://[^\)]+)\)', combined_text)
    for title, url in matches:
        add_res_if_new(url, title.strip())
        
    return changed
"""
    
    # Add function to the end if not exists
    if "_sync_extracted_node" not in content:
        content += "\n" + extracted_func
    
    # Insert call inside sync_resources_to_tree
    search_str = "changed = _sync_generic_node(node_id, node_info, res_list, repo_url, parent_child_map) or changed"
    replace_str = search_str + "\n        else:\n            # Trích xuất từ content cho các JSON ngoại lai\n            changed = _sync_extracted_node(node_id, node_info, res_list) or changed"
    
    if "changed = _sync_extracted_node" not in content:
        content = content.replace(search_str, replace_str)
        
    with open('resource_sync.py', 'w', encoding='utf-8') as f:
        f.write(content)

modify_resource_sync()
print("Patched resource_sync.py")
