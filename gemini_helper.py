import google.generativeai as genai
import re
import os
import json
import time
import threading

# Global lock
key_lock = threading.Lock()

# Models to try in order
# Prioritizing gemini-2.5-flash-lite as it is confirmed working and fast in this environment
MODEL_PRIORITY = ['gemini-2.5-flash-lite', 'gemini-flash-latest', 'gemini-3.1-pro-preview']

def get_all_api_keys():
    try:
        key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'GeminiKey', 'geminiKey.txt')
        if os.path.exists(key_path):
            with open(key_path, 'r') as f:
                return [line.strip() for line in f.readlines() if line.strip()]
    except Exception as e:
        print(f"Error reading Gemini API Keys: {e}")
    return []

def get_gemini_api_key():
    """Legacy compatibility: returns the first key"""
    keys = get_all_api_keys()
    return keys[0] if keys else None

class RobustGeminiModel:
    def __init__(self, keys, system_instruction=None):
        self.keys = keys
        self.current_key_index = 0
        self.current_model_index = 0
        self.model_name = MODEL_PRIORITY[0]
        self.working_key_saved = False
        self.system_instruction = system_instruction
        
        self._configure_current_key()
        self._init_model()

    def _init_model(self):
        # Robustly handle system_instruction (SDK versions can be picky)
        sys_inst = None
        if self.system_instruction:
            sys_inst = {'role': 'system', 'parts': [{'text': self.system_instruction}]}
            
        self.model = genai.GenerativeModel(self.model_name, system_instruction=sys_inst)

    def _prioritize_current_key(self):
        try:
            working_key = self.keys[self.current_key_index]
            # Update RAM list immediately so NEXT clicks are 0s delay
            if self.keys and self.keys[0] != working_key:
                self.keys.remove(working_key)
                self.keys.insert(0, working_key)
                self.current_key_index = 0
                print(f"✅ Đã ưu tiên Key hoạt động lên đầu bộ nhớ RAM (tránh watchfiles reload).")
        except Exception:
            pass

    def _configure_current_key(self):
        if not self.keys: return
        key = self.keys[self.current_key_index]
        genai.configure(api_key=key, transport='rest')
        print(f"🔑 Using Key #{self.current_key_index + 1} | Model: {self.model_name}")

    def _rotate_strategy(self, key_removed=False):
        with key_lock:
            if not self.keys:
                 raise Exception("All API keys are dead.")
                 
            if not key_removed:
                self.current_key_index += 1
                
            if self.current_key_index < len(self.keys):
                print(f"🔄 Switching to Key #{self.current_key_index + 1}...")
            else:
                self.current_key_index = 0
                next_model_idx = (self.current_model_index + 1) % len(MODEL_PRIORITY)
                self.current_model_index = next_model_idx
                self.model_name = MODEL_PRIORITY[next_model_idx]
                print(f"🔄 Switching to Model: {self.model_name}...")
            self._configure_current_key()
            self._init_model()

    def update_system_instruction(self, instruction):
        """Cập nhật chỉ dẫn hệ thống cho model hiện tại."""
        self.system_instruction = instruction
        self._init_model()

    def start_chat(self, *args, **kwargs):
        chat_session = self.model.start_chat(*args, **kwargs)
        return RobustChatSession(chat_session, self, args, kwargs)

    def _retry_operation(self, func, *args, **kwargs):
        max_retries = 35 # Tăng số lần thử lên vì danh sách key có thể dài
        last_error = None
        for attempt in range(max_retries):
            try:
                result = func(*args, **kwargs)
                if not getattr(self, 'working_key_saved', False):
                    self._prioritize_current_key()
                    self.working_key_saved = True
                return result
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                self.working_key_saved = False
                
                if "429" in error_str or "quota" in error_str or "404" in error_str or "403" in error_str or "leaked" in error_str:
                    print(f"⚠️ Error ({error_str[:30]}...) on Key #{self.current_key_index + 1}/{self.model_name}.")
                    
                    # Xoá key hỏng vĩnh viễn khỏi RAM
                    key_removed = False
                    if "403" in error_str or "404" in error_str or "leaked" in error_str:
                        if self.keys:
                            bad_key = self.keys[self.current_key_index]
                            self.keys.remove(bad_key)
                            key_removed = True
                            
                    self._rotate_strategy(key_removed=key_removed)
                    time.sleep(0.1) # Rút ngắn thời gian delay
                    
                    if hasattr(self.model, 'generate_content') and func.__name__ == 'generate_content':
                         func = self.model.generate_content
                    continue
                else:
                    raise e
        raise Exception(f"All keys/models exhausted. Last error: {last_error}")
    
    def generate_content(self, *args, **kwargs):
        return self._retry_operation(self.model.generate_content, *args, **kwargs)

class RobustChatSession:
    def __init__(self, chat_session, parent, start_args, start_kwargs):
        self.chat = chat_session
        self.parent = parent
        self.start_args = start_args
        self.start_kwargs = start_kwargs

    def send_message(self, *args, **kwargs):
        max_retries = 35
        for attempt in range(max_retries):
            try:
                result = self.chat.send_message(*args, **kwargs)
                if not getattr(self.parent, 'working_key_saved', False):
                    self.parent._prioritize_current_key()
                    self.parent.working_key_saved = True
                return result
            except Exception as e:
                error_str = str(e).lower()
                self.parent.working_key_saved = False
                
                if "429" in error_str or "quota" in error_str or "403" in error_str or "leaked" in error_str:
                    print(f"⚠️ Chat Error. Rotating credentials...")
                    
                    key_removed = False
                    if "403" in error_str or "404" in error_str or "leaked" in error_str:
                        if self.parent.keys:
                            bad_key = self.parent.keys[self.parent.current_key_index]
                            self.parent.keys.remove(bad_key)
                            key_removed = True
                            
                    self.parent._rotate_strategy(key_removed=key_removed)
                    time.sleep(0.1) # Fast retry
                    
                    old_history = self.chat.history
                    # Re-create chat session with updated model (which has system_instruction)
                    self.chat = self.parent.model.start_chat(history=old_history)
                    continue
                raise e
        raise Exception(f"Chat Session: All {max_retries} rotation attempts failed.")

def get_chat_model(system_instruction=None):
    keys = get_all_api_keys()
    if not keys: return None
    return RobustGeminiModel(keys, system_instruction=system_instruction)

# --- Restored Helper Functions ---

def extract_json_from_text(text):
    """Trích xuất khối JSON từ phản hồi của Gemini"""
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            json_str = match.group(0)
            return json.loads(json_str)
    except Exception as e:
        print(f"Error parsing JSON: {e}")
    return {"sentiment": "neutral", "action": "continue"}

def build_system_prompt(lesson_content):
    """Tạo Prompt kỹ thuật để Gemini đóng vai Gia sư PKT"""
    return f"""
    BẠN LÀ: Một gia sư AI thấu cảm (Empathetic Tutor) môn Thương mại điện tử.
    CONTEXT BÀI HỌC: {lesson_content}
    NHIỆM VỤ:
    1. Trả lời câu hỏi của sinh viên ngắn gọn, chính xác.
    2. Nếu sinh viên trả lời sai câu hỏi quiz, hãy giải thích tại sao sai.
    3. QUAN TRỌNG: Phân tích cảm xúc ngầm ẩn của sinh viên.
    OUTPUT FORMAT:
    Cuối câu trả lời, bạn BẮT BUỘC phải xuống dòng và viết một đoạn JSON:
    ---SEPARATOR---
    {{"sentiment": "neutral|confused|frustrated|excited", "correctness": true|false|null, "short_feedback": "..."}}
    """
