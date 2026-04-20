# change for gemini-2.0-flash
import os
import streamlit as st
import requests
from dotenv import load_dotenv
import fitz  # = PyMuPDF
import io
import re
import streamlit.components.v1 as components
import docx #dùng để đọc file người dùng upload lên
from bs4 import BeautifulSoup
import streamlit.components.v1 as components
from streamlit_javascript import st_javascript
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import tempfile
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

#from gtts import gTTS #for audio
import edge_tts #AI audio
import asyncio  #AI audio 

import base64
import uuid
import os

from firebase_admin import firestore  # ✨ Thêm dòng này ở đầu file chính



from datetime import datetime
from google.cloud.firestore_v1 import ArrayUnion

import json

# Đảm bảo st.set_page_config là lệnh đầu tiên
# Giao diện Streamlit
st.set_page_config(page_title="Tutor AI", page_icon="🎓")

if "toc_html" not in st.session_state:
    st.session_state["toc_html"] = "<p><em>Chưa có mục lục bài học.</em></p>"

#for menu content
import streamlit.components.v1 as components

from modules.content_parser import (
    clean_text,
    make_id,
    classify_section,
    parse_pdf_file,
    parse_docx_file,
    parse_uploaded_file,
	tach_noi_dung_bai_hoc_tong_quat
)

from modules.session_manager import (
    generate_session_id,
    init_session_state,
    init_lesson_progress,
    save_lesson_progress,
    load_lesson_progress_from_file,
    merge_lesson_progress,
    update_progress,
    get_current_session_info
)

from modules.progress_tracker import (
    get_progress_summary,
    list_incomplete_parts,
    get_low_understanding_parts,
    mark_part_review_needed,
    get_progress_table
)

from modules.audio_module import (
    generate_audio_filename,
    generate_audio_async,
    play_audio,
    generate_and_encode_audio
)
    
def render_audio_block(text: str, autoplay=False):
    b64 = generate_and_encode_audio(text)
    autoplay_attr = "autoplay" if autoplay else ""
    st.markdown(f"""
    <audio controls {autoplay_attr}>
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        Trình duyệt của bạn không hỗ trợ phát âm thanh.
    </audio>
    """, unsafe_allow_html=True)
    

from modules.firestore_logger import (
    save_exchange_to_firestore,
    save_part_feedback,
    get_history
)

from modules.file_reader import (
    extract_text_from_uploaded_file,
    extract_pdf_text_from_url    
)

from modules.text_utils import (
    clean_html_to_text,
    format_mcq_options,
    convert_to_mathjax,
    convert_to_mathjax1,
    convert_parentheses_to_latex,
    extract_headings_with_levels,
    generate_sidebar_radio_from_headings
    
)

from modules.firebase_config import init_firestore  # 🛠 Đừng quên dòng này nữa nếu dùng Firestore
#khởi tạo db
db = init_firestore()

doc_reading_enabled = False

#from dashboard import show_progress_dashboard, show_part_detail_table

#for data firebase
if "firebase_enabled" not in st.session_state:
    st.session_state["firebase_enabled"] = True # False  # hoặc True nếu muốn mặc định bật
    
import uuid
import time

if "session_id" not in st.session_state:
    # dùng timestamp hoặc uuid ngắn gọn
    st.session_state["session_id"] = f"{int(time.time())}"  # hoặc uuid.uuid4().hex[:8]

if "user_id" not in st.session_state:
    st.session_state["user_id"] = f"user_{uuid.uuid4().hex[:8]}"
    
#mở lại danh sách các bài học
st.session_state["show_sidebar_inputs"] = True

#thiết lập font size
st.markdown("""
<style>
    .element-container .markdown-text-container {
        font-size: 17px;
        line-height: 1.7;
    }
    code {
        background-color: #f4f4f4;
        padding: 2px 4px;
        border-radius: 4px;
        font-size: 15px;
    }
    h3 {
        color: #2a73cc;
        margin-top: 1.5em;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
h1 {
    font-size: 24px !important;
    line-height: 1.5;
    font-weight: 600;
}
h2 {
    font-size: 21px !important;
}
h3 {
    font-size: 19px !important;
}
</style>
""", unsafe_allow_html=True)

uploaded_files = []  # ✅ đảm bảo biến tồn tại trong mọi trường hợp

input_key = st.session_state.get("GEMINI_API_KEY", "")

# Lấy từ localStorage
key_from_local = st_javascript("JSON.parse(window.localStorage.getItem('gemini_api_key') || '\"\"')")

# Nếu chưa có thì gán
if not input_key and key_from_local:
    st.session_state["GEMINI_API_KEY"] = key_from_local
    input_key = key_from_local

# Lấy danh sách API keys từ secrets
api_keys = st.secrets["gemini_keys"]["keys"]
api_index = 0  # Index ban đầu

# Hàm gọi API với cơ chế thử nhiều key
def call_api_with_fallback(request_func):
    global api_index
    max_attempts = len(api_keys)

    for attempt in range(max_attempts):
        current_key = api_keys[api_index]
        try:
            # Gọi hàm truyền vào với API key hiện tại
            return request_func(current_key)
        except Exception as e:
            st.warning(f"API key {current_key} failed with error: {e}")
            api_index = (api_index + 1) % max_attempts  # chuyển sang key tiếp theo
    raise RuntimeError("All API keys failed.")

def get_data(api_key):
    response = some_api_call(api_key=api_key)
    if response.status_code != 200:
        raise Exception(f"Bad status: {response.status_code}")
    return response.json()
    
@st.cache_data
def load_available_lessons_from_txt(url):
    try:
        #response = requests.get(url)
        response = requests.get(url, allow_redirects=True)
        if response.status_code == 200:
            lines = response.text.strip().splitlines()
            lessons = {"👉 Chọn bài học...": ""}
            for line in lines:
                if "|" in line:
                    name, link = line.split("|", 1)
                    lessons[name.strip()] = link.strip()
            return lessons
        else:
            st.warning("⚠️ Không thể tải danh sách bài học từ GitHub.")
            return {"👉 Chọn bài học...": ""}
    except Exception as e:
        st.error(f"Lỗi khi đọc danh sách bài học: {e}")
        return {"👉 Chọn bài học...": ""}
        
LESSON_LIST_URL = "https://raw.githubusercontent.com/tranthanhthangbmt/GeminiTutorAI_07052025/main/Data/DiscreteMathematicsLesson3D.txt"  
available_lessons = load_available_lessons_from_txt(LESSON_LIST_URL) 

