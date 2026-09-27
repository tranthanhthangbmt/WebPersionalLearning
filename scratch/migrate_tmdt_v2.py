"""
Migration Script v2: TMDT Đồng Bộ → v2.0 (MIT Standard Schema)
Creates a NEW tree file preserving ALL resources/questions.
Distributes macro-level resources to their corresponding micro nodes.
"""
import json
import os
import uuid
import re
import copy

SOURCE = 'user_data/thanhthangbmt/trees/e69bf65f.json'
USERNAME = 'thanhthangbmt'
NEW_COURSE_NAME = 'Thương mại điện tử v2.0 (MIT)'

def main():
    with open(SOURCE, 'r', encoding='utf-8') as f:
        old_tree = json.load(f)
    
    old_nodes = old_tree.get('nodes', {})
    total_res_before = sum(len(n.get('resources', [])) for n in old_nodes.values())
    total_q_before = sum(len(n.get('questions', [])) for n in old_nodes.values())
    print(f"[Source] nodes={len(old_nodes)}, resources={total_res_before}, questions={total_q_before}")
    
    macros_raw = {k: v for k, v in old_nodes.items() if v.get('type') == 'macro'}
    micros_raw = {k: v for k, v in old_nodes.items() if v.get('type') == 'micro'}
    assess_raw = {k: v for k, v in old_nodes.items() if v.get('type') == 'assess'}
    
    # ── Build macro_nodes ──
    macro_nodes = []
    macro_order = []
    macro_resources_map = {}  # macro_id -> resources to distribute
    
    for mid in sorted(macros_raw.keys(), key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 9999):
        m = macros_raw[mid]
        macro_nodes.append({
            'id': mid,
            'title': m.get('label', f'Chương {mid}'),
            'type': 'macro',
        })
        macro_order.append(mid)
        macro_resources_map[mid] = copy.deepcopy(m.get('resources', []))
    
    # ── Build micro_nodes + distribute macro resources ──
    micro_nodes = []
    chapter_micros = {}
    
    sorted_micro_ids = sorted(micros_raw.keys(), key=lambda x: (
        int(re.search(r'Chuong_(\d+)', x).group(1)) if re.search(r'Chuong_(\d+)', x) else 999,
        int(re.search(r'Tiet_(\d+)', x).group(1)) if re.search(r'Tiet_(\d+)', x) else 999
    ))
    
    for mic_id in sorted_micro_ids:
        mic = micros_raw[mic_id]
        
        chap_match = re.search(r'Chuong_(\d+)', mic_id)
        parent_macro = f"m{chap_match.group(1)}" if chap_match else 'm999'
        if parent_macro not in macros_raw:
            parent_macro = 'm999'
        
        micro_node = {
            'id': mic_id,
            'title': mic.get('label', mic_id),
            'type': 'micro',
            'parent_macro': parent_macro,
            'prerequisites': [],
            'resources': copy.deepcopy(mic.get('resources', [])),
            'questions': copy.deepcopy(mic.get('questions', [])),
        }
        if 'bloom_profile' in mic:
            micro_node['bloom_profile'] = copy.deepcopy(mic['bloom_profile'])
        
        micro_nodes.append(micro_node)
        chapter_micros.setdefault(parent_macro, []).append(mic_id)
    
    # Distribute macro resources to micro nodes
    # Strategy: 
    #   - "Trắc nghiệm" links → first micro of that chapter
    #   - "Kịch bản Video: Tiết X" → matching micro Chuong_Y_Tiet_X
    micro_lookup = {m['id']: m for m in micro_nodes}
    distributed = 0
    
    for macro_id, resources in macro_resources_map.items():
        chap_num_match = re.search(r'\d+', macro_id)
        chap_num = chap_num_match.group() if chap_num_match else '999'
        first_micro_id = chapter_micros.get(macro_id, [None])[0]
        
        for res in resources:
            title = res.get('title', '')
            
            # Try to match "Kịch bản Video: Tiết X" to corresponding micro
            tiet_match = re.search(r'Chuong_(\d+)_Tiet_(\d+)', title)
            if not tiet_match:
                tiet_match = re.search(r'Tiết (\d+)', title)
                if tiet_match:
                    target_id = f"Chuong_{chap_num}_Tiet_{tiet_match.group(1)}"
                else:
                    target_id = None
            else:
                target_id = f"Chuong_{tiet_match.group(1)}_Tiet_{tiet_match.group(2)}"
            
            if target_id and target_id in micro_lookup:
                micro_lookup[target_id]['resources'].append(copy.deepcopy(res))
                distributed += 1
            elif first_micro_id and first_micro_id in micro_lookup:
                # Fallback: put on first micro of chapter (e.g., quiz links)
                micro_lookup[first_micro_id]['resources'].append(copy.deepcopy(res))
                distributed += 1
            else:
                print(f"  [WARN] Could not distribute: {title} from {macro_id}")
    
    print(f"[Distributed] {distributed} macro resources -> micro nodes")
    
    # ── Build assess_nodes ──
    assess_nodes = []
    for ass_id in sorted(assess_raw.keys()):
        ass = assess_raw[ass_id]
        parent_micro = ass_id.replace('a_', '', 1)
        if parent_micro not in micros_raw:
            parent_micro = None
        
        assess_node = {
            'id': ass_id,
            'title': ass.get('label', f'Đánh giá {parent_micro}'),
            'type': 'assess',
            'parent_micro': parent_micro,
            'questions': copy.deepcopy(ass.get('questions', [])),
            'theta_pass': ass.get('theta_pass', 0.6),
            'resources': copy.deepcopy(ass.get('resources', [])),
        }
        if 'bloom_profile' in ass:
            assess_node['bloom_profile'] = copy.deepcopy(ass['bloom_profile'])
        assess_nodes.append(assess_node)
    
    # ── Build MIT-standard edges ──
    new_edges = []
    
    # Macro sequence
    for i in range(len(macro_order) - 1):
        if macro_order[i+1] != 'm999':
            new_edges.append({
                'source': macro_order[i], 'target': macro_order[i+1],
                'type': 'prerequisite', 'reason': 'Chương trước là tiên quyết.'
            })
    
    # Within-chapter edges
    for macro_id in macro_order:
        micros_in = chapter_micros.get(macro_id, [])
        if not micros_in:
            continue
        if len(micros_in) <= 6:
            for j in range(1, len(micros_in)):
                new_edges.append({
                    'source': micros_in[0], 'target': micros_in[j],
                    'type': 'prerequisite', 'reason': 'Bài mở đầu là tiên quyết.'
                })
        else:
            for j in range(len(micros_in) - 1):
                new_edges.append({
                    'source': micros_in[j], 'target': micros_in[j+1],
                    'type': 'prerequisite', 'reason': 'Tuần tự trong chương.'
                })
    
    # Cross-chapter bridges
    for i in range(len(macro_order) - 1):
        curr = chapter_micros.get(macro_order[i], [])
        nxt = chapter_micros.get(macro_order[i+1], [])
        if curr and nxt:
            new_edges.append({
                'source': curr[-1], 'target': nxt[0],
                'type': 'prerequisite', 'reason': 'Cầu nối chương.'
            })
    
    # Clean edges
    seen = set()
    clean_edges = []
    for e in new_edges:
        key = (e['source'], e['target'])
        if key[0] != key[1] and key not in seen:
            seen.add(key)
            clean_edges.append(e)
    
    # ── Assemble ──
    new_tree = {
        'course_name': NEW_COURSE_NAME,
        'macro_nodes': macro_nodes,
        'micro_nodes': micro_nodes,
        'assess_nodes': assess_nodes,
        'edges': clean_edges,
    }
    
    # ── Verify ──
    total_res_after = (
        sum(len(m.get('resources', [])) for m in micro_nodes) +
        sum(len(a.get('resources', [])) for a in assess_nodes)
    )
    total_q_after = (
        sum(len(m.get('questions', [])) for m in micro_nodes) +
        sum(len(a.get('questions', [])) for a in assess_nodes)
    )
    
    print(f"\n[Result] macro={len(macro_nodes)}, micro={len(micro_nodes)}, assess={len(assess_nodes)}, edges={len(clean_edges)}")
    print(f"[Verify] resources: {total_res_before} -> {total_res_after} {'✅' if total_res_before == total_res_after else '❌ MISMATCH!'}")
    print(f"[Verify] questions: {total_q_before} -> {total_q_after} {'✅' if total_q_before == total_q_after else '❌ MISMATCH!'}")
    
    if total_res_before != total_res_after or total_q_before != total_q_after:
        print("❌ ABORTING!")
        return
    
    # ── Save ──
    new_id = uuid.uuid4().hex[:8]
    out_dir = f'user_data/{USERNAME}/trees'
    os.makedirs(out_dir, exist_ok=True)
    out_path = f'{out_dir}/{new_id}.json'
    
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(new_tree, f, ensure_ascii=False, indent=2)
    print(f"\n[Saved] {out_path}")
    
    # ── Register ──
    subj_file = f'user_data/{USERNAME}/subjects.json'
    subj_data = {'subjects': []}
    if os.path.exists(subj_file):
        with open(subj_file, 'r', encoding='utf-8') as f:
            subj_data = json.load(f)
    
    total_nodes = len(macro_nodes) + len(micro_nodes) + len(assess_nodes)
    subj_data['subjects'].append({
        'id': new_id,
        'title': NEW_COURSE_NAME,
        'filename': out_path,
        'total_nodes': total_nodes
    })
    with open(subj_file, 'w', encoding='utf-8') as f:
        json.dump(subj_data, f, ensure_ascii=False, indent=2)
    
    print(f"[Registered] '{NEW_COURSE_NAME}' ({total_nodes} nodes)")
    print(f"\n🎉 Done! Tree ID: {new_id}")

if __name__ == '__main__':
    main()
