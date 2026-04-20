import codecs
lines = codecs.open('main.py', 'r', 'utf-8').read().splitlines()

# Line 896 (index 895) and below
lines[895] = ' ' * 25 + "with ui.column().classes('w-full p-4 border-t border-gray-100 bg-white gap-2 z-10 no-wrap'):"
lines[896] = ' ' * 29 + "with ui.row().classes('w-full items-center gap-2 relative'):"
lines[897] = ' ' * 33 + "tutor_input = ui.input(placeholder='Hỏi gia sư...').props('rounded outlined dense borderless').classes('w-full bg-gray-100 pr-10').on('keydown.enter', tutor_send_message)"
lines[898] = ' ' * 33 + "ui.button(icon='send', on_click=tutor_send_message).props('flat round dense color=blue').classes('absolute right-1 top-1/2 transform -translate-y-1/2')"

codecs.open('main.py', 'w', 'utf-8').write('\n'.join(lines))
print("Indentation forced to 25/29/33 spaces.")
