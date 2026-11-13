from typing import Dict, Any, List, Tuple
import re

class FactVerificationSkill:
    """
    Kỹ năng 1: Thẩm định & Chuẩn hóa Dữ kiện (Fact Verification & Cleaning)
    - Loại bỏ số liệu lặp do cùng nguồn gốc.
    - Phát hiện kỳ thống kê lỗi thời hoặc mâu thuẫn giữa các nguồn.
    - Phát hiện các trường thông tin bị thiếu.
    - Lưu lại căn cứ trích dẫn (Citations).
    """
    def __init__(self, current_year: int = 2024):
        self.current_year = current_year

    def verify_territory_facts(self, territory: Dict[str, Any]) -> Dict[str, Any]:
        tid = territory.get("id")
        tname = territory.get("name")
        market_reports = territory.get("market_reports", [])
        competitors = territory.get("competitors", [])
        customer_demands = territory.get("customer_demands", {})

        verified_data = {
            "id": tid,
            "name": tname,
            "citations": [],
            "issues_detected": [],
            "missing_fields": [],
            "retail_chains_count": None,
            "estimated_market_value": None,
            "growth_rate_pct": None,
            "is_data_reliable": True,
            "raw_citations": []
        }

        # 1. Kiểm tra thiếu trường dữ liệu
        if not market_reports:
            verified_data["missing_fields"].append("market_reports")
        if not competitors:
            verified_data["missing_fields"].append("competitors (chưa có hồ sơ đối thủ)")
        if not customer_demands:
            verified_data["missing_fields"].append("customer_demands (chưa có phản hồi khách hàng)")
        elif not customer_demands.get("support_requirement"):
            verified_data["missing_fields"].append("customer_demands.support_requirement (thiếu yêu cầu hỗ trợ)")

        # 2. Xử lý trùng lặp nguồn & mâu thuẫn số liệu báo cáo
        unique_sources = set()
        verified_reports = []

        for report in market_reports:
            source = report.get("source", "Không rõ nguồn")
            period = str(report.get("period", ""))
            
            # Kiểm tra trích dẫn lặp lại nguồn gốc
            note = report.get("note", "").lower()
            if "dẫn lại nguồn" in note or "trùng lặp" in note:
                verified_data["issues_detected"].append(
                    f"Cảnh báo trùng lặp: Báo cáo '{source}' sao chép số liệu từ nguồn gốc trước đó, không tính cộng dồn."
                )
                continue

            if source in unique_sources:
                verified_data["issues_detected"].append(f"Trùng lặp nguồn báo cáo: {source}")
                continue

            unique_sources.add(source)
            verified_reports.append(report)

            # Cảnh báo kỳ thống kê cũ
            try:
                period_year = int(re.search(r"\d{4}", period).group())
                if self.current_year - period_year >= 2:
                    verified_data["issues_detected"].append(
                        f"Kỳ thống kê cũ ({period_year}): Cần thẩm tra lại trước khi chốt, nguy cơ sai lệch số liệu hiện tại."
                    )
            except Exception:
                pass

        # Kiểm tra mâu thuẫn nếu có >= 2 báo cáo độc lập
        if len(verified_reports) >= 2:
            val1 = verified_reports[0].get("retail_chains_count")
            val2 = verified_reports[1].get("retail_chains_count")
            if val1 and val2 and abs(val1 - val2) / max(val1, val2) > 0.3:
                verified_data["issues_detected"].append(
                    f"MÂU THUẪN NGHIÊM TRỌNG: Hai nguồn độc lập báo cáo số lượng chuỗi chênh lệch > 30% ({val1} vs {val2})."
                )
                verified_data["is_data_reliable"] = False

        # Chọn báo cáo mới nhất làm căn cứ Fact
        if verified_reports:
            primary_report = verified_reports[0]
            verified_data["retail_chains_count"] = primary_report.get("retail_chains_count")
            verified_data["estimated_market_value"] = primary_report.get("estimated_market_value_vnd")
            raw_growth = str(primary_report.get("annual_growth_rate", "0%"))
            try:
                verified_data["growth_rate_pct"] = float(raw_growth.replace("%", "").strip())
            except ValueError:
                verified_data["growth_rate_pct"] = 0.0

            verified_data["raw_citations"].append(
                f"Nguồn: {primary_report.get('source')} (Kỳ: {primary_report.get('period')}) - "
                f"Quy mô: {verified_data['retail_chains_count']} chuỗi, Giá trị: {verified_data['estimated_market_value']}, Tăng trưởng: {raw_growth}"
            )

        return verified_data


