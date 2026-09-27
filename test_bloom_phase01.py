"""
Test script cho Phase 0+1: Bloom Taxonomy + Node Content Engine
Chạy: python test_bloom_phase01.py
"""
import json
import os
import sys

# ============================================================
#  TEST 1: bloom_taxonomy.py — Unit tests
# ============================================================

def test_bloom_taxonomy():
    print("=" * 60)
    print("TEST 1: bloom_taxonomy.py")
    print("=" * 60)
    
    from bloom_taxonomy import (
        BLOOM_LEVELS, calibrate_bloom_from_alpha, user_adjust_bloom,
        calculate_overall_bloom, check_level_unlocked, get_bloom_color,
        create_bloom_profile, create_node_bloom_scores, update_bloom_score,
        load_bloom_state, save_bloom_state, get_all_bloom_scores
    )
    
    # Test BLOOM_LEVELS config
    assert len(BLOOM_LEVELS) == 6, f"Expected 6 levels, got {len(BLOOM_LEVELS)}"
    for lvl in range(1, 7):
        assert lvl in BLOOM_LEVELS
        assert "name" in BLOOM_LEVELS[lvl]
        assert "assessment_types" in BLOOM_LEVELS[lvl]
    print("  ✅ BLOOM_LEVELS: 6 bậc đầy đủ")
    
    # Test calibration
    assert calibrate_bloom_from_alpha(10) == [1, 2], f"alpha=10 should be [1,2]"
    assert calibrate_bloom_from_alpha(15) == [1, 2, 3], f"alpha=15 should be [1,2,3]"
    assert calibrate_bloom_from_alpha(22) == [2, 3, 4], f"alpha=22 should be [2,3,4]"
    assert calibrate_bloom_from_alpha(28) == [3, 4, 5], f"alpha=28 should be [3,4,5]"
    # End-of-course bonus
    result = calibrate_bloom_from_alpha(28, node_position_ratio=0.9)
    assert 6 in result, "End-of-course node should include L6"
    print("  ✅ calibrate_bloom_from_alpha: Các mức calibrate đúng")
    
    # Test user adjust
    assert user_adjust_bloom([1, 2], [1, 2, 3]) == [1, 2, 3], "Should allow adding L3"
    assert user_adjust_bloom([1, 2], [3, 4]) == [1, 2, 3, 4], "Should keep old + add new"
    assert user_adjust_bloom([2, 3], [1]) == [1, 2, 3], "Should allow adding lower too"
    print("  ✅ user_adjust_bloom: Union logic đúng")
    
    # Test scoring
    scores = {
        "1": {"correct": 8, "total": 10, "score": 0.8, "types_done": ["mcq", "flashcard"]},
        "2": {"correct": 5, "total": 8, "score": 0.625, "types_done": ["matching"]},
    }
    overall = calculate_overall_bloom(scores)
    assert 0 < overall < 6, f"Overall should be 0-6, got {overall}"
    print(f"  ✅ calculate_overall_bloom: {overall:.3f} (L1=80%, L2=62.5%)")
    
    # Test unlock
    assert check_level_unlocked(1, scores, [1, 2, 3]) == True, "L1 always unlocked"
    assert check_level_unlocked(2, scores, [1, 2, 3]) == True, "L1>=70% + 2 types → L2 open"
    scores_low = {"1": {"score": 0.5, "types_done": ["mcq"]}}
    assert check_level_unlocked(2, scores_low, [1, 2]) == False, "L1<70% → L2 locked"
    print("  ✅ check_level_unlocked: Progressive unlock logic đúng")
    
    # Test color
    assert "210" in get_bloom_color(0.0), "Bloom 0 = grey"
    assert "200" in get_bloom_color(1.5), "Bloom 1.5 = Remember blue"
    assert "280" in get_bloom_color(5.8), "Bloom 5.8 = Create violet"
    print("  ✅ get_bloom_color: Color mapping đúng")
    
    # Test bloom state I/O
    test_user = "__test_bloom__"
    test_subject = "test_subject"
    state = {"subject_id": test_subject, "nodes": {
        "c1.1": create_node_bloom_scores([1, 2, 3])
    }, "ebbinghaus": {}}
    
    # Update score
    node_state = state["nodes"]["c1.1"]
    update_bloom_score(node_state, 1, True, "mcq_recall", [1, 2, 3])
    update_bloom_score(node_state, 1, True, "flashcard", [1, 2, 3])
    update_bloom_score(node_state, 1, False, "mcq_recall", [1, 2, 3])
    assert node_state["bloom_scores"]["1"]["correct"] == 2
    assert node_state["bloom_scores"]["1"]["total"] == 3
    assert len(node_state["bloom_scores"]["1"]["types_done"]) == 2
    print(f"  ✅ update_bloom_score: L1 = {node_state['bloom_scores']['1']['score']:.1%}")
    
    # Save & load
    save_bloom_state(test_user, test_subject, state)
    loaded = load_bloom_state(test_user, test_subject)
    assert loaded["nodes"]["c1.1"]["bloom_scores"]["1"]["correct"] == 2
    print("  ✅ save/load_bloom_state: JSON I/O đúng")
    
    # Cleanup
    import shutil
    test_dir = os.path.join("user_data", test_user)
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    
    print("\n🎉 bloom_taxonomy.py: TẤT CẢ TESTS PASSED!\n")


