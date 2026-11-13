import os
import sys

# Thêm thư mục gốc vào PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent.expansion_agent import ExpansionDecisionAgent
from agent.audit_logger import AuditLogger

def run_test_suite():
    print("=" * 80)
    print(" BẮT ĐẦU CHẠY BỘ KIỂM THỬ TỰ ĐỘNG (AUTOMATED TEST SUITE) - 3 KỊCH BẢN")
    print("=" * 80)

    # --- KỊCH BẢN 1: TRƯỜNG HỢP THÔNG THƯỜNG (STANDARD CASE) ---
    print("\n>>> [TEST CASE 1]: Kiểm thử trường hợp thông thường (dataset_standard.json)")
    logger1 = AuditLogger(log_dir="logs/test_standard")
    agent1 = ExpansionDecisionAgent("data/dataset_standard.json", logger=logger1)
    res1 = agent1.run_pipeline()
    
    assert len(res1["selected_territories"]) == 2, "Lỗi: Kịch bản 1 phải chọn đúng 2 địa bàn!"
    selected_names = [s["territory"]["name"] for s in res1["selected_territories"]]
    print(f"  [PASS] Đã chọn chính xác 2 địa bàn: {selected_names}")
    
    # Kiểm tra địa bàn Duyên Hải (TERR_03) phải bị loại do đòi hỏi Onsite 24/7
    excluded_ids = [u["territory"]["id"] for u in res1["unselected_territories"] if u["score_res"]["is_excluded"]]
    assert "TERR_03" in excluded_ids, "Lỗi: Địa bàn Duyên Hải (TERR_03) vi phạm Onsite 24/7 nhưng không bị loại!"
    print("  [PASS] Loại trừ chính xác Địa bàn Duyên Hải do vượt trần năng lực On-site 24/7.")


    # --- KỊCH BẢN 2: THIẾU DỮ LIỆU & MÂU THUẪN (MISSING / CONFLICTED DATA) ---
    print("\n>>> [TEST CASE 2]: Kiểm thử trường hợp thiếu dữ liệu & mâu thuẫn (dataset_missing_info.json)")
    logger2 = AuditLogger(log_dir="logs/test_missing")
    agent2 = ExpansionDecisionAgent("data/dataset_missing_info.json", logger=logger2)
    res2 = agent2.run_pipeline()
    
    # Kiểm tra cờ cảnh báo HITL
    assert len(res2["hitl_flags"]) > 0, "Lỗi: Kịch bản 2 phải kích hoạt các cảnh báo HITL!"
    print(f"  [PASS] Đã phát hiện {len(res2['hitl_flags'])} cảnh báo cần con người xử lý:")
    for flag in res2["hitl_flags"]:
        print(f"    - {flag}")


    # --- KỊCH BẢN 3: RANH GIỚI QUY TẮC (BOUNDARY CASES) ---
    print("\n>>> [TEST CASE 3]: Kiểm thử trường hợp ranh giới quy tắc (dataset_boundary_case.json)")
    logger3 = AuditLogger(log_dir="logs/test_boundary")
    agent3 = ExpansionDecisionAgent("data/dataset_boundary_case.json", logger=logger3)
    res3 = agent3.run_pipeline()
    
    # Kiểm tra địa bàn vi phạm Onsite 24/7 (TERR_BOUND_03)
    excluded_bound = [u["territory"]["id"] for u in res3["unselected_territories"] if u["score_res"]["is_excluded"]]
    assert "TERR_BOUND_03" in excluded_bound, "Lỗi: TERR_BOUND_03 phải bị loại trừ vì vi phạm quy tắc Onsite!"
    print("  [PASS] Phát hiện vi phạm và loại bỏ TERR_BOUND_03 đúng quy tắc ranh giới.")
    
    # Kiểm tra cảnh báo chạm trần năng lực On-site (TERR_BOUND_01)
    boundary_flag_detected = any("Chạm trần ranh giới On-site" in f for f in res3["hitl_flags"])
    assert boundary_flag_detected, "Lỗi: Không phát hiện cảnh báo chạm trần năng lực cho trường hợp ranh giới!"
    print("  [PASS] Kích hoạt chính xác cờ cảnh báo ranh giới (chạm trần năng lực) chuyển xử lý cho Trưởng phòng.")

    print("\n" + "=" * 80)
    print(" TẤT CẢ 3 BỘ KIỂM THỬ ĐÃ VƯỢT QUA 100% (TEST SUITE PASSED SUCCESSFULLY)!")
    print("=" * 80)

if __name__ == "__main__":
    run_test_suite()

