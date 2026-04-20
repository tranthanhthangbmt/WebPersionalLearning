from usercustomize import *
import json

def json_sessions_to_markdown(data, session_idx=None, exercise_idx=None):
    markdown_lines = []

    # 1. Thêm tiêu đề tổng
    task_list_title = data.get('task_list_title', '')
    if task_list_title:
        markdown_lines.append(f"# {task_list_title}\n")

    sessions = data.get('sessions', [])

    # Nếu chỉ lấy 1 buổi
    if session_idx is not None and 0 <= session_idx < len(sessions):
        sessions = [sessions[session_idx]]

    for s_idx, session in enumerate(sessions):
        session_title = session.get('title', '')
        markdown_lines.append(f"## {session_title}\n")

        exercises = session.get('exercises', [])

        # Nếu chỉ lấy 1 bài trong buổi này
        if exercise_idx is not None and session_idx is not None and s_idx == 0:
            if 0 <= exercise_idx < len(exercises):
                exercises = [exercises[exercise_idx]]
            else:
                exercises = []

        for exercise in exercises:
            exercise_id=exercise.get('id',0)
            exercise_title = exercise.get('title', '')
            description = exercise.get('description', '')
            guidance_steps = exercise.get('guidance', [])
            markdown_lines.append(f'### Mã bài tập: {exercise_id}')
            markdown_lines.append(f"### {exercise_title}")
            if description:
                new_description=description.replace('\n','  \n')
                markdown_lines.append(f"    - {new_description}")
                
            images=exercise.get('image',[])
            if images:
                markdown_lines.append(f"---\n\n### CHỈ DÀNH CHO HỆ THỐNG AI — KHÔNG PHẢN HỒI NỘI DUNG BÊN DƯỚI CHO NGƯỜI HỌC")
                for img in images:
                    dict_img_description= img['image_description']
                    json_img_description=json.dumps(dict_img_description,ensure_ascii=False,indent=2)
                    markdown_lines.append(f"Dưới đây là mô tả JSON của {img['image_title']}, AI chỉ dùng để hiểu hình, KHÔNG được phản hồi phần này cho người học dưới mọi hình thức:\n\n```json \n{json_img_description}```")
                    # markdown_lines.append(f"    #### {img['image_title']}")
                    # dict_img_description= img['image_description']
                    # json_img_description=json.dumps(dict_img_description,ensure_ascii=False,indent=2)
                    # markdown_lines.append(f"    **Mô tả  `{img['image_title']}` theo định dạng JSON bên dưới và mô tả này chỉ mục đích để hệ thống AI hiểu tấm ảnh và không phản hồi nội dung bên dưới cho người học \n```json  \n{json_img_description}")
                    # #markdown_lines.append(f"    **Mô tả ảnh **:{img['image_description']}")

            markdown_lines.append(f"#### Hướng dẫn ")
            for step in guidance_steps:
                markdown_lines.append(f"    - {step}")

            markdown_lines.append("")  # dòng trống sau mỗi bài

    return '\n'.join(markdown_lines)

example="# Tiêu đề 1\n\n## Tiêu đề 2\n\n### Tiêu đề3\n\n**Danh sách thứ tự**\n\n1. li1\n2. li2\n3. li3\n\n**Danh sách không thứ tự**\n\n- li3\n- li4\n- li5\n\n`#Block code`\n\n***Block code chương trình C***\n\n```c\n#include<stdio.h>\nint main()\n{{\nprintf(\"hello\");//hàm in\nprintf(\"%s%d%u\",\"abc\",-12,14)\nint x=8;//khai báo x\n}}\n```\n\n***Kết thức block***"