#viết cho đẹp hơn
def format_pdf_text_for_display(raw_text: str) -> str:
    text = raw_text.strip()

    # ✅ 1. Xử lý ký tự lỗi & lỗi tách từ
    text = text.replace("�", "")
    text = re.sub(r"\bch\s*•", "cho ", text)
    text = re.sub(r"\bsa\s*•", "sao ", text)
    text = re.sub(r"\bthe\s*•", "theo ", text)
    text = re.sub(r"\bD\s*•", "Do ", text)
    text = re.sub(r"\bch\s+", "cho ", text)
    text = re.sub(r"\bTạ\s*", "Tạo ", text)

    # ✅ 2. Chuẩn hóa gạch đầu dòng → xuống dòng
    text = re.sub(r"\s*[•\-–●🔹🔷]+\s*", r"\n• ", text)
    text = re.sub(r"(?<!\n)• ", r"\n• ", text)

    # ✅ 3. Tách câu sau dấu chấm nếu sau đó là chữ hoa
    text = re.sub(r"(?<=[a-z0-9])\. (?=[A-Z])", ".\n", text)

    # ✅ 4. Làm nổi bật nhóm tiêu đề bằng **Markdown**
    heading_keywords = [
        "Định lý", "Ví dụ", "Lưu ý", "Ghi chú", "Nhận xét",
        "Hệ quả", "Bổ đề", "Tóm tắt", "Ứng dụng", "Phân tích",
        "Bài toán", "Thuật toán", "Ý nghĩa", "Kết luận", "Mô hình hóa",
        "Giải thích", "Phân tích chi tiết", "Định nghĩa", "Lời giải"
    ]
    for kw in heading_keywords:
        text = re.sub(
            rf"(?<!\*)\b({kw}(?: [0-9]+)?(?: \([^)]+\))?:?)",
            r"\n\n**\1**", text
        )

    # ✅ 5. Đưa PHẦN và Bài thành tiêu đề h3
    text = re.sub(r"\b(PHẦN\s*\d+[:：])", r"\n\n### \1", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(Bài\s*\d+[:：])", r"\n\n**\1**", text, flags=re.IGNORECASE)

    # ✅ 6. Làm rõ toán học
    text = text.replace("=>", "⇒").replace("<=", "⇐").replace("=", " = ")

    # ✅ 7. Format đoạn code: phát hiện lệnh Python → thêm ```python ```
    if "import " in text or "def " in text:
        text = re.sub(
            r"(import .+?)(?=\n\S|\Z)", r"\n```python\n\1\n```\n", text, flags=re.DOTALL
        )
        text = re.sub(
            r"(def .+?)(?=\n\S|\Z)", r"\n```python\n\1\n```\n", text, flags=re.DOTALL
        )

    # ✅ 8. Gộp dòng trắng thừa
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
    
# Xác thực API bằng request test
def is_valid_gemini_key(key):
    try:
        test_response = requests.post(
            GEMINI_API_URL,
            headers={"Content-Type": "application/json"},
            params={"key": key},
            json={"contents": [{"parts": [{"text": "hello"}]}]},
            timeout=5
        )
        return test_response.status_code == 200
    except Exception:
        return False

#thiết lập ẩn phần bài học
if "show_sidebar_inputs" not in st.session_state:
    st.session_state["show_sidebar_inputs"] = True  # ← bật mặc định

import random

# Lấy danh sách API keys từ secrets (ví dụ từ mục [openai_keys] hoặc [gemini_keys])
def get_random_key():
    return random.choice(st.secrets["gemini_keys"]["keys"])


# ⬇ Lấy input từ người dùng ở sidebar trước
with st.sidebar:
    st.markdown("""
    <style>
    /* Ẩn hoàn toàn iframe tạo bởi st_javascript (vẫn hoạt động, chỉ không chiếm không gian) */
    iframe[title="streamlit_javascript.streamlit_javascript"] {
        display: none !important;
    }
    
    /* Ẩn container chứa iframe (chính là div tạo khoảng trống) */
    div[data-testid="stCustomComponentV1"] {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    #for logo
    # Thay link này bằng logo thật của bạn (link raw từ GitHub)
    logo_url = "https://raw.githubusercontent.com/tranthanhthangbmt/AITutor_Gemini/main/LOGO_UDA_2023_VN_EN_chuan2.png"

    st.sidebar.markdown(
        f"""
        <div style='text-align: center; margin-bottom: 10px;'>
            <img src="{logo_url}" width="200" style="border-radius: 10px;" />
        </div>
        """,
        unsafe_allow_html=True
    )

    # 📌 Lựa chọn chế độ nhập bài học
    #cho upload file trước
    #mode = st.radio("📘 Chế độ nhập bài học:", ["Tải lên thủ công", "Chọn từ danh sách"])
    #chọn bài học trước
    mode = st.radio(
        "📘 Chế độ nhập bài học:", 
        ["Tải lên thủ công", "Chọn từ danh sách"],
        index=1  # ✅ Mặc định chọn "Tải lên thủ công"
    )
    st.session_state["show_sidebar_inputs"] = (mode == "Chọn từ danh sách")

    # ✅ Nhúng script JS duy nhất để tự động điền & lưu API key
    key_from_local = st_javascript("""
    (() => {
        const inputEl = window.parent.document.querySelector('input[data-testid="stTextInput"][type="password"]');
        const storedKey = localStorage.getItem("gemini_api_key");
    
        // Tự động điền nếu textbox rỗng
        if (inputEl && storedKey && inputEl.value === "") {
            inputEl.value = JSON.parse(storedKey);
            inputEl.dispatchEvent(new Event("input", { bubbles: true }));
        }
    
        // Lưu khi người dùng nhập
        const saveAPI = () => {
            if (inputEl && inputEl.value) {
                localStorage.setItem("gemini_api_key", JSON.stringify(inputEl.value));
            }
        };
        inputEl?.addEventListener("blur", saveAPI);
        inputEl?.addEventListener("change", saveAPI);
        inputEl?.addEventListener("keydown", e => {
            if (e.key === "Enter") saveAPI();
        });
    
        return storedKey ? JSON.parse(storedKey) : "";
    })()
    """)
    
    # ✅ Ưu tiên lấy từ localStorage nếu session chưa có
    input_key = st.session_state.get("GEMINI_API_KEY", "")
    if not input_key and key_from_local:
        st.session_state["GEMINI_API_KEY"] = key_from_local
        input_key = key_from_local
    
    # ✅ Tạo textbox với giá trị đúng
    #input_key = st.text_input("🔑 Gemini API Key", value=input_key, type="password", key="GEMINI_API_KEY")
    # ✅ Tạo textbox với giá trị đúng
    # ✅ Tạo textbox với giá trị đúng
    if "GEMINI_API_KEY" not in st.session_state or st.session_state.GEMINI_API_KEY == "":
        # Lấy random API key từ danh sách nếu chưa có sẵn
        input_key = get_random_key()
        st.session_state.GEMINI_API_KEY = input_key
    else:
        input_key = st.session_state.GEMINI_API_KEY
    
    #input_key = st.text_input("🔑 Gemini API Key", value=input_key, type="password", key="GEMINI_API_KEY")
    # ❗ Ẩn ô nhập nếu chưa có tài liệu hoặc bài học
    selected_lesson_val = st.session_state.get("selected_lesson", "👉 Chọn bài học...")
    has_lesson = not (
        selected_lesson_val == "👉 Chọn bài học..." and not uploaded_files
    )
    
    # if has_lesson:
    #     input_key = st.text_input("🔑 Gemini API Key", value=input_key, type="password", key="GEMINI_API_KEY")

    # 🔄 Chọn mô hình Gemini
    model_options = {
        "⚡ Gemini 2.0 Flash": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
        "⚡ Gemini 1.5 Flash": "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
        "🧠 Gemini 1.5 Pro": "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent",
        "🧠 Gemini 2.5 Pro Preview": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro-preview-03-25:generateContent",
        "🧪 Gemini 2.5 Pro Experimental": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro-exp-03-25:generateContent",
        "🖼️ Gemini 1.5 Pro Vision (ảnh + chữ)": "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro-vision:generateContent"
    }
    
    # ✅ Hiển thị selectbox
    selected_model_name = st.selectbox("🤖 Chọn mô hình Gemini", list(model_options.keys()), index=0)
    
    # ✅ Gán URL tương ứng vào session_state (để dùng sau)
    st.session_state["GEMINI_API_URL"] = model_options[selected_model_name]

    st_javascript("""
    (() => {
        const inputEl = window.parent.document.querySelector('input[data-testid="stTextInput"][type="password"]');
        const storedKey = localStorage.getItem("gemini_api_key");
    
        // Tự điền nếu còn trống
        const tryFillKey = () => {
            if (inputEl && storedKey && inputEl.value.trim() === "") {
                inputEl.value = JSON.parse(storedKey);
                inputEl.dispatchEvent(new Event("input", { bubbles: true }));
                console.log("✅ Tự động điền API từ localStorage.");
            }
        };
    
        tryFillKey();  // gọi ngay khi chạy
        const interval = setInterval(tryFillKey, 1000); // kiểm tra lại mỗi giây
    
        // Lưu khi thay đổi
        const saveAPI = () => {
            if (inputEl && inputEl.value) {
                localStorage.setItem("gemini_api_key", JSON.stringify(inputEl.value));
                console.log("💾 Đã lưu API vào localStorage.");
            }
        };
    
        inputEl?.addEventListener("change", saveAPI);
        inputEl?.addEventListener("blur", saveAPI);
        inputEl?.addEventListener("keydown", (e) => {
            if (e.key === "Enter") saveAPI();
        });
    })();
    """)
    "[Lấy API key tại đây](https://aistudio.google.com/app/apikey)"
    # 🔊 Cho phép bật/tắt tự động phát audio
    enable_audio_default = True  # ✅ Mặc định: Bật nghe audio
    #st.session_state["enable_audio_playback"] = st.sidebar.checkbox("🔊 Tự động phát âm thanh", value=enable_audio_default)
    #Đảm bảo không gán enable_audio_playback mặc định mỗi lần, mà chỉ gán nếu chưa tồn tại:
    if "enable_audio_playback" not in st.session_state:
        st.session_state["enable_audio_playback"] = True  # hoặc True tùy bạn

    st.session_state["enable_audio_playback"] = st.sidebar.checkbox(
        "🔊 Tự động phát âm thanh", 
        value=st.session_state["enable_audio_playback"]
    )

    if st.session_state.get("show_sidebar_inputs", False):
        st.markdown("📚 **Chọn bài học hoặc tải lên bài học**")
        
        selected_lesson = st.selectbox("📖 Chọn bài học", list(available_lessons.keys()))
        st.session_state["selected_lesson"] = selected_lesson
        default_link = available_lessons[selected_lesson]
        selected_lesson_link = available_lessons.get(selected_lesson, "").strip()
        
        if selected_lesson != "👉 Chọn bài học..." and selected_lesson_link:
            st.markdown(f"🔗 **Tài liệu:** [Xem bài học]({selected_lesson_link})", unsafe_allow_html=True)
    else:
        # uploaded_file = None #bỏ vì bạn có thể xóa dòng này nếu đã chuyển sang uploaded_files:
        selected_lesson = "👉 Chọn bài học..."        
        selected_lesson_link = "" #available_lessons.get(selected_lesson, "").strip() """
        uploaded_files = st.file_uploader(
            "📤 Tải lên nhiều file bài học (PDF, TXT, DOCX, JSON)", 
            type=["pdf", "txt", "docx", "json"],  # ➡ thêm "json" vào đây
            accept_multiple_files=True,
            key="file_uploader_thutay"
        )

        # Kiểm tra số file và kích thước tổng cộng
        MAX_FILE_COUNT = 3
        MAX_TOTAL_SIZE_MB = 5
        
        if uploaded_files:
            total_size = sum(file.size for file in uploaded_files) / (1024 * 1024)
            if len(uploaded_files) > MAX_FILE_COUNT:
                st.warning(f"⚠️ Chỉ nên tải tối đa {MAX_FILE_COUNT} file.")
            elif total_size > MAX_TOTAL_SIZE_MB:
                st.warning(f"⚠️ Tổng dung lượng file vượt quá {MAX_TOTAL_SIZE_MB}MB.")

    default_link = available_lessons[selected_lesson]
    # 📤 Tải file tài liệu (mục tiêu là đặt bên dưới link)
    #uploaded_file = None  # Khởi tạo trước để dùng điều kiện bên trên
    
    # 🔗 Hiển thị link NGAY BÊN DƯỚI selectbox, nếu thỏa điều kiện
    #if selected_lesson != "👉 Chọn bài học..." and selected_lesson_link:
    #    st.markdown(f"🔗 **Tài liệu:** [Xem bài học]({selected_lesson_link})", unsafe_allow_html=True)
    
    # ✅ Nếu người dùng upload tài liệu riêng → ẩn link (từ vòng sau trở đi)
    if uploaded_files:
        # Có thể xoá dòng link bằng session hoặc không hiển thị ở các phần sau
        pass
    #hiển thị danh sách các files đã upload lên
    if uploaded_files:
        st.markdown("📄 **Các file đã tải lên:**")
        for f in uploaded_files:
            st.markdown(f"- {f.name}")

    # ✅ CSS để giảm khoảng cách giữa các nút trong sidebar
    st.markdown("""
        <style>
        /* Loại bỏ khoảng cách giữa các nút trong sidebar */
        div[data-testid="stSidebar"] div[data-testid="stButton"] {
            margin-bottom: 2px;
        }
    
        /* Tùy chỉnh nút hoàn thành */
        .completed-btn > button {
            background-color: #d4edda !important;
            color: black !important;
            width: 100%;
            text-align: left;
        }
    
        /* Tùy chỉnh nút chưa hoàn thành */
        .incomplete-btn > button {
            background-color: #f8f9fa !important;
            color: black !important;
            width: 100%;
            text-align: left;
        }
        </style>
    """, unsafe_allow_html=True)
    
    show_content = st.sidebar.checkbox("📑 Mục lục bài học", value=False)
    #doc_reading_enabled = st.checkbox("✅ Đọc nội dung bài học trước khi đọc câu hỏi", value=False)
    # Hiển thị checkbox cho người dùng
    read_lesson_first = st.checkbox("Đọc nội dung bài học", value=False)
    
    #with st.sidebar.expander("📑 Content – Mục lục bài học", expanded=True):
    # if show_content:
    #     #st.markdown("🧠 **Chọn một mục bên dưới để bắt đầu:**", unsafe_allow_html=True)
    
    #     lesson_parts = st.session_state.get("lesson_parts", [])
    #     options = ["__none__"]  # option mặc định
    #     option_labels = ["-- Chọn mục để bắt đầu --"]
        
    #     for idx, part in enumerate(lesson_parts):
    #         part_id = part["id"]
    #         tieu_de = part.get("tieu_de", "Không có tiêu đề")
    #         progress_item = next((p for p in st.session_state.get("lesson_progress", []) if p["id"] == part_id), {})
    #         trang_thai = progress_item.get("trang_thai", "chua_hoan_thanh")
        
    #         label = f"✅ {part_id} – {tieu_de}" if trang_thai == "hoan_thanh" else f"{part_id} – {tieu_de}"
    #         options.append(f"{part_id}|{idx}")
    #         option_labels.append(label)
        
    #     # Dùng radio như bình thường
    #     selected_raw = st.radio(
    #         "Chọn mục để học:",
    #         options=options,
    #         format_func=lambda x: option_labels[options.index(x)],
    #         key="selected_part_radio"
    #     )
        
    #     # Bỏ qua nếu chưa chọn
    #     if selected_raw != "__none__":
    #         part_id, idx = selected_raw.split("|")
    #         new_selection = lesson_parts[int(idx)]
        
    #         # So sánh tránh cập nhật dư thừa
    #         current = st.session_state.get("selected_part_for_discussion", {})
    #         if current.get("id") != part_id:
    #             st.session_state["selected_part_for_discussion"] = new_selection
    #             st.session_state["force_ai_to_ask"] = True
    # if show_content:
    #     lesson_parts = st.session_state.get("lesson_parts", [])
    #     options = ["__none__"]
    #     option_labels = ["-- Chọn mục để bắt đầu --"]
    
    #     for idx, part in enumerate(lesson_parts):
    #         part_id = part["id"]
    #         tieu_de = part.get("tieu_de", "Không có tiêu đề")
    #         heading_level = part.get("heading_level", 0)
    
    #         # Trạng thái học
    #         progress_item = next(
    #             (p for p in st.session_state.get("lesson_progress", []) if p["id"] == part_id), {}
    #         )
    #         trang_thai = progress_item.get("trang_thai", "chua_hoan_thanh")
    
    #         # ✅ Thụt đầu dòng theo heading_level bằng dấu hiển thị rõ
    #         indent_symbols = ["", "➤ ", "  • ", "   → ", "    ◦ "]
    #         indent = indent_symbols[min(heading_level, len(indent_symbols) - 1)]
    
    #         prefix = "✅ " if trang_thai == "hoan_thanh" else ""
    #         label = f"{indent}{prefix}{part_id} – {tieu_de}"
    
    #         options.append(f"{part_id}|{idx}")
    #         option_labels.append(label)
    
    #     # Radio selector
    #     selected_raw = st.radio(
    #         "Chọn mục để học:",
    #         options=options,
    #         format_func=lambda x: option_labels[options.index(x)],
    #         key="selected_part_radio"
    #     )
    
    #     # Xử lý khi người dùng chọn mục
    #     if selected_raw != "__none__":
    #         part_id, idx = selected_raw.split("|")
    #         new_selection = lesson_parts[int(idx)]
    
    #         current = st.session_state.get("selected_part_for_discussion", {})
    #         if current.get("id") != part_id:
    #             st.session_state["selected_part_for_discussion"] = new_selection
    #             st.session_state["force_ai_to_ask"] = True

    if show_content:
        # Bước 1: Lấy danh sách headings từ lesson_parts
        lesson_parts = st.session_state.get("lesson_parts", [])
        headings = []

        for idx, part in enumerate(lesson_parts):
            level = part.get("heading_level", 0)
            headings.append((level, {
                "id": part["id"],
                "tieu_de": part.get("tieu_de", "Không có tiêu đề"),
            }))
    
        # Bước 2: Gọi hàm generate_sidebar_radio_from_headings
        def custom_sidebar_radio(headings):
            options = ["__none__"]
            labels = ["-- Chọn mục để bắt đầu --"]
            #prefix_symbols = ["", "➤ ", "  • ", "   → ", "    ◦ "]
            #prefix_symbols = ["", "- ", "  - ", "   - ", "    - "]
            def get_indent_prefix(level):
                return " " * level + "↳ " if level > 0 else ""
        
            for idx, (level, info) in enumerate(headings):
                part_id = info["id"]
                tieu_de = info["tieu_de"]
                #symbol = prefix_symbols[min(level, len(prefix_symbols) - 1)]
                symbol = get_indent_prefix(level)
        
                progress_item = next(
                    (p for p in st.session_state.get("lesson_progress", []) if p["id"] == part_id),
                    {}
                )
                trang_thai = progress_item.get("trang_thai", "chua_hoan_thanh")
                prefix = "✅ " if trang_thai == "hoan_thanh" else ""
                label = f"{symbol}{prefix}{part_id} – {tieu_de}"
        
                options.append(str(idx))
                labels.append(label)
        
            selected_raw = st.radio(
                "Chọn mục để học:",
                options=options,
                format_func=lambda x: labels[options.index(x)],
                key="selected_part_radio"
            )
        
            if selected_raw != "__none__":
                selected_heading = headings[int(selected_raw)]
                part_id = selected_heading[1]["id"]
        
                selected_part = next((p for p in lesson_parts if p["id"] == part_id), None)
                if selected_part:
                    current = st.session_state.get("selected_part_for_discussion", {})
                    if current.get("id") != part_id:
                        st.session_state["selected_part_for_discussion"] = selected_part
                        st.session_state["force_ai_to_ask"] = True
    
        custom_sidebar_radio(headings)
        # Kích hoạt Firebase mặc định
        st.session_state["firebase_enabled"] = True

    #đọc bài học
    # if doc_reading_enabled:
    #     #audio_text = trich_dan_tu_pdf(ten_muc_duoc_chon)  # bạn đã có đoạn trích trong nội dung trước
    #     audio_text = selected_part['noi_dung']
    #     play_audio(audio_text)  # dùng hàm TTS sẵn có
    #     time.sleep(len(audio_text) * 0.2)  # tuỳ chỉnh delay theo thời lượng
        
    #Lưu tiến độ học ra file JSON
    if st.button("💾 Lưu tiến độ học"):
        save_lesson_progress()
	
    # 🔄 Nút reset
    if st.button("🔄 Bắt đầu lại buổi học"):
        if "messages" in st.session_state:
            del st.session_state.messages
        if "lesson_loaded" in st.session_state:
            del st.session_state.lesson_loaded
        st.rerun()

    # Khởi tạo biến trạng thái nếu chưa có
    if "export_requested" not in st.session_state:
        st.session_state.export_requested = False
    
    with st.expander("📥 Kết xuất nội dung học"):
        if st.session_state.get("messages"):
            output_text = ""
            for msg in st.session_state.messages[1:]:  # Bỏ prompt hệ thống
                role = "Học sinh" if msg["role"] == "user" else "Gia sư AI"
                text = msg["parts"][0]["text"]
                output_text += f"\n[{role}]:\n{text}\n\n"
    
            # Ghi tên file
            lesson_title_safe = st.session_state.get("lesson_source", "BaiHoc_AITutor")
            lesson_title_safe = lesson_title_safe.replace("upload::", "").replace("lesson::", "").replace(" ", "_").replace(":", "")
            txt_file_name = f"BuoiHoc_{lesson_title_safe}.txt"
            pdf_file_name = f"BuoiHoc_{lesson_title_safe}.pdf"
    
            # Hiển thị nút tải file .txt
            st.download_button(
                label="📄 Tải file .txt",
                data=output_text,
                file_name=txt_file_name,
                mime="text/plain"
            )
    
            # Đăng ký font Unicode cho PDF
            pdfmetrics.registerFont(TTFont("DejaVu", "Data/fonts/DejaVuSans.ttf"))
    
            # Tạo file PDF tạm
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                c = canvas.Canvas(tmp_pdf.name, pagesize=letter)
                c.setFont("DejaVu", 12)
    
                width, height = letter
                margin = 50
                y = height - margin
                lines = output_text.split("\n")
    
                for line in lines:
                    line = line.strip()
                    if y < margin:
                        c.showPage()
                        c.setFont("DejaVu", 12)
                        y = height - margin
                    c.drawString(margin, y, line)
                    y -= 16
    
                c.save()
    
                # Đọc lại file PDF và hiển thị nút tải
                with open(tmp_pdf.name, "rb") as f:
                    pdf_bytes = f.read()
    
                st.download_button(
                    label="📕 Tải file .pdf",
                    data=pdf_bytes,
                    file_name=pdf_file_name,
                    mime="application/pdf"
                )
        else:
            st.info("📌 Bạn chưa có nội dung hội thoại để xuất file.")
    
st.title("🎓 Tutor AI")

# Nhúng script MathJax
mathjax_script = """
<script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
<script id="MathJax-script" async
  src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js">
</script>
"""

st.markdown(mathjax_script, unsafe_allow_html=True)
	
# Load biến môi trường
load_dotenv()
#API_KEY = os.getenv("GEMINI_API_KEY")
# Ưu tiên: Dùng key từ người dùng nhập ➝ nếu không có thì dùng từ môi trường
API_KEY = input_key or os.getenv("GEMINI_API_KEY")

# Kiểm tra
if not API_KEY:
    st.error("❌ Thiếu Gemini API Key. Vui lòng nhập ở sidebar hoặc thiết lập biến môi trường 'GEMINI_API_KEY'.")
    st.stop()

#input file bài học
#if selected_lesson == "👉 Chọn bài học..." and uploaded_file is None:
if selected_lesson == "👉 Chọn bài học..." and not uploaded_files: #kiểm tra là đã tải liên nhiều file
    st.info("📥 Hãy tải lên tài liệu PDF/TXT hoặc chọn một bài học từ danh sách bên trên để bắt đầu.") 
    st.stop()

# Endpoint API Gemini
#GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent" 
#GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro-preview-03-25:generateContent"
GEMINI_API_URL = st.session_state.get("GEMINI_API_URL", "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent")

#PDF_URL = "https://raw.githubusercontent.com/tranthanhthangbmt/AITutor_Gemini/main/handoutBuoi4.pdf"
#pdf_context = extract_pdf_text_from_url(PDF_URL)
pdf_context = ""

# Nếu có file upload thì lấy nội dung từ file upload
if uploaded_files:
    pdf_context = ""
    for uploaded_file in uploaded_files:
        pdf_context += extract_text_from_uploaded_file(uploaded_file) + "\n"

# Nếu không có upload mà chọn bài học thì tải nội dung từ link
elif selected_lesson != "👉 Chọn bài học..." and default_link.strip():
    pdf_context = extract_pdf_text_from_url(default_link)

# Nếu không có gì hết thì báo lỗi
if not pdf_context:
    st.error("❌ Bạn cần phải upload tài liệu hoặc chọn một bài học để bắt đầu.")
    st.stop()

def load_system_prompt_from_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()
        
# 🔹 Vai trò mặc định của Tutor AI (trước khi có tài liệu)
#SYSTEM_PROMPT_Tutor_AI = ""
try:
    prompt_path = os.path.join("Data", "system_prompt_tutor_ai.txt")
    SYSTEM_PROMPT_Tutor_AI = load_system_prompt_from_file(prompt_path)
except FileNotFoundError:
    st.error("❌ Không tìm thấy file Data/system_prompt_tutor_ai.txt")
    st.stop()

# Gọi API Gemini, gửi cả lịch sử trò chuyện
# Giới hạn số lượt hội thoại gửi cho Gemini (trừ prompt hệ thống)
def chat_with_gemini(messages):
    headers = {"Content-Type": "application/json"}
    params = {"key": API_KEY}
    
    # Giữ prompt hệ thống + 6 tương tác gần nhất (3 lượt hỏi – đáp)
    truncated = messages[:1] + messages[-6:] if len(messages) > 7 else messages
    data = {"contents": truncated}

    response = requests.post(GEMINI_API_URL, headers=headers, params=params, json=data)

    if response.status_code == 200:
        try:
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            return f"Lỗi phân tích phản hồi: {e}"
    elif response.status_code == 503:
        return None  # model quá tải
    else:
        return f"Lỗi API: {response.status_code} - {response.text}"

# Giao diện Streamlit
#st.set_page_config(page_title="Tutor AI", page_icon="🎓")
#st.title("🎓 Tutor AI - Học Toán rời rạc với Gemini")

#thiết lập ban đầu tutor AI
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "user", "parts": [{"text": SYSTEM_PROMPT_Tutor_AI}]},
        {"role": "model", "parts": [{"text": "Chào bạn! Mình là gia sư AI 🎓\n\nHãy chọn bài học hoặc nhập link tài liệu bên sidebar để mình bắt đầu chuẩn bị nội dung buổi học nhé!"}]}
    ]

