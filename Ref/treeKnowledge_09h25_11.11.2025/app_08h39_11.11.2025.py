import streamlit as st
import pandas as pd
import os
import streamlit_authenticator as stauth # (Bạn đã import ở Giai đoạn 1)
from db_utils import init_db  # <-- 1. IMPORT HÀM MỚI

# --- KHỞI TẠO CƠ SỞ DỮ LIỆU ---
init_db()  # <-- 2. GỌI HÀM ĐỂ TẠO BẢNG

# --- ĐỊNH NGHĨA ĐƯỜNG DẪN TƯƠNG ĐỐI ---
DATA_FOLDER = "knowledge"
GRAPH_FILE_PATH = os.path.join(DATA_FOLDER, "k-graph.csv")
MATRIX_FILE_PATH = os.path.join(DATA_FOLDER, "q-matrix.csv")

# --- CẤU HÌNH TRANG ---
st.set_page_config(
    page_title="Trang chủ - Ứng dụng TMĐT",
    page_icon="🏠",
    layout="wide"
)

# --- NỘI DUNG TRANG CHỦ ---
st.title("🏠 Hệ thống Hỗ trợ Học tập môn TMĐT")
st.sidebar.success("Hãy chọn một chức năng bên trên.")

st.markdown(
    """
    Chào mừng bạn đến với hệ thống hỗ trợ học tập!
    
    Hệ thống này được xây dựng để giúp bạn:
    * **Luyện tập:** Lọc và làm các câu hỏi trắc nghiệm, tự luận theo từng chủ đề.
    * **Khám phá:** Trực quan hóa mối quan hệ giữa các bài học (Đồ thị tri thức).
    
    Hãy sử dụng thanh điều hướng bên trái (sidebar) để chọn một chức năng.
    """
)

# --- TẢI DỮ LIỆU (Giữ nguyên) ---
@st.cache_data
def load_data(graph_file, matrix_file):
    try:
        k_graph = pd.read_csv(graph_file, comment='#')
        q_matrix = pd.read_csv(matrix_file, comment='#')
        return k_graph, q_matrix
    except Exception as e:
        st.error(f"Lỗi khi tải dữ liệu: {e}")
        return None, None

# --- Hiển thị dữ liệu gốc (nếu cần xem) ---
k_graph_df, q_matrix_df = load_data(GRAPH_FILE_PATH, MATRIX_FILE_PATH)

if k_graph_df is not None and q_matrix_df is not None:
    with st.expander("Xem dữ liệu gốc (Raw Data) 🔽"):
        st.header("1. Dữ liệu Đồ thị Tri thức (Knowledge Graph)")
        st.dataframe(k_graph_df)

        st.header("2. Dữ liệu Ngân hàng Câu hỏi (Q-Matrix)")
        st.dataframe(q_matrix_df)
else:
    st.error("Không thể tải dữ liệu. Vui lòng kiểm tra lại file trong thư mục 'knowledge'.")