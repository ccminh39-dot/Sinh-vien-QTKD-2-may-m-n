# HP-Expansion-Agent: AI Agent Đánh Giá Thị Trường Mở Rộng Kinh Doanh
**Học phần:** AI301 | **Đề số:** 04  
**Doanh nghiệp giả định:** Công ty Cổ phần Giải pháp Công nghệ Hưng Phát (Giải pháp quản lý kho HP-WMS cho chuỗi bán lẻ)

---

## 📌 1. Cấu trúc Thư mục Dự án

```
hungphat_expansion_agent/
├── data/
│   ├── dataset_standard.json       # Kịch bản 1: Dữ liệu thông thường (4 địa bàn)
│   ├── dataset_missing_info.json   # Kịch bản 2: Dữ liệu thiếu thông tin / mâu thuẫn
│   └── dataset_boundary_case.json  # Kịch bản 3: Dữ liệu chạm trần ranh giới quy tắc
├── agent/
│   ├── __init__.py
│   ├── tools.py                    # 3 Kỹ năng nghiệp vụ phối hợp (FactVerification, FitGap, Scorer)
│   ├── audit_logger.py             # Module ghi nhật ký truy vết (Audit Trail & Execution Trace)
│   └── expansion_agent.py          # AI Agent điều phối quy trình tự động & HITL
├── tests/
│   └── test_cases.py               # Bộ kiểm thử tự động 3 kịch bản theo yêu cầu đề bài
├── reports/                        # Nơi lưu báo cáo Markdown xuất tự động cho Ban Giám đốc
├── logs/                           # Nơi lưu vết JSON Lines toàn bộ thao tác Agent và công cụ
├── run_agent.py                    # Script chạy chính thức (Entrypoint nạp dữ liệu tại buổi thi)
└── README.md                       # Tài liệu hướng dẫn hệ thống
```

---

## 🚀 2. Hướng dẫn Chạy Chương trình tại Buổi Thi

### 2.1. Chạy với Bộ Dữ liệu Mặc định (hoặc Bộ Dữ liệu Mới của Giảng viên):
Giảng viên chỉ cần đặt file JSON dữ liệu mới và chạy lệnh:
```bash
python run_agent.py --data path/to/new_dataset.json
```
*(Nếu dùng môi trường Python máy thi, chỉ cần chỉ định đúng đường dẫn file dữ liệu JSON).*

### 2.2. Chạy Bộ Kiểm thử Tự động (Automated Test Suite - 3 Kịch bản):
```bash
python tests/test_cases.py
```
Kết quả kiểm thử sẽ kiểm tra tự động:
- **Case 1 (Thông thường):** Lọc số liệu trùng, loại địa bàn đòi hỏi Onsite 24/7 và chọn đúng 2 địa bàn tốt nhất.
- **Case 2 (Thiếu dữ liệu / Mâu thuẫn):** Phát hiện thiếu hồ sơ đối thủ, thiếu yêu cầu hỗ trợ, phát hiện chênh lệch mâu thuẫn >30% và kích hoạt cờ HITL.
- **Case 3 (Ranh giới quy tắc):** Bắt đúng ngưỡng sàn fit_score 60.0 và cảnh báo chạm trần hỗ trợ On-site cho cấp quản lý duyệt.

---

## 🔍 3. Quy chuẩn Dữ liệu Đầu vào (Data Schema)
Bộ dữ liệu gồm các trường JSON chuẩn:
```json
{
  "company_profile": { ... },       // Năng lực HP-WMS và chính sách triển khai
  "evaluation_criteria": { ... },   // Trọng số tiêu chí & Quy tắc loại trừ cứng (Exclusion Rules)
  "territories": [                  // Danh sách 4 địa bàn khảo sát
    {
      "id": "TERR_01",
      "name": "Tên địa bàn",
      "market_reports": [ ... ],    // Nguồn, kỳ thống kê, số lượng chuỗi, dung lượng thị trường
      "competitors": [ ... ],       // Danh sách đối thủ, thị phần, ưu/nhược điểm
      "customer_demands": { ... }   // Mẫu khảo sát, tính năng yêu cầu, hình thức hỗ trợ on-site/remote
    }
  ]
}
```

---

## 🛡️ 4. Cơ chế Đảm bảo Minh bạch & Tránh Hallucination
- **Phân tách rạch ròi [FACT] vs [INFERENCE]:** Số liệu thị trường bắt buộc trích dẫn từ tài liệu nguồn; suy luận của Agent được gắn nhãn riêng.
- **Nhật ký truy vết (Audit Trail):** Mỗi lượt gọi tool được ghi lại trong `logs/audit_trace_*.jsonl` với timestamp, inputs, outputs, và quy tắc áp dụng.
- **Human-in-the-Loop (HITL):** Các trường hợp rủi ro cao hoặc thiếu căn cứ đều được chuyển thành Cờ cảnh báo (Flags) cho Trưởng phòng phê duyệt trước khi hành động.

