import re

file_path = 'main.py'
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # == NEXUS BRIDGE REPLACEMENTS ==
    # We replace the entire check_nexus_3d_bridge and timer logic
    old_nexus_block = r"                                  async def check_nexus_3d_bridge\(\):[\s\S]*?ui\.timer\(0\.5, check_nexus_3d_bridge\)"
    new_nexus_block = """                                  def handle_nexus_3d_click(e):
                                      if getattr(e, 'value', None) is None: return
                                      import json
                                      try:
                                          payload = json.loads(e.value)
                                          if payload and isinstance(payload, dict):
                                              node_id = payload.get('id')
                                              action = payload.get('action', 'video')                                              
                                              if node_id:
                                                  print(f"[Nexus] Bắt được sự kiện 3D Bridge: {node_id}, Action: {action}")
                                                  try:
                                                      target_tab = None
                                                      if action == 'video': target_tab = tab_video
                                                      elif action == 'quiz': target_tab = tab_quiz
                                                      if target_tab:
                                                          load_lesson_ui(node_id, target_tab=target_tab)
                                                      
                                                      if action == 'tutor':
                                                          try:
                                                              subject_id = os.path.basename(last_path).replace('.json', '')
                                                              ui.run_javascript(f"window.open('/quiz_node/{subject_id}/{node_id}', '_blank', 'width=1100,height=800,left=200,top=100')")
                                                          except Exception as tutor_e:
                                                              print(f"[Nexus] Lỗi khi mở Khảo Thí Cấp Cao: {tutor_e}")
                                                  except Exception as err:
                                                      print(f"[Nexus] Lỗi khi xử lý thao tác 3D: {err}")
                                      except Exception:
                                          pass

                                  bridge = ui.input(on_change=handle_nexus_3d_click).props('id="nexus-bridge"').classes('absolute -top-[1000px] left-0 opacity-0 z-[-1]')
"""
    if re.search(old_nexus_block, content):
        content = re.sub(old_nexus_block, new_nexus_block, content)
    else:
        print("Warning: Nexus block not found via regex.")

    # == STUDIO BRIDGE REPLACEMENTS ==
    old_studio_block = r"                         async def check_studio_3d_bridge\(\):[\s\S]*?ui\.timer\(0\.5, check_studio_3d_bridge\)"
    new_studio_block = """                         def handle_3d_click(e):
                             if getattr(e, 'value', None) is None: return
                             import json
                             try:
                                 payload = json.loads(e.value)
                                 if payload and isinstance(payload, dict):
                                     node_id = payload.get('id')
                                     action = payload.get('action', 'video')                                          
                                     if node_id:
                                         print(f"Bắt được sự kiện 3D Bridge: {node_id}, Action: {action}")
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
                                     
                         bridge = ui.input(on_change=handle_3d_click).props('id="studio-bridge"').classes('absolute -top-[1000px] left-0 opacity-0 z-[-1]')
"""
    if re.search(old_studio_block, content):
        content = re.sub(old_studio_block, new_studio_block, content)
    else:
        print("Warning: Studio block not found via regex.")

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print('main.py updated successfully (Input Revert).')
except Exception as e:
    print('Failed:', str(e))
