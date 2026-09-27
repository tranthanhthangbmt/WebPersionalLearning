# tests/test_tree_editor_ai.py
"""
Test script cho tree_editor_ai.py
Bao gồm: test merge logic (offline) + test AI calls (online, cần Gemini API key)

Chạy: python tests/test_tree_editor_ai.py
      python tests/test_tree_editor_ai.py --with-ai   (test gọi Gemini thật)
"""

import os
import sys
import json
import copy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tree_editor_ai import (
    merge_ai_result_into_tree,
    format_ai_result_preview,
)

PASS = 0
FAIL = 0

# Sample tree for testing
SAMPLE_TREE = {
    "course_name": "Thương mại điện tử",
    "macro_nodes": [
        {"id": "m1", "title": "Tổng quan TMĐT"},
        {"id": "m2", "title": "Giao dịch điện tử"}
    ],
    "micro_nodes": [
        {"id": "c1.1", "parent_macro": "m1", "title": "Khái niệm TMĐT", "content": "Giới thiệu TMĐT", "alpha_base": 12},
        {"id": "c1.2", "parent_macro": "m1", "title": "Cơ sở hạ tầng", "content": "Hạ tầng CNTT", "alpha_base": 13},
        {"id": "c2.1", "parent_macro": "m2", "title": "Hợp đồng điện tử", "content": "Quy trình HĐ", "alpha_base": 18}
    ],
    "assess_nodes": [
        {"id": "a1.1", "target_micro": "c1.1", "theta_pass": 0.6, "questions": [
            {"question": "TMĐT là gì?", "options": ["A. ...", "B. ...", "C. ...", "D. ..."], "answer": "A"}
        ]}
    ],
    "edges": [
        {"source": "c1.1", "target": "c1.2", "reason": "Prerequisite"},
        {"source": "c1.1", "target": "c2.1", "reason": "Prerequisite"}
    ]
}


def test(name, func):
    global PASS, FAIL
    try:
        func()
        print(f"  ✅ {name}")
        PASS += 1
    except Exception as e:
        print(f"  ❌ {name}: {e}")
        FAIL += 1