# ============================================================
#  TEST 2: node_content_engine.py — Library sync (no AI)
# ============================================================

def test_content_engine_sync():
    print("=" * 60)
    print("TEST 2: node_content_engine.py — Library Sync (no AI)")
    print("=" * 60)
    
    from node_content_engine import (
        _empty_content_pack, publish_to_library, load_from_library,
        _save_user_cache, _load_user_cache, sync_bloom_content_for_tree,
        _make_course_id, LIBRARY_DIR
    )
    
    test_course = "Test_Course_Bloom"
    course_id = _make_course_id(test_course)
    test_node = "test_c1.1"
    test_user_a = "__test_user_a__"
    test_user_b = "__test_user_b__"
    
    # Create a content pack
    pack = _empty_content_pack(test_node, course_id)
    pack["study_material"]["detailed_content"] = "# Test Content\n\nThis is test content."
    pack["study_material"]["learning_objectives"] = ["CLO1: Test objective"]
    pack["study_material"]["key_concepts"] = [{"term": "Test", "definition": "A test term"}]
    pack["bloom_profile"]["effective_levels"] = [1, 2, 3]
    pack["question_bank"] = {
        "L1": [{"type": "mcq_recall", "question": "Test Q?", "options": {"A": "Yes", "B": "No"}, "correct": "A"}],
        "L2": [{"type": "fill_blank", "sentence": "Test [BLANK]", "answer": "answer"}],
    }
    
    # User A publishes
    path = publish_to_library(pack, author=test_user_a)
    assert os.path.exists(path), f"Published file should exist: {path}"
    print(f"  ✅ publish_to_library: Saved to {path}")
    
    # Verify library load
    loaded = load_from_library(course_id, test_node)
    assert loaded is not None, "Should load from library"
    assert loaded["study_material"]["detailed_content"] == "# Test Content\n\nThis is test content."
    assert loaded["author"] == test_user_a
    print("  ✅ load_from_library: Content loaded correctly")
    
    # User B gets content via cache
    _save_user_cache(test_user_b, loaded)
    cached = _load_user_cache(test_user_b, course_id, test_node)
    assert cached is not None, "User B cache should exist"
    assert cached["study_material"]["detailed_content"] == loaded["study_material"]["detailed_content"]
    print("  ✅ User cache: User B can load from cache")
    
    # Test tree sync (create a minimal tree)
    test_tree = {
        "course_name": test_course,
        "micro_nodes": [
            {"id": test_node, "title": "Test Node", "content": "Test", "alpha_base": 15},
            {"id": "test_c1.2", "title": "Node 2", "content": "Test 2", "alpha_base": 20},
        ]
    }
    tree_path = os.path.join("user_data", "__test_sync__", "test_tree.json")
    os.makedirs(os.path.dirname(tree_path), exist_ok=True)
    with open(tree_path, 'w', encoding='utf-8') as f:
        json.dump(test_tree, f)
    
    synced = sync_bloom_content_for_tree(tree_path, "__test_sync__")
    print(f"  ✅ sync_bloom_content_for_tree: Synced {synced} nodes from library")
    
    # Verify sync result
    cached_sync = _load_user_cache("__test_sync__", course_id, test_node)
    assert cached_sync is not None, "Synced node should be cached"
    print("  ✅ Auto-sync: test_c1.1 loaded from library into __test_sync__ user")
    
    # Cleanup
    import shutil
    for d in [
        os.path.join("user_data", test_user_a),
        os.path.join("user_data", test_user_b),
        os.path.join("user_data", "__test_sync__"),
        os.path.join(LIBRARY_DIR, course_id),
    ]:
        if os.path.exists(d):
            shutil.rmtree(d)
    
    print("\n🎉 node_content_engine.py (sync): TẤT CẢ TESTS PASSED!\n")


