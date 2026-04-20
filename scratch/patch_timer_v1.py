import re

file_path = 'main.py'
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # == NEXUS BRIDGE REPLACEMENTS ==
    # Replace the async def handle_nexus_3d_click and bridge button
    old_nexus_block = r"                                  async def handle_nexus_3d_click\(e\):[\s\S]*?bridge = ui\.button\('Hidden'.*?\)\n"
    
    new_nexus_block = """                                  async def check_nexus_3d_bridge():
                                      try:
                                          payload = await ui.run_javascript('if(window.__bridge_payload){ let p = window.__bridge_payload; window.__bridge_payload = null; return p; } else { return null; }', timeout=1.0)
                                          if payload and isinstance(payload, dict):
                                              node_id = payload.get('id')
                                              action = payload.get('action', 'video')
                                              
                                              if node_id:
                                                  print(f"[Nexus] Bắt được sự kiện Click từ 3D Bridge: {node_id}, Action: {action}")
                                                  try:
                                                      target_tab = None
                                                      if action == 'video': target_tab = tab_video
                                                      elif action == 'quiz': target_tab = tab_quiz
                                                      if target_tab:
                                                          load_lesson_ui(node_id, target_tab=target_tab)
                                                      
                                                      if action == 'tutor':
                                                          subject_id = os.path.basename(last_path).replace('.json', '')
                                                          ui.run_javascript(f"window.open('/quiz_node/{subject_id}/{node_id}', '_blank', 'width=1100,height=800,left=200,top=100')")
                                                  except Exception as err:
                                                      print(f"[Nexus] Lỗi khi xử lý thao tác 3D: {err}")
                                      except Exception:
                                          pass

                                  # Poll every 500ms
                                  ui.timer(0.5, check_nexus_3d_bridge)
"""
    # Replace ONLY if it finds it
    if re.search(old_nexus_block, content):
        content = re.sub(old_nexus_block, new_nexus_block, content)
    else:
        print("Warning: Nexus block not found via regex.")

    # == STUDIO BRIDGE REPLACEMENTS ==
    old_studio_block = r"                          async def handle_3d_click\(e\):[\s\S]*?bridge = ui\.button\('Hidden'.*?\)\n"
    
    new_studio_block = """                          async def check_studio_3d_bridge():
                              try:
                                  payload = await ui.run_javascript('if(window.__bridge_payload){ let p = window.__bridge_payload; window.__bridge_payload = null; return p; } else { return null; }', timeout=1.0)
                                  if payload and isinstance(payload, dict):
                                      node_id = payload.get('id')
                                      action = payload.get('action', 'video')                                          
                                      if node_id:
                                          print(f"Bắt được sự kiện Click từ 3D Bridge: {node_id}, Action: {action}")
                                          try:
                                              target_tab = None
                                              if action == 'video': target_tab = tab_video
                                              elif action == 'quiz': target_tab = tab_quiz
                                              if target_tab:
                                                  load_lesson_ui(node_id, target_tab=target_tab)
                                              
                                              if action == 'tutor':
                                                  import os
                                                  subject_id = os.path.basename(json_file_path).replace('.json', '')
                                                  ui.run_javascript(f"window.open('/quiz_node/{subject_id}/{node_id}', '_blank', 'width=1100,height=800,left=200,top=100')")
                                          except Exception as err:
                                              print(f"Lỗi khi xử lý thao tác 3D: {err}")
                              except Exception:
                                  pass
                                      
                          # Poll every 500ms
                          ui.timer(0.5, check_studio_3d_bridge)
"""
    if re.search(old_studio_block, content):
        content = re.sub(old_studio_block, new_studio_block, content)
    else:
        print("Warning: Studio block not found via regex.")

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print('main.py updated successfully (Timer polling logic).')
except Exception as e:
    print('Failed:', str(e))