import tempfile
import requests

# 1. Đọc các file upload vào
all_parts = []
uploaded_json = None

if uploaded_files:
    for uploaded_file in uploaded_files:
        file_name = uploaded_file.name.lower()
        uploaded_file.seek(0)
    
        if file_name.endswith(".json"):
            uploaded_json = uploaded_file  # chỉ lưu lại file json, chưa đọc vội
    
        elif file_name.endswith(".pdf"):
            file_bytes = uploaded_file.read()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
                tmpfile.write(file_bytes)
                tmpfile_path = tmpfile.name
    
            parts = tach_noi_dung_bai_hoc_tong_quat(tmpfile_path) #parse_pdf_file(tmpfile_path)
            all_parts.extend(parts)
    
        else:
            st.warning(f"⚠️ File {file_name} không hỗ trợ tự động đọc nội dung bài học.")
    
        lesson_title = " + ".join([file.name for file in uploaded_files])
        current_source = f"upload::{lesson_title}"

elif selected_lesson != "👉 Chọn bài học..." and default_link.strip():
    # Tải file PDF từ link về
    response = requests.get(default_link)
    if response.status_code == 200:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            tmpfile.write(response.content)
            tmpfile_path = tmpfile.name
        try:
            parts = tach_noi_dung_bai_hoc_tong_quat(tmpfile_path) #parse_pdf_file(tmpfile_path)
            all_parts.extend(parts)
        finally:
            if os.path.exists(tmpfile_path):
                os.remove(tmpfile_path)

        lesson_title = selected_lesson
        current_source = f"lesson::{selected_lesson}"
    else:
        st.error("Không tải được file PDF từ link.")
        all_parts = []

