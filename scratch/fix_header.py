import sys

file_path = 'i:/MY_CODE/WebPersionalLearning/main.py'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = 0
for i, line in enumerate(lines):
    if skip > 0:
        skip -= 1
        continue
    
    # Replace show_graph_view and show_library_view
    if 'def show_graph_view():' in line and 'studio_library_view.classes' in lines[i+1]:
        indent = line[:line.find('def')]
        new_lines.append(f"{indent}def show_graph_view():\n")
        new_lines.append(f"{indent}    studio_library_view.classes('hidden', remove='w-full')\n")
        new_lines.append(f"{indent}    studio_graph_view.classes(remove='hidden')\n")
        new_lines.append(f"{indent}    studio_graph_view.classes('w-full')\n")
        new_lines.append(f"{indent}    header_left_group.classes('hidden')\n")
        new_lines.append(f"{indent}    header_lesson_container.classes('hidden')\n")
        new_lines.append(f"{indent}    header_context_container.classes(remove='hidden')\n")
        skip = 3
        continue
    
    if 'def show_library_view():' in line and 'studio_graph_view.classes' in lines[i+1]:
        indent = line[:line.find('def')]
        new_lines.append(f"{indent}def show_library_view():\n")
        new_lines.append(f"{indent}    studio_graph_view.classes('hidden', remove='w-full')\n")
        new_lines.append(f"{indent}    studio_library_view.classes(remove='hidden')\n")
        new_lines.append(f"{indent}    studio_library_view.classes('w-full')\n")
        new_lines.append(f"{indent}    header_left_group.classes(remove='hidden')\n")
        new_lines.append(f"{indent}    header_lesson_container.classes(remove='hidden')\n")
        new_lines.append(f"{indent}    header_context_container.classes('hidden')\n")
        skip = 3
        continue

    # Replace the local bar in render_3d_graph
    if 'with ui.row().classes(\'w-full items-center px-4 py-3 bg-white border-b shadow-sm\'):' in line:
        indent = line[:line.find('with')]
        # Find where it ends (usually 5 lines)
        new_lines.append(f"{indent}with header_context_container:\n")
        new_lines.append(f"{indent}    header_context_container.clear()\n")
        new_lines.append(f"{indent}    ui.button(icon='arrow_back', on_click=show_library_view).props('flat round color=blue').classes('hover:bg-blue-50')\n")
        new_lines.append(f"{indent}    ui.label('Mạng lưới Giáo dục 3D').classes('font-black text-xl text-blue-800')\n")
        new_lines.append(f"{indent}    ui.button(icon='close', on_click=show_library_view).props('flat round color=grey-4').classes('scale-90')\n")
        skip = 4
        continue

    new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("File modified successfully")
