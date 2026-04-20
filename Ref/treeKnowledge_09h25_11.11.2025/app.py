import streamlit as st
import pandas as pd
import os
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from db_utils import init_db # Import hàm khởi tạo CSDL

# --- 0. KHỞI TẠO CSDL ---
init_db() 

# --- 1. TẢI CẤU HÌNH XÁC THỰC (Giữ nguyên) ---
st.set_page_config(
    page_title="Hệ thống Cây tri thức",
    page_icon="🌳",
    layout="wide"
)

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# --- 2. XỬ LÝ ĐĂNG NHẬP / ĐĂNG KÝ (SỬA LỖI LỚN) ---
if "authentication_status" not in st.session_state:
    st.session_state["authentication_status"] = None

login_tab, register_tab = st.tabs(["Đăng nhập", "Đăng ký"])

# --- THAY ĐỔI TRONG TAB ĐĂNG NHẬP ---
with login_tab:
    # Hàm login() mới nhất chỉ gọi như thế này.
    # Nó sẽ tự động cập nhật st.session_state
    authenticator.login() 
# --- KẾT THÚC THAY ĐỔI ---

with register_tab:
    try:
        # --- THAY ĐỔI TRONG TAB ĐĂNG KÝ ---
        # Hàm register_user() mới nhất gọi như thế này
        if authenticator.register_user(preauthorization=config['preauthorized']):
        # --- KẾT THÚC THAY ĐỔI ---
            st.success('Đăng ký người dùng thành công! Vui lòng quay lại tab "Đăng nhập".')
            # Tự động cập nhật file config.yaml
            with open('config.yaml', 'w') as file:
                yaml.dump(config, file, default_flow_style=False)
    except Exception as e:
        st.error(e)

# --- 3. BẢO VỆ ỨNG DỤNG (Giữ nguyên) ---
# Logic này bây giờ hoạt động vì authenticator.login() đã cập nhật
# st.session_state["authentication_status"] một cách ngầm.

if st.session_state["authentication_status"] == False:
    st.error('Tên đăng nhập hoặc mật khẩu không chính xác.')

if st.session_state["authentication_status"] == None:
    st.warning('Vui lòng đăng nhập hoặc đăng ký để tiếp tục.')

if st.session_state["authentication_status"]:
    # --- PHẦN ỨNG DỤNG CHÍNH (Giữ nguyên) ---
    st.sidebar.title(f"Chào mừng, {st.session_state['name']}!")
    authenticator.logout('Đăng xuất', 'sidebar')
    
    st.sidebar.success("Hãy chọn một chức năng (trang) bên trên.")
    
    st.title(f"🌳 Chào mừng tới Cây Tri Thức TMĐT")
    st.markdown(
        """
        Đây là trang chủ. Hệ thống đã xác thực bạn thành công.
        Sử dụng thanh điều hướng bên trái để truy cập các chức năng.
        """
    )

    # --- Hiển thị dữ liệu gốc (Giữ nguyên) ---
    DATA_FOLDER = "knowledge"
    GRAPH_FILE_PATH = os.path.join(DATA_FOLDER, "k-graph.csv")
    MATRIX_FILE_PATH = os.path.join(DATA_FOLDER, "q-matrix.csv")

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

    if k_graph_df is not None:
        with st.expander("Xem dữ liệu gốc (Raw Data) 🔽"):
            st.dataframe(k_graph_df)
            st.dataframe(q_matrix_df)