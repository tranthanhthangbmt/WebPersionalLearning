import json

def merge():
    # Load original course
    with open('DB/public_trees/2e288b09.json', 'r', encoding='utf-8') as f:
        original = json.load(f)
        
    # Load generated course
    with open('khan_academy_toan_6.json', 'r', encoding='utf-8') as f:
        generated = json.load(f)
        
    # Filter macros from m2 to m7
    new_macros = [m for m in generated['macro_nodes'] if m['id'] != 'm1']
    
    # Filter micros for m2 to m7
    new_micros = [c for c in generated['micro_nodes'] if c['parent_macro'] != 'm1']
    
    # Filter assess for m2 to m7
    new_assess = [a for a in generated.get('assess_nodes', []) if not a['id'].endswith('m1')]
    
    original['macro_nodes'].extend(new_macros)
    original['micro_nodes'].extend(new_micros)
    if 'assess_nodes' not in original:
        original['assess_nodes'] = []
    original['assess_nodes'].extend(new_assess)
    
    # Update course name
    original['course_name'] = "Toán lớp 6 - Khan Academy"
    
    with open('DB/public_trees/2e288b09.json', 'w', encoding='utf-8') as f:
        json.dump(original, f, ensure_ascii=False, indent=4)
        
    print("Merged successfully!")

if __name__ == "__main__":
    merge()
