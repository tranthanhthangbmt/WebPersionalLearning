import re

file_path = 'main.py'
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # == NEXUS BRIDGE REPLACEMENTS ==
    # Replace def handle_nexus_3d_click(e):
    old_nexus_def = r"                                  def handle_nexus_3d_click\(e\):[\s\S]*?                                      try:[\s\S]*?                                          data = json\.loads\(e\.value\)[\s\S]*?                                          node_id = data\.get\('id'\)[\s\S]*?                                          action = data\.get\('action', 'video'\)\s*[\s\S]*?                                          if node_id:"
    
    new_nexus_def = """                                  async def handle_nexus_3d_click(e):
                                      try:
                                          payload = await ui.run_javascript('return window.__bridge_payload || {};')
                                          node_id = payload.get('id')
                                          action = payload.get('action', 'video')
                                          
                                          if node_id:"""
    content = re.sub(old_nexus_def, new_nexus_def, content)

    # Replace nexus bridge element
    old_nexus_bridge = r"                                  # Hidden bridge input for robust iframe-to-parent communication[\n\r\s]*bridge = ui.input\(on_change=handle_nexus_3d_click\).props\('id=\"nexus-bridge\"'\).style\('display: none;'\)"
    new_nexus_bridge = "                                  # Hidden bridge button for Click & Fetch communication\n                                  bridge = ui.button('Hidden', on_click=handle_nexus_3d_click).props('id=\"nexus-bridge\"').style('display: none;')"
    content = re.sub(old_nexus_bridge, new_nexus_bridge, content)

    # == STUDIO BRIDGE REPLACEMENTS ==
    # Replace def handle_3d_click(e):
    old_studio_def = r"                          def handle_3d_click\(e\):[\s\S]*?                              try:[\s\S]*?                                  data = json\.loads\(e\.value\)[\s\S]*?                                  node_id = data\.get\('id'\)[\s\S]*?                                  action = data\.get\('action', 'video'\)\s*[\s\S]*?                                  if node_id:"
    
    new_studio_def = """                          async def handle_3d_click(e):
                              try:
                                  payload = await ui.run_javascript('return window.__bridge_payload || {};')
                                  node_id = payload.get('id')
                                  action = payload.get('action', 'video')
                                  
                                  if node_id:"""
    content = re.sub(old_studio_def, new_studio_def, content)

    # Replace studio bridge element
    old_studio_bridge = r"                          # Hidden receiver widget for iframe Javascript[\n\r\s]*bridge = ui.input\(on_change=handle_3d_click\).props\('id=\"studio-bridge\"'\).style\('display: none;'\)"
    new_studio_bridge = "                          # Hidden receiver widget for iframe Javascript\n                          bridge = ui.button('Hidden', on_click=handle_3d_click).props('id=\"studio-bridge\"').style('display: none;')"
    content = re.sub(old_studio_bridge, new_studio_bridge, content)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print('main.py updated successfully to Click & Fetch model.')
except Exception as e:
    print('Failed:', str(e))
