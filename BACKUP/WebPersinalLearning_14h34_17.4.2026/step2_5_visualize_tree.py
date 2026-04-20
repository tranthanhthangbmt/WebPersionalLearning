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
        
    # Process Micro Nodes (Lessons)
    for c in data.get("micro_nodes", []):
        c_id = c.get("id")
        parent_macro = c.get("parent_macro")
        
        flat_graph["nodes"][c_id] = {
            "type": "micro",
            "label": c.get("title"),
            "content": c.get("content"),
            "resources": c.get("resources", []),
            "alpha_base": c.get("alpha_base", 10),
            "color": "#ffaa00", # Orange for lessons
            "val": c.get("alpha_base", 10), # Size proportional to importance
            "prerequisites": [] # Will be filled from edges
        }
        
        # Link Macro -> Micro (contains)
        if parent_macro:
            flat_graph["edges"].append({
                "source": parent_macro,
                "target": c_id,
                "relation": "contains"
            })
            
    # Process Assess Nodes (Quizzes)
    for a in data.get("assess_nodes", []):
        a_id = a.get("id")
        target_micro = a.get("target_micro")
        
        flat_graph["nodes"][a_id] = {
            "type": "assess",
            "label": "Đánh giá " + target_micro,
            "theta_pass": a.get("theta_pass", 0.6),
            "resources": a.get("resources", []),
            "question_count": len(a.get("questions", [])),
            "color": "#ff3366", # Pink/Red for assessments
            "val": 10
        }
        
        # Link Micro -> Assess (assessed_by)
        if target_micro:
            flat_graph["edges"].append({
                "source": target_micro,
                "target": a_id,
                "relation": "assessed_by"
            })
            
    # Process existing edges (prerequisites)
    for edge in data.get("edges", []):
        src = edge.get("source")
        tgt = edge.get("target")
        flat_graph["edges"].append({
            "source": src,
            "target": tgt,
            "relation": "prerequisite_for",
            "reason": edge.get("reason", "")
        })
        # Record prerequisite in target node
        if tgt in flat_graph["nodes"]:
            if "prerequisites" not in flat_graph["nodes"][tgt]:
                flat_graph["nodes"][tgt]["prerequisites"] = []
            flat_graph["nodes"][tgt]["prerequisites"].append(src)
    
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
    
    mastery_map = {node_id: student_state.get_mastery(node_id) for node_id in flat_data["nodes"]}
    
    # 3. Calculate Next Action
    next_best_node_id = None
    for node_id, node_data in flat_data["nodes"].items():
        if node_data["type"] == "macro": continue
        is_acc, _ = student_state.is_node_accessible(node_id, node_data.get("prerequisites", []))
        if is_acc and student_state.get_mastery(node_id) < 0.6:
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
    json_string = json.dumps(graph_data_array, ensure_ascii=False)

    html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Knowledge Galaxy 3D — PKT Bio-Tutor</title>
    <script src="https://unpkg.com/three@0.141.0/build/three.min.js"></script>
    <script src="https://unpkg.com/3d-force-graph@1.70.16/dist/3d-force-graph.min.js"></script>
    <script src="https://unpkg.com/three@0.141.0/examples/js/postprocessing/EffectComposer.js"></script>
    <script src="https://unpkg.com/three@0.141.0/examples/js/postprocessing/RenderPass.js"></script>
    <script src="https://unpkg.com/three@0.141.0/examples/js/postprocessing/ShaderPass.js"></script>
    <script src="https://unpkg.com/three@0.141.0/examples/js/shaders/CopyShader.js"></script>
    <script src="https://unpkg.com/three@0.141.0/examples/js/shaders/LuminosityHighPassShader.js"></script>
    <script src="https://unpkg.com/three@0.141.0/examples/js/postprocessing/UnrealBloomPass.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">
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
        const USER_STATE = {{"mastery": {mastery_map_json}}};
        let Graph = null;

        function getMasteryLevel(id) {{ return USER_STATE.mastery[id] || 0; }}
        function getNodeStatus(n) {{
            if (n.type === 'macro') return 'macro';
            const m = getMasteryLevel(n.id);
            if (m >= 0.8) return 'mastered';
            if (m >= 0.4) return 'learning';
            return 'weak';
        }}
        function getNodeColor(n) {{
            const s = getNodeStatus(n);
            if (s === 'macro') return '#38bdf8';
            if (s === 'mastered') return '#4ade80';
            if (s === 'learning') return '#fbbf24';
            return '#f87171';
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
            const payload = {{ node_id: window.currentNodeId, action: type }};
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
                .nodeLabel(n => (isLocked(n) ? '🔒 ' : '') + (n.label || n.id))
                .linkColor(() => 'rgba(255,255,255,0.08)')
                .nodeThreeObject(n => {{
                    const size = n.type === 'macro' ? 10 : 5;
                    const mat = new THREE.MeshPhongMaterial({{ color: getNodeColor(n), transparent: true, opacity: isLocked(n)?0.3:0.9 }});
                    return new THREE.Mesh(new THREE.SphereGeometry(size, 16, 16), mat);
                }})
                .onNodeClick(n => {{
                    if (isLocked(n)) return;
                    Graph.cameraPosition({{ x: n.x*1.5, y: n.y*1.5, z: n.z*1.5 }}, n, 1000);
                    const p = document.getElementById('info-panel'); p.classList.add('visible');
                    document.getElementById('info-title').innerText = n.label || n.id;
                    document.getElementById('info-desc').innerText = n.content || 'Select an action to continue.';
                    document.getElementById('action-buttons').style.display = (n.type === 'macro' ? 'none' : 'block');
                    window.currentNodeId = n.id;
                }});
            const bloom = new THREE.UnrealBloomPass(); bloom.strength = 1.0; Graph.postProcessingComposer().addPass(bloom);
            document.getElementById('loading-screen').style.opacity = '0';
            setTimeout(() => document.getElementById('loading-screen').remove(), 1000);
        }}
        window.addEventListener('DOMContentLoaded', init);
        setInterval(() => {{
            fetch(`/user_data/{user_id}/states/{subject_id}_state.json?t=${{Date.now()}}`)
                .then(r => r.json()).then(data => {{ if(data && data.mastery) {{ USER_STATE.mastery = data.mastery; updateStats(); if(Graph) Graph.refresh(); }} }});
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