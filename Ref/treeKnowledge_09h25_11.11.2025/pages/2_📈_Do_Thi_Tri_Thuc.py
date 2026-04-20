import streamlit as st
import pandas as pd
import numpy as np
import ast
import os
import sys
from streamlit_agraph import agraph, Node, Edge, Config

# Thêm đường dẫn thư mục gốc để import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db_utils import get_user_progress # <-- Import hàm ĐỌC

# --- BẢO VỆ TRANG ---
if st.session_state.get("authentication_status", False):

    # --- ĐỊNH NGHĨA ĐƯỜNG DẪN TƯƠNG ĐỐI ---
    DATA_FOLDER = "knowledge"
    GRAPH_FILE_PATH = os.path.join(DATA_FOLDER, "k-graph.csv")
    MATRIX_FILE_PATH = os.path.join(DATA_FOLDER, "q-matrix.csv")

    st.set_page_config(page_title="Đồ thị Tương tác", page_icon="✨", layout="wide")
    st.title("✨ Bản đồ Năng lực Cá nhân")

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

    if k_graph_df is None or q_matrix_df is None:
        st.error("Không thể tải đủ dữ liệu.")
        st.stop()

    # --- 1. ĐẾM SỐ LƯỢNG CÂU HỎI (TỔNG QUAN) ---
    source_nodes = k_graph_df['source'].unique()
    target_nodes = k_graph_df['target'].unique()
    all_node_ids = np.unique(np.concatenate((source_nodes, target_nodes)))
    skill_counts = {skill: 0 for skill in all_node_ids}
    for _, row in q_matrix_df.iterrows():
        try:
            skill_list = ast.literal_eval(row['skill_id_list'])
            if isinstance(skill_list, list):
                for skill in skill_list:
                    if skill in skill_counts:
                        skill_counts[skill] += 1
        except Exception:
            pass
            
    # --- 2. LẤY TIẾN TRÌNH CÁ NHÂN TỪ CSDL ---
    username = st.session_state["username"]
    user_mastery_data = get_user_progress(username) # <-- ĐỌC TỪ CSDL
    st.success(f"Đang hiển thị bản đồ năng lực cho: {st.session_state['name']}")

    # --- 3. XÂY DỰNG NODES (Tô màu từ CSDL) ---
    nodes = []
    edges = []
    COLOR_UNTESTED = "#D3D3D3"
    COLOR_CHAPTER = "#ADD8E6"
    COLOR_WEAK = "#F08080"
    COLOR_MEDIUM = "#FFFFE0"
    COLOR_STRONG = "#90EE90"

    for node_id_str in all_node_ids:
        node_id = str(node_id_str)
        is_chapter = "Chg" in node_id
        count = skill_counts.get(node_id, 0)
        label = f"{node_id}\n({count} câu hỏi)"
        
        color = COLOR_CHAPTER if is_chapter else COLOR_UNTESTED
        title_text = f"Tổng số {count} câu hỏi liên quan."

        if not is_chapter and node_id in user_mastery_data:
            mastery_info = user_mastery_data[node_id]
            total = mastery_info['total']
            if total > 0:
                correct = mastery_info['correct']
                ratio = correct / total
                if ratio < 0.5: color = COLOR_WEAK
                elif ratio < 0.8: color = COLOR_MEDIUM
                else: color = COLOR_STRONG
                title_text = f"Năng lực: {correct}/{total} câu đúng ({ratio:.0%})"
        
        nodes.append(
            Node(id=node_id, label=label, shape="box" if is_chapter else "dot",
                 color=color, size=15 if is_chapter else 10, title=title_text)
        )

    # Tạo Edges
    for _, row in k_graph_df.iterrows():
        edges.append(Edge(source=str(row['source']), target=str(row['target']), arrows="to"))

    # --- 4. CẤU HÌNH VÀ VẼ ĐỒ THỊ ---
    config = Config(width=1100, height=400, directed=True, physics=True, hierarchical=False,
                    interaction={"selectByNode": True, "navigationButtons": True, "tooltipDelay": 200},
                    selection={"mode": "nodes", "multiple": False})

    st.info("Hãy nhấn vào một chủ đề (nút) trên đồ thị để xem các câu hỏi liên quan.")
    st.markdown(
        """
        **Chú thích màu sắc (Năng lực cá nhân):**
        * <span style="color:{};">●</span> **Xanh lá**: Đã nắm vững (>80%)
        * <span style="color:{};">●</span> **Vàng**: Đang học (50-80%)
        * <span style="color:{};">●</span> **Đỏ**: Cần ôn tập (<50%)
        * <span style="color:{};">●</span> **Xám**: Chưa kiểm tra
        * <span style="color:{};">■</span> **Xanh nhạt**: Chương (Tổng quan)
        """.format(COLOR_STRONG, COLOR_MEDIUM, COLOR_WEAK, COLOR_UNTESTED, COLOR_CHAPTER),
        unsafe_allow_html=True
    )
    return_value = agraph(nodes=nodes, edges=edges, config=config)
    st.divider()

    # --- 5. LỌC VÀ HIỂN THỊ CÂU HỎI ---
    selected_skill = return_value if return_value else None
    if selected_skill:
        st.success(f"Bạn đã chọn chủ đề: **{selected_skill}**")
        st.header(f"Các câu hỏi liên quan đến: {selected_skill}")
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
                        with st.expander("Xem đáp án"):
                            st.success(f"Đáp án đúng: {row['answer']}")
                    except Exception as e:
                        st.error(f"Lỗi khi hiển thị các lựa..." )
                else:
                    st.info("Đây là câu hỏi Tự luận / Thực hành.")
                st.markdown("---")
    else:
        st.subheader("Chưa chọn chủ đề")
        st.write("Hãy nhấn vào một nút trên đồ thị bên trên để bắt đầu.")

else:
    # --- HIỂN THỊ NẾU CHƯA ĐĂNG NHẬP ---
    st.error("🔒 Bạn phải đăng nhập để truy cập trang này.")
    st.info("Vui lòng quay lại trang chủ (Home) để đăng nhập.")