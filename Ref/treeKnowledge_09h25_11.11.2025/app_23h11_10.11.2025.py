import streamlit as st
import pandas as pd
import os # Import thư viện 'os' để xử lý đường dẫn

# --- ĐỊNH NGHĨA ĐƯỜNG DẪN TƯƠNG ĐỐI ---
# 'knowledge' là thư mục con nằm bên trong thư mục chứa file app.py
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
st.write("Phiên bản demo - Đã cập nhật đường dẫn tương đối.")

# --- TẢI DỮ LIỆU ---
@st.cache_data
def load_data(graph_file, matrix_file):
    k_graph = pd.read_csv(graph_file, comment='#')
    q_matrix = pd.read_csv(matrix_file, comment='#')
    return k_graph, q_matrix

# --- HIỂN THỊ DỮ LIỆU ---
st.header("1. Dữ liệu Đồ thị Tri thức (Knowledge Graph)")
st.write(f"Đang tải từ: {GRAPH_FILE_PATH}") # Hiển thị đường dẫn để kiểm tra

try:
    # Gọi hàm để tải dữ liệu từ đường dẫn đã cập nhật
    k_graph_df, q_matrix_df = load_data(GRAPH_FILE_PATH, MATRIX_FILE_PATH)

    st.dataframe(k_graph_df)

    st.header("2. Dữ liệu Ngân hàng Câu hỏi (Q-Matrix)")
    st.write(f"Đang tải từ: {MATRIX_FILE_PATH}") # Hiển thị đường dẫn để kiểm tra
    st.dataframe(q_matrix_df)

except FileNotFoundError:
    st.error(f"LỖI: Không tìm thấy file tại đường dẫn tương đối.")
    st.error(f"Đường dẫn đang tìm kiếm K-Graph: {GRAPH_FILE_PATH}")
    st.error(f"Đường dẫn đang tìm kiếm Q-Matrix: {MATRIX_FILE_PATH}")
    st.info(f"Hãy đảm bảo bạn đang chạy 'streamlit run app.py' từ thư mục 'D:\MY_CODE\treeKnowledge' và thư mục 'knowledge' có tồn tại bên trong nó.")
except Exception as e:
    st.error(f"Đã xảy ra lỗi khi đọc file: {e}")