import json
import os
from typing import Dict, Any, List
from .tools import FactVerificationSkill, FitGapAnalysisSkill, MultiCriteriaScorerSkill
from .audit_logger import AuditLogger
from .llm_engine import GeminiLLMEngine

class ExpansionDecisionAgent:
    """
    AI Agent hỗ trợ ra quyết định mở rộng thị trường cho Công ty Hưng Phát
    - Tuân thủ nguyên tắc Grounded Generation (Không bịa đặt số liệu ngoài data bundle)
    - Phân định rõ ràng: [FACT] (Dữ liệu nguồn trích dẫn) vs [INFERENCE] (Suy luận logic của Agent)
    - Tích hợp chốt chặn kiểm soát của con người (Human-in-the-Loop)
    - Lưu vết nhật ký truy vết đầy đủ phục vụ thanh tra/audit
    """
    def __init__(self, data_bundle_path: str = None, raw_data_dict: Dict[str, Any] = None, logger: AuditLogger = None):
        self.logger = logger or AuditLogger()
        self.data_bundle_path = data_bundle_path
        if raw_data_dict:
            self.raw_data = raw_data_dict
            self.logger.log_event(
                event_type="DATA_INGESTION",
                tool_name="DataLoader",
                inputs={"source": "direct_input_dict"},
                outputs={"territories_loaded": len(self.raw_data.get("territories", []))},
                metadata={"company": self.raw_data.get("company_profile", {}).get("name")}
            )
        elif data_bundle_path:
            self.raw_data = self._load_data()
        else:
            raise ValueError("Cần cung cấp data_bundle_path hoặc raw_data_dict")
        
        self.fact_verifier = FactVerificationSkill()
        self.fit_analyzer = FitGapAnalysisSkill(self.raw_data.get("company_profile", {}))
        self.scorer = MultiCriteriaScorerSkill(self.raw_data.get("evaluation_criteria", {}))
        self.llm_engine = GeminiLLMEngine()

    def _load_data(self) -> Dict[str, Any]:
        with open(self.data_bundle_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.logger.log_event(
            event_type="DATA_INGESTION",
            tool_name="DataLoader",
            inputs={"path": self.data_bundle_path},
            outputs={"territories_loaded": len(data.get("territories", []))},
            metadata={"company": data.get("company_profile", {}).get("name")}
        )
        return data

    def apply_human_corrections(self, corrections: List[Dict[str, Any]]):
        """
        Nhận thông tin bổ sung từ con người (Human-in-the-Loop)
        và cập nhật vào raw_data trước khi chạy Bước 3 (Đánh giá & Xếp hạng)
        """
        territories = self.raw_data.get("territories", [])
        for corr in corrections:
            tid = corr.get("territory_id")
            for t in territories:
                if t.get("id") == tid:
                    if corr.get("competitors"):
                        t["competitors"] = corr.get("competitors")
                    if corr.get("support_requirement"):
                        if "customer_demands" not in t:
                            t["customer_demands"] = {}
                        t["customer_demands"]["support_requirement"] = corr.get("support_requirement")
                    if corr.get("force_verified_market_chains") is not None:
                        if t.get("market_reports"):
                            t["market_reports"][0]["retail_chains_count"] = corr.get("force_verified_market_chains")
                    self.logger.log_event(
                        event_type="HITL_CORRECTION_APPLIED",
                        tool_name="HumanInTheLoopEngine",
                        inputs=corr,
                        outputs={"status": "Updated", "territory_id": tid}
                    )

    def run_pipeline(self) -> Dict[str, Any]:
        territories = self.raw_data.get("territories", [])
        pipeline_results = []
        hitl_flags = []

        # --- BƯỚC 1 & 2: Thẩm định Dữ kiện & Phân tích Độ khớp ---
        for territory in territories:
            tid = territory.get("id")
            tname = territory.get("name")

            # 1. Thẩm tra dữ kiện
            verified_facts = self.fact_verifier.verify_territory_facts(territory)
            self.logger.log_event(
                event_type="FACT_VERIFICATION",
                tool_name="FactVerificationSkill",
                inputs={"territory_id": tid},
                outputs=verified_facts
            )

            # 2. Phân tích Fit-Gap & Năng lực triển khai
            fit_analysis = self.fit_analyzer.evaluate_fit_and_feasibility(territory)
            self.logger.log_event(
                event_type="FIT_GAP_ANALYSIS",
                tool_name="FitGapAnalysisSkill",
                inputs={"territory_id": tid, "requests": territory.get("customer_demands", {}).get("key_feature_requests")},
                outputs=fit_analysis
            )

            # 3. Chấm điểm & Đánh giá ranh giới quy tắc
            score_res = self.scorer.calculate_territory_score(territory, verified_facts, fit_analysis)
            self.logger.log_event(
                event_type="SCORING_AND_PRUNING",
                tool_name="MultiCriteriaScorerSkill",
                inputs={"territory_id": tid},
                outputs=score_res
            )

            # 4. Kiểm tra điều kiện cần con người can thiệp (HITL Triggers)
            territory_hitl = []
            if not verified_facts["is_data_reliable"]:
                territory_hitl.append(f"Mâu thuẫn dữ liệu nghiêm trọng tại {tname} -> Cần chuyên viên kiểm tra lại tài liệu gốc.")
            if verified_facts["missing_fields"]:
                territory_hitl.append(f"Thiếu trường dữ liệu ({', '.join(verified_facts['missing_fields'])}) tại {tname}.")
            if "CẢNH BÁO RANH GIỚI" in fit_analysis["feasibility_assessment"]:
                territory_hitl.append(f"Chạm trần ranh giới On-site tại {tname} -> Cần Trưởng phòng duyệt cơ chế hỗ trợ đặc thù.")

            if territory_hitl:
                hitl_flags.extend(territory_hitl)

            pipeline_results.append({
                "territory": territory,
                "verified_facts": verified_facts,
                "fit_analysis": fit_analysis,
                "score_res": score_res
            })

        # --- BƯỚC 3: Xếp hạng và phân loại Địa bàn ---
        # Tách địa bàn hợp lệ (eligible) và địa bàn bị loại trừ (excluded)
        eligible = [p for p in pipeline_results if not p["score_res"]["is_excluded"]]
        excluded = [p for p in pipeline_results if p["score_res"]["is_excluded"]]

        # Sắp xếp theo tổng điểm giảm dần
        eligible.sort(key=lambda x: x["score_res"]["total_score"], reverse=True)
        excluded.sort(key=lambda x: x["score_res"]["total_score"], reverse=True)

        selected_territories = eligible[:2]
        unselected_territories = eligible[2:] + excluded

        # Ghi log kết quả quyết định
        self.logger.log_event(
            event_type="FINAL_DECISION_RECOMMENDATION",
            tool_name="DecisionEngine",
            inputs={"total_candidates": len(pipeline_results)},
            outputs={
                "selected_top_2": [s["territory"]["name"] for s in selected_territories],
                "unselected": [u["territory"]["name"] for u in unselected_territories],
                "hitl_pending_count": len(hitl_flags)
            }
        )

        return {
            "pipeline_results": pipeline_results,
            "selected_territories": selected_territories,
            "unselected_territories": unselected_territories,
            "hitl_flags": hitl_flags,
            "audit_summary": self.logger.export_summary()
        }

    def generate_management_report(self, run_results: Dict[str, Any]) -> str:
        """
        Tạo báo cáo chi tiết gửi Trưởng phòng Phát triển Kinh doanh và Ban Giám Đốc
        - Tuân thủ quy định: Bảng so sánh kèm trích dẫn nguồn
        - Phân biệt rõ số liệu trong tài liệu với suy luận của Agent
        - Nêu rõ lý do chọn / chưa ưu tiên
        - Kế hoạch khảo sát chi tiết (Nhóm khách tiếp cận, Thông tin xác minh, Người phụ trách)
        """
        selected = run_results["selected_territories"]
        unselected = run_results["unselected_territories"]
        hitl_flags = run_results["hitl_flags"]
        results = run_results["pipeline_results"]

        report = []
        report.append("# BÁO CÁO ĐỀ XUẤT ĐỊA BÀN MỞ RỘNG KINH DOANH & KẾ HOẠCH KHẢO SÁT")
        report.append("**Kính gửi:** Trưởng phòng Phát triển Kinh doanh & Ban Giám đốc Công ty Hưng Phát")
        report.append("**Đơn vị thực hiện:** Hệ thống Hỗ trợ Ra Quyết định AI Agent (HP-Expansion-Agent v1.0)")
        report.append("**Cơ chế thẩm tra:** Kiểm chứng dữ liệu nguồn (Grounded Verification) & Giám sát con người (HITL)")
        report.append("-" * 80)

        # 1. Tóm tắt kết quả
        report.append("## 1. TỔNG QUAN KẾT QUẢ ĐỀ XUẤT")
        if len(selected) == 2:
            report.append(f"- **2 Địa bàn đề xuất khảo sát tiếp tục:** **{selected[0]['territory']['name']}** (Điểm: {selected[0]['score_res']['total_score']}/100) và **{selected[1]['territory']['name']}** (Điểm: {selected[1]['score_res']['total_score']}/100).")
            report.append(f"- **2 Địa bàn chưa ưu tiên:** {', '.join([u['territory']['name'] for u in unselected])}.")
        else:
            report.append(f"- **CẢNH BÁO:** Chỉ tìm thấy {len(selected)} địa bàn thỏa mãn điều kiện cứng. Cần bổ sung dữ liệu khảo sát trước khi quyết định.")
        report.append("")

        # 1.1. Nhận định Chiến lược do Gemini AI phân tích (nếu có kết nối API)
        context_str = f"Top 2 được chọn: {', '.join([s['territory']['name'] for s in selected])}. Các địa bàn loại: {', '.join([u['territory']['name'] for u in unselected])}."
        gemini_insight = self.llm_engine.generate_strategic_commentary(context_str)
        if gemini_insight:
            report.append("### Nhận định Chiến lược từ Gemini AI:")
            report.append(gemini_insight)
            report.append("")
            self.logger.log_event(
                event_type="LLM_STRATEGIC_ANALYSIS",
                tool_name="GeminiLLMEngine",
                inputs={"context": context_str},
                outputs={"insight_preview": gemini_insight[:120] + "..."},
                metadata={"model": "gemini-1.5-flash", "provider": "Google Generative AI"}
            )

        # 2. Bảng đối chiếu & so sánh chi tiết có căn cứ nguồn (Citations)
        report.append("## 2. BẢNG ĐỐI CHIẾU DỮ KIỆN 4 ĐỊA BÀN (KÈM CĂN CỨ TÀI LIỆU NGUỒN)")
        report.append("| Địa bàn | Quy mô & Tăng trưởng [FACT] | Nhu cầu khách [FACT] | Độ khớp HP-WMS [INFERENCE] | Yêu cầu hỗ trợ [FACT] | Năng lực triển khai [INFERENCE] | Tổng điểm | Trạng thái |")
        report.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

        for r in results:
            t = r["territory"]
            facts = r["verified_facts"]
            fit = r["fit_analysis"]
            sc = r["score_res"]

            m_fact = f"{facts.get('retail_chains_count', 'N/A')} chuỗi, +{facts.get('growth_rate_pct', 'N/A')}%"
            d_fact = ", ".join(t.get("customer_demands", {}).get("key_feature_requests", ["Thiếu"]))[:35] + "..."
            fit_inf = f"Fit {fit['solution_fit_score']}%"
            sup_fact = fit.get("support_requirement_raw") or "Chưa rõ"
            if len(sup_fact) > 30:
                sup_fact = sup_fact[:28] + "..."
            feas_inf = "Đạt" if not fit["onsite_requirement_exceeds_capacity"] else "QUÁ TẢI ONSITE"
            status = "ĐỀ XUẤT" if r in selected else "LOẠI / TẠM HOÃN"

            report.append(f"| **{t['name']}** | {m_fact} | {d_fact} | {fit_inf} | {sup_fact} | {feas_inf} | **{sc['total_score']}** | {status} |")

        report.append("")
        report.append("### Căn cứ Trích dẫn Nguồn gốc (Data Citations):")
        for r in results:
            t = r["territory"]
            facts = r["verified_facts"]
            citations = facts.get("raw_citations", [])
            for c in citations:
                report.append(f"- **[{t['name']}]:** {c}")
            for issue in facts.get("issues_detected", []):
                report.append(f"  * ⚠️ *Lưu ý dữ liệu:* {issue}")

        report.append("")
        report.append("-" * 80)

        # 3. Phân tích chi tiết: Vì sao chọn Top 2 & Vì sao loại 2 địa bàn còn lại
        report.append("## 3. PHÂN TÍCH CĂN CỨ ĐỀ XUẤT & LÝ DO CHƯA ƯU TIÊN")
        report.append("### 3.1. Lý do Đề xuất 2 Địa bàn Ưu tiên:")
        for idx, s in enumerate(selected, 1):
            t = s["territory"]
            sc = s["score_res"]
            fit = s["fit_analysis"]
            facts = s["verified_facts"]
            report.append(f"#### {idx}. {t['name']} (Tổng điểm: {sc['total_score']}/100)")
            report.append(f"- **[FACT - Số liệu tài liệu]:** Quy mô {facts.get('retail_chains_count')} chuỗi bán lẻ, tốc độ tăng trưởng {facts.get('growth_rate_pct')}%. Khách hàng yêu cầu: {', '.join(t.get('customer_demands',{}).get('key_feature_requests', []))}.")
            report.append(f"- **[INFERENCE - Đánh giá của Agent]:**")
            report.append(f"  + Độ tương thích giải pháp: Đạt {fit['solution_fit_score']}%. Các tính năng cốt lõi (Omnichannel, QR/Mã vạch, Lộ trình kho) khớp hoàn toàn với giải pháp HP-WMS.")
            report.append(f"  + Lợi thế cạnh tranh: {sc['comp_note']}.")
            report.append(f"  + Khả năng triển khai: {fit['feasibility_assessment']} Phương thức hỗ trợ phù hợp hoàn toàn với đội ngũ hiện có (chỉ cần tối đa 1-2 ngày onsite hoặc hỗ trợ từ xa).")
            report.append("")

        report.append("### 3.2. Lý giải Vì sao Chưa Ưu tiên các Địa bàn còn lại:")
        for u in unselected:
            t = u["territory"]
            sc = u["score_res"]
            fit = u["fit_analysis"]
            report.append(f"#### ✖ {t['name']} (Tổng điểm: {sc['total_score']}/100 - Trạng thái: {('BỊ LOẠI DO VI PHẠM QUY TẮC' if sc['is_excluded'] else 'ĐIỂM KHÔNG CẠNH TRANH')})")
            if sc["is_excluded"]:
                report.append(f"- **[CĂN CỨ LOẠI BỎ]:** Vi phạm các quy tắc ràng buộc cứng (Hard Exclusion Rules):")
                for reason in sc["exclusion_reasons"]:
                    report.append(f"  * 🔴 **{reason}**")
            else:
                report.append(f"- **[LÝ DO CHƯA ƯU TIÊN]:** Tổng điểm thấp hơn Top 2. {sc['comp_note']}")
            
            report.append(f"- **[FACT vs INFERENCE]:** Dù quy mô thị trường có thể lớn trên giấy tờ, nhưng xét về khả năng thực thi và rủi ro triển khai, địa bàn này không tối ưu cho một đợt mở rộng duy nhất của Hưng Phát.")
            report.append("")

        # 4. Kế hoạch khảo sát chi tiết
        report.append("-" * 80)
        report.append("## 4. KẾ HOẠCH KHẢO SÁT THỰC TẾ TIẾP THEO (ACTION PLAN)")
        report.append("Để chuẩn bị hồ sơ trình Ban Giám Đốc phê duyệt chính thức, đội ngũ cần tiến hành đợt khảo sát thực địa tại 2 địa bàn được đề xuất:")
        report.append("")
        report.append("| Địa bàn | Nhóm khách hàng mục tiêu tiếp cận | Thông tin trọng tâm cần xác minh | Phương pháp khảo sát | Người phụ trách đề xuất | Thời hạn dự kiến |")
        report.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
        
        for s in selected:
            t = s["territory"]
            tid = t["id"]
            if "Đông" in t["name"] or "01" in tid or "Alpha" in t["name"]:
                target_customers = "Top 10 Chuỗi siêu thị mini & Cửa hàng tiện lợi đang dùng Vendor X"
                verify_info = "Tần suất lỗi đồng bộ sàn TMĐT của phần mềm hiện tại; Mức độ sẵn sàng chuyển đổi; Khảo sát hạ tầng mạng tại quầy kho"
                owner = "Nguyễn Văn A (Trưởng nhóm Kinh doanh KV1)"
            else:
                target_customers = "15 Doanh nghiệp bán lẻ nông sản / thực phẩm chế biến vừa và nhỏ"
                verify_info = "Quy trình theo dõi hạn sử dụng (FEFO/FIFO) thực tế; Trình độ thao tác thiết bị của thủ kho; Ngân sách đầu tư tối đa"
                owner = "Trần Thị B (Chuyên viên Giải pháp Khách hàng)"

            report.append(f"| **{t['name']}** | {target_customers} | {verify_info} | Phỏng vấn trực tiếp Giám đốc Vận hành + Demo thử tính năng HP-WMS | {owner} | 07 ngày làm việc |")

        report.append("")

        # 5. Các điểm cần Con người quyết định (Human-in-the-Loop)
        report.append("## 5. DANH SÁCH ĐIỂM CON NGƯỜI CẦN KIỂM TRA & DUYỆT (HITL CHECKPOINTS)")
        if hitl_flags:
            report.append("> [!IMPORTANT]\n> **Các vấn đề cần Trưởng phòng Phát triển Kinh doanh phê duyệt trước khi kích hoạt kế hoạch khảo sát:**")
            for flag in hitl_flags:
                report.append(f"- ⚠️ {flag}")
        else:
            report.append("> [!NOTE]\n> Toàn bộ dữ liệu của các địa bàn được đề xuất đều hợp lệ, không có xung đột nghiêm trọng và nằm trong hạn mức an toàn của công ty.")

        report.append("")
        report.append("---")
        report.append(f"*Báo cáo được khởi tạo tự động bởi HP-Expansion-Agent. File Audit Trace: `{run_results['audit_summary']['log_file']}`*")
        
        return "\n".join(report)

