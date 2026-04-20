import time

class BehaviorTracker:
    def __init__(self):
        # Biến trạng thái in-memory cho session hiện tại.
        # Trong hệ thống thực tế có thể load/save từ DB hoặc Redis.
        self.fatigue = 0.0  # 0.0 (Khoẻ mạnh) đến 1.0 (Kiệt sức)
        self.consecutive_correct = 0
        self.last_action_time = time.time()
    
    def log_action(self, action_type: str, time_spent_sec: float = 10.0):
        """
        action_type can be: 'correct', 'wrong', 'rest', 'video'
        """
        now = time.time()
        idle_time = now - self.last_action_time
        
        # Idle recovery
        if idle_time > 300: # Nghỉ ngơi > 5 phút
            self.fatigue = max(0.0, self.fatigue - 0.5)
            
        if action_type == 'correct':
            self.consecutive_correct += 1
            # Thưởng momentum nếu đúng liên tiếp
            recovery = 0.02 + 0.01 * min(self.consecutive_correct, 5)
            self.fatigue = max(0.0, self.fatigue - recovery)
            
            # Gõ nhanh / trả lời nhanh cũng làm giảm mệt ít (nếu time_spent < 5s)
            if time_spent_sec < 5:
                self.fatigue = max(0.0, self.fatigue - 0.01)
                
        elif action_type == 'wrong':
            self.consecutive_correct = 0
            # Sai phạt nặng hơn
            self.fatigue = min(1.0, self.fatigue + 0.1)
            
            # Khựng lại lâu (Hesitation) trước khi trả lời sai => tăng fatigue thêm
            if time_spent_sec > 20: 
                self.fatigue = min(1.0, self.fatigue + 0.05)
                
        elif action_type == 'video':
            # Học thụ động giúp hồi pin từ từ
            self.fatigue = max(0.0, self.fatigue - 0.1 * (time_spent_sec / 60))
            
        elif action_type == 'rest':
            self.fatigue = max(0.0, self.fatigue - 0.05 * (time_spent_sec / 60))

        self.last_action_time = now
        return self.fatigue
    
    def get_fatigue_level(self) -> float:
        return self.fatigue
        
    def reset(self):
        self.fatigue = 0.0
        self.consecutive_correct = 0
        self.last_action_time = time.time()
