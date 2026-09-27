from database import engine, Session, select, KnowledgeState, log_interaction, User
from datetime import datetime
import os
import json

class StudentState:
    def __init__(self, user_db_id):
        self.user_db_id = user_db_id
        try:
            self.username = self._get_username()
        except Exception:
            self.username = "unknown"
        self.current_fatigue = 0.0
        self.current_concept_id = None
        self.quiz_history = {} # {concept_id: {question_idx: 'correct'/'wrong'}}
        # Load Elo từ DB khi khởi tạo
        try:
            self.knowledge_cache = self._load_from_db()
        except Exception as e:
            print(f"[StudentState] Error loading from DB: {e}")
            self.knowledge_cache = {}

    def _get_username(self):
        from database import get_user_by_id
        user = get_user_by_id(self.user_db_id)
        return user.username if user else "unknown"

    def _load_from_db(self):
        """Đọc trạng thái từ DB lên Cache"""
        cache = {}
        with Session(engine) as session:
            statement = select(KnowledgeState).where(KnowledgeState.user_id == self.user_db_id)
            results = session.exec(statement)
            for row in results:
                cache[row.concept_id] = row.elo_rating
        return cache

    def get_elo(self, concept_id):
        return self.knowledge_cache.get(concept_id, 1200.0)
    
    def get_mastery(self, concept_id):
        # Convert Elo to 0.0 - 1.0 scale
        elo = self.get_elo(concept_id)
        elo_mastery = max(0.0, min(1.0, (elo - 400) / 1600))
        
        # Factor in real Bloom score if available
        # If Bloom score is >= 4.0 (Analyze), mastery should be at least 0.8
        real_bloom = self.calculate_inferred_bloom(concept_id)
        if real_bloom >= 4.0:
            return max(elo_mastery, 0.8 + (real_bloom - 4.0) * 0.1)
        elif real_bloom >= 2.0:
            return max(elo_mastery, 0.6 + (real_bloom - 2.0) * 0.1)
            
        return elo_mastery

    def calculate_inferred_bloom(self, concept_id, subject_id=None):
        """
        Lấy Bloom score: Ưu tiên dữ liệu thực tế từ Bloom Hub, 
        nếu không có thì mới suy luận từ Elo.
        """
        # 1. Thử lấy từ Bloom Hub State (Real Assessment)
        try:
            from bloom_taxonomy import load_bloom_state
            # Tìm subject_id nếu không có
            if not subject_id:
                # Fallback: scan all subjects for this user to find the node
                user_dir = os.path.join(os.getcwd(), 'user_data', self.username, 'bloom_state')
                if os.path.exists(user_dir):
                    for f in os.listdir(user_dir):
                        if f.endswith('.json'):
                            sid = f.replace('.json', '')
                            state = load_bloom_state(self.username, sid)
                            if concept_id in state.get("nodes", {}):
                                return state["nodes"][concept_id].get("overall_bloom", 0.0)
            else:
                state = load_bloom_state(self.username, subject_id)
                if concept_id in state.get("nodes", {}):
                    return state["nodes"][concept_id].get("overall_bloom", 0.0)
        except Exception as e:
            print(f"[StudentState] Error fetching real bloom: {e}")

        # 2. Fallback: Suy luận từ Elo (Logic cũ)
        elo = self.get_elo(concept_id)
        base_bloom = max(0.0, min(6.0, (elo - 1050) / 150.0))
        
        node_hist = self.quiz_history.get(concept_id, {})
        correct_count = 0
        total_count = 0
        for q_id, stats in node_hist.items():
            if isinstance(stats, dict):
                correct_count += stats.get('correct', 0)
                total_count += stats.get('correct', 0) + stats.get('wrong', 0)
                
        if total_count > 0:
            accuracy = correct_count / total_count
            if accuracy > 0.8:
                base_bloom += 0.2
            elif accuracy < 0.4:
                base_bloom -= 0.2
                
        return min(6.0, max(0.0, base_bloom))

    def is_node_accessible(self, concept_id, prerequisites):
        """
        Kiểm tra xem node hiện tại đã đủ điều kiện mở khóa chưa.
        Trả về: (bool: is_locked, list: missing_prerequisites)
        """
        if not prerequisites:
            return True, []
            
        missing = []
        for p_id in prerequisites:
            mastery = self.get_mastery(p_id)
            if mastery < 0.6: # Ngưỡng tối thiểu để mở khóa node tiếp theo
                missing.append(p_id)
        
        return len(missing) == 0, missing

    def update_elo(self, concept_id, is_correct, sentiment="neutral"):
        # 1. Tính toán Elo (Logic cũ giữ nguyên)
        current_elo = self.get_elo(concept_id)
        expected = 1 / (1 + 10 ** ((1200 - current_elo) / 400)) # Giả sử độ khó tb = 1200
        actual = 1.0 if is_correct else 0.0
        k_factor = 32
        new_elo = current_elo + k_factor * (actual - expected)
        
        # 2. Cập nhật Cache (RAM)
        self.knowledge_cache[concept_id] = new_elo
        
        # 3. Cập nhật DB (Disk) - Upsert
        with Session(engine) as session:
            statement = select(KnowledgeState).where(
                KnowledgeState.user_id == self.user_db_id,
                KnowledgeState.concept_id == concept_id
            )
            record = session.exec(statement).first()
            
            if not record:
                record = KnowledgeState(user_id=self.user_db_id, concept_id=concept_id)
            
            record.elo_rating = new_elo
            record.last_review = datetime.now()
            
            session.add(record)
            session.commit()
            
        # Update Fatigue based on sentiment and result
        self.update_fatigue(sentiment, is_correct)

        # 4. Ghi Log chi tiết hành vi
        log_interaction(
            user_id=self.user_db_id,
            concept=concept_id,
            action="quiz_attempt",
            mastery=new_elo,
            fatigue=self.current_fatigue,
            sentiment=sentiment,
            details_dict={"correct": is_correct, "expected_score": expected}
        )
        
        # 5. Đồng bộ vào file JSON linh động
        try:
            self.sync_to_json()
        except Exception as e:
            print(f"[StudentState] Lỗi khi tạo JSON: {e}")
        
        return new_elo

    def update_fatigue(self, sentiment, is_correct):
        fatigue_increment = 0.05
        if sentiment == "frustrated": fatigue_increment = 0.15
        if sentiment == "bored": fatigue_increment = 0.1
        if sentiment == "excited": fatigue_increment = -0.05 # Hồi phục năng lượng
        
        self.current_fatigue = max(0.0, min(1.0, self.current_fatigue + fatigue_increment))

    def process_interaction(self, concept_id, correctness, sentiment, difficulty=0.5):
        # Wrapper for update_elo to match previous logic structure if needed
        new_elo = self.update_elo(concept_id, correctness, sentiment)
        return {
            "mastery": self.get_mastery(concept_id),
            "fatigue": self.current_fatigue,
            "recommendation": self._get_recommendation()
        }

    def _get_recommendation(self):
        """Logic của CLADC: Quyết định hành động tiếp theo"""
        if self.current_fatigue > 0.8:
            return "REST" # Bắt buộc nghỉ ngơi
        if self.current_fatigue > 0.6:
            return "VIDEO" # Chuyển sang thụ động (xem video) để giảm tải
        return "QUIZ" # Tiếp tục thử thách

    def to_dict(self, current_concept_id=None):
        """Serialize state for storage and AI context"""
        cid = current_concept_id or self.current_concept_id
        mastery = self.get_mastery(cid) if cid else 0.0
        bloom = self.calculate_inferred_bloom(cid) if cid else 0.0
        
        return {
            "user_db_id": self.user_db_id,
            "username": self.username,
            "current_fatigue": self.current_fatigue,
            "current_concept_id": cid,
            "current_mastery": float(mastery),
            "current_bloom": float(bloom),
            "quiz_history": self.quiz_history,
            "last_fatigue_update": datetime.now().strftime("%Y-%m-%d")
        }

    def sync_to_json(self):
        """Đồng bộ trạng thái tiến độ ra file JSON linh động định kỳ/khi có thay đổi"""
        try:
            with Session(engine) as session:
                user = session.exec(select(User).where(User.id == self.user_db_id)).first()
                if not user: return
                
                user_dir = os.path.join(os.getcwd(), 'user_data', user.username)
                if not os.path.exists(user_dir):
                    os.makedirs(user_dir)
                states_dir = os.path.join(user_dir, 'states')
                if not os.path.exists(states_dir):
                    os.makedirs(states_dir)
                    
                file_path = os.path.join(states_dir, 'student_state.json')
                
                payload = {
                    "user": user.username,
                    "nodes_mastery": {str(cid): float(self.get_mastery(cid)) for cid in self.knowledge_cache.keys()},
                    "inferred_blooms": {str(cid): float(self.calculate_inferred_bloom(cid)) for cid in self.knowledge_cache.keys()},
                    "history": self.quiz_history,
                    "last_fatigue_update": datetime.now().strftime("%Y-%m-%d"),
                    "current_fatigue": self.current_fatigue
                }
                
                # Add per-level bloom scores if available
                try:
                    from bloom_taxonomy import get_all_bloom_level_scores
                    # Scan user's bloom_state directory for all subjects
                    bloom_dir = os.path.join(os.getcwd(), 'user_data', user.username, 'bloom_state')
                    if os.path.exists(bloom_dir):
                        all_level_scores = {}
                        for bf in os.listdir(bloom_dir):
                            if bf.endswith('.json'):
                                sid = bf.replace('.json', '')
                                lvl_scores = get_all_bloom_level_scores(user.username, sid)
                                all_level_scores.update(lvl_scores)
                        payload["bloom_level_scores"] = all_level_scores
                except Exception:
                    pass
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(payload, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[StudentState] Error in sync_to_json (non-critical): {e}")

    @classmethod
    def from_dict(cls, data):
        """Restore state from storage"""
        instance = cls(data["user_db_id"])
        instance.current_fatigue = data.get("current_fatigue", 0.0)
        instance.current_concept_id = data.get("current_concept_id")
        
        # Restore and Migrate Quiz History
        raw_history = data.get("quiz_history", {})
        migrated_history = {}
        
        for cid, questions in raw_history.items():
            migrated_history[cid] = {}
            for qid, val in questions.items():
                if isinstance(val, str):
                    # Migration: 'correct' -> {'correct': 1, 'wrong': 0}
                    if val == 'correct':
                        migrated_history[cid][qid] = {'correct': 1, 'wrong': 0}
                    else:
                        migrated_history[cid][qid] = {'correct': 0, 'wrong': 1}
                else:
                    migrated_history[cid][qid] = val
                    
        instance.quiz_history = migrated_history
        
        # --- DAILY RESET LOGIC ---
        last_update_str = data.get("last_fatigue_update")
        if not last_update_str:
            # Handle legacy data or new user without date -> Reset to 0.0
            instance.current_fatigue = 0.0
        else:
            last_date = datetime.strptime(last_update_str, "%Y-%m-%d").date()
            if datetime.now().date() > last_date:
                instance.current_fatigue = 0.0 # Reset for new day
        
        return instance
