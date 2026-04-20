import os
import sys
import json
sys.path.append(os.getcwd())
from step2_5_visualize_tree import visualize_knowledge_tree

def fix_all_user_graphs():
    user_data_dir = 'user_data'
    if not os.path.exists(user_data_dir):
        print("User data directory not found.")
        return

    users = [d for d in os.listdir(user_data_dir) if os.path.isdir(os.path.join(user_data_dir, d)) and not d.startswith('_')]
    
    for user_id in users:
        print(f"--- Processing user: {user_id} ---")
        subj_file = f"user_data/{user_id}/subjects.json"
        if os.path.exists(subj_file):
            try:
                with open(subj_file, 'r', encoding='utf-8') as f:
                    subjects = json.load(f).get("subjects", [])
                    for subj in subjects:
                        json_path = subj.get('filename')
                        if json_path and os.path.exists(json_path):
                            print(f"  Regenerating: {subj.get('title')} ({json_path})")
                            try:
                                visualize_knowledge_tree(user_id, json_path)
                            except Exception as e:
                                print(f"    Error: {e}")
            except Exception as e:
                print(f"  Error reading subjects for {user_id}: {e}")
        else:
            print(f"  No subjects.json found for {user_id}")

if __name__ == "__main__":
    fix_all_user_graphs()
