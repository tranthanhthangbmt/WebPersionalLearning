lines = open('main.py', 'r', encoding='utf-8').read().splitlines()
idx = -1
for i, l in enumerate(lines):
    if "tutor_input = ui.input" in l:
        idx = i
        break

if idx != -1:
    print(f"Found input at line {idx}")
    lines[idx-2] = ' ' * 25 + "with ui.column().classes('w-full p-4 border-t border-gray-100 bg-white gap-2 z-10 no-wrap'):"
    lines[idx-1] = ' ' * 29 + "with ui.row().classes('w-full items-center gap-2 relative'):"
    lines[idx] = ' ' * 33 + "tutor_input = ui.input(placeholder='Hỏi gia sư...').props('rounded outlined dense borderless').classes('w-full bg-gray-100 pr-10').on('keydown.enter', tutor_send_message)"
    lines[idx+1] = ' ' * 33 + "ui.button(icon='send', on_click=tutor_send_message).props('flat round dense color=blue').classes('absolute right-1 top-1/2 transform -translate-y-1/2')"
    
    open('main.py', 'w', encoding='utf-8').write('\n'.join(lines))
    print("Patched successfully")
else:
    print("Could not find tutor_input")