else:
    all_parts = []
    lesson_title = "Chưa có bài học"
    current_source = ""

#xuất ra TOC file pdf
import pandas as pd

# Sau khi lấy all_parts xong
if all_parts:
    # 1. Sắp xếp
    thu_tu_muc = {
        "ly_thuyet": 1,
        "bai_tap_co_giai": 2,
        "trac_nghiem": 3,
        "luyen_tap": 4,
        "du_an": 5
    }
    parts_sorted = sorted(all_parts, key=lambda x: thu_tu_muc.get(x["loai"], 999))

    # Sinh HTML mục lục
    toc_html = "<ul>"
    for part in parts_sorted:
        toc_html += f"<li><strong>{part['id']}</strong> – {part['tieu_de']} ({part['loai']})</li>"
    toc_html += "</ul>"
    
    st.session_state["toc_html"] = toc_html  # lưu để dùng phía dưới

    # 2. Hiển thị bảng mục lục (mục lục trên messages)
    #st.markdown("### 📚 **Mục lục bài học**")

    
    df = pd.DataFrame(parts_sorted)
    #st.dataframe(df[["id", "loai", "tieu_de"]]) #đang ẩn để dùng nút content

    # 3. Lưu session để dùng tiếp
    st.session_state["lesson_parts"] = parts_sorted

    # 📌 Chọn phần học từ danh sách Content (mục lục trên messages)
    # with st.expander("🎯 Chọn mục để bắt đầu từ Content", expanded=False):
    #     lesson_part_titles = [f"{part['id']} – {part['tieu_de']} ({part['loai']})" for part in st.session_state["lesson_parts"]]
    #     selected_idx = st.selectbox("🔍 Chọn phần học để AI đặt câu hỏi:", list(range(len(lesson_part_titles))), format_func=lambda i: lesson_part_titles[i])
    
    #     if st.button("🚀 Bắt đầu mục này"):
    #         selected_part = st.session_state["lesson_parts"][selected_idx]
    #         st.session_state["selected_part_for_discussion"] = selected_part
    #         st.session_state["force_ai_to_ask"] = True
    #         #st.rerun()

    #         # Chỉ giữ lại prompt hệ thống để tránh lặp lại phần chào hỏi
    #         if st.session_state.messages:
    #             st.session_state.messages = [st.session_state.messages[0]]

    # 👉 Nếu người dùng chọn một phần → sinh câu hỏi kiểm tra
    if (
        st.session_state.get("force_ai_to_ask", False)
        and st.session_state.get("selected_part_for_discussion")
        and st.session_state.get("lesson_parts")
    ):
        selected_part = st.session_state["selected_part_for_discussion"]
        question_prompt = f"""
        Bây giờ người học đã chọn mục : "{selected_part['tieu_de']}" trong tài liệu đính kèm, hãy tiếp tục hướng dẫn người học từ đoạn này theo phong cách đã thiết lập từ đầu buổi học.
        Nếu phần nội dung này là các câu hỏi trắc nghiệm thì trích dẫn câu trắc nghiệm được chọn đó hoặc nếu là nhiều câu hỏi trắc nghiệm nhưng tiêu đề chung không phải 1 câu thì lần lượt hiển thị câu hỏi trắc nghiệm.
        Nội dung được trích ra từ tài liệu đính kèm:
        ---
        {selected_part['noi_dung']}
        ---
        """

        question_promptFilter = f"""        
        {selected_part['noi_dung']}
        """
        
        #st.subheader("🧪 Nội dung gửi lên Gemini:")
        #st.code(question_prompt, language="markdown")  # để debug prompt

        
        with st.spinner("🤖 Đang tạo câu hỏi từ phần bạn chọn..."):
            user_message = {
                "role": "user",
                "parts": [{"text": question_prompt}]
            }
            user_messageFilter = {
                "role": "user",
                "parts": [{"text": question_promptFilter}]
            }
            #if read_lesson_first:
            st.session_state.messages.append(user_messageFilter)
        
            # 🏷️ Đánh dấu index của message là phần giới thiệu bài học
            if "lesson_intro_indices" not in st.session_state:
                st.session_state["lesson_intro_indices"] = []
            lesson_intro_index = len(st.session_state.messages) - 1
            st.session_state["lesson_intro_indices"].append(lesson_intro_index)
        
            # ✅ Phát audio NGAY nếu bật tính năng đọc bài học
            # if st.session_state.get("read_lesson_first", False) and st.session_state.get("enable_audio_playback", True):
            #     render_audio_block(question_prompt, autoplay=True)

            # ✅ Phát audio ngay nếu bật chế độ đọc bài học
            # if st.session_state.get("read_lesson_first") and st.session_state.get("enable_audio_playback", True):
            #     render_audio_block(question_prompt, autoplay=True)

            # # 🔊 Phát audio tự động nội dung vừa thêm            
            # # Nếu người dùng chọn checkbox và có nội dung để đọc
            # if read_lesson_first and question_prompt:
            #     b64 = None
            #     if st.session_state.get("enable_audio_playback", True):
            #         b64 = generate_and_encode_audio(question_prompt)
                
            #     # Hiển thị audio player
            #     if b64:
            #         autoplay_attr = "autoplay" if st.session_state.get("enable_audio_playback", True) else ""
            #         st.markdown(f"""
            #         <audio controls {autoplay_attr}>
            #             <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            #             Trình duyệt của bạn không hỗ trợ phát âm thanh.
            #         </audio>
            #         """, unsafe_allow_html=True)

            #Bước 2: Gợi ý cách viết prompt tốt (ngắn + rõ)
            selected_part = st.session_state["selected_part_for_discussion"]

            #Bước 3: Hiển thị câu hỏi AI phản hồi
            ai_question = chat_with_gemini(st.session_state.messages)

            #Xử lý kết quả:
            if ai_question is None:
                st.warning("⚠️ Gemini đang quá tải hoặc phản hồi lỗi. Vui lòng thử lại sau.")
            else:
                ai_question = clean_html_to_text(ai_question)
                #ai_question = format_mcq_options(ai_question)
                #st.chat_message("🤖 Gia sư AI").markdown(ai_question)
                st.session_state.messages.append({"role": "model", "parts": [{"text": ai_question}]})
        
    # ✅ Nếu vừa khôi phục tiến độ, thông báo ra
    if st.session_state.get("progress_restored"):
        st.success(f"✅ Đã khôi phục tiến độ học từ {st.session_state['progress_restored']}.")
        del st.session_state["progress_restored"]

    # Nếu tài liệu mới, reset
    if st.session_state.get("lesson_source") != current_source:
        st.session_state["lesson_progress_initialized"] = False
        st.session_state["current_part_index"] = 0

    # Khởi tạo tiến độ học chỉ 1 lần duy nhất
    uploaded_json = None
    for file in uploaded_files:
        if file.name.endswith(".json"):
            uploaded_json = file
            break
    
    if "lesson_progress_initialized" not in st.session_state or not st.session_state["lesson_progress_initialized"]:
        init_lesson_progress(all_parts)
        st.session_state["lesson_progress_initialized"] = True
    
        # 👉 Merge ngay sau init
        if uploaded_json:
            uploaded_json.seek(0)
            loaded_progress = json.load(uploaded_json)
            merge_lesson_progress(st.session_state["lesson_progress"], loaded_progress)
            st.session_state["progress_restored"] = uploaded_json.name  # 👉 Ghi tên file đã restore

    # 🚀 Đảm bảo current_part_index luôn có
    if "current_part_index" not in st.session_state:
        st.session_state["current_part_index"] = 0
