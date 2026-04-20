import json
import os

def convert_to_flat_graph(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    flat_graph = {
        "subject_id": "TMDT101",
        "title": data.get("course_name", "Unknown Course"),
        "user_id": data.get("user_id", "sv01"),
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
        
    # Save the flattened graph
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(flat_graph, f, ensure_ascii=False, indent=2)
        
    print(f"✅ Đã chuyển đổi thành công {len(flat_graph['nodes'])} Nodes và {len(flat_graph['edges'])} Edges.")
    print(f"👉 File mới được lưu tại: {output_path}")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(current_dir, "DB", "TreeDB", "sv01_knowledge_tree.json")
    output_file = os.path.join(current_dir, "DB", "TreeDB", "sv01_flat_graph.json")
    
    if os.path.exists(input_file):
        convert_to_flat_graph(input_file, output_file)
    else:
        print(f"❌ Không tìm thấy file {input_file}")
