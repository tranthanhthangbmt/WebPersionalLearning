import streamlit as st
import pandas as pd
import numpy as np
import ast
import os
# Import thư viện mới
from streamlit_agraph import agraph, Node, Edge, Config

# --- ĐỊNH NGHĨA ĐƯỜNG DẪN TƯƠNG ĐỐI ---
DATA_FOLDER = "knowledge"
GRAPH_FILE_PATH = os.path.join(DATA_FOLDER, "k-graph.csv")
MATRIX_FILE_PATH = os.path.join(DATA_FOLDER, "q-matrix.csv") # Cần file này

# --- CẤU HÌNH TRANG ---
st.set_page_config(
    page_title="Đồ thị Tương tác",
    page_icon="✨",
    layout="wide"
)

st.title("✨ Đồ thị Tri thức Tương tác")

# --- TẢI DỮ LIỆU (Tải cả 2 file) ---
@st.cache_data
def load_data(graph_file, matrix_file):
    try:
        k_graph = pd.read_csv(graph_file, comment='#')
        q_matrix = pd.read_csv(matrix_file, comment='#')
        return k_graph, q_matrix
    except Exception as e:
        st.error(f"Lỗi khi tải dữ liệu: {e}")
        return None, None

# Tải dữ liệu
k_graph_df, q_matrix_df = load_data(GRAPH_FILE_PATH, MATRIX_FILE_PATH)

# --- XỬ LÝ NẾU TẢI LỖI ---
if k_graph_df is None or q_matrix_df is None:
    st.error("Không thể tải đủ dữ liệu. Vui lòng kiểm tra lại file trong thư mục 'knowledge'.")
    st.stop() # Dừng chạy nếu không có dữ liệu

# --- 1. XÂY DỰNG NODES VÀ EDGES CHO AGRAH ---
nodes = []
edges = []

# Lấy tất cả các ID nút duy nhất từ k-graph
source_nodes = k_graph_df['source'].unique()
target_nodes = k_graph_df['target'].unique()
all_node_ids = np.unique(np.concatenate((source_nodes, target_nodes)))

# Tạo đối tượng Node cho mỗi ID
for node_id in all_node_ids:
    is_chapter = "Chg" in str(node_id)
    nodes.append(
        Node(
            id=str(node_id),
            label=str(node_id), # Nhãn hiển thị
            shape="box" if is_chapter else "dot",
            color="#ADD8E6" if is_chapter else "#D3D3D3", # Xanh cho Chương, Xám cho Kỹ năng
            size=15 if is_chapter else 10
        )
    )

# Tạo đối tượng Edge cho mỗi quan hệ
for _, row in k_graph_df.iterrows():
    edges.append(
        Edge(
            source=str(row['source']),
            target=str(row['target']),
            arrows="to" # Thêm mũi tên
        )
    )

# --- 2. CẤU HÌNH ĐỒ THỊ ---
# Đây là phần cấu hình cho thư viện vis.js (mà agraph sử dụng)
config = Config(
    width=1100, # Chiều rộng
    height=400, # Chiều cao
    directed=True, # Có hướng (mũi tên)
    physics=True, # Bật hiệu ứng vật lý để các nút tự sắp xếp
    hierarchical=False, # Không xếp theo phân cấp (để vật lý tự chạy)
    
    # **QUAN TRỌNG: Cấu hình tương tác**
    interaction={
        "selectByNode": True, # Cho phép chọn bằng cách nhấn vào nút
        "navigationButtons": True, # Thêm nút zoom/pan
        "tooltipDelay": 200
    },
    # Cấu hình cách chọn
    selection={
        "mode": "nodes",
        "multiple": False # Chỉ cho phép chọn 1 nút tại 1 thời điểm
    }
)

st.info("Hãy nhấn vào một chủ đề (nút) trên đồ thị để xem các câu hỏi liên quan.")

# --- 3. VẼ ĐỒ THỊ VÀ NHẬN GIÁ TRỊ TRẢ VỀ ---
# `return_value` sẽ là ID của nút được nhấn gần nhất
return_value = agraph(nodes=nodes, edges=edges, config=config)

st.divider() # Thêm đường kẻ

# --- 4. XỬ LÝ SỰ KIỆN NHẤN (CLICK) ---
selected_skill = None

if return_value:
    selected_skill = return_value # return_value chính là ID của nút được chọn
    st.success(f"Bạn đã chọn chủ đề: **{selected_skill}**")
else:
    st.subheader("Chưa chọn chủ đề")
    st.write("Hãy nhấn vào một nút trên đồ thị bên trên để bắt đầu.")

# --- 5. LỌC VÀ HIỂN THỊ CÂU HỎI (Giống code trang 1) ---
if selected_skill:
    st.header(f"Các câu hỏi liên quan đến: {selected_skill}")
    
    # Lọc q_matrix
    filtered_questions = q_matrix_df[
        q_matrix_df['skill_id_list'].str.contains(selected_skill, na=False)
    ]
    
    if filtered_questions.empty:
        st.warning("Không tìm thấy câu hỏi nào cho chủ đề này.")
    else:
        st.info(f"Tìm thấy {len(filtered_questions)} câu hỏi:")
        
        # Hiển thị từng câu hỏi
        for index, row in filtered_questions.iterrows():
            st.markdown(f"**Câu hỏi (ID: {row['question_id']}):** {row['content']}")
            st.caption(f"Độ khó: {row['difficulty']} | Mã kỹ năng: {row['skill_id_list']}")
            
            # Xử lý hiển thị câu hỏi Trắc nghiệm (MCQ)
            if pd.notna(row['answer']) and str(row['answer']).strip() != "":
                try:
                    options_list = ast.literal_eval(row['options'])
                    st.radio(
                        "Các lựa chọn:",
                        options=options_list,
                        key=f"radio_{row['question_id']}"
                    )
                    with st.expander("Xem đáp án"):
                        st.success(f"Đáp án đúng: {row['answer']}")
                except Exception as e:
                    st.error(f"Lỗi khi hiển thị các lựa chọn: {e}")
            else:
                st.info("Đây là câu hỏi Tự luận / Thực hành.")
            
            st.markdown("---") # Kẻ ngang mỏng hơn