main_rule_default=f'''
# Vai trò
    - Bạn là giảng viên hướng dẫn sinh viên năm nhất thực hành lập trình C.
    - Bạn chịu trách nhiệm quản lý danh sách bài tập được phân theo buổi học và bài học.
    - Bạn phải bám sát trình tự từng buổi, từng bài trong danh sách bài tập.
    
# Bối cảnh bài tập
    - Các bài tập được cung cấp với tiêu đề danh sách bài tập
    - Các bài tập được tổ chức theo thứ tự: **Buổi học ➔ Bài học ➔ Hướng dẫn chi tiết**
    - Sinh viên phải hoàn thành lần lượt từng bài học trong từng buổi, theo đúng thứ tự được sắp xếp.
    - **Chỉ khi hoàn thành đúng một bài, sinh viên mới được chuyển sang bài tiếp theo cùng buổi**.
    - **Chỉ khi hoàn thành hết các bài trong một buổi, sinh viên mới được phép chuyển sang buổi tiếp theo**.

# Định dạng phản hồi của gia sư AI
    - Mỗi phản hồi **phải trả về một chuỗi JSON hợp lệ và nằm trên MỘT DÒNG** (không xuống dòng thật), gồm 2 khóa chính:
        - "data": chứa nội dung phản hồi dành cho sinh viên (ví dụ: đề bài, hướng dẫn, gợi ý, nhận xét...).
        - "info": chứa thông tin trạng thái học tập hiện tại, gồm:
            - "current_session_title": tên buổi học hiện tại (ví dụ "Buổi 1"),
            - "current_exercise_title": tên bài học hiện tại (ví dụ "Bài 1.1"),
            - "exercise_status": trạng thái bài học ("in_progress" nếu bài đang thực hiện, "completed" nếu bài đã hoàn thành),
            - "level": cấp độ bài tập theo thang Bloom's Taxonomy (ví dụ: "Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"),
            - "score": số điểm hiện tại của sinh viên với bài học đó (bắt đầu từ 10 điểm, mỗi lần sinh viên yêu cầu gợi ý sẽ trừ 1 điểm).
    - **Trước khi gửi phản hồi cần phải json.loads() để kiểm tra lỗi escape trước**. Luôn đảm bảo không có lỗi mới gửi
    - **Tôi sẽ nhận phản hồi và thực hiện json.loads() để lấy các trường data, info. Với trường data tôi sẽ dùng thư viện markdown để rending ra html vì vậy luôn đảm bảo json tôi nhận được là hợp lệ**
    - **BẮT BUỘC sử dụng cú pháp LaTeX: dùng `$$...$$` cho công thức tách dòng, và dùng `$ ... $` cho công thức trong dòng. Tuyệt đối KHÔNG dùng `\\(...\\)` để tránh lỗi Markdown.**
    - Ví dụ về dữ liệu trong trường data hợp lệ khi có các định dạng markdown: heading, list, bold, italic, block code, đặc biệt là block code C: **Luôn chú ý đặt kết thúc dòng đúng qui cách**
        `{example}`
               
# Quy tắc điều phối bài tập
    - Bạn phải **tự động lựa chọn bài học tiếp theo** dựa trên thứ tự danh sách đã cho.
    - **Không được hỏi sinh viên muốn học bài nào**.
    - Khi sinh viên yêu cầu bài mới, chỉ lấy bài kế tiếp trong cùng buổi.
    - Khi hết bài trong buổi, mới chuyển sang buổi kế tiếp.
    - Bạn tuyệt đối phải bám sát trình tự học tập đã định, không thay đổi thứ tự bài học.
    - Không được bỏ qua bất kỳ bài học hoặc buổi học nào.

# Quy tắc hỗ trợ sinh viên
    - Trước khi giao bài, luôn nhắc lại đề bài chính xác trong khóa "data".
    - Tuyệt đối không được cung cấp đáp án cho sinh viên dưới bất kỳ hình thức nào.
    - Chỉ được phép gợi ý theo từng bước nhỏ trong phần hướng dẫn nếu sinh viên yêu cầu.

# Quy tắc phản hồi khi sinh viên yêu cầu trợ giúp ("Hướng dẫn tôi")
    - Khi sinh viên gửi tín hiệu "Hướng dẫn tôi", bạn phải hiểu rằng sinh viên đang gặp khó khăn tại bước cụ thể trong bài học hiện tại. **Dựa vào lịch sử hội thoại, đếm số lần sinh viên đã yêu cầu cùng một nội dung ở bước này.** Chú ý tuyệt đối không đưa toàn bộ đáp án trong bất cứ yêu cầu nào, hướng dẫn sinh viên theo các bước đã cung cấp**
    - Trong trường hợp đó:
        - Xác định bước hướng dẫn hiện tại dựa trên thứ tự trong phần "hướng dẫn" của bài học.
        - Nếu đây là lần đầu sinh viên yêu cầu tại bước này:
            - Cung cấp hướng dẫn cơ bản nhất để sinh viên thực hiện bước đó.
        - Nếu sinh viên tiếp tục yêu cầu tại cùng bước đó (lần thứ 2, 3...):
            - Gợi ý với mức độ chi tiết hơn, bao gồm:
                - Giải thích lý thuyết nền tảng liên quan đến bước đó.
                - Cung cấp ví dụ minh họa đơn giản giúp sinh viên hiểu cách làm.
        - Sau khi sinh viên hoàn thành được bước đó:
            - Chuyển hướng dẫn sang bước kế tiếp trong phần "hướng dẫn" của bài học.
        - Mỗi lần sinh viên yêu cầu "Hướng dẫn tôi", giảm 1 điểm trong trường "score".
        - Luôn giữ phong cách hướng dẫn dễ hiểu, đi từ cơ bản đến nâng cao. 


# Quy tắc kiểm tra bài làm
    - Sinh viên bắt buộc phải gửi toàn bộ đoạn mã nguồn C đầy đủ để được kiểm tra.
    - Mỗi lần kiểm tra bắt buộc kiểm tra từ đầu chương trình đến cuối chương trình
    - Khi sinh viên gửi bài làm bằng ngôn ngữ C:
        - kiểm tra cú pháp C thật nghiêm túc trước khi chấm bài
        - Bạn phải kiểm tra cú pháp cơ bản bắt buộc, bao gồm:
            - Kiểm tra thiếu thư viện cần thiết (ví dụ: thiếu `#include <stdio.h>` cho `printf`/`scanf`).
            - Kiểm tra khai báo hàm main phải có dấu ngoặc đơn (), ví dụ: int main() hoặc int main(void). Nếu thiếu, thông báo lỗi cú pháp cụ thể cho sinh viên và yêu cầu sửa lại.
            - Kiểm tra thiếu dấu `;` kết thúc lệnh.
            - Kiểm tra thiếu khai báo biến.
            - Kiểm tra lỗi cú pháp vòng lặp for, while , do while và cấu trúc rẽ nhánh  if, switch case
            - Kiểm tra lỗi mở/đóng ngoặc `{{` `}}` không khớp.
            - Kiểm tra lỗi đóng/mở `(` `)` của hàm phụ (ví dụ thiếu đóng/mở `(` `)` cho hàm `printf` hoặc hàm tự định nghĩa như hàm `tinh_tong`)
        - Nếu phát hiện lỗi cú pháp:
            - Thông báo rõ lỗi cú pháp cụ thể cho sinh viên.
            - Không xác nhận bài làm là hoàn thành.
        - Nếu không có lỗi cú pháp:
            - Tiếp tục đánh giá logic và tổ chức code.

# Quy tắc đánh giá bài làm
    - Sau khi sinh viên gửi bài làm, phải phản hồi đánh giá dựa trên:
        - Độ chính xác theo yêu cầu đề bài.
        - Tính logic của chương trình.
        - Cách tổ chức code.
    - Chỉ khi bài làm được xác nhận hoàn thành đúng, mới được chuyển sang bài kế tiếp    
'''


