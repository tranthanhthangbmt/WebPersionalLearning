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

# --- 1. GIAO DIỆN CHỌN BÀI KIỂM TRA ---

st.header("Thiết lập bài kiểm tra")

# Lấy danh sách tất cả các chủ đề (kỹ năng)
source_skills = k_graph_df['source'].unique()
target_skills = k_graph_df['target'].unique()
all_skills = np.unique(np.concatenate((source_skills, target_skills)))
all_skills = sorted(all_skills)

# Cho phép chọn nhiều chủ đề
selected_topics = st.multiselect(
    "Chọn một hoặc nhiều chủ đề để kiểm tra:",
    options=all_skills
)

# Cho phép chọn số lượng câu hỏi
num_questions = st.number_input(
    "Chọn số lượng câu hỏi (Tối đa 20):",
    min_value=1,
    max_value=20,
    value=5
)

# Nút để bắt đầu tạo bài kiểm tra
if st.button("Tạo bài kiểm tra"):
    
    if not selected_topics:
        st.warning("Bạn phải chọn ít nhất một chủ đề.")
    else:
        # Lọc các câu hỏi thuộc chủ đề đã chọn
        filtered_df = q_matrix_df[
            q_matrix_df['skill_id_list'].apply(
                lambda x: any(topic in x for topic in selected_topics)
            )
        ]
        
        # Chỉ lấy các câu hỏi trắc nghiệm (MCQ) để dễ chấm
        mcq_questions = filtered_df[
            pd.notna(filtered_df['answer']) & (filtered_df['answer'].str.strip() != "")
        ].copy() # .copy() để tránh warning

        if mcq_questions.empty:
            st.error("Không tìm thấy câu hỏi trắc nghiệm nào cho các chủ đề này.")
        else:
            # Lấy ngẫu nhiên 'num_questions' câu
            # Nếu không đủ câu hỏi, lấy tối đa có thể
            actual_num = min(len(mcq_questions), num_questions)
            quiz_questions = mcq_questions.sample(n=actual_num)
            
            # **QUAN TRỌNG: Lưu bài kiểm tra vào Session State**
            # Điều này giữ cho bài kiểm tra không bị thay đổi khi người dùng trả lời
            st.session_state.quiz = quiz_questions
            st.session_state.user_answers = {} # Reset câu trả lời
            st.session_state.submitted = False # Trạng thái chưa nộp bài
            st.success(f"Đã tạo bài kiểm tra gồm {actual_num} câu. Hãy kéo xuống để làm bài!")

# --- 2. HIỂN THỊ BÀI KIỂM TRA (SỬ DỤNG FORM) ---

# Chỉ hiển thị form nếu bài kiểm tra đã được tạo trong session_state
if "quiz" in st.session_state:
    
    st.header("Làm bài kiểm tra")
    
    # st.form gom tất cả các câu hỏi lại
    with st.form(key="quiz_form"):
        user_answers = {} # Dictionary để lưu câu trả lời của người dùng
        
        quiz_df = st.session_state.quiz
        
        for index, row in quiz_df.iterrows():
            st.markdown(f"**Câu {index + 1} (ID: {row['question_id']}):** {row['content']}")
            
            try:
                # Chuyển string '["A...", "B..."]' thành list
                options_list = ast.literal_eval(row['options'])
                
                # Thêm lựa chọn "Chưa trả lời"
                options_with_none = ["---"] + options_list
                
                # Hiển thị các nút radio
                user_choice_str = st.radio(
                    "Lựa chọn của bạn:",
                    options=options_with_none,
                    key=f"radio_{row['question_id']}",
                    label_visibility="collapsed" # Ẩn nhãn "Lựa chọn của bạn:"
                )
                
                # Phân tích câu trả lời (ví dụ: "A. E-Business hẹp hơn...")
                if user_choice_str != "---":
                    # Chỉ lấy ký tự đầu tiên (A, B, C, D)
                    user_answers[row['question_id']] = user_choice_str.split('.')[0]
                else:
                    user_answers[row['question_id']] = None # Chưa trả lời
                    
            except Exception as e:
                st.error(f"Lỗi hiển thị câu hỏi {row['question_id']}: {e}")
            
            st.divider()

        # Nút nộp bài ở cuối form
        submitted = st.form_submit_button("Nộp bài")

        if submitted:
            # Lưu câu trả lời và trạng thái đã nộp
            st.session_state.user_answers = user_answers
            st.session_state.submitted = True


# --- 3. HIỂN THỊ KẾT QUẢ ---

# Chỉ hiển thị kết quả SAU KHI người dùng đã nộp bài
if "submitted" in st.session_state and st.session_state.submitted:
    
    st.header("Kết quả Bài kiểm tra")
    
    score = 0
    quiz_df = st.session_state.quiz
    user_answers = st.session_state.user_answers
    
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
        
        st.divider()

    total_questions = len(quiz_df)
    final_score = (score / total_questions) * 10
    
    st.header(f"🏁 Tổng điểm: {score}/{total_questions} ({final_score:.1f} điểm)")
    
    # Xóa bài kiểm tra khỏi bộ nhớ để làm bài mới
    del st.session_state.quiz
    del st.session_state.submitted