else:
    st.warning("⚠️ Không tìm thấy nội dung bài học phù hợp!")
    
# Nếu người học đã cung cấp tài liệu → Ghi đè để bắt đầu buổi học
#if (selected_lesson != "👉 Chọn bài học..." or file_url.strip()) and pdf_context:
if pdf_context:
    # Ưu tiên lấy dòng tiêu đề từ tài liệu
    lesson_title_extracted = None
    for line in pdf_context.splitlines():
        line = line.strip()
        if len(line) > 10 and any(kw in line.lower() for kw in ["buổi", "bài", "bài học", "chủ đề"]):
            lesson_title_extracted = line
            break

    # Xác định tên bài học hợp lý
    #fallback_name = uploaded_file.name if uploaded_file else selected_lesson
    #fallback_name = uploaded_files[0].name if uploaded_files else selected_lesson
    if uploaded_files:
        fallback_name = " + ".join([f.name for f in uploaded_files])
    elif selected_lesson != "👉 Chọn bài học...":
        fallback_name = selected_lesson
    else:
        fallback_name = "Bài học"
    lesson_title = lesson_title_extracted or fallback_name or "Bài học"

    # Gọi Gemini để tóm tắt tài liệu
    try:
        response = requests.post(
            GEMINI_API_URL,
            headers={"Content-Type": "application/json"},
            params={"key": API_KEY},
            json={
                "contents": [
                    {"parts": [{"text": f"Tóm tắt ngắn gọn (2-3 câu) nội dung sau, dùng văn phong thân thiện, không liệt kê gạch đầu dòng:\n\n{pdf_context[:2500]}"}]}
                ]
            }
        )
        if response.status_code == 200:
            lesson_summary = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        else:
            lesson_summary = ""
    except Exception as e:
        lesson_summary = ""

    # Giới hạn dung lượng tài liệu đưa vào prompt khởi tạo
    LIMITED_PDF_CONTEXT = pdf_context #[:4000]  # hoặc dùng tokenizer nếu muốn chính xác hơn
    
    PROMPT_LESSON_CONTEXT = f"""
    {SYSTEM_PROMPT_Tutor_AI}
    
    # Bạn sẽ hướng dẫn buổi học hôm nay với tài liệu sau:
    
    ## Bài học: {lesson_title}
    
    --- START OF HANDBOOK CONTENT ---
    {LIMITED_PDF_CONTEXT}
    --- END OF HANDBOOK CONTENT ---
    """

    def build_lesson_intro(lesson_summary: str, part_list: list) -> str:
        greeting = "Chào bạn! Mình đã sẵn sàng để đồng hành cùng bạn trong buổi học hôm nay.\n\n"
    
        if lesson_summary:
            greeting += f" *{lesson_summary.strip()}*\n\n"
    
        greeting += " Bạn muốn bắt đầu với phần nào:\n\n"
    
        part_types = {
            "ly_thuyet": "Lý thuyết",
            "bai_tap_co_giai": "Bài tập có lời giải",
            "trac_nghiem": "Trắc nghiệm",
            "luyen_tap": "Bài tập luyện tập",
            "du_an": "Bài tập dự án"
        }
    
        seen_loai = set()
        numbered_parts = []
    
        for part in part_list:
            loai = part.get("loai", "")
            if loai and loai not in seen_loai:
                seen_loai.add(loai)
                label = part_types.get(loai, "Phần khác")
                numbered_parts.append(f"{len(numbered_parts)+1}. **{label}**")
    
        if numbered_parts:
            greeting += "\n".join(numbered_parts)
            greeting += "\n\n Bạn muốn bắt đầu phần nào trước?"
    
        return greeting.strip()
        
    # Reset session nếu file/tài liệu mới
    # if "lesson_source" not in st.session_state or st.session_state.lesson_source != current_source:
    #     # 🔹 Greeting khởi đầu buổi học + danh sách phần học
    #     greeting = build_lesson_intro(lesson_summary, st.session_state.get("lesson_parts", []))
        
    if "lesson_source" not in st.session_state or st.session_state.lesson_source != current_source:
        greeting = "Mình đã sẵn sàng để bắt đầu buổi học dựa trên tài liệu bạn đã cung cấp."
        if lesson_summary:
            greeting += f"\n\n{lesson_summary}"
        
            greeting = build_lesson_intro(lesson_summary, st.session_state.get("lesson_parts", []))
        #greeting += "\n\nBạn đã sẵn sàng chưa?"

        st.session_state.messages = [
            {"role": "user", "parts": [{"text": PROMPT_LESSON_CONTEXT}]},
            {"role": "model", "parts": [{"text": greeting}]}
        ]
        st.session_state.lesson_source = current_source
        st.session_state.lesson_loaded = current_source  # đánh dấu đã load
        
    #Phần chọn bài học
    lesson_title = selected_lesson if selected_lesson != " Chọn bài học..." else "Bài học tùy chỉnh"

    PROMPT_LESSON_CONTEXT = f"""
    {SYSTEM_PROMPT_Tutor_AI}
    
    # Bạn sẽ hướng dẫn buổi học hôm nay với tài liệu sau:
    
    ## Bài học: {lesson_title}
    
    --- START OF HANDBOOK CONTENT ---
    {pdf_context}
    --- END OF HANDBOOK CONTENT ---
    """