class FitGapAnalysisSkill:
    """
    Kỹ năng 2: Phân tích Mức độ tương thích Giải pháp & Khả năng triển khai
    (Solution Fit & Operational Feasibility)
    - Đối chiếu tính năng khách hàng yêu cầu vs tính năng HP-WMS có thể đáp ứng.
    - Đối chiếu yêu cầu hỗ trợ Onsite/SLA vs chính sách và năng lực triển khai thực tế.
    """
    def __init__(self, company_profile: Dict[str, Any]):
        self.profile = company_profile
        self.core_caps = [c.lower() for c in company_profile.get("core_capabilities", [])]
        self.unsupported_caps = [u.lower() for u in company_profile.get("unsupported_capabilities", [])]
        self.capacity_policy = company_profile.get("deployment_capacity", {})

    def evaluate_fit_and_feasibility(self, territory: Dict[str, Any]) -> Dict[str, Any]:
        demands = territory.get("customer_demands", {})
        requests = demands.get("key_feature_requests", [])
        support_req = demands.get("support_requirement") or ""

        # 1. Tính toán Solution Fit
        matched_caps = []
        unmatched_caps = []
        critical_unsupported = []

        if not requests:
            fit_score = 40.0 # Thiếu dữ liệu đánh giá
        else:
            total_req = len(requests)
            match_count = 0
            for req in requests:
                req_lower = req.lower()
                # Kiểm tra xem có rơi vào unsupported không
                is_unsupported = any(unsup in req_lower or any(word in req_lower for word in unsup.split() if len(word) > 4) 
                                     for unsup in ["kho lạnh robotized", "siêu trọng", "robotized", "heavy sorting"])
                if is_unsupported:
                    critical_unsupported.append(req)
                    continue

                # Kiểm tra xem có match core capabilities không
                is_matched = any(
                    keyword in req_lower for keyword in ["tồn kho", "omnichannel", "đa kênh", "mã vạch", "qr", "lộ trình", "pos", "hạn dùng", "nông sản", "lấy hàng"]
                )
                if is_matched:
                    match_count += 1
                    matched_caps.append(req)
                else:
                    unmatched_caps.append(req)

            fit_score = round((match_count / total_req) * 100.0, 1)

        # 2. Đánh giá Khả năng triển khai (Operational Feasibility) & Ràng buộc cứng Onsite
        support_lower = support_req.lower()
        onsite_overload = False
        feasibility_score = 80.0
        feasibility_note = "Phù hợp năng lực triển khai hiện tại của Hưng Phát."

        if not support_req:
            feasibility_score = 50.0
            feasibility_note = "Thiếu thông tin yêu cầu hỗ trợ tại chỗ, chưa đủ cơ sở đánh giá độ sẵn sàng triển khai."
        elif "24/7" in support_lower or "túc trực" in support_lower or "15 phút" in support_lower:
            onsite_overload = True
            feasibility_score = 15.0
            feasibility_note = "VI PHẠM NĂNG LỰC: Yêu cầu trực On-site 24/7 tức thì vượt quá quy mô đội ngũ (chỉ có 4 kỹ sư, chưa có chi nhánh tại chỗ)."
        elif "2 tuần" in support_lower or "liên tục" in support_lower:
            # Sát ranh giới năng lực (Boundary case)
            feasibility_score = 60.0
            feasibility_note = "CẢNH BÁO RANH GIỚI: Yêu cầu 2 kỹ sư onsite liên tục 2 tuần chạm trần năng lực của công ty, cần Trưởng phòng duyệt phương án dự phòng."
        elif "onsite 1-2 ngày" in support_lower or "online" in support_lower or "hành chính" in support_lower or "từ xa" in support_lower or "1 buổi" in support_lower or "2 ngày" in support_lower:
            feasibility_score = 95.0
            feasibility_note = "Hoàn toàn phù hợp mô hình chuyển giao từ xa kết hợp Onsite ngắn hạn."

        return {
            "solution_fit_score": fit_score,
            "matched_capabilities": matched_caps,
            "critical_unsupported": critical_unsupported,
            "operational_feasibility_score": feasibility_score,
            "onsite_requirement_exceeds_capacity": onsite_overload,
            "feasibility_assessment": feasibility_note,
            "support_requirement_raw": support_req
        }