# ============================================================
#  TEST 3: Bloom calibration trên dữ liệu tree thực tế
# ============================================================

def test_real_tree_calibration():
    print("=" * 60)
    print("TEST 3: Bloom calibration trên tree thực tế")
    print("=" * 60)
    
    from bloom_taxonomy import calibrate_bloom_from_alpha, get_node_position_ratio, create_bloom_profile
    from node_content_engine import _get_all_micro_ids, _get_all_nodes
    
    # Tìm 1 file tree thực tế
    tree_dir = os.path.join("user_data", "thanhthangbmt7", "trees")
    if not os.path.exists(tree_dir):
        print("  ⚠️ Không tìm thấy thư mục trees. Bỏ qua test này.")
        return
    
    tree_files = [f for f in os.listdir(tree_dir) if f.endswith('.json')]
    if not tree_files:
        print("  ⚠️ Không có file tree. Bỏ qua test này.")
        return
    
    tree_path = os.path.join(tree_dir, tree_files[0])
    with open(tree_path, 'r', encoding='utf-8') as f:
        tree_data = json.load(f)
    
    course_name = tree_data.get("course_name", "Unknown")
    all_ids = _get_all_micro_ids(tree_data)
    all_nodes = _get_all_nodes(tree_data)
    
    print(f"  📚 Course: {course_name}")
    print(f"  📊 Total micro nodes: {len(all_ids)}")
    print(f"  📊 Total all nodes: {len(all_nodes)}")
    print()
    
    # Calibrate bloom for each micro node
    calibration_results = []
    for node_id in all_ids[:10]:  # First 10 only
        node = all_nodes.get(node_id, {})
        alpha = node.get("alpha_base", 15)
        position = get_node_position_ratio(node_id, all_ids)
        levels = calibrate_bloom_from_alpha(alpha, position)
        title = node.get("title", node_id)[:40]
        
        calibration_results.append({
            "id": node_id, "title": title,
            "alpha": alpha, "position": f"{position:.2f}",
            "bloom_levels": levels
        })
        
        level_str = ", ".join([f"L{l}" for l in levels])
        print(f"  📌 {node_id} (α={alpha}, pos={position:.2f}) → [{level_str}]  {title}")
    
    print(f"\n🎉 Bloom calibration: {len(calibration_results)} nodes processed!\n")


# ============================================================
#  MAIN
# ============================================================

if __name__ == "__main__":
    print("\n" + "🧬 " * 20)
    print("BLOOM LEARNING SYSTEM — Phase 0+1 Test Suite")
    print("🧬 " * 20 + "\n")
    
    test_bloom_taxonomy()
    test_content_engine_sync()
    test_real_tree_calibration()
    
    print("=" * 60)
    print("✅ ALL PHASE 0+1 TESTS COMPLETE!")
    print("=" * 60)
