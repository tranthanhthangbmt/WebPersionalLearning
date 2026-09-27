import os
import sys
import json
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_subject_dashboard import (
    load_all_subjects,
    get_subject_card_data,
    get_cross_subject_summary,
    get_unified_review_queue,
    get_bloom_radar_data,
    get_ebbinghaus_heatmap,
    get_study_streak_data,
    save_access_policy,
    load_access_policy,
    get_recommended_next_nodes,
    get_daily_tasks
)

PASS = 0
FAIL = 0

def test(name, func):
    global PASS, FAIL
    try:
        func()
        print(f"  ✅ {name}")
        PASS += 1
    except Exception as e:
        print(f"  ❌ {name}: {e}")
        FAIL += 1

def setup_test_data():
    os.makedirs("user_data/__test_user__/trees", exist_ok=True)
    os.makedirs("user_data/__test_user__/states", exist_ok=True)
    os.makedirs("user_data/__test_user__/bloom_state", exist_ok=True)
    
    subjects = {
        "subjects": [
            {"id": "s1", "title": "Subject 1", "filename": "user_data/__test_user__/trees/s1.json", "total_nodes": 10},
            {"id": "s2", "title": "Subject 2", "filename": "user_data/__test_user__/trees/s2.json", "total_nodes": 20}
        ]
    }
    with open("user_data/__test_user__/subjects.json", "w", encoding="utf-8") as f:
        json.dump(subjects, f)
        
    bloom_s1 = {
        "nodes": {
            "n1": {"overall_bloom": 3.0},
            "n2": {"overall_bloom": 0.0}
        },
        "ebbinghaus": {
            "n1": {"last_review": time.time() - 86400, "strength": 2.0, "reviews": 1}
        }
    }
    with open("user_data/__test_user__/bloom_state/s1.json", "w", encoding="utf-8") as f:
        json.dump(bloom_s1, f)
        
    bloom_s2 = {
        "nodes": {
            "n3": {"overall_bloom": 4.0},
            "n4": {"overall_bloom": 5.0}
        },
        "ebbinghaus": {
            "n3": {"last_review": time.time() - 3600, "strength": 3.0, "reviews": 2},
            "n4": {"last_review": time.time() - 172800, "strength": 1.5, "reviews": 1}
        }
    }
    with open("user_data/__test_user__/bloom_state/s2.json", "w", encoding="utf-8") as f:
        json.dump(bloom_s2, f)

def cleanup_test_data():
    import shutil
    try:
        shutil.rmtree("user_data/__test_user__")
    except:
        pass

def run_sprint_2_1_tests():
    print("\n" + "=" * 60)
    print("📊 STORY 2.1.1 — Subject Loader")
    print("=" * 60)
    
    def test_load_existing():
        subjects = load_all_subjects("__test_user__")
        assert len(subjects) == 2, f"Expected 2, got {len(subjects)}"
        assert "id" in subjects[0] and "title" in subjects[0]
        
    def test_load_missing():
        subjects = load_all_subjects("nonexistent_user_xyz")
        assert subjects == [], "Expected empty list"

    test("Load existing subjects", test_load_existing)
    test("Missing user -> empty", test_load_missing)
    
    print("\n" + "=" * 60)
    print("📋 STORY 2.1.2 — Per-Subject Progress Summary")
    print("=" * 60)
    
    def test_subject_card_fields():
        card = get_subject_card_data("__test_user__", {"id": "s1", "title": "S1", "total_nodes": 10})
        for field in ["subject_id", "title", "total_nodes", "nodes_learned",
                      "completion_pct", "avg_bloom", "review_urgency", "last_activity"]:
            assert field in card, f"Missing {field}"
            
    def test_subject_card_logic():
        card = get_subject_card_data("__test_user__", {"id": "s1", "title": "S1", "total_nodes": 10})
        assert card["nodes_learned"] == 1, f"Expected 1 nodes_learned, got {card['nodes_learned']}"
        assert card["completion_pct"] == 10.0, f"Expected pct 10.0, got {card['completion_pct']}"
        assert card["avg_bloom"] == 3.0, f"Expected avg bloom 3.0, got {card['avg_bloom']}"
        
    def test_subject_card_empty():
        card = get_subject_card_data("__test_user__", {"id": "s_empty", "title": "Empty", "total_nodes": 10})
        assert card["nodes_learned"] == 0
        assert card["completion_pct"] == 0.0
        assert card["avg_bloom"] == 0.0
        
    test("Card data has all fields", test_subject_card_fields)
    test("Card logic (nodes, pct, bloom)", test_subject_card_logic)
    test("Empty bloom state -> 0%", test_subject_card_empty)
    
    print("\n" + "=" * 60)
    print("📈 STORY 2.1.3 — Cross-Subject Aggregation")
    print("=" * 60)
    
    def test_cross_subject_summary():
        summary = get_cross_subject_summary("__test_user__")
        for field in ["total_subjects", "total_nodes", "total_learned",
                      "overall_pct", "avg_bloom", "total_review_needed"]:
            assert field in summary, f"Missing {field}"
            
        assert summary["total_subjects"] == 2, f"Expected 2 subjects, got {summary['total_subjects']}"
        assert summary["total_nodes"] == 30, f"Expected 30 nodes, got {summary['total_nodes']}"
        assert summary["total_learned"] == 3, f"Expected 3 learned, got {summary['total_learned']}"
        assert summary["overall_pct"] == 10.0, f"Expected 10.0 pct, got {summary['overall_pct']}"
        # (3.0*1 + 4.5*2) / 3 = 12.0 / 3 = 4.0
        assert summary["avg_bloom"] == 4.0, f"Expected avg bloom 4.0, got {summary['avg_bloom']}"
        
    test("Summary has required fields and logic", test_cross_subject_summary)
    
    print("\n" + "=" * 60)
    print("🗓️ STORY 2.1.4 — Unified Review Queue")
    print("=" * 60)
    
    def test_unified_queue():
        queue = get_unified_review_queue("__test_user__", max_items=5)
        if queue:
            assert "subject_title" in queue[0]
            assert "subject_id" in queue[0]
            
        for i in range(len(queue)-1):
            assert queue[i]["priority"] >= queue[i+1]["priority"]
            
        assert len(queue) <= 5
        
    test("Items have subject info, sorted by priority, max items", test_unified_queue)

