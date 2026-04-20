import codecs

with codecs.open('main.py', 'r', 'utf-8') as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if "with ui.row().classes('w-full h-full no-wrap gap-0'):" in line and "LEFT PANEL" in lines[i+1]:
        start_idx = i
    if "ui.button(icon='send'" in line and "tutor_send_message" in line and start_idx != -1:
        end_idx = i
        break

if start_idx == -1 or end_idx == -1:
    print("Could not find boundaries")
    exit(1)

new_content = """             with ui.splitter(value=20).classes('w-full h-full') as main_splitter:
                 def toggle_problem_panel():
                     if main_splitter.value > 5:
                         main_splitter.value = 4
                         problem_content_container.set_visibility(False)
                         problem_minimized_container.set_visibility(True)
                     else:
                         main_splitter.value = 20
                         problem_content_container.set_visibility(True)
                         problem_minimized_container.set_visibility(False)

                 with main_splitter.before:
                     with ui.column().classes('w-full h-full bg-white border-r border-gray-200 shadow-sm relative') as problem_panel:
                         with ui.column().classes('w-full h-full flex flex-col') as problem_content_container:
                             with ui.row().classes('w-full p-4 items-center border-b border-gray-100 justify-between'):
                                 with ui.row().classes('items-center'):
                                     ui.icon('assignment', color='blue-600').classes('text-2xl')
                                     ui.label('Đề bài').classes('font-bold text-gray-800 text-lg')
                                 ui.button(on_click=toggle_problem_panel, icon='chevron_left').props('flat round size=sm color=gray')
                             with ui.scroll_area().classes('w-full flex-grow p-4'):
                                 tutor_problem = ui.textarea(placeholder='Nhập nội dung đề bài vào đây...').classes('w-full text-base').props('borderless autogrow autofocus')
                             with ui.column().classes('w-full p-4 border-t border-gray-100 bg-gray-50'):
                                 ui.button('Bắt đầu làm bài', on_click=lambda: getattr(ui, 'timer')(0.1, tutor_start_exercise, once=True)).classes('w-full bg-blue-600 text-white shadow-md hover:bg-blue-700').props('unelevated rounded')
                         
                         with ui.column().classes('w-full h-full items-center justify-start pt-4 gap-4 bg-blue-50 cursor-pointer hover:bg-blue-100 transition-colors').style('display: none;').on('click', toggle_problem_panel) as problem_minimized_container:
                             ui.icon('assignment', color='blue-600').classes('text-xl')
                             ui.label('Đ Ề   B À I').style('writing-mode: vertical-rl; text-orientation: upright; font-weight: bold; color: #1e3a8a; font-size: 0.95rem; letter-spacing: 4px;')

                 with main_splitter.after:
                     with ui.splitter(value=65).classes('w-full h-full') as workspace_splitter:
                         with workspace_splitter.before:
                             with ui.column().classes('flex-grow h-full bg-gray-50 flex flex-col w-full'):
                                 with ui.row().classes('w-full p-4 items-center border-b border-gray-200 bg-white shadow-sm z-10'):
                                     ui.icon('code', color='green-600').classes('text-2xl')
                                     ui.label('Không gian làm bài').classes('font-bold text-gray-800 text-lg')
                                 with ui.scroll_area().classes('w-full flex-grow p-4 bg-white shadow-inner'):
                                     tutor_workspace = ui.textarea(placeholder='Hãy trình bày lời giải của bạn...').classes('w-full text-base font-mono').props('borderless autogrow')
                                 
                                 def send_predefined_prompt(action):
                                     if action == 'run':
                                         tutor_input.value = "Đóng vai trình biên dịch, hãy biên dịch đoạn code trong Không gian làm bài của tôi và in ra kết quả màn hình console hoặc lỗi cú pháp nếu có."
                                     elif action == 'eval':
                                         tutor_input.value = "Đây là phần làm bài của tôi, hãy chấm điểm và đánh giá sửa lỗi chi tiết nhé."
                                     elif action == 'help':
                                         tutor_input.value = "Tôi đang gặp khó khăn, hãy giải thích và gợi ý cho tôi vài ý tưởng để làm bước tiếp theo."
                                     getattr(ui, 'timer')(0.1, tutor_send_message, once=True)

                                 with ui.row().classes('w-full p-2 border-t border-gray-200 bg-gray-50 gap-4 justify-center items-center shadow-[0_-2px_4px_rgba(0,0,0,0.02)]'):
                                     ui.button('▶ Chạy code', on_click=lambda: send_predefined_prompt('run')).classes('bg-green-600 text-white shadow-md hover:bg-green-700 transition-all').props('unelevated rounded')
                                     ui.button('💬 Chấm bài & Đánh giá', on_click=lambda: send_predefined_prompt('eval')).classes('bg-blue-600 text-white shadow-md hover:bg-blue-700 transition-all').props('unelevated rounded')
                                     ui.button('💡 AI Giúp đỡ', on_click=lambda: send_predefined_prompt('help')).classes('bg-yellow-600 text-white shadow-md hover:bg-yellow-700 transition-all').props('unelevated rounded')
                         
                         with workspace_splitter.after:
                             with ui.column().classes('w-full h-full bg-white border-l border-gray-200 flex flex-col shadow-lg z-20'):
                                 with ui.row().classes('w-full p-4 items-center border-b border-gray-100 bg-gradient-to-r from-blue-50 to-white shadow-sm'):
                                     ui.avatar(icon='smart_toy', color='blue-600', text_color='white').props('size=sm')
                                     ui.label('Gia sư AI').classes('font-bold text-blue-900')
                                 
                                 with ui.scroll_area().classes('flex-grow w-full p-4 bg-gray-50/50') as tutor_chat_scroll:
                                     tutor_chat_container = ui.column().classes('w-full gap-4')
                                     with tutor_chat_container:
                                         with ui.chat_message(sent=False, avatar='https://www.gstatic.com/lamda/images/gemini_sparkle_v002_d4735304ff6292a690345.svg').classes('bg-blue-50/50 p-2 rounded-lg shadow-sm'):
                                             ui.markdown('Chào bạn, mình là Gia sư AI. Hãy nhập đề bài ở khung bên trái và nhấn "Bắt đầu làm bài" nhé!')
                                 
                                 async def tutor_start_exercise():
                                     prob = tutor_problem.value
                                     if not prob or not prob.strip():
                                         ui.notify('Vui lòng nhập đề bài trước khi bắt đầu!', type='warning')
                                         return
                                     
                                     if main_splitter.value > 5:
                                         toggle_problem_panel()
                                     
                                     with tutor_chat_container:
                                         spinner = ui.row().classes('items-center gap-2')
                                         with spinner:
                                             ui.spinner('dots', size='md', color='blue-500')
                                             ui.label('Đang phân tích đề bài...').classes('text-gray-400 text-xs italic')
                                     
                                     prompt = f\"\"\"Bạn là gia sư AI. Người học vừa nhập một đề bài mới để bắt đầu làm.
Đề bài: {prob}

Nhiệm vụ:
1. Gửi một lời chào thân thiện.
2. Xác nhận đã nhận đề bài và tóm tắt ngắn gọn yêu cầu (1-2 câu).
3. Khuyến khích người học bắt đầu suy nghĩ và viết lời giải vào "Không gian làm bài", sau đó nhấn "Gửi" ở khung chat để bạn hướng dẫn bước đầu tiên.
4. Trình bày bằng Markdown. KHÔNG giải bài toán lúc này.
5. BẮT BUỘC sử dụng cú pháp LaTeX: dùng `$$...$$` cho công thức tách dòng, và `\\\\(...\\\\)` cho công thức trong dòng. TUYỆT ĐỐI KHÔNG DÙNG dấu `$` đơn vì dễ bị lỗi Markdown.
6. Khi viết phép nhân trong công thức, dùng `\\\\cdot` hoặc viết liền (vd `2x^2`). TUYỆT ĐỐI KHÔNG dùng dấu `*` (asterisk) vì Markdown sẽ hiểu nhầm là in nghiêng. Nếu copy đề bài của học sinh, hãy tự động thay dấu `*` thành viết liền hoặc `\\\\cdot`.
7. Đảm bảo Xuống Dòng trước và sau mỗi gạch đầu dòng (`-` hoặc `*`) để danh sách hiển thị rõ ràng, không bị dính chùm.
\"\"\"
                                     try:
                                         response = await run.io_bound(model.generate_content, prompt)
                                         tutor_chat_container.remove(spinner)
                                         with tutor_chat_container:
                                             with ui.chat_message(sent=False, avatar='https://www.gstatic.com/lamda/images/gemini_sparkle_v002_d4735304ff6292a690345.svg').classes('bg-blue-50/50 p-2 rounded-lg shadow-sm'):
                                                 ui.markdown(response.text)
                                         ui.run_javascript('setTimeout(() => { if (window.MathJax) MathJax.typesetPromise(); }, 300);')
                                     except Exception as e:
                                         tutor_chat_container.remove(spinner)
                                         with tutor_chat_container:
                                             ui.chat_message(f"Lỗi: {str(e)}", sent=False).classes('text-red-500')
                                 
                                 async def tutor_send_message():
                                     msg = tutor_input.value
                                     if not msg: return
                                     
                                     with tutor_chat_container:
                                         ui.chat_message(msg, sent=True).classes('font-medium shadow-sm')
                                     tutor_input.value = ''
                                     
                                     with tutor_chat_container:
                                         spinner = ui.row().classes('items-center gap-2')
                                         with spinner:
                                             ui.spinner('dots', size='md', color='blue-500')
                                             ui.label('Đang suy nghĩ...').classes('text-gray-400 text-xs italic')
                                     
                                     try:
                                         problem_text = tutor_problem.value or "Chưa có đề bài"
                                         workspace_text = tutor_workspace.value or "Chưa có bài làm"
                                         
                                         prompt = f\"\"\"Bạn là gia sư AI. Người học đang hỏi bạn: "{msg}".
Đề bài của người học:
{problem_text}

Bài làm hiện tại của người học:
{workspace_text}

Nhiệm vụ:
1. Trả lời câu hỏi và hướng dẫn người học từng bước.
2. Tuyệt đối không đưa ra đáp án trực tiếp.
3. Chỉ hướng dẫn tiếp theo từ bài làm hiện tại.
4. Trình bày dưới dạng Markdown dễ đọc.
5. BẮT BUỘC sử dụng cú pháp LaTeX: dùng `$$...$$` cho công thức tách dòng, và `\\\\(...\\\\)` cho công thức trong dòng. TUYỆT ĐỐI KHÔNG DÙNG dấu `$` đơn vì dễ bị lỗi Markdown.
6. Khi viết phép nhân trong công thức, dùng `\\\\cdot` hoặc viết liền (vd `2x^2`). TUYỆT ĐỐI KHÔNG dùng dấu `*` (asterisk) vì Markdown sẽ hiểu nhầm là in nghiêng. Nếu copy đề bài của học sinh, hãy tự động thay dấu `*` thành viết liền hoặc `\\\\cdot`.
7. Đảm bảo Xuống Dòng trước và sau mỗi gạch đầu dòng (`-` hoặc `*`) để danh sách hiển thị rõ ràng, không bị dính chùm.
\"\"\"
                                         response = await run.io_bound(model.generate_content, prompt)
                                         tutor_chat_container.remove(spinner)
                                         with tutor_chat_container:
                                             with ui.chat_message(sent=False, avatar='https://www.gstatic.com/lamda/images/gemini_sparkle_v002_d4735304ff6292a690345.svg').classes('bg-blue-50/50 p-2 rounded-lg shadow-sm'):
                                                 ui.markdown(response.text)
                                         ui.run_javascript('setTimeout(() => { if (window.MathJax) MathJax.typesetPromise(); }, 300);')
                                     except Exception as e:
                                         tutor_chat_container.remove(spinner)
                                         with tutor_chat_container:
                                             ui.chat_message(f"Lỗi: {str(e)}", sent=False).classes('text-red-500')
                                 
                                 with ui.column().classes('w-full p-4 border-t border-gray-100 bg-white gap-2 z-10'):
                                     with ui.row().classes('w-full items-center gap-2 relative'):
                                         tutor_input = ui.input(placeholder='Hỏi gia sư...').props('rounded outlined dense borderless').classes('w-full bg-gray-100 pr-10').on('keydown.enter', tutor_send_message)
                                         ui.button(icon='send', on_click=tutor_send_message).props('flat round dense color=blue').classes('absolute right-1 top-1/2 transform -translate-y-1/2')
"""

lines = lines[:start_idx] + [new_content] + lines[end_idx+1:]

with codecs.open('main.py', 'w', 'utf-8') as f:
    f.writelines(lines)
print("Patch applied successfully, updated lines from {} to {}".format(start_idx, end_idx))
