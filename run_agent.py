import argparse
import sys
import os
from agent.expansion_agent import ExpansionDecisionAgent
from agent.audit_logger import AuditLogger

def main():
    parser = argparse.ArgumentParser(
        description="HP-Expansion-Agent: AI Agent Đánh giá thị trường mở rộng kinh doanh cho Công ty Hưng Phát"
    )
    parser.add_argument(
        "--data",
        type=str,
        default="data/dataset_standard.json",
        help="Đường dẫn file cấu trúc dữ liệu JSON (dataset)"
    )
    parser.add_argument(
        "--output_report",
        type=str,
        default=None,
        help="Đường dẫn file markdown xuất báo cáo (tùy chọn)"
    )

    args = parser.parse_args()

    if not os.path.exists(args.data):
        print(f"[LỖI] Không tìm thấy file dữ liệu tại: {args.data}")
        sys.exit(1)

    print("=" * 80)
    print(" HỆ THỐNG AI AGENT HỖ TRỢ ĐÁNH GIÁ MỞ RỘNG THỊ TRƯỜNG - CÔNG TY HƯNG PHÁT")
    print("=" * 80)
    print(f"[*] Nạp gói dữ liệu đầu vào: {args.data}")

    logger = AuditLogger()

    # Nhận diện định dạng file (CSV, XLSX, JSON)
    if args.data.endswith(".csv"):
        from agent.data_parsers import DataIngestionEngine
        data_dict = DataIngestionEngine.parse_csv_file(args.data)
        agent = ExpansionDecisionAgent(raw_data_dict=data_dict, logger=logger)
    elif args.data.endswith(".xlsx"):
        from agent.data_parsers import DataIngestionEngine
        data_dict = DataIngestionEngine.parse_xlsx_file(args.data)
        agent = ExpansionDecisionAgent(raw_data_dict=data_dict, logger=logger)
    else:
        agent = ExpansionDecisionAgent(data_bundle_path=args.data, logger=logger)

    print("[*] Đang khởi động Agentic Pipeline...")
    print("    -> Kỹ năng 1: Thẩm định Dữ kiện & Khử trùng lặp nguồn (FactVerificationSkill)")
    print("    -> Kỹ năng 2: Phân tích Tương thích Giải pháp & Năng lực Onsite (FitGapAnalysisSkill)")
    print("    -> Kỹ năng 3: Chấm điểm Ma trận Đa tiêu chí & Ràng buộc cứng (MultiCriteriaScorerSkill)")
    print("    -> Kỹ năng 4: Tách bạch Fact vs Inference, Tạo Kế hoạch Khảo sát (ReportGenerator)")

    results = agent.run_pipeline()

    print("\n[✔] Pipeline thực thi hoàn tất! Tóm tắt kết quả:")
    print("-" * 80)
    
    selected = results["selected_territories"]
    unselected = results["unselected_territories"]

    print("★ 2 ĐỊA BÀN ĐƯỢC CHỌN ĐỂ KHẢO SÁT TIẾP TỤC:")
    for idx, s in enumerate(selected, 1):
        t = s["territory"]
        sc = s["score_res"]
        print(f"  {idx}. {t['name']} - Tổng điểm: {sc['total_score']}/100")

    print("\n✖ CÁC ĐỊA BÀN CHƯA ƯU TIÊN / BỊ LOẠI:")
    for u in unselected:
        t = u["territory"]
        sc = u["score_res"]
        reason = ", ".join(sc["exclusion_reasons"]) if sc["is_excluded"] else f"Điểm không cạnh tranh ({sc['total_score']}/100)"
        print(f"  - {t['name']}: {reason}")

    if results["hitl_flags"]:
        print("\n⚠️ CẢNH BÁO CON NGƯỜI CẦN XỬ LÝ (HITL GATE):")
        for flag in results["hitl_flags"]:
            print(f"  * {flag}")

    # Sinh báo cáo chi tiết
    report_content = agent.generate_management_report(results)
    
    # Lưu báo cáo
    os.makedirs("reports", exist_ok=True)
    report_file = args.output_report or os.path.join(
        "reports", f"expansion_report_{os.path.basename(args.data).replace('.json', '')}.md"
    )
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_content)

    print("\n" + "=" * 80)
    print(f"[✔] Đã xuất Báo cáo hoàn chỉnh gửi Trưởng phòng: {report_file}")
    print(f"[✔] Đã lưu Nhật ký truy vết thực thi (Audit Log): {results['audit_summary']['log_file']}")
    print("=" * 80)

if __name__ == "__main__":
    main()

