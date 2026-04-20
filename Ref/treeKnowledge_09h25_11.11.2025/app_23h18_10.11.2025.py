import streamlit as st
import pandas as pd
import os
import numpy as np # Import thư viện numpy để xử lý mảng
import ast # Import thư viện ast để xử lý string list an toàn

# --- ĐỊNH NGHĨA ĐƯỜNG DẪN TƯƠNG ĐỐI ---
DATA_FOLDER = "knowledge"
GRAPH_FILE_PATH = os.path.join(DATA_FOLDER, "k-graph.csv")
MATRIX_FILE_PATH = os.path.join(DATA_FOLDER, "q-matrix.csv")

# --- CẤU HÌNH TRANG ---
st.set_page_config(
    page_title="Ứng dụng TMĐT",
    page_icon="🎓",
    layout="wide"
)

# --- TIÊU ĐỀ ỨNG DỤNG ---
st.title("🎓 Hệ thống Hỗ trợ Học tập môn TMĐT")
st.write("Phiên bản 2.0 - Lọc câu hỏi theo chủ đề")

# --- TẢI DỮ LIỆU (Giữ nguyên) ---
@st.cache_data
def load_data(graph_file, matrix_file):
    try:
        k_graph = pd.read_csv(graph_file, comment='#')
        q_matrix = pd.read_csv(matrix_file, comment='#')
        return k_graph, q_matrix
    except FileNotFoundError as e:
        st.error(f"LỖI: Không tìm thấy file. {e}")
        st.info(f"Đảm bảo file tồn tại tại: {graph_file} và {matrix_file}")
        return None, None
    except Exception as e:
        st.error(f"Lỗi khi đọc file CSV: {e}")
        st.warning("Hãy đảm bảo nội dung file CSV của bạn là chính xác, không bị lỗi (như đã sửa ở bước trước).")
        return None, None

# Tải dữ liệu
k_graph_df, q_matrix_df = load_data(GRAPH_FILE_PATH, MATRIX_FILE_PATH)

# --- BƯỚC TIẾP THEO BẮT ĐẦU TỪ ĐÂY ---

# Chỉ tiếp tục nếu_x cả 2 file được tải thành công
if k_graph_df is not None and q_matrix_df is not None:

    st.header("🎯 Luyện tập theo Chủ đề")
    
    # --- 1. Lấy danh sách Kỹ năng (Skills) ---
    # Lấy tất cả các giá trị duy nhất từ cột 'source' và 'target' trong k-graph
    source_skills = k_graph_df['source'].unique()
    target_skills = k_graph_df['target'].unique()
    
    # Kết hợp cả hai và_x lọc lại các giá trị duy nhất, sau đó sắp xếp
    all_skills = np.unique(np.concatenate((source_skills, target_skills)))
    all_skills = sorted(all_skills) # Sắp xếp cho dễ nhìn
    
    # Thêm một lựa chọn "mặc định" vào đầu danh sách
    all_skills_with_prompt = ["--- Chọn một chủ đề / kỹ năng ---"] + all_skills

    # --- 2. Tạo Selectbox (Menu thả xuống) ---
    selected_skill = st.selectbox(
        "Chọn một chủ đề bạn muốn ôn tập:",
        options=all_skills_with_prompt
    )

    # --- 3. Lọc và Hiển thị Câu hỏi ---
    # Chỉ thực hiện khi người dùng đã chọn một chủ đề
    if selected_skill != "--- Chọn một chủ đề / kỹ năng ---":
        
        st.subheader(f"Các câu hỏi liên quan đến: {selected_skill}")
        
        # Lọc q_matrix
        # Cột 'skill_id_list' của bạn có dạng string '["1.1_DinhNghia_EC_EB"]'
        # Chúng ta dùng .str.contains() để_x tìm_xem 'skill_id_list' có chứa 'selected_skill' không
        filtered_questions = q_matrix_df[
            q_matrix_df['skill_id_list'].str.contains(selected_skill, na=False)
        ]
        
        # Hiển thị kết quả
        if filtered_questions.empty:
            st.warning("Không tìm thấy câu hỏi nào cho chủ đề này.")
        else:
            st.info(f"Tìm thấy {len(filtered_questions)} câu hỏi:")
            
            # Hiển thị từng câu hỏi một cách_x đẹp mắt
            for index, row in filtered_questions.iterrows():
                st.markdown(f"**Câu hỏi (ID: {row['question_id']}):** {row['content']}")
                st.caption(f"Độ khó: {row['difficulty']} | Mã kỹ năng: {row['skill_id_list']}")
                
                # Kiểm tra xem đây có phải là câu hỏi MCQ không
                # Bằng cách_x xem cột 'answer' có nội dung hay không
                if pd.notna(row['answer']) and str(row['answer']).strip() != "":
                    try:
                        # 'options' là một string '["A...", "B..."]'
                        # ast.literal_eval sẽ_x chuyển nó thành 1 list Python an toàn
                        options_list = ast.literal_eval(row['options'])
                        
                        # Tạo các nút radio cho các lựa chọn
                        st.radio(
                            "Các lựa chọn:",
                            options=options_list,
                            key=f"radio_{row['question_id']}" # key duy nhất_x cho mỗi câu hỏi
                        )
                        st.success(f"Đáp án đúng (Check): {row['answer']}")
                    except Exception as e:
                        st.error(f"Lỗi khi hiển thị các lựa chọn: {e}")
                        st.write("Dữ liệu gốc của lựa chọn:", row['options'])
                else:
                    st.info("Đây là câu hỏi Tự luận / Thực hành.")
                
                st.divider() # Thêm một đường kẻ_x ngang_x

# --- Hiển thị dữ liệu gốc (nếu cần xem) ---
with st.expander("Xem dữ liệu gốc (Raw Data) 🔽"):
    st.header("1. Dữ liệu Đồ thị Tri thức (Knowledge Graph)")
    st.dataframe(k_graph_df)

    st.header("2. Dữ liệu Ngân hàng Câu hỏi (Q-Matrix)")
    st.dataframe(q_matrix_df)