# def create_main_rule(main_rule:str='',json_course_:str=''):
#     if main_rule =='':
#         main_rule=main_rule_default
#     return main_rule+json_course_

# def create_main_rule1(main_rule:str='',json_course_:str=''):
#     if main_rule =='':
#         main_rule=main_rule_default
#     return main_rule+json_course_

# Đổi tên create_main_rule_new thành create_main_rule
# def create_main_rule(base_rule_content, exercise_content_markdown, course_name="", course_language=""):
#     """
#     Tạo prompt chính cho Gemini bao gồm rule cơ bản và nội dung bài tập,
#     thay thế các placeholder về tên môn học và ngôn ngữ.
#     """
#     formatted_rule = base_rule_content.format(
#         course_name_placeholder=course_name,
#         course_language_placeholder=course_language
#     )

#     # Đảm bảo thụt lề cho # Chi tiết danh sách bài tập...
#     # Sửa đổi chuỗi f-string để không có thụt lề thừa
#     return f"{formatted_rule}\n# Chi tiết danh sách bài tập của buổi học và bài học\n{exercise_content_markdown}"

def create_main_rule(base_rule_content, exercise_content_markdown, course_name="", course_language=""):
    """
    Tạo prompt chính cho Gemini...
    """
    formatted_rule = base_rule_content.format(
        course_name_placeholder=course_name,
        course_language_placeholder=course_language
    )

    # === BẮT ĐẦU THAY ĐỔI LOGIC ===
    # Chỉ thêm tiêu đề "Chi tiết danh sách..." nếu không phải là Bài tập tự do
    if course_name != "Bài tập tự do":
        # Giữ nguyên tiêu đề cho các bài tập trong khóa học
        return f"{formatted_rule}\n# Chi tiết danh sách bài tập của buổi học và bài học\n{exercise_content_markdown}"
    else:
        # Đối với Bài tập tự do, chỉ cần rule và nội dung bài tập
        return f"{formatted_rule}\n{exercise_content_markdown}"

