import streamlit as st
import pandas as pd
import numpy as np
import ast  # Import thư viện ast để xử lý string list
import os
from streamlit_agraph import agraph, Node, Edge, Config

# --- ĐỊNH NGHĨA ĐƯỜNG DẪN TƯƠNG ĐỐI ---
DATA_FOLDER = "knowledge"
GRAPH_FILE_PATH = os.path.join(DATA_FOLDER, "k-graph.csv")
MATRIX_FILE_PATH = os.path.join(DATA_FOLDER, "q-matrix.csv")

# --- CẤU HÌNH TRANG ---
st.set_page_config(
    page_title="Đồ thị Tương tác",
    page_icon="✨",
    layout="wide"
)

st.title("✨ Đồ thị Tri thức Tương tác (Dashboard)")

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
    st.stop()

# --- 1. ĐẾM SỐ LƯỢNG CÂU HỎI (NÂNG CẤP) ---

# Lấy tất cả các ID nút duy nhất từ k-graph
source_nodes = k_graph_df['source'].unique()
target_nodes = k_graph_df['target'].unique()
all_node_ids = np.unique(np.concatenate((source_nodes, target_nodes)))

# Tạo một dictionary để đếm câu hỏi cho mỗi skill
# Khởi tạo tất cả các nút với 0 câu hỏi
skill_counts = {skill: 0 for skill in all_node_ids}

# Lặp qua q_matrix để đếm
for _, row in q_matrix_df.iterrows():
    try:
        # Chuyển string '["skill1", "skill2"]' thành list
        skill_list = ast.literal_eval(row['skill_id_list'])
        
        if isinstance(skill_list, list):
            for skill in skill_list:
                if skill in skill_counts:
                    # Tăng số đếm cho skill tương ứng
                    skill_counts[skill] += 1
    except Exception:
        # Bỏ qua nếu 'skill_id_list' rỗng hoặc sai định dạng
        pass

# --- 2. XÂY DỰNG NODES VÀ EDGES (ĐÃ CẬP NHẬT) ---
nodes = []
edges = []

# Tạo đối tượng Node cho mỗi ID (với label đã cập nhật)
for node_id_str in all_node_ids:
    node_id = str(node_id_str)
    is_chapter = "Chg" in node_id
    
    # Lấy số lượng câu hỏi đã đếm
    count = skill_counts.get(node_id, 0)
    
    # **NÂNG CẤP: Thêm (count) vào nhãn**
    label = f"{node_id}\n({count} câu hỏi)"

    nodes.append(
        Node(
            id=node_id,
            label=label,  # Sử dụng nhãn mới
            shape="box" if is_chapter else "dot",
            color="#ADD8E6" if is_chapter else "#D3D3D3",
            size=15 if is_chapter else 10,
            # Thêm title để xem chi tiết khi hover
            title=f"{count} câu hỏi liên quan"
        )
    )

# Tạo đối tượng Edge cho mỗi quan hệ (Giữ nguyên)
for _, row in k_graph_df.iterrows():
    edges.append(
        Edge(
            source=str(row['source']),
            target=str(row['target']),
            arrows="to"
        )
    )

# --- 3. CẤU HÌNH VÀ VẼ ĐỒ THỊ (Giữ nguyên) ---
config = Config(
    width=1100,
    height=400,
    directed=True,
    physics=True,
    hierarchical=False,
    interaction={
        "selectByNode": True,
        "navigationButtons": True,
        "tooltipDelay": 200
    },
    selection={
        "mode": "nodes",
        "multiple": False
    }
)

st.info("Hãy nhấn vào một chủ đề (nút) trên đồ thị để xem các câu hỏi liên quan.")

return_value = agraph(nodes=nodes, edges=edges, config=config)

st.divider()

# --- 4. XỬ LÝ SỰ KIỆN NHẤN (Giữ nguyên) ---
selected_skill = return_value if return_value else None

if selected_skill:
    st.success(f"Bạn đã chọn chủ đề: **{selected_skill}**")
else:
    st.subheader("Chưa chọn chủ đề")
    st.write("Hãy nhấn vào một nút trên đồ thị bên trên để bắt đầu.")

# --- 5. LỌC VÀ HIỂN THỊ CÂU HỎI (Giữ nguyên) ---
if selected_skill:
    st.header(f"Các câu hỏi liên quan đến: {selected_skill}")
    
    filtered_questions = q_matrix_df[
        q_matrix_df['skill_id_list'].str.contains(selected_skill, na=False)
    ]
    
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
            
            st.markdown("---")