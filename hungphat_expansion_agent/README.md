# HP-Expansion-Agent: AI Agent Thẩm Định Mở Rộng Thị Trường B2B WMS
**Học phần:** AI301 | **Đề số:** 04  
**Doanh nghiệp giả định:** Công ty Cổ phần Giải pháp Công nghệ Hưng Phát (Giải pháp quản lý kho HP-WMS cho chuỗi bán lẻ)

---

## 📌 1. Cấu Trúc Dự Án (Chuẩn Git Repository)

```text
hungphat_expansion_agent/
├── .gitignore                      # Cấu hình bỏ qua tệp rác, venv, cache khi đẩy lên GitHub
├── .env.example                    # Mẫu cấu hình môi trường (API Key Gemini tùy chọn)
├── requirements.txt                # Danh sách thư viện (100% Python Standard Library, không lỗi thiếu thư viện)
├── README.md                       # Hướng dẫn chi tiết triển khai & bảo vệ
├── DEFENSE_GUIDE.md                # Kịch bản bảo vệ trước hội đồng giám khảo
├── run_web_ui.bat                  # [1-Click] Khởi động Giao diện Web trên Windows (Tự nhận diện Python)
├── run_web_ui.ps1                  # Khởi động Giao diện Web bằng PowerShell
├── run_tests.bat                   # [1-Click] Chạy bộ kiểm thử tự động 3 kịch bản
├── run_cli_agent.bat               # [1-Click] Chạy Agent chế độ dòng lệnh CLI
├── run_agent.py                    # Điểm thực thi chính thức của Agent qua CLI
├── web_server.py                   # Máy chủ Web Server đa luồng (Port 8080)
├── agent/                          # Mã nguồn nghiệp vụ AI Agent & State Machine
│   ├── __init__.py
│   ├── config.py                   # Cấu hình tham số hệ thống
│   ├── audit_logger.py             # Truy vết hoạt động (Audit Trail & Grounded Citations)
│   ├── data_parsers.py             # Bộ nạp dữ liệu (Google Sheets, CSV, Excel XLSX, JSON)
│   ├── expansion_agent.py          # Bộ não Agent điều phối thẩm định & HITL
│   ├── llm_engine.py               # Kết nối Gemini AI + Bộ nhận định chiến lược dự phòng
│   ├── tools.py                    # Kỹ năng FactVerification, FitGap & Scorer
│   └── workflow_engine.py          # Động cơ State Machine 5 bước tương tác
├── data/                           # Bộ dữ liệu mẫu chuẩn (CSV, Excel XLSX, JSON)
│   ├── dataset_standard.json       # Kịch bản 1: Chuẩn
│   ├── dataset_missing_info.json   # Kịch bản 2: Thiếu dữ liệu / Cần phản hồi
│   ├── dataset_boundary_case.json  # Kịch bản 3: Ranh giới quy tắc Onsite
│   ├── file_mau_dung_dinh_dang_hungphat.csv   # Mẫu CSV cho người dùng
│   ├── file_mau_dung_dinh_dang_hungphat.xlsx  # Mẫu Excel cho người dùng
│   └── sample_territories.csv      # Bảng 4 địa bàn mẫu
├── logs/                           # Thư mục lưu vết nhật ký thực thi (JSONL)
├── reports/                        # Nơi lưu báo cáo Markdown xuất tự động
├── tests/
│   └── test_cases.py               # Bộ kiểm thử tự động 3 ca kiểm thử
└── ui/                             # Giao diện Web Editorial Magazine & PDF Guru Dropzone
    ├── index.html                  # Giao diện đơn trang hoàn chỉnh
    └── assets/
        └── hero_bg.jpg             # Ảnh phong cảnh thiên nhiên dãy núi Thụy Sĩ
```

---

## 🚀 2. Hướng Dẫn Clone & Chạy Trên Máy Mới (Không Bị Lỗi)

### 2.1. Yêu Cầu Môi Trường
- **Python:** Phiên bản 3.9 trở lên (Khuyến nghị 3.10, 3.11, 3.12, 3.13).
- **Hệ điều hành:** Windows 10/11, macOS hoặc Linux.
- **Thư viện:** Dự án sử dụng **100% Python Standard Library** (`http.server`, `urllib`, `json`, `zipfile`, `xml.etree`, `re`, `csv`), **KHÔNG bắt buộc cài thêm thư viện ngoài**, đảm bảo chạy ngay trên mọi máy mà không bị lỗi thiếu package.

### 2.2. Khởi Động Giao Diện Web (Khuyến Nghị):
Chỉ cần **nhấp đúp chuột** vào tệp:
👉 **`run_web_ui.bat`**

*Tệp `.bat` đã được trang bị cơ chế tự động dò tìm Python (trong PATH, py launcher, hoặc venv) và tự động mở trình duyệt tại `http://localhost:8080/`.*

### 2.3. Chạy Bằng Dòng Lệnh (CLI):
```bash
# 1. Chạy máy chủ Web
python web_server.py

# 2. Hoặc chạy kiểm thử tự động 3 kịch bản
python tests/test_cases.py

# 3. Hoặc chạy Agent CLI với tệp dữ liệu chỉ định
python run_agent.py --data data/dataset_standard.json
```

---

## 📤 3. Hướng Dẫn Đẩy Lên GitHub & Kéo Về Dự Án Mới

### 3.1. Đẩy Từ Thư Mục Này Lên GitHub:
Mở Terminal / PowerShell tại thư mục `hungphat_expansion_agent`:
```bash
# 1. Khởi tạo Git
git init

# 2. Thêm toàn bộ tệp (đã có .gitignore tự lọc tệp rác)
git add .

# 3. Tạo commit đầu tiên
git commit -m "feat: complete hungphat expansion ai agent with state machine web ui"

# 4. Đổi tên nhánh chính thành main
git branch -M main

# 5. Gắn link repository GitHub của bạn (thay bằng link của bạn)
git remote add origin https://github.com/YOUR_USERNAME/hungphat_expansion_agent.git

# 6. Đẩy mã nguồn lên
git push -u origin main
```

### 3.2. Khi Kéo Về Máy Khác (Clone to New Machine):
```bash
git clone https://github.com/YOUR_USERNAME/hungphat_expansion_agent.git
cd hungphat_expansion_agent

# Nhấp đúp vào run_web_ui.bat là chạy được ngay!
```

---

## 🛡️ 4. Các Quy Chuẩn Nghiệp Vụ Quan Trọng
1. **Bảo Toàn File Gốc:** Hệ thống chỉ đọc dữ liệu từ Google Sheets, CSV hoặc Excel; tuyệt đối không ghi đè, không tự ý sửa đổi tệp gốc của người gửi.
2. **Quy Tắc Ranh Giới On-site (RULE_EXCLUDE_ONSITE_OVERLOAD):** Giới hạn tối đa 4 kỹ sư triển khai, chưa có chi nhánh địa phương, tự động loại trừ địa bàn đòi hỏi Onsite 24/7.
3. **Phân Tách [FACT] và [INFERENCE]:** Mọi số liệu báo cáo đều có căn cứ xuất xứ rõ ràng, chống hiện tượng ảo giác (hallucination).
4. **Human-in-the-Loop (HITL):** Khi phát hiện thiếu dữ liệu hoặc vi phạm chính sách, hệ thống dừng lại kích hoạt ô Feedback cho chuyên viên can thiệp.