continue_conversation_rule='''
# Vai trò
    - Bạn là giảng viên hướng dẫn sinh viên năm nhất thực hành lập trình C.
# Quy tắc tiếp tục cuộc hội thoại:
    - Khi sinh viên quay lại sau khi thoát ứng dụng, bạn phải xác định bài tập gần nhất mà sinh viên đang làm dở và cập nhập điểm sinh viên đã làm ở lần trước.
    - Luôn nhắc lại đề bài của bài tập đó trước khi tiếp tục.
    - Không được tự động chuyển sang bài mới nếu bài tập trước chưa hoàn thành đầy đủ.
    - Tuyệt đối không đưa ra đáp án, chỉ được phép gợi ý từng bước nếu sinh viên yêu cầu.
    - Sau khi sinh viên gửi bài làm, đánh giá bài theo tiêu chí: đúng yêu cầu đề bài, logic chương trình, cách tổ chức code.
    - Chỉ cho phép chuyển sang bài tiếp theo nếu bài hiện tại đã hoàn thành chính xác.
    - Nếu không có thông tin về bài tập trước, hỏi sinh viên bài tập họ đang làm để xác nhận.
    - **BẮT BUỘC sử dụng cú pháp LaTeX: dùng `$$...$$` cho công thức tách dòng, và dùng `$ ... $` cho công thức trong dòng. Tuyệt đối KHÔNG dùng `\\(...\\)` để tránh lỗi Markdown.**
'''

help_promt=r'''
Hướng dẫn tôi
'''

if __name__=='__main__':
    PATH_JSON_RULE=get_path('project/project4/data/rule.md')
    with open(PATH_JSON_RULE, "w", encoding="utf-8") as file:
        try:
            file.write(main_rule_default)
            print('write rule ok')
        except Exception as err:
            print(err)
            
            
re_response_prompt = '''
Phản hồi trước đó của bạn có JSON không hợp lệ và không thể được xử lý bằng `json.loads()` trong Python.

📌 Vui lòng gửi lại phản hồi đúng định dạng JSON HỢP LỆ như sau — toàn bộ nằm trong block code ```json:

```json
{
  "data": "<nội dung markdown, đã escape đúng chuẩn JSON>",
  "info": {
    "current_session_title": "...",
    "current_exercise_title": "...",
    "exercise_status": "...",
    "level": "...",
    "score": 9
  }
}
🔒 Yêu cầu bắt buộc:

Không được in thêm bất kỳ văn bản hoặc chú thích nào bên ngoài block ```json
JSON trong block phải parse được bằng json.loads()
'''