def run_offline_tests():
    """Tests that don't require Gemini API."""
    print("\n" + "=" * 60)
    print("🧪 TEST MERGE LOGIC (OFFLINE)")
    print("=" * 60)

    # ─── TEST EXPAND MERGE ───
    print("\n🔀 Test merge: Expand mode")

    def test_expand_merge():
        tree = copy.deepcopy(SAMPLE_TREE)
        ai_result = {
            "remove_node_id": "c1.1",
            "new_micro_nodes": [
                {"id": "c1.1a", "parent_macro": "m1", "title": "Định nghĩa TMĐT", "content": "...", "alpha_base": 10},
                {"id": "c1.1b", "parent_macro": "m1", "title": "Phân loại TMĐT", "content": "...", "alpha_base": 12},
            ],
            "new_assess_nodes": [
                {"id": "a1.1a", "target_micro": "c1.1a", "theta_pass": 0.6, "questions": []}
            ],
            "new_edges": [
                {"source": "c1.1a", "target": "c1.1b", "reason": "Cần biết định nghĩa trước"}
            ]
        }
        result = merge_ai_result_into_tree(tree, ai_result, mode='expand')

        # c1.1 should be removed
        assert not any(n['id'] == 'c1.1' for n in result['micro_nodes']), "c1.1 should be removed"
        # c1.1a, c1.1b should exist
        ids = {n['id'] for n in result['micro_nodes']}
        assert 'c1.1a' in ids, "c1.1a should be added"
        assert 'c1.1b' in ids, "c1.1b should be added"
        # Old assess for c1.1 should be removed
        assert not any(a.get('target_micro') == 'c1.1' for a in result['assess_nodes']), "Old assess should be removed"
        # New assess should exist
        assert any(a['id'] == 'a1.1a' for a in result['assess_nodes']), "New assess should be added"
        # Old edges with c1.1 should be removed
        assert not any(e['source'] == 'c1.1' or e['target'] == 'c1.1' for e in result['edges']), "Old edges should be removed"
        # New edge should exist
        assert any(e['source'] == 'c1.1a' and e['target'] == 'c1.1b' for e in result['edges']), "New edge should be added"
        # c1.2 and c2.1 should still exist
        assert 'c1.2' in ids and 'c2.1' in ids, "Other nodes should remain"

    test("Expand: xóa node gốc + thêm nodes mới", test_expand_merge)

    # ─── TEST UPDATE MERGE ───
    print("\n🔄 Test merge: Update mode")

    def test_update_merge():
        tree = copy.deepcopy(SAMPLE_TREE)
        ai_result = {
            "updated_node": {
                "id": "c1.1", "title": "Khái niệm TMĐT (cập nhật)",
                "content": "Nội dung mới chi tiết hơn.", "alpha_base": 14
            },
            "updated_assess": {
                "id": "a1.1", "target_micro": "c1.1", "theta_pass": 0.6,
                "questions": [{"question": "Câu hỏi mới?", "options": ["A", "B", "C", "D"], "answer": "B"}]
            }
        }
        result = merge_ai_result_into_tree(tree, ai_result, mode='update')

        node = next(n for n in result['micro_nodes'] if n['id'] == 'c1.1')
        assert node['title'] == "Khái niệm TMĐT (cập nhật)", f"Title not updated: {node['title']}"
        assert node['content'] == "Nội dung mới chi tiết hơn."
        assert node['alpha_base'] == 14
        assess = next(a for a in result['assess_nodes'] if a.get('target_micro') == 'c1.1')
        assert assess['questions'][0]['answer'] == 'B'

    test("Update: cập nhật title/content/alpha/assess", test_update_merge)

    # ─── TEST ADD MERGE ───
    print("\n➕ Test merge: Add mode")

    def test_add_merge():
        tree = copy.deepcopy(SAMPLE_TREE)
        ai_result = {
            "new_macro_nodes": [{"id": "m3", "title": "Marketing điện tử"}],
            "new_micro_nodes": [
                {"id": "c3.1", "parent_macro": "m3", "title": "SEO", "content": "...", "alpha_base": 20}
            ],
            "new_assess_nodes": [],
            "new_edges": [{"source": "c1.1", "target": "c3.1", "reason": "Cần TMĐT trước"}]
        }
        result = merge_ai_result_into_tree(tree, ai_result, mode='add')

        assert any(m['id'] == 'm3' for m in result['macro_nodes']), "m3 should be added"
        assert any(n['id'] == 'c3.1' for n in result['micro_nodes']), "c3.1 should be added"
        assert any(e['source'] == 'c1.1' and e['target'] == 'c3.1' for e in result['edges']), "Edge should be added"
        # Original should remain
        assert len(result['macro_nodes']) == 3
        assert len(result['micro_nodes']) == 4

    test("Add: thêm chương mới + micro + edge", test_add_merge)

    # ─── TEST DEDUP ───
    print("\n🔒 Test deduplication")

    def test_dedup():
        tree = copy.deepcopy(SAMPLE_TREE)
        ai_result = {
            "new_micro_nodes": [
                {"id": "c1.1", "parent_macro": "m1", "title": "DUPLICATE", "content": "...", "alpha_base": 10}
            ],
            "new_assess_nodes": [],
            "new_edges": [
                {"source": "c1.1", "target": "c1.2", "reason": "DUPLICATE EDGE"}
            ]
        }
        result = merge_ai_result_into_tree(tree, ai_result, mode='refine')
        # Should NOT add duplicate c1.1
        c1_nodes = [n for n in result['micro_nodes'] if n['id'] == 'c1.1']
        assert len(c1_nodes) == 1, f"Should have exactly 1 c1.1, got {len(c1_nodes)}"
        assert c1_nodes[0]['title'] == "Khái niệm TMĐT", "Original should remain"
        # Should NOT add duplicate edge
        dup_edges = [e for e in result['edges'] if e['source'] == 'c1.1' and e['target'] == 'c1.2']
        assert len(dup_edges) == 1, f"Should have exactly 1 edge c1.1→c1.2, got {len(dup_edges)}"

    test("Dedup: không trùng ID và edge", test_dedup)

    # ─── TEST PREVIEW ───
    print("\n📋 Test format_ai_result_preview")

    def test_preview_expand():
        result = {
            "remove_node_id": "c1.1",
            "new_micro_nodes": [{"id": "c1.1a", "title": "Test", "alpha_base": 10}],
            "new_assess_nodes": [{"id": "a1.1a", "questions": [{}]}],
            "new_edges": [{"source": "c1.1a", "target": "c1.1b"}]
        }
        text = format_ai_result_preview(result, 'expand')
        assert "c1.1" in text
        assert "c1.1a" in text
        assert "1 bài học" in text

    def test_preview_update():
        result = {
            "updated_node": {"id": "c1.1", "title": "Updated", "alpha_base": 15},
            "updated_assess": {"questions": [{}]}
        }
        text = format_ai_result_preview(result, 'update')
        assert "c1.1" in text

    test("Preview expand", test_preview_expand)
    test("Preview update", test_preview_update)