def run_sprint_2_2_tests():
    print("\n" + "=" * 60)
    print("🕸️ STORY 2.2.1 — Bloom Radar Data")
    print("=" * 60)
    
    def test_bloom_radar():
        radar = get_bloom_radar_data("__test_user__", "s1")
        assert len(radar["labels"]) == 6, f"Expected 6 labels, got {len(radar['labels'])}"
        assert len(radar["data"]) == 6, f"Expected 6 data points, got {len(radar['data'])}"
        assert all(0 <= v <= 1 for v in radar["data"]), "Values must be in [0, 1]"
        assert "Remember" in radar["labels"][0] or "L1" in radar["labels"][0]
        
    test("Radar has 6 axes and valid values", test_bloom_radar)
    
    print("\n" + "=" * 60)
    print("🔥 STORY 2.2.2 — Ebbinghaus Heatmap Data")
    print("=" * 60)
    
    def test_heatmap_data():
        heatmap = get_ebbinghaus_heatmap("__test_user__", "s1")
        if heatmap:
            item = heatmap[0]
            assert "retention" in item
            assert item["status"] in ("critical", "warning", "good", "excellent")
            
        for i in range(len(heatmap)-1):
            assert heatmap[i]["retention"] <= heatmap[i+1]["retention"]
            
    test("Heatmap has status and is sorted by retention ascending", test_heatmap_data)
    
    print("\n" + "=" * 60)
    print("📆 STORY 2.2.3 — Study Activity Stats")
    print("=" * 60)
    
    def test_study_activity():
        stats = get_study_streak_data("__test_user__")
        for field in ["total_sessions", "active_days", "weekly_activity"]:
            assert field in stats
        assert len(stats["weekly_activity"]) == 7
        
    test("Study stats have required fields and 7-day array", test_study_activity)

def run_sprint_2_3_tests():
    print("\n" + "=" * 60)
    print("⚙️ STORY 2.3.1 — Access Policy Persistence")
    print("=" * 60)
    
    def test_save_load_policy():
        save_access_policy("__test_user__", "k12_strict")
        assert load_access_policy("__test_user__") == "k12_strict"
        
    def test_default_policy():
        assert load_access_policy("nonexistent_user") == "university_flexible"
        
    def test_invalid_policy():
        save_access_policy("__test_user__", "invalid_policy")
        # Should not have changed
        assert load_access_policy("__test_user__") == "k12_strict"
        
    test("Save and load policy", test_save_load_policy)
    test("Default policy is university_flexible", test_default_policy)
    test("Invalid policy is ignored", test_invalid_policy)
    
    print("\n" + "=" * 60)
    print("🧠 STORY 2.3.2 — Cross-Subject KST Recommendations")
    print("=" * 60)
    
    def test_kst_recommendations():
        # Requires soft_prerequisite to work, if it doesn't return anything we at least check format
        recs = get_recommended_next_nodes("__test_user__", max_items=3)
        if recs:
            assert "subject_title" in recs[0]
            assert "readiness_score" in recs[0]
            
        for i in range(len(recs)-1):
            assert recs[i]["readiness_score"] >= recs[i+1]["readiness_score"]
            
    test("KST recommendations have required fields and sorted", test_kst_recommendations)
    
    print("\n" + "=" * 60)
    print("🎯 STORY 2.3.3 — Daily Tasks Generator")
    print("=" * 60)
    
    def test_daily_tasks():
        tasks = get_daily_tasks("__test_user__", max_tasks=3)
        assert len(tasks) <= 3
        if tasks:
            task = tasks[0]
            for field in ["type", "title", "description", "priority"]:
                assert field in task
                
    test("Daily tasks have required fields and respect max_tasks", test_daily_tasks)

def main():
    setup_test_data()
    run_sprint_2_1_tests()
    run_sprint_2_2_tests()
    run_sprint_2_3_tests()
    cleanup_test_data()
    
    total = PASS + FAIL
    print("\n" + "=" * 60)
    if FAIL == 0:
        print(f"🎉 TẤT CẢ {total} TEST SPRINT 2.1 - 2.3 ĐỀU PASS!")
    else:
        print(f"📊 Kết quả: {PASS}/{total} PASS, {FAIL} FAIL")
    print("=" * 60)
    
    return FAIL == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
