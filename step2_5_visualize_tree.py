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

def visualize_knowledge_tree(user_id, input_json_path=None):
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

    # 2. Get Student State
    from database import get_user_by_username
    from pkt_engine import StudentState
    
    db_user = get_user_by_username(user_id)
    user_db_id = db_user.id if db_user else 1
    student_state = StudentState(user_db_id)
    
    # Pass mastery/bloom of all micro nodes from DB cache to Front-End 
    # (since the graph only shows meso nodes, JS will average their micro children)
    mastery_map = {cid: student_state.get_mastery(cid) for cid in student_state.knowledge_cache.keys()}
    bloom_map = {cid: student_state.calculate_inferred_bloom(cid) for cid in student_state.knowledge_cache.keys()}
    
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

    html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Knowledge Galaxy 3D — PKT Bio-Tutor</title>
    <script src="https://unpkg.com/three@0.141.0/build/three.min.js"></script>
    <script src="https://unpkg.com/3d-force-graph@1.70.16/dist/3d-force-graph.min.js"></script>
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
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ overflow: hidden; font-family: 'Inter', sans-serif; color: var(--text-primary); background: var(--bg-color); }}
        #3d-graph {{ position: absolute; top: 0; left: 0; width: 100vw; height: 100vh; }}
        .glass-panel {{ background: var(--glass-bg); backdrop-filter: blur(20px); border: 1px solid var(--glass-border); border-radius: 16px; padding: 20px; pointer-events: auto; }}
        header {{ position: absolute; top: 24px; left: 24px; pointer-events: none; }}
        header h1 {{ font-size: 24px; font-weight: 800; background: linear-gradient(135deg, #38bdf8 0%, #818cf8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        #dashboard-panel {{ position: absolute; top: 90px; left: 24px; width: 230px; }}
        .stat-card {{ background: rgba(255, 255, 255, 0.03); border-radius: 10px; padding: 12px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; border-left: 3px solid transparent; }}
        .stat-label {{ font-size: 10px; color: var(--text-muted); font-weight: 700; text-transform: uppercase; }}
        .stat-value {{ font-size: 18px; font-weight: 800; }}
        .legend {{ position: absolute; bottom: 30px; left: 24px; display: flex; flex-direction: column; gap: 8px; }}
        .legend-item {{ display: flex; align-items: center; gap: 10px; font-size: 11px; font-weight: 600; color: var(--text-muted); }}
        .legend-item .dot {{ width: 10px; height: 10px; border-radius: 50%; }}
        #info-panel {{ position: absolute; top: 24px; right: 24px; width: 320px; max-height: calc(100vh - 48px); overflow-y: auto; transform: translateX(350px); transition: transform 0.5s ease; }}
        #info-panel.visible {{ transform: translateX(0); }}
        .badge {{ display: inline-block; padding: 4px 10px; border-radius: 6px; font-size: 10px; font-weight: 800; margin-bottom: 12px; }}
        .type-macro {{ background: rgba(56, 189, 248, 0.15); color: var(--accent); }}
        .resource-list {{ display: flex; flex-direction: column; gap: 8px; margin-top: 15px; margin-bottom: 15px; max-height: 150px; overflow-y: auto; }}
        .resource-item {{ display: flex; align-items: center; justify-content: space-between; gap: 8px; background: rgba(255,255,255,0.05); padding: 8px 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1); transition: 0.2s; font-size: 12px; text-decoration: none; color: var(--text-primary); cursor: pointer; }}
        .resource-item:hover {{ background: rgba(255,255,255,0.1); border-color: var(--accent); }}
        .play-btn {{ color: var(--green); opacity: 0.6; transition: 0.2s; display: flex; align-items: center; }}
        .play-btn:hover {{ opacity: 1; transform: scale(1.2); }}
        .action-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 20px; }}
        .action-btn {{ background: rgba(255,255,255,0.08); border-radius: 12px; padding: 12px; text-align: center; cursor: pointer; transition: 0.2s; border: 1px solid transparent; }}
        .action-btn:hover {{ background: rgba(255,255,255,0.12); border-color: var(--accent); }}
        #loading-screen {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: var(--bg-color); z-index: 1000; display: flex; flex-direction: column; align-items: center; justify-content: center; transition: opacity 0.8s; }}
        .loader-ring {{ width: 60px; height: 60px; border: 4px solid rgba(56, 189, 248, 0.2); border-top-color: var(--accent); border-radius: 50%; animation: spin 1s infinite linear; }}
        @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
        #toast-container {{ position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%); z-index: 9999; }}
        .toast {{ background: var(--glass-bg); border: 1px solid var(--accent); padding: 10px 20px; border-radius: 10px; font-size: 13px; font-weight: 600; box-shadow: 0 10px 40px rgba(0,0,0,0.5); }}
    </style>