def run_ai_tests():
    """Tests that call Gemini API (requires API key)."""
    print("\n" + "=" * 60)
    print("🤖 TEST AI CALLS (ONLINE — Gemini API)")
    print("=" * 60)

    from tree_editor_ai import ai_expand_node, ai_update_node, ai_refine_region, ai_add_from_document

    tree = copy.deepcopy(SAMPLE_TREE)

    # Test expand
    print("\n🔀 Test ai_expand_node:")
    def test_ai_expand():
        result = ai_expand_node(tree, "c1.1", "Tách thành 2 phần: Định nghĩa và Phân loại")
        assert 'new_micro_nodes' in result, "Missing new_micro_nodes"
        assert len(result['new_micro_nodes']) >= 2, f"Expected ≥2 nodes, got {len(result['new_micro_nodes'])}"
        for n in result['new_micro_nodes']:
            assert 'id' in n and 'title' in n, f"Node missing id/title: {n}"
        print(f"    → AI tạo {len(result['new_micro_nodes'])} nodes mới")
    test("Expand c1.1 → ≥2 nodes", test_ai_expand)

    # Test update
    print("\n🔄 Test ai_update_node:")
    def test_ai_update():
        result = ai_update_node(tree, "c2.1", "Thêm ví dụ thực tế về hợp đồng điện tử tại Việt Nam")
        assert 'updated_node' in result, "Missing updated_node"
        assert result['updated_node']['id'] == 'c2.1'
        print(f"    → Title: {result['updated_node'].get('title', '?')[:50]}")
    test("Update c2.1 với ví dụ thực tế", test_ai_update)

    # Test refine
    print("\n📌 Test ai_refine_region:")
    def test_ai_refine():
        result = ai_refine_region(tree, "m2", "Thêm 2 bài mới về thanh toán và bảo mật")
        assert 'new_micro_nodes' in result
        assert len(result['new_micro_nodes']) >= 1, "Expected ≥1 new node"
        for n in result['new_micro_nodes']:
            assert n.get('parent_macro') == 'm2', f"Wrong parent: {n.get('parent_macro')}"
        print(f"    → AI tạo {len(result['new_micro_nodes'])} bài mới cho m2")
    test("Refine m2 → ≥1 bài mới", test_ai_refine)

    # Test add
    print("\n📄 Test ai_add_from_document:")
    def test_ai_add():
        doc = "Chương mới: Logistics trong TMĐT. Bao gồm quản lý kho, vận chuyển, last-mile delivery."
        result = ai_add_from_document(tree, doc, "Bổ sung chương logistics vào cây")
        has_new = bool(result.get('new_macro_nodes') or result.get('new_micro_nodes'))
        assert has_new, "Should add new content"
        print(f"    → +{len(result.get('new_macro_nodes', []))} chương, +{len(result.get('new_micro_nodes', []))} bài")
    test("Add từ tài liệu logistics", test_ai_add)


def main():
    global PASS, FAIL
    with_ai = '--with-ai' in sys.argv

    run_offline_tests()

    if with_ai:
        run_ai_tests()
    else:
        print("\n💡 Để test gọi Gemini thật, chạy: python tests/test_tree_editor_ai.py --with-ai")

    print("\n" + "=" * 60)
    total = PASS + FAIL
    if FAIL == 0:
        print(f"🎉 TẤT CẢ {total} TEST ĐỀU PASS!")
    else:
        print(f"📊 Kết quả: {PASS}/{total} PASS, {FAIL} FAIL")
    print("=" * 60)
    return FAIL == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
