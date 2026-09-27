import os
import asyncio
from typing import List, Optional
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from nicegui import ui, app, run

from services.google_drive_service import GoogleDriveService
from gemini_helper import get_gemini_api_key

class RAGService:
    """
    Service xử lý Retrieval-Augmented Generation (RAG).
    - Ingestion: PDF -> Chunks -> Embeddings -> FAISS
    - Sync: FAISS -> Google Drive
    - Query: User Query -> Similarity Search -> Gemini Response
    """
    
    TEMP_DIR = "temp_rag"
    
    @classmethod
    def _ensure_temp_dir(cls, subject_id: str):
        path = os.path.join(cls.TEMP_DIR, subject_id)
        os.makedirs(path, exist_ok=True)
        return path

    @classmethod
    async def ingest_pdf(cls, file_path: str, subject_id: str, progress_callback=None):
        """Xử lý file PDF và tạo Vector Index."""
        try:
            if progress_callback: progress_callback(0.1, "📄 Đang đọc file PDF...")
            
            # 1. Load PDF
            loader = PyPDFLoader(file_path)
            docs = await asyncio.to_thread(loader.load)
            
            if progress_callback: progress_callback(0.3, f"✂️ Đang phân đoạn văn bản ({len(docs)} trang)...")
            
            # 2. Split text
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
            chunks = text_splitter.split_documents(docs)
            print(f"[RAG] 📦 Đã chia tài liệu thành {len(chunks)} đoạn.")
            
            if progress_callback: progress_callback(0.5, f"🧠 Đang tạo Vector Embeddings ({len(chunks)} đoạn)...")
            
            # 3. Create Embeddings
            api_key = get_gemini_api_key()
            embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=api_key)
            
            # 4. Create FAISS Index with Batching to avoid Rate Limit (429)
            print(f"[RAG] 🧠 Bắt đầu tạo Vector Index theo đợt (Batch size: 15)...")
            batch_size = 15
            vectorstore = None
            
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                current_count = min(i + batch_size, len(chunks))
                
                # Vòng lặp thử lại nếu gặp lỗi Quota
                max_retries = 5
                for retry in range(max_retries):
                    try:
                        if progress_callback: 
                            progress_callback(0.5 + (i/len(chunks))*0.3, f"🧠 Đang tạo Vector đoạn {current_count}/{len(chunks)}...")
                        
                        if vectorstore is None:
                            vectorstore = await asyncio.to_thread(FAISS.from_documents, batch, embeddings)
                        else:
                            await asyncio.to_thread(vectorstore.add_documents, batch)
                        break # Thành công thì thoát vòng lặp retry
                    except Exception as e:
                        if "429" in str(e) and retry < max_retries - 1:
                            wait_time = 60 * (retry + 1)
                            print(f"[RAG] ⚠️ Bị giới hạn Quota, đang ngủ {wait_time}s trước khi thử lại...")
                            if progress_callback: progress_callback(0.5 + (i/len(chunks))*0.3, f"⏳ Quá tải, đang đợi {wait_time}s...")
                            await asyncio.sleep(wait_time)
                        else:
                            raise e # Lỗi khác hoặc hết lượt retry thì báo lỗi
                
                # Nghỉ 10 giây giữa các đợt bình thường
                if i + batch_size < len(chunks):
                    await asyncio.sleep(10)
            
            if progress_callback: progress_callback(0.8, "💾 Đang lưu Index cục bộ...")
            
            # 5. Save locally
            save_path = cls._ensure_temp_dir(subject_id)
            await asyncio.to_thread(vectorstore.save_local, save_path)
            
            if progress_callback: progress_callback(1.0, "✅ Hoàn thành xử lý Vector!")
            return True, save_path
        except Exception as e:
            print(f"[RAGService] ❌ Lỗi Ingestion: {e}")
            return False, str(e)

    @classmethod
    async def sync_to_drive(cls, subject_id: str, user_id: int, original_pdf_path: str, progress_callback=None):
        """Đồng bộ PDF và Index lên Drive."""
        try:
            if progress_callback: progress_callback(0.1, "☁️ Đang chuẩn bị đồng bộ lên Drive...")
            
            service = GoogleDriveService.get_user_service(user_id)
            if not service: raise Exception("Không thể kết nối Google Drive")
            
            # Lấy folder ID của môn học (giả sử đã có trong StateManager hoặc DB)
            # Trong thực tế, ta cần lấy Subjects folder ID và tìm/tạo thư mục subject_id
            # Để đơn giản, ta sẽ lấy subjects_folder_id từ app.storage.user
            subjects_root = app.storage.user.get('drive_subjects_folder_id')
            if not subjects_root: raise Exception("Không tìm thấy thư mục Subjects trên Drive")
            
            # 1. Tạo thư mục riêng cho môn học nếu chưa có
            subject_folder_id = await asyncio.to_thread(
                GoogleDriveService.find_folder, service, subject_id, subjects_root
            )
            if not subject_folder_id:
                subject_folder_id = await asyncio.to_thread(
                    GoogleDriveService.create_folder, service, subject_id, subjects_root
                )

            # 2. Upload các file
            local_dir = os.path.join(cls.TEMP_DIR, subject_id)
            files_to_upload = [
                (original_pdf_path, os.path.basename(original_pdf_path), "application/pdf"),
                (os.path.join(local_dir, "index.faiss"), "index.faiss", "application/octet-stream"),
                (os.path.join(local_dir, "index.pkl"), "index.pkl", "application/octet-stream"),
            ]
            
            total = len(files_to_upload)
            for i, (path, name, mime) in enumerate(files_to_upload):
                if progress_callback: progress_callback(0.2 + (i/total)*0.7, f"📤 Đang upload {name}...")
                await asyncio.to_thread(GoogleDriveService.upload_file, service, path, name, subject_folder_id, mime)
            
            if progress_callback: progress_callback(1.0, "✅ Đã đồng bộ toàn bộ tài liệu lên Drive!")
            return True
        except Exception as e:
            print(f"[RAGService] ❌ Lỗi Sync: {e}")
            return False

    @classmethod
    async def query(cls, subject_id: str, user_query: str):
        """Truy vấn RAG."""
        try:
            local_path = os.path.join(cls.TEMP_DIR, subject_id)
            if not os.path.exists(os.path.join(local_path, "index.faiss")):
                user_id = app.storage.user.get('id')
                if not user_id:
                    return "Bạn cần đăng nhập để truy xuất tài liệu."
                
                service = GoogleDriveService.get_user_service(user_id)
                if not service:
                    return "Không thể kết nối Google Drive. Hãy tải tài liệu lên trước."
                
                subjects_root = app.storage.user.get('drive_subjects_folder_id')
                if not subjects_root:
                    return "Không tìm thấy thư mục Subjects trên Drive."
                    
                subject_folder_id = await asyncio.to_thread(
                    GoogleDriveService.find_folder, service, subject_id, subjects_root
                )
                if not subject_folder_id:
                    return "Chưa có dữ liệu sách cho môn học này trên Drive. Hãy upload PDF trước."
                     
                faiss_id = await asyncio.to_thread(
                    GoogleDriveService._find_file, service, "index.faiss", subject_folder_id
                )
                pkl_id = await asyncio.to_thread(
                    GoogleDriveService._find_file, service, "index.pkl", subject_folder_id
                )
                
                if faiss_id and pkl_id:
                    os.makedirs(local_path, exist_ok=True)
                    print(f"[RAG] Đang tải cấu trúc Vector từ Drive (FAISS)...")
                    await asyncio.to_thread(GoogleDriveService.download_file, service, faiss_id, os.path.join(local_path, "index.faiss"))
                    await asyncio.to_thread(GoogleDriveService.download_file, service, pkl_id, os.path.join(local_path, "index.pkl"))
                else:
                    return "Chưa có dữ liệu sách cho môn học này trên Drive. Hãy upload PDF trước."

            # 1. Load Index
            api_key = get_gemini_api_key()
            embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=api_key)
            vectorstore = await asyncio.to_thread(FAISS.load_local, local_path, embeddings, allow_dangerous_deserialization=True)
            
            # 2. Search
            docs = await asyncio.to_thread(vectorstore.similarity_search, user_query, k=3)
            context = "\n\n".join([f"[Trang {d.metadata.get('page', '?')}]: {d.page_content}" for d in docs])
            
            # 3. Generate Answer
            llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)
            prompt = f"""Bạn là một trợ lý học tập thông thái. Hãy dựa vào nội dung tài liệu sau để trả lời câu hỏi của người dùng.
            Nếu thông tin không có trong tài liệu, hãy nói rằng bạn không biết dựa trên sách này, nhưng có thể trả lời dựa trên kiến thức chung (ghi rõ).
            
            NỘI DUNG TÀI LIỆU:
            {context}
            
            CÂU HỎI: {user_query}
            
            TRẢ LỜI:"""
            
            response = await asyncio.to_thread(llm.invoke, prompt)
            return response.content
        except Exception as e:
            return f"❌ Lỗi truy vấn RAG: {e}"
