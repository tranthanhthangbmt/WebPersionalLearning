import streamlit as st
import pandas as pd
import numpy as np
import ast
import os
import sys

# Thêm đường dẫn thư mục gốc để import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- BẢO VỆ TRANG ---
if st.session_state.get("authentication_status", False):

    # --- TOÀN BỘ CODE CỦA TRANG LUYỆN TẬP CỦA BẠN NẰM Ở ĐÂY ---
    st.set_page_config(page_title="Luyện tập", page_icon="🎓", layout="wide")
    st.title("🎓 Luyện tập theo Chủ đề")
    
    # --- ĐỊNH NGHĨA ĐƯỜNG DẪN TƯƠNG ĐỐI ---
    DATA_FOLDER = "knowledge"
    GRAPH_FILE_PATH = os.path.join(DATA_FOLDER, "k-graph.csv")
    MATRIX_FILE_PATH = os.path.join(DATA_FOLDER, "q-matrix.csv")

    # --- TẢI DỮ LIỆU ---
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

    if k_graph_df is not None and q_matrix_df is not None:
        source_skills = k_graph_df['source'].unique()
        target_skills = k_graph_df['target'].unique()
        all_skills = np.unique(np.concatenate((source_skills, target_skills)))
        all_skills = sorted(all_skills)
        all_skills_with_prompt = ["--- Chọn một chủ đề / kỹ năng ---"] + all_skills

        selected_skill = st.selectbox(
            "Chọn một chủ đề bạn muốn ôn tập:",
            options=all_skills_with_prompt
        )

        if selected_skill != "--- Chọn một chủ đề / kỹ năng ---":
            st.subheader(f"Các câu hỏi liên quan đến: {selected_skill}")
            filtered_questions = q_matrix_df[q_matrix_df['skill_id_list'].str.contains(selected_skill, na=False)]
            
            if filtered_questions.empty:
                st.warning("Không tìm thấy câu hỏi nào cho chủ đề này.")
            else:
                st.info(f"Tìm thấy {len(filtered_questions)} câu hỏi:")
                for index, row in filtered_questions.iterrows():
                    st.markdown(f"**Câu hỏi (ID: {row['question_id']}):** {row['content']}")
                    st.caption(f"Độ khó: {row['difficulty']} | Mã kỹ năng: {row['skill_id_list']}")
                    if pd.notna(row['answer']) and str(row['answer']).strip() != "":
                        try:
                            options_list = ast.literal_eval(row['options'])
                            st.radio("Các lựa chọn:", options=options_list, key=f"radio_{row['question_id']}")
                            st.success(f"Đáp án đúng (Check): {row['answer']}")
                        except Exception as e:
                            st.error(f"Lỗi khi hiển thị các lựa chọn: {e}")
                    else:
                        st.info("Đây là câu hỏi Tự luận / Thực hành.")
                    st.divider()
    else:
        st.error("Không thể tải dữ liệu để hiển thị trang Luyện tập.")

else:
    # --- HIỂN THỊ NẾU CHƯA ĐĂNG NHẬP ---
    st.error("🔒 Bạn phải đăng nhập để truy cập trang này.")
    st.info("Vui lòng quay lại trang chủ (Home) để đăng nhập.")