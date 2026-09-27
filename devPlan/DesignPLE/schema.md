# Data Schema Definition (Sprint 2)

Hệ thống sử dụng kiến trúc Single JSON để lưu trữ toàn bộ dữ liệu người dùng trên Google Drive. 

## 1. profile.json
Lưu trữ thông tin tổng quát của người dùng và danh sách các môn học.

**Path trên Drive:** `KnowledgeGalaxy_Data/profile.json`

```json
{
  "version": "1.1",
  "updated_at": "2026-05-01T00:00:00Z",
  "user_stats": {
    "total_xp": 1250,
    "level": 5,
    "streak": {
      "current": 3,
      "longest": 10,
      "last_active": "2026-04-30"
    },
    "total_study_minutes": 450,
    "badges": ["pioneer", "fast_learner"]
  },
  "subjects": [
    {
      "id": "subject_001",
      "name": "Trí tuệ nhân tạo (AIUD)",
      "folder_id": "google_drive_folder_id_xyz",
      "file_id": "google_drive_file_id_abc",
      "last_opened": "2026-04-30T15:00:00Z"
    }
  ],
  "settings": {
    "theme": "dark",
    "language": "vi",
    "notifications": true
  }
}
```

## 2. [subject_id].json
Lưu trữ cấu trúc cây tri thức và tiến độ học tập chi tiết của từng node.

**Path trên Drive:** `KnowledgeGalaxy_Data/Subjects/[subject_id].json`

```json
{
  "subject_id": "subject_001",
  "name": "Trí tuệ nhân tạo (AIUD)",
  "nodes": [
    {
      "id": "c1.1",
      "label": "Khai phá Đại dương Số",
      "bloom_score": 85,
      "mastery_score": 0.75,
      "last_interaction": "2026-04-30T14:30:00Z",
      "status": "completed",
      "review_schedule": {
        "ef": 2.5,
        "interval": 4,
        "next_review": "2026-05-04"
      }
    }
  ],
  "edges": [
    { "from": "c1.1", "to": "c1.2", "type": "prerequisite" }
  ]
}
```
