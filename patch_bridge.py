import sys
import re

file_path = 'main.py'
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # == NEXUS BRIDGE REPLACEMENTS ==
    # 1. Def
    content = re.sub(
        r"                                  def handle_nexus_3d_click\(e\):[\s\S]*?                                      if node_id:",
        "                                  def handle_nexus_3d_click(e):\n                                      if not e.value: return\n                                      import json\n                                      try:\n                                          data = json.loads(e.value)\n                                          node_id = data.get('id')\n                                          action = data.get('action', 'video')                                          \n                                          if node_id:",
        content
    )
    # 2. Try-Except block end
    content = content.replace(
        "                                          except Exception as err:\n                                              print(f\"[Nexus] Lỗi khi xử lý thao tác 3D: {err}\")",
        "                                          except Exception as err:\n                                              print(f\"[Nexus] Lỗi khi xử lý thao tác 3D: {err}\")\n                                      except Exception as parse_err:\n                                          print(f\"[Nexus] Lỗi đọc JSON từ Bridge: {parse_err}\")"
    )
    # 3. Element
    content = content.replace(
        "                                  # Hidden bridge element for iframe-to-parent communication\n                                  bridge = ui.element('div').props('id=\"nexus-bridge\"').classes('hidden')\n                                  bridge.on('node_click', handle_nexus_3d_click, ['detail'])",
        "                                  # Hidden bridge element for iframe-to-parent communication\n                                  bridge = ui.input(on_change=handle_nexus_3d_click).props('id=\"nexus-bridge\"').style('display: none;')\n"
    )

    # == STUDIO BRIDGE REPLACEMENTS ==
    # 1. Def
    content = re.sub(
        r"                          def handle_3d_click\(e\):[\s\S]*?                              if node_id:",
        "                          def handle_3d_click(e):\n                              if not e.value: return\n                              import json\n                              try:\n                                  data = json.loads(e.value)\n                                  node_id = data.get('id')\n                                  action = data.get('action', 'video')                                          \n                                  if node_id:",
        content
    )
    # 2. Try-Except block end
    content = content.replace(
        "                                  except Exception as err:\n                                      print(f\"Lỗi khi xử lý thao tác 3D: {err}\")",
        "                                  except Exception as err:\n                                      print(f\"Lỗi khi xử lý thao tác 3D: {err}\")\n                              except Exception as parse_err:\n                                  print(f\"Lỗi đọc JSON từ Bridge: {parse_err}\")"
    )
    # 3. Element
    content = content.replace(
        "                          # Hidden receiver widget for iframe Javascript\n                          bridge = ui.element('div').props('id=\"studio-bridge\"').classes('hidden')\n                          bridge.on('node_click', handle_3d_click, ['detail'])",
        "                          # Hidden receiver widget for iframe Javascript\n                          bridge = ui.input(on_change=handle_3d_click).props('id=\"studio-bridge\"').style('display: none;')\n"
    )

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print('main.py updated successfully via python patch.')
except Exception as e:
    print('Failed:', str(e))
