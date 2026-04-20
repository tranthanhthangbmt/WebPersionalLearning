import re

file_path = 'main.py'
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace nexus bridge element
    old_nexus_bridge = r"bridge = ui\.button\('Hidden', on_click=handle_nexus_3d_click\)\.props\('id=\"nexus-bridge\"'\)\.style\('display: none;'\)"
    new_nexus_bridge = "bridge = ui.button('Hidden', on_click=handle_nexus_3d_click).props('id=\"nexus-bridge\"').classes('absolute -top-[1000px] left-0 opacity-0 pointer-events-none z-[-1]')"
    content = re.sub(old_nexus_bridge, new_nexus_bridge, content)

    # Replace studio bridge element
    old_studio_bridge = r"bridge = ui\.button\('Hidden', on_click=handle_3d_click\)\.props\('id=\"studio-bridge\"'\)\.style\('display: none;'\)"
    new_studio_bridge = "bridge = ui.button('Hidden', on_click=handle_3d_click).props('id=\"studio-bridge\"').classes('absolute -top-[1000px] left-0 opacity-0 pointer-events-none z-[-1]')"
    content = re.sub(old_studio_bridge, new_studio_bridge, content)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print('main.py updated successfully (CSS patch).')
except Exception as e:
    print('Failed:', str(e))
