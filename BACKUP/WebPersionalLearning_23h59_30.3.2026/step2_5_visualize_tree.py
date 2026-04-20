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
            "alpha_base": c.get("alpha_base", 10),
            "color": "#ffaa00", # Orange for lessons
            "val": c.get("alpha_base", 10) # Size proportional to importance
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
        flat_graph["edges"].append({
            "source": edge.get("source"),
            "target": edge.get("target"),
            "relation": "prerequisite_for",
            "reason": edge.get("reason", "")
        })
    
    return flat_graph

def visualize_knowledge_tree(user_id, input_json_path=None):
    """Đọc file JSON (Flat Graph) và tạo giao diện WebGL 3D Force-Graph HTML duy nhất"""
    
    # 1. Nếu không được truyền file cụ thể, lấy file upload mặc định của user 
    json_path = input_json_path if input_json_path else f"user_data/{user_id}/{user_id}_knowledge_tree.json"
    
    if not os.path.exists(json_path):
        print(f"❌ Không tìm thấy file {json_path}. Hãy chạy Step 1 và Step 2 trước.")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        tree_data = json.load(f)

    print(f"🎨 Đang vẽ Cây Tri Thức Không Gian 3D cho {user_id} từ {json_path}...")

    # Chuyển đổi dữ liệu
    flat_data = convert_to_flat_graph_internal(tree_data)

    # Load Student State (Knowledge Tracing)
    subject_id = os.path.basename(json_path).split('.')[0]
    from knowledge_tracing import get_student_state
    student_state = get_student_state(user_id, subject_id)
    state_string = json.dumps(student_state, ensure_ascii=False)

    # Convert to array format for 3d-force-graph
    graph_data_array = {
        "nodes": [{"id": k, **v} for k, v in flat_data["nodes"].items()],
        "links": [{"source": e["source"], "target": e["target"], "relation": e["relation"]} for e in flat_data["edges"]]
    }
    
    json_string = json.dumps(graph_data_array, ensure_ascii=False)

    html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Knowledge Tree 3D Visualizer</title>
    <!-- Thư viện 3D Force Graph WebGL -->
    <script src="//unpkg.com/3d-force-graph"></script>
    <!-- Font chữ hiện đại -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #0d1117;
            --glass-bg: rgba(22, 27, 34, 0.65);
            --glass-border: rgba(255, 255, 255, 0.1);
            --text-primary: #f0f6fc;
            --text-muted: #8b949e;
            --accent: #58a6ff;
        }}
        body {{
            margin: 0; padding: 0; overflow: hidden;
            background-color: var(--bg-color);
            font-family: 'Inter', -apple-system, sans-serif;
            color: var(--text-primary);
        }}
        #3d-graph {{
            position: absolute; top: 0; left: 0;
            width: 100vw; height: 100vh; z-index: 1;
        }}
        #ui-overlay {{
            position: absolute; top: 0; left: 0;
            width: 100%; height: 100%;
            pointer-events: none; z-index: 10;
            display: flex; flex-direction: column;
        }}
        .glass-panel {{
            background: var(--glass-bg);
            backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
            border: 1px solid var(--glass-border);
            border-radius: 16px; padding: 24px; pointer-events: auto;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        }}
        header {{
            position: absolute; top: 30px; left: 40px; pointer-events: auto;
        }}
        header h1 {{
            margin: 0; font-size: 32px; font-weight: 800;
            background: linear-gradient(135deg, #00ffcc, #58a6ff);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            letter-spacing: -1px;
        }}
        header .subtitle {{
            margin-top: 5px; color: var(--text-muted); font-size: 14px; font-weight: 500;
        }}
        .search-box {{
            position: absolute; top: 40px; right: 40px;
            display: flex; align-items: center;
            background: var(--glass-bg); backdrop-filter: blur(10px);
            border: 1px solid var(--glass-border); border-radius: 50px;
            padding: 8px 20px; pointer-events: auto; transition: all 0.3s ease;
        }}
        .search-box:focus-within {{
            border-color: var(--accent); box-shadow: 0 0 15px rgba(88, 166, 255, 0.4);
        }}
        .search-box input {{
            background: transparent; border: none; color: white;
            font-family: 'Inter', sans-serif; font-size: 15px; width: 250px; outline: none;
        }}
        .search-box input::placeholder {{ color: #666; }}
        .search-box button {{
            background: transparent; border: none; color: var(--text-muted);
            cursor: pointer; display: flex; align-items: center; justify-content: center;
        }}
        .search-box button:hover {{ color: var(--text-primary); }}
        
        #info-panel {{
            position: absolute; bottom: 40px; right: 40px; width: 320px;
            transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275), opacity 0.3s ease;
        }}
        #info-panel.hidden {{ transform: translateY(20px) scale(0.95); opacity: 0; pointer-events: none; }}
        #info-panel h2 {{ margin: 0 0 10px 0; font-size: 22px; font-weight: 600; }}
        .badge {{
            display: inline-block; padding: 4px 10px; border-radius: 6px;
            font-size: 12px; font-weight: 600; text-transform: uppercase;
            letter-spacing: 0.5px; margin-bottom: 15px;
        }}
        .type-macro {{ background: rgba(0, 255, 204, 0.15); color: #00ffcc; border: 1px solid rgba(0, 255, 204, 0.3); }}
        .type-micro {{ background: rgba(255, 170, 0, 0.15); color: #ffaa00; border: 1px solid rgba(255, 170, 0, 0.3); }}
        .type-assess {{ background: rgba(255, 51, 102, 0.15); color: #ff3366; border: 1px solid rgba(255, 51, 102, 0.3); }}
        #info-meta {{ font-size: 14px; color: var(--text-muted); margin-bottom: 12px; }}
        #info-desc {{
            font-size: 14px; line-height: 1.6; color: #c9d1d9;
            max-height: 150px; overflow-y: auto; margin-bottom: 20px;
        }}
        .legend {{
            position: absolute; bottom: 40px; left: 40px;
            display: flex; flex-direction: column; gap: 12px; pointer-events: auto;
        }}
        .legend-item {{ display: flex; align-items: center; font-size: 13px; font-weight: 500; color: var(--text-muted); }}
        .legend-item .dot {{ width: 12px; height: 12px; border-radius: 50%; margin-right: 12px; box-shadow: 0 0 8px currentColor; }}
        ::-webkit-scrollbar {{ width: 6px; }}
        ::-webkit-scrollbar-track {{ background: rgba(0,0,0,0.1); }}
        ::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.2); border-radius: 4px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: rgba(255,255,255,0.4); }}
        .assess-btn {{
            background: linear-gradient(135deg, #FF3366, #FF6633);
            border: none; color: white; padding: 10px 15px; border-radius: 8px;
            font-weight: 600; cursor: pointer; width: 100%; transition: all 0.2s;
            margin-top: 10px; display: none;
        }}
        .assess-btn.visible {{ display: block; }}
        .assess-btn:hover {{ background: linear-gradient(135deg, #FF6633, #FF3366); box-shadow: 0 0 10px rgba(255, 51, 102, 0.5); transform: translateY(-1px); }}
        
        .adaptive-btn {{
            position: absolute; bottom: 40px; left: 50%; transform: translateX(-50%);
            background: linear-gradient(90deg, #58a6ff, #00ffcc);
            border: none; border-radius: 30px; padding: 15px 40px;
            color: #0d1117; font-weight: 800; font-size: 16px; cursor: pointer;
            box-shadow: 0 0 20px rgba(0, 255, 204, 0.4); transition: all 0.3s ease;
            pointer-events: auto; z-index: 100;
        }}
        .adaptive-btn:hover {{ transform: translateX(-50%) scale(1.05); box-shadow: 0 0 30px rgba(0, 255, 204, 0.6); }}

        #dashboard-panel {{
            position: absolute; top: 110px; left: 40px; width: 280px;
            display: flex; flex-direction: column; gap: 15px; pointer-events: auto;
        }}
        .stat-card {{
            background: rgba(0, 0, 0, 0.3); border-radius: 12px; padding: 12px 18px;
            display: flex; justify-content: space-between; align-items: center;
        }}
        .stat-value {{ font-size: 26px; font-weight: 800; font-family: monospace; letter-spacing: -1px; }}
        .text-green {{ color: #33ff33; text-shadow: 0 0 10px rgba(51, 255, 51, 0.5); }}
        .text-orange {{ color: #ffaa00; text-shadow: 0 0 10px rgba(255, 170, 0, 0.5); }}
        .text-red {{ color: #ff3333; text-shadow: 0 0 10px rgba(255, 51, 51, 0.5); }}
        .pulse-warning {{ animation: pulseWarning 2s infinite; }}
        @keyframes pulseWarning {{ 0% {{ box-shadow: 0 0 0 0 rgba(255, 170, 0, 0.4); }} 70% {{ box-shadow: 0 0 0 15px rgba(255, 170, 0, 0); }} 100% {{ box-shadow: 0 0 0 0 rgba(255, 170, 0, 0); }} }}
    </style>
</head>
<body>
    <div id="ui-overlay">
        <header>
            <h1>Knowledge Galaxy</h1>
            <p class="subtitle">Thương mại điện tử &bull; Đồ thị Không Gian Tri Thức</p>
        </header>

        <div class="search-box">
            <input type="text" id="searchInput" placeholder="Tìm kiếm bài học, chương...">
            <button id="searchBtn">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="11" cy="11" r="8"></circle>
                    <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                </svg>
            </button>
        </div>

        <!-- Dashboard UI -->
        <div id="dashboard-panel" class="glass-panel">
            <h3 style="margin: 0 0 10px 0; font-size: 16px; color: #58a6ff; display: flex; align-items: center; gap: 8px;">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20V10M18 20V4M6 20v-4"></path></svg>
                HỒ SƠ NĂNG LỰC
            </h3>
            <div class="stat-card" style="border-left: 4px solid #33ff33;">
                <div>
                    <div style="font-size: 11px; color: #8b949e; text-transform: uppercase; font-weight: bold;">Đã Thông Thạo</div>
                    <div style="font-size: 10px; color: #666;">(Mastery > 80%)</div>
                </div>
                <div id="stat-mastered" class="stat-value text-green">0</div>
            </div>
            <div class="stat-card pulse-warning" style="border-left: 4px solid #ffaa00;">
                <div>
                    <div style="font-size: 11px; color: #8b949e; text-transform: uppercase; font-weight: bold;">Đang Nhạt Dần</div>
                    <div style="font-size: 10px; color: #666;">(Cần ôn tập gấp)</div>
                </div>
                <div id="stat-decaying" class="stat-value text-orange">0</div>
            </div>
            <div class="stat-card" style="border-left: 4px solid #ff3333;">
                <div>
                    <div style="font-size: 11px; color: #8b949e; text-transform: uppercase; font-weight: bold;">Hổng Kiến Thức</div>
                    <div style="font-size: 10px; color: #666;">(Mastery < 50%)</div>
                </div>
                <div id="stat-weak" class="stat-value text-red">0</div>
            </div>
        </div>

        <div id="info-panel" class="hidden">
            <h2 id="info-title">Tiêu đề Node</h2>
            <div class="badge" id="info-type">Loại</div>
            <div class="meta" id="info-meta"></div>
            <p id="info-desc">Nội dung chi tiết sẽ xuất hiện ở đây...</p>
            <button id="btn-assess" class="assess-btn" onclick="startAssessment()">Tạo bài Kiểm tra Năng lực AI</button>
        </div>
        
        <div class="legend glass-panel">
            <div class="legend-item"><span class="dot" style="background:#00ffcc"></span> Chương (Macro)</div>
            <div class="legend-item"><span class="dot" style="background:#ffaa00"></span> Bài học (Micro)</div>
            <div class="legend-item"><span class="dot" style="background:#ff3366"></span> Bài tập (Assess)</div>
        </div>
        
        <button class="adaptive-btn" onclick="findWeakestNode()">
            🎯 Tôi Cần Học & Ôn Gì Hôm Nay?
        </button>
    </div>

    <div id="3d-graph"></div>

    <script>
        const GRAPH_DATA = {json_string};
        const USER_STATE = {state_string};
        window.currentNodeId = null;
        window.currentNodeContent = null;

        document.addEventListener('DOMContentLoaded', () => {{
            const graphElem = document.getElementById('3d-graph');
            
            function getNodeColor(node) {{
                if (node.type === 'macro') return '#00ffcc'; // Chương (Cyan gốc)
                const masteryData = USER_STATE.mastery[node.id];
                if (!masteryData || masteryData.attempts === 0) return 'rgba(136, 136, 136, 0.4)'; // Chưa học (Xám)
                
                const level = masteryData.level;
                if (masteryData._decayed && level < 0.9) return '#ffaa00'; // Đang nhạt dần -> Vàng Cam Ebbinghaus
                if (level < 0.5) return '#ff3333'; // Đỏ (Hổng kiến thức)
                if (level < 0.8) return '#ffdd33'; // Vàng nhạt (Mới biết)
                return '#33ff33'; // Xanh lục (Master)
            }}

            // Dashboard Analytics Engine
            function updateDashboard() {{
                let mastered = 0, decaying = 0, weak = 0, untouched = 0;
                GRAPH_DATA.nodes.forEach(n => {{
                    if(n.type === 'micro' || n.type === 'assess') {{
                        const m = USER_STATE.mastery[n.id];
                        if(m && m.attempts > 0) {{
                            if (m._decayed && m.level < 0.9) decaying++;
                            else if (m.level >= 0.8) mastered++;
                            else if (m.level < 0.5) weak++;
                        }} else {{
                            untouched++;
                        }}
                    }}
                }});
                document.getElementById('stat-mastered').innerText = mastered;
                document.getElementById('stat-decaying').innerText = decaying;
                document.getElementById('stat-weak').innerText = weak;
            }}
            updateDashboard();

            const Graph = ForceGraph3D()(graphElem)
                .backgroundColor('#0d1117')
                .nodeLabel('label')
                .nodeColor(node => getNodeColor(node))
                .nodeVal(node => {{
                    if(node.type === 'macro') return 25;
                    const masteryData = USER_STATE.mastery[node.id];
                    if (!masteryData) return 10;
                    return 10 + (masteryData.level * 15);
                }})
                .linkDirectionalArrowLength(3.5)
                .linkDirectionalArrowRelPos(1)
                .linkColor(() => 'rgba(255,255,255,0.2)')
                .linkWidth(0.5)
                .graphData(GRAPH_DATA)
                .onNodeClick(node => handleNodeClick(node))
                .onNodeHover(node => {{
                    graphElem.style.cursor = node ? 'pointer' : null;
                }});

            const panel = document.getElementById('info-panel');
            const pTitle = document.getElementById('info-title');
            const pType = document.getElementById('info-type');
            const pMeta = document.getElementById('info-meta');
            const pDesc = document.getElementById('info-desc');

            function handleNodeClick(node) {{
                const distance = 80;
                const distRatio = 1 + distance/Math.hypot(node.x || Math.random(), node.y || Math.random(), node.z || Math.random());
                
                Graph.cameraPosition(
                    {{ x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio }}, 
                    node, 1500
                );
                
                panel.classList.add('glass-panel');
                pTitle.innerText = node.label || 'Không có tiêu đề';
                
                pType.className = 'badge'; 
                if(node.type === 'macro') {{
                    pType.classList.add('type-macro'); pType.innerText = "CHƯƠNG KIẾN THỨC";
                    pMeta.innerText = "Mã Node: " + node.id;
                    pDesc.innerText = "Đây là một chương (mục) lớn của môn học.";
                }} else if(node.type === 'micro') {{
                    pType.classList.add('type-micro'); pType.innerText = "BÀI HỌC QUAN TRỌNG";
                    const mastery = USER_STATE.mastery[node.id] ? USER_STATE.mastery[node.id].level : 0;
                    pMeta.innerText = "Điểm Thông thạo (Mastery): " + Math.round(mastery*100) + "/100 🏆";
                    pDesc.innerText = node.content || "Chưa có nội dung chi tiết cho bài học này.";
                }} else if(node.type === 'assess') {{
                    pType.classList.add('type-assess'); pType.innerText = "BÀI KIỂM TRA ĐÁNH GIÁ";
                    pMeta.innerText = "Ngưỡng đạt (Theta): " + (node.theta_pass || '--');
                    pDesc.innerText = "Bài kiểm tra này dùng để đánh giá năng lực của bạn trong node " + (node.id).replace('a', 'c') + ".";
                }}

                // Xử lý nút Assess
                const assessBtn = document.getElementById('btn-assess');
                if((node.type === 'micro' || node.type === 'assess') && node.content) {{
                    window.currentNodeId = node.id;
                    window.currentNodeContent = node.content;
                    assessBtn.classList.add('visible');
                }} else {{
                    assessBtn.classList.remove('visible');
                }}

                panel.classList.remove('hidden');
            }}
            window.startAssessment = function() {{
                if(!window.currentNodeId) return;
                // Popup mở tính năng AI Quiz
                window.open(`/quiz_node/${{USER_STATE.subject_id}}/${{window.currentNodeId}}`, '_blank', 'width=800,height=750,top=100,left=300');
            }};

            window.findWeakestNode = function() {{
                let target = null;
                
                // Thuật toán Adaptive Pathfinding Lõi AI:
                // 1. Ưu tiên cao nhất: Module đang bị nhạt do quên lãng Ebbinghaus (Tức là đã học mà rụng)
                let decayingNodes = GRAPH_DATA.nodes.filter(n => {{
                    const m = USER_STATE.mastery[n.id];
                    return m && m._decayed && m.level < 0.9 && (n.type === 'micro' || n.type === 'assess');
                }});
                
                if (decayingNodes.length > 0) {{
                    // Ưu tiên node rụng sâu nhất
                    decayingNodes.sort((a,b) => USER_STATE.mastery[a.id].level - USER_STATE.mastery[b.id].level);
                    target = decayingNodes[0];
                    alert('🚨 [CẢNH BÁO EBBINGHAUS]: Có kiến thức bạn đang dần quên lãng. Đề xuất ưu tiên ôn tập nhanh Node: ' + (target.label || target.id));
                }} else {{
                    // 2. Không có node nhạt, đi tìm node chưa học mà có tiên quyết (Hoặc gốc cây)
                    let untouchedNodes = GRAPH_DATA.nodes.filter(n => (n.type === 'micro' || n.type === 'assess') && (!USER_STATE.mastery[n.id] || USER_STATE.mastery[n.id].attempts === 0));
                    
                    if (untouchedNodes.length > 0) {{
                        target = untouchedNodes[0];
                        alert('🌱 Đề xuất bài học tiếp theo theo lộ trình gốc: ' + (target.label || target.id));
                    }} else {{
                        // 3. Nếu học hết rồi thì tìm cái điểm cùi bắp nhất để cải thiện
                        let lowestScore = 999;
                        for (let i = 0; i < GRAPH_DATA.nodes.length; i++) {{
                            const n = GRAPH_DATA.nodes[i];
                            if (n.type === 'micro' || n.type === 'assess') {{
                                const mastery = USER_STATE.mastery[n.id];
                                if (mastery && mastery.level < lowestScore) {{
                                    lowestScore = mastery.level;
                                    target = n;
                                }}
                            }}
                        }}
                        if (target && lowestScore < 0.8) {{
                            alert('🎯 Điểm của bạn đang hổng ở mức ' + Math.round(lowestScore*100) + '/100. Hãy thử sức để cải thiện Node: ' + (target.label || target.id));
                        }} else {{
                            target = null;
                        }}
                    }}
                }}
                
                if (target) {{
                    handleNodeClick(target); // Lệnh Camera bay tới nút đó
                }} else {{
                    alert('🏆 CHÚC MỪNG! Bạn đã đạt mốc Master toàn bộ cây kiến thức này xuất sắc!');
                }}
            }};

            // Khởi tạo Interval Timer cập nhật realtime nhẹ
            setInterval(() => {{
                // Fetch file trạng thái thực tế từ local web server (Phải thêm cache buster để tránh Browser Cache đè)
                fetch(`/user_data/{user_id}/states/{subject_id}_state.json?t=${{Date.now()}}`)
                    .then(r => r.json())
                    .then(data => {{
                        let changed = false;
                        if(data && data.mastery) {{
                            // So sánh và merge
                            Object.keys(data.mastery).forEach(key => {{
                                if (!USER_STATE.mastery[key] || USER_STATE.mastery[key].level !== data.mastery[key].level || USER_STATE.mastery[key].attempts !== data.mastery[key].attempts) {{
                                    USER_STATE.mastery[key] = data.mastery[key];
                                    changed = true;
                                }}
                            }});
                        }}
                        if (changed) {{
                            // Cập nhật lại màu sắc Node trên 3D Graph
                            Graph.nodeColor(Graph.nodeColor());
                            Graph.nodeVal(Graph.nodeVal());
                            // Cập nhật lại Dashboard góc trên
                            updateDashboard();
                            
                            // Nếu node đang xem nằm trong Info Panel thì cập nhật text
                            if (window.currentNodeId) {{
                                const currentMastery = USER_STATE.mastery[window.currentNodeId] ? USER_STATE.mastery[window.currentNodeId].level : 0;
                                document.getElementById('info-meta').innerText = "Điểm Thông thạo (Mastery): " + Math.round(currentMastery*100) + "/100 🏆";
                            }}
                        }}
                    }})
                    .catch(e => console.log('Silently ignoring fetch sync error', e));
            }}, 3000);

            const searchInput = document.getElementById('searchInput');
            const searchBtn = document.getElementById('searchBtn');

            function doSearch() {{
                const query = searchInput.value.toLowerCase().trim();
                if(!query) return;

                const target = GRAPH_DATA.nodes.find(n => (n.label || '').toLowerCase().includes(query));
                if(target) {{
                    handleNodeClick(target);
                }} else {{
                    alert("Không tìm thấy kết quả nào trùng khớp với từ khóa của bạn!");
                }}
            }}

            searchBtn.addEventListener('click', doSearch);
            searchInput.addEventListener('keydown', (e) => {{
                if(e.key === 'Enter') doSearch();
            }});
        }});
    </script>
</body>
</html>"""

    # Lưu file HTML Iframe làm file hiển thị duy nhất (current_visual_tree.html)
    output_html = f"user_data/{user_id}/current_visual_tree.html"
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"✅ Đã tạo xong giao diện 3D! File được ghi trực tiếp tại: {os.path.abspath(output_html)}")

# --- CHẠY THỬ NGHIỆM ---
if __name__ == "__main__":
    visualize_knowledge_tree(user_id="sv01")