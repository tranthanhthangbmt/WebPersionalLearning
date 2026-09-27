"""
Test script cho Phase 2: Tree-level Bloom Calibration + User Adjust + Ebbinghaus
Chạy: python test_bloom_phase02.py
"""
import json
import os
import sys
import time
import shutil
import copy


def test_tree_calibration():
    """TEST 1: Calibrate toàn bộ tree thật."""
    print("=" * 60)
    print("TEST 1: calibrate_tree_bloom() trên tree thật")
    print("=" * 60)
    
    from bloom_taxonomy import calibrate_tree_bloom, get_effective_levels
    
    # Find a real tree
    tree_dir = os.path.join("user_data", "thanhthangbmt7", "trees")
    if not os.path.exists(tree_dir):
        print("  ⚠️ Không tìm thấy thư mục trees. Skip.")
        return None
    
    tree_files = [f for f in os.listdir(tree_dir) if f.endswith('.json')]
    if not tree_files:
        print("  ⚠️ Không có tree files. Skip.")
        return None
    
    # Work on a COPY to avoid modifying user data
    src_path = os.path.join(tree_dir, tree_files[0])
    test_dir = os.path.join("user_data", "__test_phase2__", "trees")
    os.makedirs(test_dir, exist_ok=True)
    test_path = os.path.join(test_dir, "test_tree.json")
    shutil.copy2(src_path, test_path)
    
    # Calibrate
    stats = calibrate_tree_bloom(test_path)
    print(f"  📊 Total nodes: {stats['total']}")
    print(f"  ✅ Calibrated: {stats['calibrated']}")
    print(f"  ⏭️ Skipped: {stats['skipped']}")
    
    assert stats["calibrated"] > 0, "Should calibrate at least 1 node"
    
    # Verify bloom_profile written into JSON
    with open(test_path, 'r', encoding='utf-8') as f:
        tree_data = json.load(f)
    
    # Check micro nodes have bloom_profile
    micro_count = 0
    for n in tree_data.get("micro_nodes", []):
        if n.get("bloom_profile"):
            micro_count += 1
            levels = get_effective_levels(n["bloom_profile"])
            assert len(levels) >= 2, f"Node {n['id']} should have >= 2 bloom levels"
    
    print(f"  ✅ {micro_count} micro nodes have bloom_profile in JSON")
    
    # Verify idempotency (run again → should skip all)
    stats2 = calibrate_tree_bloom(test_path, force=False)
    assert stats2["calibrated"] == 0, "Second run should skip all (already calibrated)"
    assert stats2["skipped"] == stats["total"], "All should be skipped"
    print(f"  ✅ Idempotency: 2nd run skipped all {stats2['skipped']} nodes")
    
    # Force re-calibrate
    stats3 = calibrate_tree_bloom(test_path, force=True)
    assert stats3["calibrated"] == stats["total"], "Force should re-calibrate all"
    print(f"  ✅ Force recalibrate: {stats3['calibrated']} nodes")
    
    # Print sample calibrations
    print("\n  📋 Sample calibrations:")
    for n in tree_data.get("micro_nodes", [])[:5]:
        profile = n.get("bloom_profile", {})
        levels = get_effective_levels(profile)
        alpha = profile.get("alpha_base", "?")
        level_str = ", ".join([f"L{l}" for l in levels])
        title = n.get("title", n.get("id", "?"))[:45]
        print(f"     {n['id']:8s} (α={alpha:>2}) → [{level_str:12s}] {title}")
    
    print(f"\n🎉 TEST 1 PASSED!\n")
    return test_path


def test_user_adjust(test_path):
    """TEST 2: User điều chỉnh Bloom levels."""
    print("=" * 60)
    print("TEST 2: adjust_node_bloom_in_tree()")
    print("=" * 60)
    
    from bloom_taxonomy import adjust_node_bloom_in_tree, get_effective_levels
    
    if not test_path:
        print("  ⚠️ No test tree available. Skip.")
        return
    
    # Load to find first micro node
    with open(test_path, 'r', encoding='utf-8') as f:
        tree_data = json.load(f)
    
    micro_nodes = tree_data.get("micro_nodes", [])
    if not micro_nodes:
        print("  ⚠️ No micro nodes. Skip.")
        return
    
    node = micro_nodes[0]
    node_id = node["id"]
    original_levels = get_effective_levels(node.get("bloom_profile", {}))
    print(f"  📌 Node: {node_id}")
    print(f"  📌 Original levels: {original_levels}")
    
    # Adjust UP: add higher levels
    result = adjust_node_bloom_in_tree(test_path, node_id, [1, 2, 3, 4, 5])
    assert result["success"] == True
    new_levels = result["effective_levels"]
    assert set(original_levels).issubset(set(new_levels)), "Old levels must be preserved"
    assert 5 in new_levels, "L5 should be added"
    print(f"  ✅ Adjusted to: {new_levels}")
    print(f"     Message: {result['message']}")
    
    # Verify persisted in JSON
    with open(test_path, 'r', encoding='utf-8') as f:
        tree_data2 = json.load(f)
    persisted = tree_data2["micro_nodes"][0]["bloom_profile"]
    assert persisted["user_adjusted_levels"] is not None
    assert persisted["effective_levels"] == new_levels
    print(f"  ✅ Persisted in JSON: effective_levels = {persisted['effective_levels']}")
    
    # Non-existent node
    result2 = adjust_node_bloom_in_tree(test_path, "nonexistent_xyz", [1, 2])
    assert result2["success"] == False
    print(f"  ✅ Non-existent node: returns error correctly")
    
    print(f"\n🎉 TEST 2 PASSED!\n")