# Hiển thị lịch sử chat
for idx, msg in enumerate(st.session_state.messages[1:]):  
    role = "🧑‍🎓 Học sinh" if msg["role"] == "user" else "🤖 Gia sư AI"
    formatted_text = format_pdf_text_for_display(msg["parts"][0]["text"])
    st.chat_message(role).markdown(formatted_text)

    # ✅ Greeting ban đầu — ưu tiên dùng audio có sẵn nếu có
    if idx == 0 and role == "🤖 Gia sư AI" and st.session_state.get("enable_audio_playback", False):
        greeting_text = st.session_state["messages"][1]["parts"][0]["text"]
        if st.session_state.get("enable_audio_playback", False) is True:
            render_audio_block(greeting_text, autoplay=True)
    # if (
    #     idx == 0
    #     and role == "🤖 Gia sư AI"
    #     and st.session_state.get("enable_audio_playback", False)
    # ):
    #     greeting_text = st.session_state["messages"][1]["parts"][0]["text"]
    #     render_audio_block(greeting_text, autoplay=True)

    # ✅ Greeting ban đầu — chỉ phát audio nếu "Tự động phát âm thanh" được bật
    # if (
    #     idx == 0 
    #     and role == "🤖 Gia sư AI" 
    #     and "enable_audio_playback" in st.session_state 
    #     and st.session_state["enable_audio_playback"] is True
    # ):
    #     greeting_text = st.session_state["messages"][1]["parts"][0]["text"]
    #     render_audio_block(greeting_text, autoplay=True)
    # elif role == "🤖 Gia sư AI":
    #     autoplay_setting = st.session_state.get("enable_audio_playback", False)
    #     render_audio_block(msg["parts"][0]["text"], autoplay=False)

    # ✅ Phát audio cho tất cả các message của Gia sư AI
    # if role == "🤖 Gia sư AI":
    #     autoplay_setting = st.session_state.get("enable_audio_playback", True)
    #     render_audio_block(msg["parts"][0]["text"], autoplay=False)

