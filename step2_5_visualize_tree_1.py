import os
import json

def convert_to_flat_graph_internal(data):
    flat_graph = {
        "nodes": {},
        "edges": []
    }
    
    # Process Macro Nodes (Chapters) -> M01, M02...
    for m in data.get("macro_nodes", []):
        m_id = m.get("id")
        flat_graph["nodes"][m_id] = {
            "type": "macro",
            "label": m.get("title"),
            "resources": m.get("resources", []),
            "color": "#00ffcc",  # Neon Cyan for chapters
            "val": 25  # Size in 3D graph
        }
        
    # Group micro nodes by their parent_macro
    from collections import defaultdict
    macro_to_micros = defaultdict(list)
    for c in data.get("micro_nodes", []):
        macro_to_micros[c.get("parent_macro")].append(c)

    # Chunking parameter: How many micro lessons per Meso node?
    CHUNK_SIZE = 3
    meso_map = {} # micro_id -> meso_id

    for macro_id, micros in macro_to_micros.items():
        for i in range(0, len(micros), CHUNK_SIZE):
            chunk = micros[i:i+CHUNK_SIZE]
            meso_idx = i // CHUNK_SIZE + 1
            meso_id = f"{macro_id}_Meso_{meso_idx}"
            
            # Aggregate micro nodes into meso
            meso_resources = []
            meso_children = []
            for idx, m_node in enumerate(chunk):
                meso_map[m_node.get("id")] = meso_id
                meso_children.append({
                    "id": m_node.get("id"),
                    "title": m_node.get("title"),
                    "content": m_node.get("content"),
                    "resources": m_node.get("resources", [])
                })
                meso_resources.extend(m_node.get("resources", []))

            flat_graph["nodes"][meso_id] = {
                "type": "meso",
                "label": f"Phần {meso_idx}",
                "micro_children": meso_children, # Save detailed children for UI
                "resources": meso_resources,
                "val": 15,
                "prerequisites": []
            }
            
            # Link Macro -> Meso
            if macro_id:
                flat_graph["edges"].append({
                    "source": macro_id,
                    "target": meso_id,
                    "relation": "contains"
                })

    # TỰ ĐỘNG TẠO MACRO PATH (Xương sống kết nối các Chương) 
    # Ngăn chặn việc Graph bị đứt gãy thành nhiều cụm và bị vật lý d3 đẩy bay mất khỏi Camera (thành màn hình đen)
    macro_list = [m.get("id") for m in data.get("macro_nodes", [])]
    for i in range(len(macro_list) - 1):
        flat_graph["edges"].append({
            "source": macro_list[i],
            "target": macro_list[i+1],
            "relation": "macro_path"
        })
                
    # Process existing edges (prerequisites) and map them to Meso
    meso_edges_seen = set()
    for edge in data.get("edges", []):
        src = edge.get("source")
        tgt = edge.get("target")
        
        # Determine meso IDs for src and tgt
        src_meso = meso_map.get(src, src)
        tgt_meso = meso_map.get(tgt, tgt)
        
        # Don't link a meso to itself
        if src_meso != tgt_meso:
            edge_tuple = (src_meso, tgt_meso)
            if edge_tuple not in meso_edges_seen:
                meso_edges_seen.add(edge_tuple)
                flat_graph["edges"].append({
                    "source": src_meso,
                    "target": tgt_meso,
                    "relation": "prerequisite_for"
                })
                if tgt_meso in flat_graph["nodes"]:
                    if "prerequisites" not in flat_graph["nodes"][tgt_meso]:
                        flat_graph["nodes"][tgt_meso]["prerequisites"] = []
                    if src_meso not in flat_graph["nodes"][tgt_meso]["prerequisites"]:
                        flat_graph["nodes"][tgt_meso]["prerequisites"].append(src_meso)

    return flat_graph