def test_course_summary(test_path):
    """TEST 3: Course bloom summary."""
    print("=" * 60)
    print("TEST 3: get_course_bloom_summary()")
    print("=" * 60)
    
    from bloom_taxonomy import get_course_bloom_summary
    
    if not test_path:
        print("  ⚠️ No test tree. Skip.")
        return
    
    summary = get_course_bloom_summary(test_path)
    assert "error" not in summary
    
    print(f"  📚 Course: {summary['course_name']}")
    print(f"  📊 Total nodes: {summary['total_nodes']}")
    print(f"  📊 Calibrated: {summary['nodes_calibrated']}")
    print(f"  📊 Bloom distribution:")
    for lvl in range(1, 7):
        from bloom_taxonomy import BLOOM_LEVELS
        bl = BLOOM_LEVELS[lvl]
        count = summary['bloom_distribution'].get(lvl, 0)
        bar = "█" * count + "░" * (20 - count)
        print(f"     {bl['icon']} L{lvl} {bl['vi']:8s} {bar} {count} nodes")
    
    assert summary["nodes_calibrated"] > 0
    assert sum(summary["bloom_distribution"].values()) > 0
    
    print(f"\n🎉 TEST 3 PASSED!\n")


def test_ebbinghaus():
    """TEST 4: Ebbinghaus forgetting curve."""
    print("=" * 60)
    print("TEST 4: Ebbinghaus decay + review update")
    print("=" * 60)
    
    from bloom_taxonomy import (
        create_node_bloom_scores, update_bloom_score,
        apply_ebbinghaus_decay, update_ebbinghaus_after_review
    )
    
    # Create a node with some scores
    node_state = create_node_bloom_scores([1, 2, 3])
    for _ in range(8):
        update_bloom_score(node_state, 1, True, "mcq_recall", [1, 2, 3])
    for _ in range(2):
        update_bloom_score(node_state, 1, False, "flashcard", [1, 2, 3])
    for _ in range(5):
        update_bloom_score(node_state, 2, True, "matching", [1, 2, 3])
    
    print(f"  📊 Before decay:")
    print(f"     L1 score: {node_state['bloom_scores']['1']['score']:.1%}")
    print(f"     L2 score: {node_state['bloom_scores']['2']['score']:.1%}")
    print(f"     Overall: {node_state['overall_bloom']:.3f}")
    
    # Simulate review 3 hours ago
    ebbinghaus = {}
    ebbinghaus = update_ebbinghaus_after_review(ebbinghaus, "c1.1", 0.8)
    ebbinghaus["c1.1"]["last_review"] = time.time() - (3 * 3600)  # 3 hours ago
    
    print(f"  ⏱️ Strength after good review: {ebbinghaus['c1.1']['strength']:.1f}h")
    
    # Apply decay
    decayed = apply_ebbinghaus_decay(node_state, ebbinghaus, "c1.1")
    retention = decayed.get("retention", 1.0)
    decayed_bloom = decayed.get("overall_bloom_decayed", 0)
    
    print(f"\n  📊 After 3h decay:")
    print(f"     Retention: {retention:.1%}")
    print(f"     L1 decayed: {decayed['bloom_scores']['1'].get('decayed_score', '?')}")
    print(f"     Overall decayed: {decayed_bloom:.3f}")
    
    assert retention < 1.0, "After 3h, retention should be < 100%"
    assert retention > 0.1, "After 3h, retention should be > 10%"
    assert decayed_bloom < node_state["overall_bloom"], "Decayed bloom should be lower"
    
    # Simulate another good review → strength increases
    ebbinghaus = update_ebbinghaus_after_review(ebbinghaus, "c1.1", 0.9)
    new_strength = ebbinghaus["c1.1"]["strength"]
    print(f"\n  📈 After 2nd good review:")
    print(f"     Strength: {new_strength:.1f}h (increased)")
    print(f"     Reviews: {ebbinghaus['c1.1']['reviews']}")
    
    assert new_strength > 2.0, "Strength should increase after good review"
    
    print(f"\n🎉 TEST 4 PASSED!\n")