class MultiCriteriaScorerSkill:
    """
    Kỹ năng 3: Chấm điểm Ma trận & Phân loại Đề xuất (Multi-Criteria Scorer)
    - Tính điểm tổng hợp theo trọng số chuẩn.
    - Áp dụng các quy tắc loại trừ nghiêm ngặt (Hard Exclusion Rules).
    - Phân tách rõ ràng giữa Top 2 Đề xuất & Các địa bàn Chưa ưu tiên.
    """
    def __init__(self, criteria_config: Dict[str, Any]):
        self.weights = criteria_config.get("weights", {
            "market_size_and_growth": 0.25,
            "solution_fit": 0.30,
            "competitive_advantage": 0.20,
            "operational_feasibility": 0.25
        })
        self.exclusion_rules = criteria_config.get("exclusion_rules", [])

    def calculate_territory_score(self, territory_data: Dict[str, Any], 
                                  verified_facts: Dict[str, Any], 
                                  fit_analysis: Dict[str, Any]) -> Dict[str, Any]:
        
        # 1. Điểm Thị trường & Tăng trưởng (0 - 100)
        chains = verified_facts.get("retail_chains_count") or 0
        growth = verified_facts.get("growth_rate_pct") or 0.0
        
        # Normalize: Giả định chuẩn 100 chuỗi = 70 điểm; Tăng trưởng 20% = 30 điểm
        market_score = min(70.0, (chains / 120.0) * 70.0) + min(30.0, (growth / 25.0) * 30.0)
        market_score = round(market_score, 1)

        # 2. Điểm Khớp giải pháp
        fit_score = fit_analysis.get("solution_fit_score", 0.0)

        # 3. Điểm Lợi thế cạnh tranh (Đánh giá mức độ áp đảo của đối thủ)
        competitors = territory_data.get("competitors", [])
        if not competitors:
            comp_score = 40.0 # Thiếu dữ liệu đối thủ
            comp_note = "Thiếu thông tin đối thủ cạnh tranh trên địa bàn."
        else:
            # Kiểm tra xem có đối thủ thống trị độc quyền không
            has_dominant_vendor = any(float(str(c.get("market_share", "0")).replace("%","")) >= 60 for c in competitors)
            if has_dominant_vendor:
                comp_score = 35.0
                comp_note = "Thị trường bị chi phối bởi đối thủ thống trị lớn, rào cản chuyển đổi rất cao."
            else:
                comp_score = 85.0
                comp_note = "Thị trường phân mảnh hoặc đối thủ có nhiều nhược điểm (phần mềm cũ, hay lỗi đồng bộ)."

        # 4. Điểm Khả thi triển khai
        feasibility_score = fit_analysis.get("operational_feasibility_score", 50.0)

        # 5. Kiểm tra Quy tắc loại trừ cứng (Exclusion Rules)
        exclusion_triggered = []
        if fit_analysis.get("onsite_requirement_exceeds_capacity", False):
            exclusion_triggered.append("RULE_EXCLUDE_ONSITE_OVERLOAD: Yêu cầu Onsite 24/7 vượt quá năng lực phục vụ")
        if fit_score < 60.0:
            exclusion_triggered.append(f"RULE_MINIMUM_FIT_SCORE: Điểm tương thích giải pháp ({fit_score}) dưới ngưỡng 60/100")

        # 6. Tính điểm tổng hợp (Weighted Score)
        total_score = (
            market_score * self.weights["market_size_and_growth"] +
            fit_score * self.weights["solution_fit"] +
            comp_score * self.weights["competitive_advantage"] +
            feasibility_score * self.weights["operational_feasibility"]
        )
        total_score = round(total_score, 2)

        return {
            "territory_id": territory_data.get("id"),
            "territory_name": territory_data.get("name"),
            "market_score": market_score,
            "fit_score": fit_score,
            "comp_score": comp_score,
            "feasibility_score": feasibility_score,
            "total_score": total_score,
            "is_excluded": len(exclusion_triggered) > 0,
            "exclusion_reasons": exclusion_triggered,
            "comp_note": comp_note
        }