def visualize_knowledge_tree(user_id, input_json_path=None, stats_data=None):
    """Generates a robust 3D Knowledge Galaxy UI within a single HTML file."""
    
    # 1. Path resolution
    json_path = input_json_path if input_json_path else f"user_data/{user_id}/{user_id}_knowledge_tree.json"
    subject_id = os.path.basename(json_path).replace(".json", "")
    
    if not os.path.exists(json_path):
        print(f"❌ File not found: {json_path}")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        tree_data = json.load(f)

    print(f"🎨 Rendering 3D Knowledge Galaxy for {user_id}...")

    # Data Conversion
    if "nodes" in tree_data and isinstance(tree_data["nodes"], dict):
        flat_data = tree_data
    else:
        flat_data = convert_to_flat_graph_internal(tree_data)

    # 2. Get Student State & Real Bloom Scores
    from database import get_user_by_username
    from pkt_engine import StudentState
    from bloom_taxonomy import get_all_bloom_scores
    
    db_user = get_user_by_username(user_id)
    user_db_id = db_user.id if db_user else 0
    student_state = StudentState(user_db_id)
    
    # 2.5 Get Gamification Stats
    if stats_data:
        stats = stats_data
    else:
        from gamification.xp_engine import XPEngine
        # Note: This might fail if called from a background thread for a guest
        try:
            stats = XPEngine.get_user_stats(user_db_id)
        except:
            stats = {"total_xp": 0, "current_level": 1, "level_name": "Newbie", "level_icon": "🌱", "xp_progress": 0}
            
    stats_json = json.dumps(stats, ensure_ascii=False)
    
    # Pass mastery/bloom of all micro nodes from DB cache to Front-End 
    mastery_map = {cid: student_state.get_mastery(cid) for cid in student_state.knowledge_cache.keys()}
    
    # NEW: Use real Bloom assessment scores from JSON-first system
    bloom_map = get_all_bloom_scores(user_id, subject_id)
    
    # 3. Calculate Next Action
    next_best_node_id = None
    for node_id, node_data in flat_data["nodes"].items():
        if node_data["type"] == "macro": continue
        # Meso node check if all prerequisites (other Meso nodes) are mastered
        is_acc = True
        for p in node_data.get("prerequisites", []):
            # Evaluate prerequisite meso's average mastery
            p_node = flat_data["nodes"].get(p)
            if p_node and p_node["type"] == "meso":
                children = p_node.get("micro_children", [])
                if children:
                    avg_mst = sum(student_state.get_mastery(c["id"]) for c in children) / len(children)
                    if avg_mst < 0.6: is_acc = False
        
        # Current Meso node average mastery
        children = node_data.get("micro_children", [])
        avg_mst = sum(student_state.get_mastery(c["id"]) for c in children) / len(children) if children else 0
        
        if is_acc and avg_mst < 0.6:
            next_best_node_id = node_id
            break

    # Array format for ForceGraph3D
    graph_data_array = {
        "nodes": [{"id": k, "next_best": (k == next_best_node_id), **v} for k, v in flat_data.get("nodes", {}).items()],
        "links": [{
            "source": e.get("source"), 
            "target": e.get("target"), 
            "relation": e.get("relation", "prerequisite_for")
        } for e in flat_data.get("edges", []) if e.get("source") and e.get("target")]
    }

    # 4. JSON Serialization
    mastery_map_json = json.dumps(mastery_map, ensure_ascii=False)
    bloom_map_json = json.dumps(bloom_map, ensure_ascii=False)
    json_string = json.dumps(graph_data_array, ensure_ascii=False)

    # 5. Chapter Navigation Data
    import re as _re
    chapter_list = []
    for nid, ndata in flat_data.get("nodes", {}).items():
        if ndata.get("type") == "macro":
            order_match = _re.search(r'\d+', nid)
            order = int(order_match.group()) if order_match else 999
            chapter_list.append({"id": nid, "title": ndata.get("label", nid), "order": order})
    chapter_list.sort(key=lambda x: x["order"])
    chapter_list_json = json.dumps(chapter_list, ensure_ascii=False)

    html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Knowledge Galaxy 3D — PKT Bio-Tutor</title>
    <script src="https://unpkg.com/three@0.141.0/build/three.min.js"></script>
    <script src="https://unpkg.com/3d-force-graph@1.70.16/dist/3d-force-graph.min.js"></script>
    <script src="https://unpkg.com/three-spritetext@1.8.2/dist/three-spritetext.min.js"></script>
    <script src="https://unpkg.com/three@0.141.0/examples/js/postprocessing/EffectComposer.js"></script>
    <script src="https://unpkg.com/three@0.141.0/examples/js/postprocessing/RenderPass.js"></script>
    <script src="https://unpkg.com/three@0.141.0/examples/js/postprocessing/UnrealBloomPass.js"></script>
    <script src="https://unpkg.com/three@0.141.0/examples/js/shaders/LuminosityHighPassShader.js"></script>
    <script src="https://unpkg.com/three@0.141.0/examples/js/shaders/CopyShader.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #060714;
            --glass-bg: rgba(10, 14, 40, 0.75);
            --glass-border: rgba(255, 255, 255, 0.06);
            --text-primary: #f0f4ff;
            --text-muted: #7b8ab8;
            --accent: #38bdf8;
            --green: #4ade80;
            --yellow: #fbbf24;
            --red: #f87171;
            --header-height: 70px;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ overflow: hidden; font-family: 'Inter', sans-serif; color: var(--text-primary); background: var(--bg-color); }}
        #3d-graph {{ position: absolute; top: 0; left: 0; width: 100vw; height: 100vh; }}
        
        .glass-panel {{ 
            background: var(--glass-bg); 
            backdrop-filter: blur(20px); 
            border: 1px solid var(--glass-border); 
            border-radius: 16px; 
            pointer-events: auto; 
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        
        header h1 {{ display: none; }} /* Kept for reference but hidden */
        
        .icon-btn {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: #fff;
            width: 38px;
            height: 38px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: 0.2s;
        }}
        .icon-btn:hover {{ background: rgba(255, 255, 255, 0.15); border-color: var(--accent); color: var(--accent); }}

        .top-toolbar {{ display: none; }}
        
        /* ── Panels ── */
        .side-panel {{ 
            position: absolute; 
            width: 260px; 
            display: flex; 
            flex-direction: column;
            overflow: hidden;
            z-index: 50;
        }}
        
        .panel-header {{
            padding: 14px 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            cursor: pointer;
            user-select: none;
            background: rgba(255,255,255,0.03);
            font-size: 11px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: var(--accent);
        }}
        .panel-header:hover {{ background: rgba(255,255,255,0.07); }}
        .panel-content {{ 
            padding: 16px; 
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            max-height: 60vh;
            overflow-y: auto;
            opacity: 1;
        }}
        .panel-content::-webkit-scrollbar {{ width: 3px; }}
        .panel-content::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.1); border-radius: 3px; }}
        
        .side-panel.collapsed .panel-content {{ 
            max-height: 0; 
            padding-top: 0; 
            padding-bottom: 0; 
            opacity: 0;
            pointer-events: none;
        }}
        .toggle-icon {{ transition: transform 0.4s; font-size: 18px; }}
        .side-panel.collapsed .toggle-icon {{ transform: rotate(-90deg); }}

        #dashboard-panel {{ top: 90px; left: 24px; }}
        #notes-panel {{ top: 325px; left: 24px; }}
        #chapter-nav {{ top: 90px; right: 24px; width: 240px; }}

        .stat-card {{ background: rgba(255, 255, 255, 0.03); border-radius: 10px; padding: 12px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; border-left: 3px solid transparent; }}
        .stat-label {{ font-size: 10px; color: var(--text-muted); font-weight: 700; text-transform: uppercase; }}
        .stat-value {{ font-size: 18px; font-weight: 800; }}
        
        .notes-area {{
            width: 100%;
            height: 120px;
            background: rgba(0,0,0,0.25);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 10px;
            color: var(--text-primary);
            padding: 12px;
            font-size: 13px;
            line-height: 1.5;
            resize: none;
            outline: none;
            transition: border-color 0.2s;
        }}
        .notes-area:focus {{ border-color: var(--accent); }}

        .legend {{ position: absolute; bottom: 30px; left: 24px; display: flex; flex-direction: column; gap: 8px; padding: 16px; pointer-events: none; }}
        .legend-item {{ display: flex; align-items: center; gap: 10px; font-size: 11px; font-weight: 600; color: var(--text-muted); }}
        .legend-item .dot {{ width: 10px; height: 10px; border-radius: 50%; }}
        
        #info-panel {{ position: fixed; width: 340px; max-height: 75vh; overflow-y: auto; opacity: 0; pointer-events: none; transition: opacity 0.3s, transform 0.3s; transform: scale(0.92); z-index: 200; }}
        #info-panel.visible {{ opacity: 1; pointer-events: auto; transform: scale(1); }}
        #info-panel::-webkit-scrollbar {{ width: 4px; }} #info-panel::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.15); border-radius: 4px; }}

        .badge {{ display: inline-block; padding: 3px 10px; border-radius: 6px; font-size: 10px; font-weight: 800; }}
        .type-macro {{ background: rgba(56,189,248,0.15); color: var(--accent); }}
        .close-btn {{ position: absolute; top: 12px; right: 12px; background: rgba(255,255,255,0.08); border: none; color: var(--text-muted); width: 28px; height: 28px; border-radius: 50%; cursor: pointer; font-size: 18px; display: flex; align-items: center; justify-content: center; transition: 0.2s; z-index: 10; }}
        .close-btn:hover {{ background: rgba(248,113,113,0.3); color: #fff; }}
        
        .node-header {{ display: flex; align-items: center; gap: 14px; margin: 12px 0 16px; }}
        .mastery-ring {{ position: relative; width: 56px; height: 56px; flex-shrink: 0; }}
        .mastery-ring svg {{ transform: rotate(-90deg); }}
        .mastery-ring .pct {{ position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 800; color: #fff; }}
        
        .bloom-badge {{ display: inline-block; padding: 4px 10px; border-radius: 6px; font-size: 10px; font-weight: 800; margin-top: 4px; }}
        .section-hdr {{ font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 1.5px; color: var(--text-muted); margin: 18px 0 10px; padding-bottom: 6px; border-bottom: 1px solid rgba(255,255,255,0.08); display: flex; align-items: center; gap: 8px; }}
        
        .res-card {{ background: rgba(255,255,255,0.04); padding: 8px 12px; border-radius: 10px; font-size: 12px; color: var(--text-primary); border: 1px solid rgba(255,255,255,0.06); margin-bottom: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; cursor: pointer; }}
        .res-card:hover {{ background: rgba(255,255,255,0.08); border-color: var(--accent); }}
        
        .cta-btn {{ display: block; width: 100%; padding: 12px; border-radius: 12px; border: none; font-size: 14px; font-weight: 700; cursor: pointer; text-align: center; transition: all 0.2s; margin-top: 10px; }}
        .cta-learn {{ background: linear-gradient(135deg, #2563eb, #7c3aed); color: #fff; }}
        .cta-learn:hover {{ filter: brightness(1.2); transform: translateY(-2px); box-shadow: 0 8px 24px rgba(37,99,235,0.4); }}
        .cta-assess {{ background: rgba(56,189,248,0.12); color: var(--accent); border: 1px solid rgba(56,189,248,0.3); }}
        .cta-assess:hover {{ background: rgba(56,189,248,0.25); transform: translateY(-2px); }}
        
        .mini-bloom {{ display: flex; align-items: center; gap: 8px; margin-bottom: 6px; font-size: 10px; }}
        .mini-bloom .lbl {{ width: 28px; font-weight: 700; color: var(--text-muted); }}
        .mini-bloom .bar {{ flex: 1; height: 6px; background: rgba(255,255,255,0.08); border-radius: 3px; overflow: hidden; }}
        .mini-bloom .bar .fill {{ height: 100%; border-radius: 3px; transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1); }}
        .mini-bloom .val {{ width: 35px; text-align: right; color: var(--text-muted); font-weight: 600; }}

        /* ── Progress Breadcrumb ── */
        #progress-bar {{ position: absolute; top: 18px; left: 50%; transform: translateX(-50%); display: flex; align-items: center; gap: 4px; z-index: 50; max-width: 65vw; overflow-x: auto; padding: 12px 20px; opacity: 0.85; pointer-events: auto; }}
        #progress-bar::-webkit-scrollbar {{ height: 3px; }} #progress-bar::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.15); border-radius: 3px; }}
        .prog-item {{ display: flex; flex-direction: column; align-items: center; gap: 4px; min-width: 80px; cursor: pointer; padding: 8px; border-radius: 12px; transition: all 0.2s; }}
        .prog-item:hover {{ background: rgba(255,255,255,0.05); }}
        .prog-label {{ font-size: 10px; font-weight: 700; color: var(--text-muted); white-space: nowrap; max-width: 80px; overflow: hidden; text-overflow: ellipsis; text-align: center; }}
        .prog-bar {{ width: 70px; height: 5px; background: rgba(255,255,255,0.08); border-radius: 3px; overflow: hidden; }}
        .prog-fill {{ height: 100%; background: var(--accent); border-radius: 3px; transition: width 0.6s ease-out; }}
        .prog-pct {{ font-size: 10px; font-weight: 800; color: var(--text-muted); }}
        .prog-arrow {{ color: rgba(255,255,255,0.15); font-size: 14px; font-weight: 800; margin: 0 4px; flex-shrink: 0; }}

        /* ── TOC Items ── */
        .nav-item {{ display: flex; align-items: center; gap: 10px; padding: 10px 12px; border-radius: 10px; font-size: 12px; font-weight: 600; color: var(--text-muted); cursor: pointer; transition: all 0.2s; border: 1px solid transparent; margin-bottom: 4px; }}
        .nav-item:hover {{ background: rgba(56,189,248,0.1); color: var(--text-primary); border-color: rgba(56,189,248,0.2); }}
        .nav-icon {{ font-size: 16px; color: var(--accent); opacity: 0.7; }}

        /* ── Lesson Group Cards in Info Panel ── */
        .lesson-group {{ margin-bottom: 8px; border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; overflow: hidden; }}
        .lesson-header {{ display: flex; align-items: center; gap: 10px; padding: 10px 12px; background: rgba(255,255,255,0.03); cursor: pointer; transition: background 0.2s; }}
        .lesson-header:hover {{ background: rgba(56,189,248,0.08); }}
        .lesson-step {{ width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 800; color: #fff; flex-shrink: 0; }}
        .lesson-title {{ flex: 1; font-size: 12px; font-weight: 700; color: var(--text-primary); line-height: 1.4; }}
        .lesson-mastery {{ font-size: 10px; font-weight: 800; padding: 3px 8px; border-radius: 6px; }}
        .lesson-resources {{ padding: 6px 12px 10px 44px; display: none; }}
        .lesson-resources.open {{ display: block; }}
        .lesson-res-item {{ font-size: 11px; color: var(--text-muted); padding: 5px 0; display: flex; align-items: center; gap: 8px; cursor: pointer; transition: color 0.2s; }}
        .lesson-res-item:hover {{ color: var(--text-primary); }}

        #loading-screen {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: var(--bg-color); z-index: 2000; display: flex; flex-direction: column; align-items: center; justify-content: center; transition: opacity 0.8s; }}
        .loader-ring {{ width: 64px; height: 64px; border: 4px solid rgba(56, 189, 248, 0.2); border-top-color: var(--accent); border-radius: 50%; animation: spin 1s infinite linear; }}
        @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
        #toast-container {{ position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%); z-index: 1000; pointer-events: none; }}
        .toast {{ background: var(--glass-bg); border: 1px solid var(--accent); padding: 12px 24px; border-radius: 12px; font-size: 14px; font-weight: 600; box-shadow: 0 10px 40px rgba(0,0,0,0.5); animation: toast-up 0.3s ease-out; }}
        @keyframes toast-up {{ from {{ transform: translateY(20px); opacity: 0; }} to {{ transform: translateY(0); opacity: 1; }} }}
        
        /* ── Mobile Responsive ── */
        @media (max-width: 768px) {{
            header h1 {{ display: none; }}
            .header-center {{ display: none; }}
            .side-panel {{ width: 200px; left: 12px; right: auto; }}
            #chapter-nav {{ top: auto; bottom: 80px; left: 12px; }}
            #notes-panel {{ top: auto; bottom: 260px; left: 12px; }}
            #progress-bar {{ max-width: 90vw; padding: 8px 12px; }}
            .prog-item {{ min-width: 60px; padding: 6px; }}
            .prog-label, .prog-pct {{ font-size: 8px; }}
            .prog-bar {{ width: 50px; }}
        }}
    </style>
</head>
<body>
    <div id="loading-screen">
        <div class="loader-ring"></div>
        <div class="loader-ring" style="width:48px;height:48px;border-color:rgba(124,58,237,0.15);border-top-color:#7c3aed;animation-direction:reverse;position:absolute;"></div>
        <div style="margin-top: 32px; font-size:16px; font-weight:700; letter-spacing:4px; background:linear-gradient(135deg,#38bdf8,#818cf8,#c084fc); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">INITIALIZING GALAXY</div>
        <div style="margin-top:10px;font-size:11px;color:rgba(255,255,255,0.3);letter-spacing:1px;text-transform:uppercase;">Personalized Knowledge Tree v3.0</div>
    </div>

    <div id="3d-graph"></div>

    <div id="ui-overlay">
        <!-- Removed redundant header and toolbar -->


        <div id="progress-bar" class="glass-panel"><div id="progress-chapters" style="display:flex;align-items:center;gap:4px;"></div></div>

        <div id="dashboard-panel" class="side-panel glass-panel">
            <div class="panel-header" onclick="toggleCollapse('dashboard-panel')">
                <span><span class="material-icons" style="font-size:16px; vertical-align: middle; margin-right:6px;">analytics</span> THỐNG KÊ</span>
                <span class="material-icons toggle-icon">expand_more</span>
            </div>
            <div class="panel-content">
                <div class="stat-card" style="border-left-color: var(--green)"><span class="stat-label">MASTERED</span><span class="stat-value" id="stat-mastered">0</span></div>
                <div class="stat-card" style="border-left-color: var(--yellow)"><span class="stat-label">LEARNING</span><span class="stat-value" id="stat-learning">0</span></div>
                <div class="stat-card" style="border-left-color: var(--red)"><span class="stat-label">WEAK</span><span class="stat-value" id="stat-weak">0</span></div>
            </div>
        </div>

        <div id="notes-panel" class="side-panel glass-panel">
            <div class="panel-header" onclick="toggleCollapse('notes-panel')">
                <span><span class="material-icons" style="font-size:16px; vertical-align: middle; margin-right:6px;">edit_note</span> GHI CHÚ</span>
                <span class="material-icons toggle-icon">expand_more</span>
            </div>
            <div class="panel-content">
                <textarea class="notes-area" placeholder="Ghi chú bài học tại đây..."></textarea>
            </div>
        </div>

        <div id="chapter-nav" class="side-panel glass-panel">
            <div class="panel-header" onclick="toggleCollapse('chapter-nav')">
                <span><span class="material-icons" style="font-size:16px; vertical-align: middle; margin-right:6px;">menu_book</span> MỤC LỤC</span>
                <span class="material-icons toggle-icon">expand_more</span>
            </div>
            <div class="panel-content" id="chapter-list"></div>
        </div>

        <div class="legend glass-panel">
            <div class="legend-item"><span class="dot" style="background:var(--accent)"></span> Chương / Topic</div>
            <div class="legend-item"><span class="dot" style="background:var(--green)"></span> Mastered (&gt;80%)</div>
            <div class="legend-item"><span class="dot" style="background:var(--yellow)"></span> Developing</div>
            <div class="legend-item"><span class="dot" style="background:var(--red)"></span> Weak Point</div>
        </div>

        <div id="info-panel" class="glass-panel">
            <button class="close-btn" onclick="closePanel()" title="Đóng">&times;</button>
            <div id="info-type" class="badge type-macro">SELECT A NODE</div>
            <h2 id="info-title" style="font-size:18px;font-weight:800;margin:6px 0 0;line-height:1.3;padding-right:32px;">Star Map</h2>
            <div class="node-header">
                <div class="mastery-ring" id="mastery-ring">
                    <svg width="56" height="56"><circle cx="28" cy="28" r="24" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="4"/><circle id="ring-fill" cx="28" cy="28" r="24" fill="none" stroke="var(--accent)" stroke-width="4" stroke-dasharray="150.8" stroke-dashoffset="150.8" stroke-linecap="round"/></svg>
                    <div class="pct" id="ring-pct">0%</div>
                </div>
                <div>
                    <div id="bloom-badge" class="bloom-badge" style="background:rgba(74,222,128,0.15);color:#4ade80;">L1 Ghi nhớ</div>
                    <div style="font-size:11px;color:var(--text-muted);margin-top:4px;" id="info-subtitle">Chọn node để xem chi tiết</div>
                </div>
            </div>
            <div id="learn-section" style="display:none;">
                <div class="section-hdr"><span class="material-icons" style="font-size:16px;">school</span> Học tập</div>
                <div id="learn-resources"></div>
                <button class="cta-btn cta-learn" onclick="startAction('video')">▶ &nbsp;Bắt đầu bài học</button>
            </div>
            <div id="assess-section">
                <div class="section-hdr"><span class="material-icons" style="font-size:16px;">psychology</span> Đánh giá năng lực</div>
                <div id="mini-bloom-bars"></div>
                <button class="cta-btn cta-assess" onclick="startAction('bloom_hub')">🧪 &nbsp;Bloom Assessment Hub</button>
            </div>
        </div>
        <div id="toast-container"></div>
    </div>

    <script>
        const GRAPH_DATA = {json_string};
        const USER_STATE = {{
            "mastery": {mastery_map_json},
            "inferred_blooms": {bloom_map_json},
            "stats": {stats_json}
        }};
        const CHAPTER_LIST = {chapter_list_json};
        let Graph = null;

        // ═══ UI LOGIC ═══
        function toggleCollapse(id) {{
            document.getElementById(id).classList.toggle('collapsed');
        }}



        function renderChapterNav() {{
            const container = document.getElementById('chapter-list');
            if (!container) return;
            container.innerHTML = '';
            CHAPTER_LIST.forEach(ch => {{
                const item = document.createElement('div');
                item.className = 'nav-item';
                item.innerHTML = '<span class="material-icons nav-icon">folder</span> ' + ch.title;
                item.onclick = function() {{ focusNode(ch.id); }};
                container.appendChild(item);
            }});
        }}

        function renderProgressBar() {{
            const container = document.getElementById('progress-chapters');
            if (!container) return;
            container.innerHTML = '';
            CHAPTER_LIST.forEach((ch, idx) => {{
                const mesoNodes = GRAPH_DATA.nodes.filter(n => n.type === 'meso' && n.id.startsWith(ch.id + '_'));
                let totalM = 0, cnt = 0;
                mesoNodes.forEach(mn => {{ totalM += getMasteryLevel(mn.id); cnt++; }});
                const pct = cnt > 0 ? Math.round((totalM / cnt) * 100) : 0;
                
                const item = document.createElement('div');
                item.className = 'prog-item';
                const shortTitle = ch.title.length > 12 ? ch.title.substring(0, 10) + '\u2026' : ch.title;
                item.innerHTML = `
                    <div class="prog-label">${{shortTitle}}</div>
                    <div class="prog-bar"><div class="prog-fill" style="width:${{pct}}%; background:${{pct>=80?'var(--green)':'var(--accent)'}}"></div></div>
                    <div class="prog-pct" style="color:${{pct>=80?'var(--green)':'var(--text-muted)'}}">${{pct}}%</div>
                `;
                item.onclick = function() {{ focusNode(ch.id); }};
                container.appendChild(item);
                
                if (idx < CHAPTER_LIST.length - 1) {{
                    const arrow = document.createElement('span');
                    arrow.className = 'prog-arrow';
                    arrow.textContent = '\u2192';
                    container.appendChild(arrow);
                }}
            }});
        }}

        function focusNode(nodeId) {{
            const node = GRAPH_DATA.nodes.find(n => n.id === nodeId);
            if (node && Graph) {{
                Graph.cameraPosition(
                    {{ x: node.x * 1.6, y: node.y * 1.6, z: node.z * 1.6 }},
                    node, 1500
                );
            }}
        }}

        // ═══ GRAPH HELPER FUNCTIONS ═══
        function getMasteryLevel(id) {{ 
            const node = GRAPH_DATA.nodes.find(n => n.id === id);
            if (node && node.type === 'meso') {{
                let total = 0, count = 0;
                (node.micro_children || []).forEach(c => {{
                    total += (USER_STATE.mastery[c.id] || 0);
                    count++;
                }});
                return count > 0 ? total / count : 0;
            }}
            return USER_STATE.mastery[id] || 0; 
        }}
        
        function getBloomLevel(id) {{
            const node = GRAPH_DATA.nodes.find(n => n.id === id);
            if (node && node.type === 'meso') {{
                let total = 0, count = 0;
                (node.micro_children || []).forEach(c => {{
                    total += (USER_STATE.inferred_blooms[c.id] || 0);
                    count++;
                }});
                return count > 0 ? total / count : 0;
            }}
            return USER_STATE.inferred_blooms[id] || 0; 
        }}

        function getNodeStatus(n) {{
            if (n.type === 'macro') return 'macro';
            const m = getMasteryLevel(n.id);
            if (m >= 0.8) return 'mastered';
            if (m >= 0.4) return 'learning';
            return 'weak';
        }}
        
        function getNodeColor(n) {{
            if (n.type === 'macro') return 'hsl(210, 80%, 60%)'; 
            const bloom = getBloomLevel(n.id);
            if (bloom === 0) return 'hsl(210, 20%, 30%)';
            if (bloom < 1.0) return 'hsl(210, 20%, 40%)'; 
            let h = 200, s = 80, l = 50;
            if (bloom < 2.0) {{ h = 200; s = 80; l = 50; }} // L1
            else if (bloom < 3.0) {{ h = 140; s = 70; l = 45; }} // L2
            else if (bloom < 4.0) {{ h = 45; s = 90; l = 50; }} // L3
            else if (bloom < 5.0) {{ h = 20; s = 85; l = 55; }} // L4
            else {{ h = 280; s = 80; l = 60; }} // L5/L6
            return `hsl(${{h}}, ${{s}}%, ${{l}}%)`;
        }}
        
        function isLocked(n) {{
            if (n.type === 'macro') return false;
            return (n.prerequisites || []).some(p => getMasteryLevel(p) < 0.6);
        }}

        function getShortLabel(node) {{
            if (node.type === 'macro') {{
                const match = node.id.match(/(\d+)/);
                if (match) {{
                    const num = match[1];
                    if (num === '999') return '✉ Phụ lục';
                    return 'Ch.' + num + ': ' + (node.label || '').substring(0, 14);
                }}
                return (node.label || node.id).substring(0, 16);
            }}
            if (node.micro_children && node.micro_children.length > 0) {{
                const t = node.micro_children[0].title || node.label || '';
                return t.length > 22 ? t.substring(0, 20) + '…' : t;
            }}
            return (node.label || node.id).substring(0, 20);
        }}

        function updateStats() {{
            let m=0, l=0, w=0;
            GRAPH_DATA.nodes.forEach(n => {{
                if (n.type !== 'macro') {{
                    const s = getNodeStatus(n);
                    if (s === 'mastered') m++; else if (s === 'learning') l++; else w++;
                }}
            }});
            document.getElementById('stat-mastered').innerText = m;
            document.getElementById('stat-learning').innerText = l;
            document.getElementById('stat-weak').innerText = w;
        }}

        // ═══ INFO PANEL LOGIC ═══
        function closePanel() {{
            document.getElementById('info-panel').classList.remove('visible');
            window.currentNodeId = null;
        }}

        function startAction(type) {{
            if (!window.currentNodeId) return;
            const node = GRAPH_DATA.nodes.find(n => n.id === window.currentNodeId);
            const payload = {{ 
                id: window.currentNodeId, 
                action: type,
                label: document.getElementById('info-title').innerText,
                children: node && node.micro_children ? node.micro_children : []
            }};
            if (window.parent) window.parent.postMessage({{ type: 'graph3d_action', payload }}, '*');
            showToast('🚀 Đang mở ' + (type === 'video' ? 'Bài giảng' : 'Bloom Hub'));
        }}

        function showToast(msg) {{
            const container = document.getElementById('toast-container');
            const t = document.createElement('div');
            t.className = 'toast';
            t.innerText = msg;
            container.appendChild(t);
            setTimeout(() => {{
                t.style.opacity = '0';
                t.style.transform = 'translateY(-20px)';
                setTimeout(() => t.remove(), 300);
            }}, 3000);
        }}

        function positionPanel(node) {{
            const panel = document.getElementById('info-panel');
            const renderer = Graph.renderer();
            const camera = Graph.camera();
            const vec = new THREE.Vector3(node.x, node.y, node.z);
            vec.project(camera);
            const hw = renderer.domElement.clientWidth / 2;
            const hh = renderer.domElement.clientHeight / 2;
            let sx = (vec.x * hw) + hw + 40;
            let sy = -(vec.y * hh) + hh - 60;
            const pw = 340, ph = panel.offsetHeight || 400, margin = 20;
            if (sx + pw > window.innerWidth - margin) sx = window.innerWidth - pw - margin;
            if (sx < margin) sx = margin;
            if (sy + ph > window.innerHeight - margin) sy = window.innerHeight - ph - margin;
            if (sy < margin) sy = margin;
            panel.style.left = sx + 'px';
            panel.style.top = sy + 'px';
        }}

        function renderMasteryRing(mastery) {{
            const circumference = 2 * Math.PI * 24; 
            const offset = circumference * (1 - mastery);
            const fill = document.getElementById('ring-fill');
            fill.style.strokeDasharray = circumference;
            fill.style.strokeDashoffset = offset;
            fill.style.stroke = mastery >= 0.8 ? '#4ade80' : mastery >= 0.4 ? '#fbbf24' : mastery > 0 ? '#f87171' : 'rgba(255,255,255,0.2)';
            document.getElementById('ring-pct').innerText = Math.round(mastery * 100) + '%';
        }}

        const BLOOM_LABELS = {{1:'Ghi nhớ',2:'Hiểu',3:'Áp dụng',4:'Phân tích',5:'Đánh giá',6:'Sáng tạo'}};
        const BLOOM_COLORS = {{1:'#60a5fa',2:'#4ade80',3:'#fbbf24',4:'#fb923c',5:'#f87171',6:'#c084fc'}};

        function renderBloomBadge(bloomLevel) {{
            const badge = document.getElementById('bloom-badge');
            const lvl = Math.max(1, Math.min(6, Math.ceil(bloomLevel || 0)));
            const label = BLOOM_LABELS[lvl] || 'Chưa đánh giá';
            const color = BLOOM_COLORS[lvl] || '#60a5fa';
            badge.style.background = color + '22';
            badge.style.color = color;
            badge.innerText = bloomLevel > 0 ? ('L' + lvl + ' ' + label) : '\u23f3 Ch\u01b0a \u0111\u00e1nh gi\u00e1';
        }}

        function renderMiniBloom(nodeId) {{
            const container = document.getElementById('mini-bloom-bars');
            container.innerHTML = '';
            for (let lvl = 1; lvl <= 3; lvl++) {{
                const bloom = getBloomLevel(nodeId);
                const pct = bloom >= lvl ? 100 : (bloom >= lvl - 1 ? (bloom - (lvl-1)) * 100 : 0);
                container.innerHTML += `
                    <div class="mini-bloom">
                        <span class="lbl">L${{lvl}}</span>
                        <div class="bar"><div class="fill" style="width:${{Math.round(pct)}}%; background:${{BLOOM_COLORS[lvl]}}"></div></div>
                        <span class="val">${{Math.round(pct)}}%</span>
                    </div>`;
            }}
        }}

        function toggleLesson(idx) {{
            const el = document.getElementById('lg_' + idx);
            if (el) el.classList.toggle('open');
        }}

        function renderLearnResources(node) {{
            const container = document.getElementById('learn-resources');
            container.innerHTML = '';
            const children = node.micro_children || [];
            if (children.length === 0) {{
                const res = node.resources || [];
                res.slice(0, 5).forEach(r => {{
                    if (!r || !r.url) return;
                    container.innerHTML += `<div class="res-card">${{r.icon || '📎'}} ${{r.title || 'Tài nguyên'}}</div>`;
                }});
                return;
            }}
            const stepColors = ['#3b82f6','#8b5cf6','#06b6d4','#10b981','#f59e0b','#ef4444'];
            children.forEach((child, idx) => {{
                const mastery = USER_STATE.mastery[child.id] || 0;
                const mPct = Math.round(mastery * 100);
                const color = stepColors[idx % stepColors.length];
                const mColor = mastery >= 0.8 ? 'var(--green)' : mastery >= 0.4 ? 'var(--yellow)' : 'rgba(255,255,255,0.3)';
                const mBg = mastery >= 0.8 ? 'rgba(74,222,128,0.15)' : mastery >= 0.4 ? 'rgba(251,191,36,0.15)' : 'rgba(255,255,255,0.05)';
                
                let html = `
                    <div class="lesson-group">
                        <div class="lesson-header" onclick="toggleLesson(${{idx}})">
                            <div class="lesson-step" style="background:${{color}}">${{idx + 1}}</div>
                            <div class="lesson-title">${{child.title}}</div>
                            <div class="lesson-mastery" style="color:${{mColor}}; background:${{mBg}}">${{mPct}}%</div>
                        </div>
                        <div class="lesson-resources" id="lg_${{idx}}">`;
                
                (child.resources || []).forEach(r => {{
                    const rIcon = r.type === 'youtube' ? '🎬' : '📄';
                    html += `<div class="lesson-res-item"><span>${{rIcon}}</span> ${{r.title}}</div>`;
                }});
                if (!(child.resources || []).length) html += `<div class="lesson-res-item" style="opacity:0.4">Ch\u01b0a c\u00f3 t\u00e0i nguy\u00ean</div>`;
                
                html += `</div></div>`;
                container.innerHTML += html;
            }});
        }}

        // ═══ CORE GRAPH INIT ═══
        function init() {{
            updateStats();
            renderChapterNav();
            renderProgressBar();

            Graph = ForceGraph3D()(document.getElementById('3d-graph'))
                .graphData(GRAPH_DATA)
                .backgroundColor('#060714')
                .showNavInfo(false)
                .dagMode('radialout')
                .dagLevelDistance(65)
                .d3AlphaDecay(0.02)
                .d3VelocityDecay(0.3)
                .nodeVal('val')
                .nodeLabel(n => (isLocked(n) ? '🔒 ' : '') + (n.label || n.id))
                .nodeThreeObject(node => {{
                    const group = new THREE.Group();
                    const color = new THREE.Color(getNodeColor(node));
                    
                    if (node.type === 'macro') {{
                        // STAR style
                        const coreGeo = new THREE.IcosahedronGeometry(node.val / 2.2, 2);
                        const coreMat = new THREE.MeshPhongMaterial({{ color, emissive: color, emissiveIntensity: 0.8, transparent: true, opacity: 0.95, shininess: 120 }});
                        group.add(new THREE.Mesh(coreGeo, coreMat));
                        
                        const glowGeo = new THREE.SphereGeometry(node.val / 1.8, 24, 16);
                        const glowMat = new THREE.MeshBasicMaterial({{ color, transparent: true, opacity: 0.12, side: THREE.BackSide }});
                        group.add(new THREE.Mesh(glowGeo, glowMat));
                        
                        const ringGeo = new THREE.TorusGeometry(node.val / 1.6, 0.35, 16, 64);
                        const ringMat = new THREE.MeshBasicMaterial({{ color, transparent: true, opacity: 0.25 }});
                        const ring = new THREE.Mesh(ringGeo, ringMat);
                        ring.rotation.x = Math.PI / 2.5;
                        group.add(ring);
                    }} else {{
                        // PLANET style
                        const mastery = getMasteryLevel(node.id);
                        const radius = node.val / 2.8;
                        const coreGeo = new THREE.SphereGeometry(radius, 24, 18);
                        const coreMat = new THREE.MeshPhongMaterial({{ color, emissive: color, emissiveIntensity: mastery > 0.5 ? 0.6 : 0.25, transparent: true, opacity: isLocked(node) ? 0.2 : 0.92, shininess: 80 }});
                        group.add(new THREE.Mesh(coreGeo, coreMat));
                        
                        if (!isLocked(node)) {{
                            const atmoGeo = new THREE.SphereGeometry(radius * 1.35, 24, 18);
                            const atmoMat = new THREE.MeshBasicMaterial({{ color, transparent: true, opacity: 0.08, side: THREE.BackSide }});
                            group.add(new THREE.Mesh(atmoGeo, atmoMat));
                        }}
                        
                        if (node.next_best) {{
                            const pGeo = new THREE.TorusGeometry(radius * 1.6, 0.5, 16, 48);
                            const pMat = new THREE.MeshBasicMaterial({{ color: 0x38bdf8, transparent: true, opacity: 0.7 }});
                            const pRing = new THREE.Mesh(pGeo, pMat);
                            pRing.rotation.x = Math.PI / 2;
                            group.add(pRing);
                        }}
                    }}
                    
                    const label = new SpriteText(getShortLabel(node));
                    label.color = '#ffffff';
                    label.textHeight = node.type === 'macro' ? 3.5 : 2;
                    label.backgroundColor = label.backgroundColor = node.type === 'macro' ? 'rgba(15,20,50,0.85)' : 'rgba(10,15,40,0.75)';
                    label.padding = node.type === 'macro' ? [3, 6] : [2, 4];
                    label.borderRadius = node.type === 'macro' ? 6 : 4;
                    label.fontFace = 'Inter, sans-serif';
                    label.fontWeight = node.type === 'macro' ? '700' : '500';
                    const yOff = node.type === 'macro' ? node.val / 1.2 + 8 : node.val / 2 + 6;
                    label.position.set(0, yOff, 0);
                    label.material.depthTest = false;
                    label.renderOrder = 999;
                    group.add(label);
                    
                    return group;
                }})
                .nodeThreeObjectExtend(false)
                .linkColor(l => l.relation === 'macro_path' ? 'rgba(100, 160, 255, 0.35)' : 'rgba(56, 189, 248, 0.18)')
                .linkWidth(l => l.relation === 'macro_path' ? 2 : 0.5)
                .linkDirectionalParticles(l => l.relation === 'prerequisite_for' ? 4 : 1)
                .linkDirectionalParticleWidth(1.5)
                .linkDirectionalParticleSpeed(0.004)
                .onBackgroundClick(() => closePanel())
                .onNodeClick(n => {{
                    if (isLocked(n)) return;
                    focusNode(n.id);
                    window.currentNodeId = n.id;
                    const pType = document.getElementById('info-type');
                    pType.className = 'badge';
                    if (n.type === 'macro') {{ pType.classList.add('type-macro'); pType.innerText = 'CH\u01af\u01a0NG KI\u1ebeN TH\u1ee8C'; }}
                    else {{ pType.style.background = getNodeColor(n) + '33'; pType.style.color = getNodeColor(n); pType.innerText = 'PH\u1ea6N B\u00c0I H\u1eccc'; }}
                    document.getElementById('info-title').innerText = n.label || n.id;
                    const mastery = getMasteryLevel(n.id);
                    renderMasteryRing(mastery);
                    renderBloomBadge(getBloomLevel(n.id));
                    document.getElementById('info-subtitle').innerText = mastery >= 0.8 ? '\u0110\u00e3 th\u00e0nh th\u1ea1o' : mastery >= 0.4 ? '\u0110ang h\u1ecdc' : 'Ch\u01b0a b\u1eaft \u0111\u1ea7u';
                    
                    const learnSec = document.getElementById('learn-section');
                    if (n.type !== 'macro') {{ learnSec.style.display = 'block'; renderLearnResources(n); }}
                    else {{ learnSec.style.display = 'none'; }}
                    
                    document.getElementById('assess-section').style.display = n.type === 'macro' ? 'none' : 'block';
                    if (n.type !== 'macro') renderMiniBloom(n.id);
                    
                    const panel = document.getElementById('info-panel');
                    panel.classList.add('visible');
                    setTimeout(() => positionPanel(n), 50);
                }});

            // Lighting
            const scene = Graph.scene();
            scene.add(new THREE.AmbientLight(0x1a1a3a, 1.5));
            const keyLight = new THREE.DirectionalLight(0x6090ff, 0.8);
            keyLight.position.set(150, 250, 100);
            scene.add(keyLight);
            const fillLight = new THREE.DirectionalLight(0xff6040, 0.3);
            fillLight.position.set(-100, -50, -100);
            scene.add(fillLight);
            const rimLight = new THREE.PointLight(0x38bdf8, 1.0, 800);
            rimLight.position.set(0, 120, 0);
            scene.add(rimLight);
            const accentLight = new THREE.PointLight(0x7c3aed, 0.5, 500);
            accentLight.position.set(-80, -40, 60);
            scene.add(accentLight);

            // ═══ STARFIELD BACKGROUND ═══
            const starGeo = new THREE.BufferGeometry();
            const starCount = 2500;
            const starPos = new Float32Array(starCount * 3);
            const starSizes = new Float32Array(starCount);
            for (let i = 0; i < starCount; i++) {{
                starPos[i*3] = (Math.random() - 0.5) * 2000;
                starPos[i*3+1] = (Math.random() - 0.5) * 2000;
                starPos[i*3+2] = (Math.random() - 0.5) * 2000;
                starSizes[i] = Math.random() * 1.5 + 0.3;
            }}
            starGeo.setAttribute('position', new THREE.BufferAttribute(starPos, 3));
            starGeo.setAttribute('size', new THREE.BufferAttribute(starSizes, 1));
            const starMat = new THREE.PointsMaterial({{
                color: 0xccddff, size: 0.8, transparent: true, opacity: 0.7,
                sizeAttenuation: true, blending: THREE.AdditiveBlending
            }});
            scene.add(new THREE.Points(starGeo, starMat));
            // Nebula cloud (second layer, warmer stars)
            const nebGeo = new THREE.BufferGeometry();
            const nebPos = new Float32Array(500 * 3);
            for (let i = 0; i < 500; i++) {{
                nebPos[i*3] = (Math.random() - 0.5) * 1200;
                nebPos[i*3+1] = (Math.random() - 0.5) * 600;
                nebPos[i*3+2] = (Math.random() - 0.5) * 1200;
            }}
            nebGeo.setAttribute('position', new THREE.BufferAttribute(nebPos, 3));
            const nebMat = new THREE.PointsMaterial({{
                color: 0x6040ff, size: 2.0, transparent: true, opacity: 0.15,
                sizeAttenuation: true, blending: THREE.AdditiveBlending
            }});
            scene.add(new THREE.Points(nebGeo, nebMat));

            // ═══ POST-PROCESSING BLOOM ═══
            try {{
                const renderer = Graph.renderer();
                renderer.toneMapping = THREE.ReinhardToneMapping;
                renderer.toneMappingExposure = 1.2;
                const composer = new THREE.EffectComposer(renderer);
                const renderPass = new THREE.RenderPass(scene, Graph.camera());
                composer.addPass(renderPass);
                const bloomPass = new THREE.UnrealBloomPass(
                    new THREE.Vector2(window.innerWidth, window.innerHeight),
                    0.8, 0.4, 0.85
                );
                composer.addPass(bloomPass);
                // Override render loop
                const origTick = Graph._animationCycle || null;
                (function animate() {{
                    requestAnimationFrame(animate);
                    composer.render();
                }})();
            }} catch(bErr) {{
                console.log('Bloom postprocessing not available:', bErr);
            }}

            // ═══ CINEMATIC INTRO ═══
            Graph.cameraPosition({{ x: 0, y: 0, z: 500 }}, {{ x: 0, y: 0, z: 0 }}, 0);
            setTimeout(() => {{
                Graph.cameraPosition({{ x: 80, y: 40, z: 200 }}, {{ x: 0, y: 0, z: 0 }}, 2500);
            }}, 800);

            document.getElementById('loading-screen').style.opacity = '0';
            setTimeout(() => document.getElementById('loading-screen').remove(), 1000);
            setTimeout(() => renderProgressBar(), 1500);

            window.addEventListener('resize', () => {{
                const w = window.innerWidth || document.documentElement.clientWidth;
                const h = window.innerHeight || document.documentElement.clientHeight;
                if(Graph && w > 0 && h > 0) {{
                    Graph.width(w).height(h);
                }}
            }});
            setTimeout(() => window.dispatchEvent(new Event('resize')), 500);
        }}
        // Safety: always dismiss loading after 5s even if error
        setTimeout(() => {{
            const ls = document.getElementById('loading-screen');
            if (ls) {{ ls.style.opacity = '0'; setTimeout(() => ls.remove(), 500); }}
        }}, 5000);
        window.addEventListener('DOMContentLoaded', function() {{
            try {{ init(); }} catch(e) {{
                console.error('Galaxy init error:', e);
                const ls = document.getElementById('loading-screen');
                if (ls) {{ ls.style.opacity = '0'; setTimeout(() => ls.remove(), 500); }}
            }}
        }});
        setInterval(() => {{
            fetch(`/user_data/{user_id}/states/student_state.json?t=${{Date.now()}}`)
                .then(r => r.json())
                .then(data => {{ 
                    if(data) {{ 
                        if(data.nodes_mastery) USER_STATE.mastery = data.nodes_mastery; 
                        if(data.inferred_blooms) USER_STATE.inferred_blooms = data.inferred_blooms;
                        updateStats(); 
                        if(Graph) Graph.nodeColor(getNodeColor);
                    }} 
                }})
                .catch(e => console.log(e));
        }}, 5000);
    </script>
</body>
</html>"""

    # Final File Writing
    output_html = f"user_data/{user_id}/current_visual_tree.html"
    with open(output_html, "w", encoding="utf-8", errors="replace") as f:
        f.write(html_content)
    
    print(f"✅ Success! 3D Interface created at: {output_html}")

if __name__ == "__main__":
    visualize_knowledge_tree(user_id="sv01")