def test_bloom_state_integration():
    """TEST 5: Full integration — calibrate tree → create user state → simulate learning."""
    print("=" * 60)
    print("TEST 5: Full Integration — Simulate learning journey")
    print("=" * 60)
    
    from bloom_taxonomy import (
        calibrate_tree_bloom, create_node_bloom_scores, update_bloom_score,
        save_bloom_state, load_bloom_state, get_all_bloom_scores,
        get_bloom_color, check_level_unlocked, get_effective_levels,
        create_empty_bloom_state, BLOOM_LEVELS
    )
    
    test_user = "__test_learner__"
    test_subject = "test_subject_001"
    
    # Simulate a mini tree
    tree = {
        "course_name": "Test Course",
        "micro_nodes": [
            {"id": "n1", "title": "Intro", "alpha_base": 12},
            {"id": "n2", "title": "Concepts", "alpha_base": 18},
            {"id": "n3", "title": "Advanced", "alpha_base": 25},
        ]
    }
    tree_path = os.path.join("user_data", test_user, "test_tree.json")
    os.makedirs(os.path.dirname(tree_path), exist_ok=True)
    with open(tree_path, 'w', encoding='utf-8') as f:
        json.dump(tree, f)
    
    # Step 1: Calibrate
    stats = calibrate_tree_bloom(tree_path)
    print(f"  📊 Calibrated {stats['calibrated']} nodes")
    
    # Reload to get profiles
    with open(tree_path, 'r', encoding='utf-8') as f:
        tree = json.load(f)
    
    # Step 2: Create user bloom state
    state = create_empty_bloom_state(test_subject)
    
    for n in tree["micro_nodes"]:
        levels = get_effective_levels(n["bloom_profile"])
        state["nodes"][n["id"]] = create_node_bloom_scores(levels)
    
    # Step 3: Simulate learning journey for node n1
    print("\n  🎮 Simulating learning for node 'n1' (Intro, α=12):")
    n1_state = state["nodes"]["n1"]
    n1_levels = get_effective_levels(tree["micro_nodes"][0]["bloom_profile"])
    
    # L1: 10 MCQ attempts (8 correct)
    for i in range(8):
        update_bloom_score(n1_state, 1, True, "mcq_recall", n1_levels)
    for i in range(2):
        update_bloom_score(n1_state, 1, False, "mcq_recall", n1_levels)
    # L1: 5 flashcards (4 correct)
    for i in range(4):
        update_bloom_score(n1_state, 1, True, "flashcard", n1_levels)
    update_bloom_score(n1_state, 1, False, "flashcard", n1_levels)
    
    l1_score = n1_state["bloom_scores"]["1"]["score"]
    l1_types = n1_state["bloom_scores"]["1"]["types_done"]
    l2_unlocked = check_level_unlocked(2, n1_state["bloom_scores"], n1_levels)
    
    print(f"     L1 Score: {l1_score:.1%} | Types: {l1_types}")
    print(f"     L2 Unlocked: {'✅ Yes' if l2_unlocked else '🔒 No'}")
    
    # L2: 6 matching (5 correct)
    if l2_unlocked:
        for i in range(5):
            update_bloom_score(n1_state, 2, True, "matching", n1_levels)
        update_bloom_score(n1_state, 2, False, "fill_blank", n1_levels)
    
    l2_score = n1_state["bloom_scores"].get("2", {}).get("score", 0)
    overall = n1_state["overall_bloom"]
    color = get_bloom_color(overall)
    
    print(f"     L2 Score: {l2_score:.1%}")
    print(f"     Overall Bloom: {overall:.3f}")
    print(f"     3D Color: {color}")
    
    # Save state
    save_bloom_state(test_user, test_subject, state)
    
    # Verify load
    loaded = load_bloom_state(test_user, test_subject)
    all_scores = get_all_bloom_scores(test_user, test_subject)
    print(f"\n  📊 All bloom scores: {all_scores}")
    
    assert all_scores.get("n1", 0) > 0, "n1 should have bloom score > 0"
    assert all_scores.get("n2", 0) == 0, "n2 should be 0 (not attempted)"
    
    # Cleanup
    shutil.rmtree(os.path.join("user_data", test_user))
    
    print(f"\n🎉 TEST 5 PASSED!\n")


# ============================================================
#  MAIN
# ============================================================

if __name__ == "__main__":
    print("\n" + "🧬 " * 20)
    print("BLOOM LEARNING SYSTEM — Phase 2 Test Suite")
    print("🧬 " * 20 + "\n")
    
    test_path = test_tree_calibration()
    test_user_adjust(test_path)
    test_course_summary(test_path)
    test_ebbinghaus()
    test_bloom_state_integration()
    
    # Cleanup test data
    test_dir = os.path.join("user_data", "__test_phase2__")
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    
    print("=" * 60)
    print("✅ ALL PHASE 2 TESTS COMPLETE!")
    print("=" * 60)
