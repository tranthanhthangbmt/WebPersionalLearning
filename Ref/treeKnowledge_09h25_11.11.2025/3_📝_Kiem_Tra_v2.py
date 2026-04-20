import streamlit as st
import pandas as pd
import numpy as np
import os
import ast # Để xử lý list trong file CSV

# --- ĐỊNH NGHĨA ĐƯỜNG DẪN TƯƠNG ĐỐI ---
DATA_FOLDER = "knowledge"
GRAPH_FILE_PATH = os.path.join(DATA_FOLDER, "k-graph.csv")
MATRIX_FILE_PATH = os.path.join(DATA_FOLDER, "q-matrix.csv")

# --- CẤU HÌNH TRANG ---
st.set_page_config(
    page_title="Bài kiểm tra TMĐT",
    page_icon="📝",
    layout="wide"
)

st.title("📝 Bài kiểm tra Nhanh")

# --- TẢI DỮ LIỆU (Cần cả 2 file) ---
@st.cache_data
def load_data(graph_file, matrix_file):
    try:
        k_graph = pd.read_csv(graph_file, comment='#')
        q_matrix = pd.read_csv(matrix_file, comment='#')
        return k_graph, q_matrix
    except Exception as e:
        st.error(f"Lỗi khi tải dữ liệu: {e}")
        return None, None

k_graph_df, q_matrix_df = load_data(GRAPH_FILE_PATH, MATRIX_FILE_PATH)

# --- XỬ LÝ NẾU TẢI LỖI ---
if k_graph_df is None or q_matrix_df is None:
    st.error("Không thể tải đủ dữ liệu. Vui lòng kiểm tra lại file trong thư mục 'knowledge'.")
    st.stop()

# --- 1. GIAO DIỆN CHỌN BÀI KIỂM TRA (Giữ nguyên) ---

st.header("Thiết lập bài kiểm tra")

source_skills = k_graph_df['source'].unique()
target_skills = k_graph_df['target'].unique()
all_skills = np.unique(np.concatenate((source_skills, target_skills)))
all_skills = sorted(all_skills)

selected_topics = st.multiselect(
    "Chọn một hoặc nhiều chủ đề để kiểm tra:",
    options=all_skills
)

num_questions = st.number_input(
    "Chọn số lượng câu hỏi (Tối đa 20):",
    min_value=1,
    max_value=20,
    value=5
)

if st.button("Tạo bài kiểm tra"):
    
    if not selected_topics:
        st.warning("Bạn phải chọn ít nhất một chủ đề.")
    else:
        filtered_df = q_matrix_df[
            q_matrix_df['skill_id_list'].apply(
                lambda x: any(topic in x for topic in selected_topics)
            )
        ]
        
        mcq_questions = filtered_df[
            pd.notna(filtered_df['answer']) & (filtered_df['answer'].str.strip() != "")
        ].copy()

        if mcq_questions.empty:
            st.error("Không tìm thấy câu hỏi trắc nghiệm nào cho các chủ đề này.")
        else:
            actual_num = min(len(mcq_questions), num_questions)
            quiz_questions = mcq_questions.sample(n=actual_num)
            
            st.session_state.quiz = quiz_questions
            st.session_state.user_answers = {}
            st.session_state.submitted = False
            st.success(f"Đã tạo bài kiểm tra gồm {actual_num} câu. Hãy kéo xuống để làm bài!")

# --- 2. HIỂN THỊ BÀI KIỂM TRA (Giữ nguyên) ---

if "quiz" in st.session_state:
    
    st.header("Làm bài kiểm tra")
    
    with st.form(key="quiz_form"):
        user_answers = {}
        quiz_df = st.session_state.quiz
        
        for index, row in quiz_df.iterrows():
            st.markdown(f"**Câu {index + 1} (ID: {row['question_id']}):** {row['content']}")
            
            try:
                options_list = ast.literal_eval(row['options'])
                options_with_none = ["---"] + options_list
                
                user_choice_str = st.radio(
                    "Lựa chọn của bạn:",
                    options=options_with_none,
                    key=f"radio_{row['question_id']}",
                    label_visibility="collapsed"
                )
                
                if user_choice_str != "---":
                    user_answers[row['question_id']] = user_choice_str.split('.')[0]
                else:
                    user_answers[row['question_id']] = None
                    
            except Exception as e:
                st.error(f"Lỗi hiển thị câu hỏi {row['question_id']}: {e}")
            
            st.divider()

        submitted = st.form_submit_button("Nộp bài")

        if submitted:
            st.session_state.user_answers = user_answers
            st.session_state.submitted = True