# Ô nhập câu hỏi mới
user_input = st.chat_input("Nhập câu trả lời hoặc câu hỏi...")

if user_input:
    # 1. Hiển thị câu trả lời học sinh
    st.chat_message("🧑‍🎓 Học sinh").write(user_input)
    st.session_state.messages.append({"role": "user", "parts": [{"text": user_input}]})

    # 2. Gọi AI phản hồi
    with st.spinner("🤖 Đang phản hồi..."):
        # Lấy phần học hiện tại
        uncompleted_parts = [part for part in st.session_state["lesson_progress"] if part["trang_thai"] != "hoan_thanh"]

        if not uncompleted_parts:
            st.success("🎉 Bạn đã hoàn thành toàn bộ bài học! Chúc mừng!")
            st.stop()
        
        # Chọn phần chưa hoàn thành đầu tiên
        current_part = uncompleted_parts[0]
        
        # Gán luôn current_part_id
        st.session_state["current_part_id"] = current_part["id"]
        
        # Tạo prompt tutor AI dựa trên nội dung phần hiện tại
        prompt = f"""
        Dựa trên nội dung sau, hãy đặt 1 câu hỏi kiểm tra hiểu biết cho học sinh, rồi chờ học sinh trả lời:
        ---
        {current_part['noi_dung']}
        ---
        Hãy đặt câu hỏi ngắn gọn, rõ ràng, liên quan trực tiếp đến nội dung trên.
        """
        
        reply = chat_with_gemini(st.session_state.messages)

        # Nếu có thể xuất HTML (như <p>...</p>)
        reply = clean_html_to_text(reply)
        
        # Xử lý trắc nghiệm tách dòng
        reply = format_mcq_options(reply)

        if st.session_state.get("firebase_enabled", False):
            save_exchange_to_firestore(
                user_id=st.session_state.get("user_id", f"user_{uuid.uuid4().hex[:8]}"),
                lesson_source=st.session_state.get("lesson_source", "Chua_xac_dinh"),
                question=user_input,
                answer=reply,
                session_id=st.session_state.get("session_id", "default")
            )
        
        # 3. Hiển thị phản hồi
        st.chat_message("🤖 Gia sư AI").markdown(reply)

        # ✅ Gọi audio ngay sau hiển thị
        # autoplay_setting = st.session_state.get("enable_audio_playback", True)
        # render_audio_block(reply, autoplay=True)
        if st.session_state.get("enable_audio_playback", False):
            render_audio_block(reply, autoplay=True)

        # Sau đó mới append vào session_state để lưu
        st.session_state.messages.append({"role": "model", "parts": [{"text": reply}]})

  		# 🚀 TỰ ĐỘNG CHẤM ĐIỂM
        scoring_prompt = f"""
	    Chấm điểm câu trả lời sau trên thang điểm 0–100, chỉ trả về số, không giải thích.
	    ---
	    Câu trả lời: {user_input}
	    ---
	    """
     
        diem_raw = chat_with_gemini([
	        {"role": "user", "parts": [{"text": scoring_prompt}]}
	    ])
     
        try:
	        diem_so = int(re.findall(r"\d+", diem_raw)[0])
        except:
            diem_so = 90  # fallback nếu có lỗi
        
	    # Cập nhật tiến độ
        update_progress(
            #part_id=st.session_state.get("current_part_id", "UNKNOWN_PART"),
            part_id=current_part["id"],
            trang_thai="hoan_thanh",
            diem_so=diem_so
        )

        #Khi học sinh trả lời xong → chấm điểm → cập nhật tiến độ cho
        st.session_state["current_part_index"] += 1

        # 🚀 Buộc chạy lại để message mới được render audio trong vòng for
        #!st.rerun()
    
        # b64 = generate_and_encode_audio(reply)
        # b64 = None
        # if st.session_state.get("enable_audio_playback", True):
        #     b64 = generate_and_encode_audio(reply)
        #     render_audio_block(reply, autoplay=True)
        
        # # Hiển thị nút nghe
        # if b64:
        #     autoplay_attr = "autoplay" if st.session_state.get("enable_audio_playback", True) else ""
        #     st.markdown(f"""
        #     <audio controls {autoplay_attr}>
        #         <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        #         Trình duyệt của bạn không hỗ trợ phát âm thanh.
        #     </audio>
        #     """, unsafe_allow_html=True)

    # Chuyển biểu thức toán trong ngoặc đơn => LaTeX inline
    #reply = convert_parentheses_to_latex(reply)
    #reply_processed = convert_to_mathjax1(reply)

    # Hiển thị Markdown để MathJax render công thức
    #st.chat_message("🤖 Gia sư AI").markdown(reply_processed)
    #st.chat_message("🤖 Gia sư AI").markdown(reply)

    # Lưu lại phản hồi gốc
    #st.session_state.messages.append({"role": "model", "parts": [{"text": reply}]})

    #Khi học sinh trả lời xong → chấm điểm → cập nhật tiến độ cho
    # st.session_state["current_part_index"] += 1