</head>
<body>
    <div id="loading-screen"><div class="loader-ring"></div><div style="margin-top: 20px; color: var(--accent);">GALAXY BOOTING...</div></div>
    <div id="3d-graph"></div>
    <div id="ui-overlay">
        <header><h1>Knowledge Galaxy</h1></header>
        <div id="dashboard-panel" class="glass-panel">
            <div class="stat-card" style="border-left-color: var(--green)"><span class="stat-label">MASTERED</span><span class="stat-value" id="stat-mastered">0</span></div>
            <div class="stat-card" style="border-left-color: var(--yellow)"><span class="stat-label">LEARNING</span><span class="stat-value" id="stat-learning">0</span></div>
            <div class="stat-card" style="border-left-color: var(--red)"><span class="stat-label">WEAK</span><span class="stat-value" id="stat-weak">0</span></div>
        </div>
        <div class="legend glass-panel">
            <div class="legend-item"><span class="dot" style="background:var(--accent)"></span> Chương / Topic</div>
            <div class="legend-item"><span class="dot" style="background:var(--green)"></span> Mastered (&gt;80%)</div>
            <div class="legend-item"><span class="dot" style="background:var(--yellow)"></span> Developing</div>
            <div class="legend-item"><span class="dot" style="background:var(--red)"></span> Weak Point</div>
        </div>
        <div id="info-panel" class="glass-panel">
            <div id="info-type" class="badge type-macro">SELECT A NODE</div>
            <h2 id="info-title">Star Map</h2>
            <p id="info-desc">Select a node to view details and start learning journey.</p>
            <div id="node-resources" class="resource-list" style="display: none;"></div>
            <div id="action-buttons" style="display: none;">
                <div class="action-grid">
                    <div class="action-btn" onclick="startAction('video')">📺 VIDEO</div>
                    <div class="action-btn" onclick="startAction('quiz')">📝 QUIZ</div>
                    <div class="action-btn" onclick="startAction('ai_tutor')">🤖 AI TUTOR</div>
                    <div class="action-btn" onclick="startAction('flashcard')">📇 FLASHCARDS</div>
                </div>
            </div>
        </div>
        <div id="toast-container"></div>
    </div>
    <script>
        const GRAPH_DATA = {json_string};
        const USER_STATE = {{
            "mastery": {mastery_map_json},
            "inferred_blooms": {bloom_map_json}
        }};
        let Graph = null;

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
            if (n.type === 'macro') return 'hsl(210, 80%, 60%)'; // Solid Blue
            
            const bloom = getBloomLevel(n.id);
            if (bloom === 0) return 'hsl(210, 20%, 30%)'; // Uncharted (Gray)
            if (bloom < 1.0) return 'hsl(210, 20%, 40%)'; 
            
            let h = 200, s = 80, l = 50;
            if (bloom < 2.0) {{ // L1 - Remember
                h = 200; s = 80; l = 50;
            }} else if (bloom < 3.0) {{ // L2 - Understand
                h = 140; s = 70; l = 45;
            }} else if (bloom < 4.0) {{ // L3 - Apply
                h = 45; s = 90; l = 50;
            }} else if (bloom < 5.0) {{ // L4 - Analyze
                h = 20; s = 85; l = 55;
            }} else {{ // L5/L6 - Mastery
                h = 280; s = 80; l = 60;
            }}
            return `hsl(${{h}}, ${{s}}%, ${{l}}%)`;
        }}
        
        function isLocked(n) {{
            if (n.type === 'macro') return false;
            return (n.prerequisites || []).some(p => getMasteryLevel(p) < 0.6);
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
            const t = document.createElement('div'); t.className='toast'; t.innerText='🚀 Starting '+type.toUpperCase();
            document.getElementById('toast-container').appendChild(t);
            setTimeout(() => t.remove(), 2500);
        }}
        function init() {{
            updateStats();
            Graph = ForceGraph3D()(document.getElementById('3d-graph'))
                .graphData(GRAPH_DATA)
                .backgroundColor('#060714')
                .showNavInfo(false)
                .nodeColor(getNodeColor)
                .nodeVal('val')
                .nodeLabel(n => (isLocked(n) ? '🔒 ' : '') + (n.label || n.id))
                .linkColor(link => link.relation === 'macro_path' ? 'rgba(255, 255, 255, 0.7)' : (link.relation === 'contains' ? 'rgba(56, 189, 248, 0.4)' : 'rgba(251, 191, 36, 0.8)'))
                .linkWidth(link => link.relation === 'macro_path' ? 4.5 : (link.relation === 'contains' ? 1.5 : 2.5))
                .linkDirectionalParticles(link => link.relation === 'prerequisite_for' ? 5 : (link.relation === 'macro_path' ? 6 : 0))
                .linkDirectionalParticleWidth(link => link.relation === 'macro_path' ? 3.0 : 2.0)
                .linkDirectionalParticleSpeed(link => link.relation === 'macro_path' ? 0.008 : 0.005)
                .linkDirectionalParticleColor(() => '#ffffff')
                .onNodeClick(n => {{
                    if (isLocked(n)) return;
                    Graph.cameraPosition({{ x: n.x*1.5, y: n.y*1.5, z: n.z*1.5 }}, n, 1000);
                    const p = document.getElementById('info-panel'); p.classList.add('visible');
                    document.getElementById('info-title').innerText = n.label || n.id;
                    document.getElementById('info-desc').innerText = n.content || 'Chọn một hành động bên dưới để bắt đầu học.';
                    
                    const pType = document.getElementById('info-type');
                    pType.className = 'badge';
                    if (n.type === 'macro') {{
                        pType.classList.add('type-macro');
                        pType.innerText = 'CHƯƠNG KIẾN THỨC';
                    }} else if (n.type === 'meso') {{
                        pType.classList.add('type-micro');
                        pType.innerText = 'PHẦN BÀI HỌC';
                        pType.style.background = getNodeColor(n);
                        pType.style.color = '#000';
                    }} else if (n.type === 'assess') {{
                        pType.classList.add('type-assess');
                        pType.innerText = 'BÀI ĐÁNH GIÁ';
                    }}

                    const resContainer = document.getElementById('node-resources');
                    resContainer.innerHTML = '';
                    const resources = n.resources || [];
                    if (resources.length > 0) {{
                        resContainer.style.display = 'flex';
                        resources.forEach(res => {{
                            if (!res || !res.url) return;
                            const resTitle = res.title || 'Tài nguyên chưa đặt tên';
                            const resIcon = res.icon || '📎';
                            const resType = (res.type || '').toLowerCase();

                            const a = document.createElement('a');
                            a.className = 'resource-item';
                            if (resType === 'youtube' || resTitle.toLowerCase().includes('video')) {{
                                a.href = '#';
                                a.onclick = (e) => {{ e.preventDefault(); startAction('video'); }};
                            }} else {{
                                a.href = res.url;
                                a.target = '_blank';
                            }}
                            a.innerHTML = `
                                <div style="display: flex; align-items: center; gap: 8px; flex: 1; overflow: hidden;">
                                    <span>${{resIcon}}</span>
                                    <span style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 180px;" title="${{resTitle}}">${{resTitle}}</span>
                                </div>
                                <div class="play-btn" title="Học ngay với Player" onclick="event.stopPropagation(); event.preventDefault(); startAction('video');">
                                    <i class="material-icons" style="font-size: 20px;">play_circle_outline</i>
                                </div>
                            `;
                            resContainer.appendChild(a);
                        }});
                    }} else {{
                        resContainer.style.display = 'none';
                    }}
                    
                    document.getElementById('action-buttons').style.display = (n.type === 'macro' ? 'none' : 'block');
                    window.currentNodeId = n.id;
                }});
                
            document.getElementById('loading-screen').style.opacity = '0';
            setTimeout(() => document.getElementById('loading-screen').remove(), 1000);
            
            // Fix canvas resize inside iframe
            window.addEventListener('resize', () => {{
                const w = window.innerWidth || document.documentElement.clientWidth;
                const h = window.innerHeight || document.documentElement.clientHeight;
                if(Graph && w > 0 && h > 0) {{
                    Graph.width(w).height(h);
                }}
            }});
            setTimeout(() => window.dispatchEvent(new Event('resize')), 500);
        }}
        window.addEventListener('DOMContentLoaded', init);
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
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"✅ Success! 3D Interface created at: {output_html}")

if __name__ == "__main__":
    visualize_knowledge_tree(user_id="sv01")