# --- 3. HIỂN THỊ KẾT QUẢ (ĐÃ NÂNG CẤP) ---

# Chỉ hiển thị kết quả SAU KHI người dùng đã nộp bài
if "submitted" in st.session_state and st.session_state.submitted:
    
    st.header("Kết quả Bài kiểm tra")
    
    score = 0
    quiz_df = st.session_state.quiz
    user_answers = st.session_state.user_answers
    
    # *** BẮT ĐẦU NÂNG CẤP ***
    # Tạo một dictionary để đếm các kỹ năng bị sai
    weak_skills_counter = {}
    # *** KẾT THÚC NÂNG CẤP ***

    for question_id, user_ans in user_answers.items():
        # Lấy câu hỏi tương ứng từ quiz_df
        question_row = quiz_df[quiz_df['question_id'] == question_id].iloc[0]
        correct_ans = question_row['answer']
        
        st.subheader(f"Câu hỏi: {question_row['content']}")
        st.write(f"Câu trả lời của bạn: **{user_ans}**")
        
        if user_ans == correct_ans:
            score += 1
            st.success(f"Chính xác! Đáp án đúng là: **{correct_ans}**")
        else:
            st.error(f"Không chính xác. Đáp án đúng là: **{correct_ans}**")
            
            # *** BẮT ĐẦU NÂNG CẤP: PHÂN TÍCH LỖI SAI ***
            try:
                # Đọc skill_id_list (ví dụ: '["1.4_LoiIch_HanChe"]')
                skill_list_str = question_row['skill_id_list']
                skills = ast.literal_eval(skill_list_str) # Chuyển thành list
                
                if isinstance(skills, list):
                    for skill in skills:
                        # Tăng bộ đếm cho kỹ năng này
                        weak_skills_counter[skill] = weak_skills_counter.get(skill, 0) + 1
            except Exception as e:
                # Bỏ qua nếu có lỗi khi đọc skill_id (ví dụ: list rỗng)
                pass
            # *** KẾT THÚC NÂNG CẤP ***
        
        st.divider()

    total_questions = len(quiz_df)
    final_score = (score / total_questions) * 10
    
    st.header(f"🏁 Tổng điểm: {score}/{total_questions} ({final_score:.1f} điểm)")
    
    # *** BẮT ĐẦU NÂNG CẤP: HIỂN THỊ GỢI Ý ***
    if weak_skills_counter:
        st.subheader("💡 Gợi ý ôn tập")
        st.info(
            "Hệ thống nhận thấy bạn có vẻ chưa nắm vững các chủ đề sau đây. "
            "Hãy quay lại trang 'Luyện tập' hoặc 'Đồ thị' để ôn lại nhé!"
        )
        
        # Sắp xếp các kỹ năng yếu theo số lần sai nhiều nhất
        sorted_weak_skills = sorted(
            weak_skills_counter.items(), 
            key=lambda item: item[1], 
            reverse=True
        )
        
        for skill, count in sorted_weak_skills:
            st.markdown(f"* **{skill}**: Bạn đã sai {count} câu liên quan.")
    
    elif score == total_questions:
        st.balloons() # Thêm hiệu ứng chúc mừng nếu đạt điểm tuyệt đối
        st.success("Tuyệt vời! Bạn đã trả lời đúng tất cả các câu hỏi!")
    # *** KẾT THÚC NÂNG CẤP ***

    # Xóa bài kiểm tra khỏi bộ nhớ để làm bài mới
    del st.session_state.quiz
    del st.session_state.submitted