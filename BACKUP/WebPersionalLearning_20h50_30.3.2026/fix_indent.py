import codecs
content = codecs.open('main.py', 'r', 'utf-8').read()
old_part = """                                 with ui.column().classes('w-full p-4 border-t border-gray-100 bg-white gap-2 z-10 no-wrap'):
                                     with ui.row().classes('w-full items-center gap-2 relative'):
                                         tutor_input = ui.input(placeholder='Hỏi gia sư...').props('rounded outlined dense borderless').classes('w-full bg-gray-100 pr-10').on('keydown.enter', tutor_send_message)
                                         ui.button(icon='send', on_click=tutor_send_message).props('flat round dense color=blue').classes('absolute right-1 top-1/2 transform -translate-y-1/2')"""

new_part = """                         with ui.column().classes('w-full p-4 border-t border-gray-100 bg-white gap-2 z-10 no-wrap'):
                             with ui.row().classes('w-full items-center gap-2 relative'):
                                 tutor_input = ui.input(placeholder='Hỏi gia sư...').props('rounded outlined dense borderless').classes('w-full bg-gray-100 pr-10').on('keydown.enter', tutor_send_message)
                                 ui.button(icon='send', on_click=tutor_send_message).props('flat round dense color=blue').classes('absolute right-1 top-1/2 transform -translate-y-1/2')"""

content = content.replace('\r\n', '\n')
old_part = old_part.replace('\r\n', '\n')
new_part = new_part.replace('\r\n', '\n')

content = content.replace(old_part, new_part)

with codecs.open('main.py', 'w', 'utf-8') as f:
    f.write(content)
print("Fix executed!")
