# CẨM NANG THUYẾT TRÌNH & BẢO VỆ ĐỒ ÁN AI301 - ĐỀ SỐ 04
**Đề tài:** Đánh giá thị trường để mở rộng kinh doanh - Công ty Hưng Phát  
**Sản phẩm:** HP-Expansion-Agent (Hệ thống AI Agent Hỗ trợ Ra Quyết định Mở rộng Thị trường)

---

## 🎯 PHẦN 1: KỊCH BẢN LIVE DEMO TẠI BUỔI THI (3-5 PHÚT)

Khi bước vào phòng thi, nhóm thực hiện demo theo 4 bước sau để tạo ấn tượng mạnh nhất với Giảng viên:

### Bước 1: Giới thiệu Tổng quan Kiến trúc (30 giây)
- Mở sơ đồ Workflow trên giao diện Web (`http://localhost:8080`) hoặc trình chiếu ảnh To-Be Process.
- **Lời thoại mẫu:**  
  *"Thưa thầy/cô, hệ thống HP-Expansion-Agent được xây dựng theo kiến trúc Tool-Grounded Pipeline với 5 giai đoạn: từ tiếp nhận đa định dạng (Google Sheets, CSV, Excel), qua 3 kỹ năng nghiệp vụ độc lập có kiểm soát con người (HITL), và xuất kết quả kinh doanh kèm Audit Trail 100% minh bạch."*

### Bước 2: Demo Kịch bản 1 - Trường hợp Thông thường (1 phút)
- Trên giao diện Web, chọn **Kịch bản 1 (Trường hợp Thông thường)** $\rightarrow$ Bấm **"Khởi động AI Agent Đánh Giá"**.
- Điểm cần nhấn mạnh với Giảng viên:
  1. **Khử trùng lặp số liệu:** Chỉ ra rằng Báo cáo Logistics Miền Đông sao chép số liệu từ Báo cáo Bán lẻ 2024 đã được Agent lọc tự động, không tính cộng dồn.
  2. **Loại trừ quá tải Onsite 24/7:** Địa bàn Duyên Hải có quy mô rất lớn (120 chuỗi) nhưng bị loại ngay lập tức vì vi phạm quy tắc ràng buộc cứng về năng lực đội ngũ (chỉ có 4 kỹ sư, chưa có chi nhánh tại chỗ).
  3. **Kết quả Top 2:** Địa bàn Miền Đông (88.55 điểm) và Địa bàn Cao Nguyên (78.55 điểm).

### Bước 3: Demo Kịch bản 2 - Điểm nhấn "Human-in-the-Loop" (1.5 phút)
- Chọn **Kịch bản 2 (Thiếu Dữ liệu & Mâu thuẫn)** $\rightarrow$ Bấm **"Khởi động AI Agent Đánh Giá"**.
- Hệ thống lập tức dừng lại ở Bước 2, đổi trạng thái sang màu vàng và hiển thị khung **"CỬA SỔ KIỂM SOÁT CON NGƯỜI (HITL GATE)"**.
- **Lời thoại mẫu:**  
  *"Thưa thầy/cô, đây là điểm then chốt của quy trình To-Be: Agent không tự ý bịa đặt số liệu để lấp chỗ trống (chống Hallucination). Khi phát hiện thiếu hồ sơ đối thủ tại Tây Nam và thiếu yêu cầu hỗ trợ tại Cao Nguyên, hệ thống dừng lại và yêu cầu chuyên viên con người bổ sung thông tin."*
- Nhập thông tin bổ sung vào ô input $\rightarrow$ Bấm **"Xác nhận Bổ sung & Tiếp tục"** $\rightarrow$ Agent tiếp tục chạy sang Bước 3, 4, 5 và render Dashboard hoàn tất.

### Bước 4: Demo Nạp Dữ Liệu Thực Tế Mới (CSV / XLSX / Google Sheets) (1 phút)
- Chuyển sang tab **"Tải File CSV / XLSX"** $\rightarrow$ Tải file `sample_territories.xlsx` hoặc `sample_territories.csv`.
- Hoặc dán link Google Sheets công khai $\rightarrow$ Agent nạp dữ liệu mới và tính toán trong vòng chưa đầy 1 giây.
- Mở khung **"Nhật Ký Truy Vết Thực Thi (Audit Log)"** để chứng minh mọi phép tính đều có timestamp, căn cứ nguồn và không hề hard-code kết quả.

---

## 💡 PHẦN 2: BỘ CÂU HỎI PHẢN BIỆN DỰ KIẾN CỦA GIẢNG VIÊN & CÂU TRẢ LỜI MẪU

### Câu hỏi 1: Tại sao nhóm không dùng trực tiếp một mô hình LLM (như GPT-4 hay Gemini) để đưa ra kết luận luôn mà phải chia thành nhiều Tool và Rule-Engine?
* **Trả lời:**
  * Nếu dùng LLM thuần túy dạng zero-shot prompt, hệ thống sẽ gặp 3 rủi ro chí mạng trong bài toán kinh doanh thực tế:
    1. **Hiện tượng ảo giác (Hallucination):** Khi thiếu dữ liệu về đối thủ hoặc yêu cầu hỗ trợ, LLM có xu hướng tự "sáng tác" thông tin cho hợp lý thay vì thừa nhận là dữ liệu bị thiếu.
    2. **Tính toán sai lệch trọng số:** LLM xử lý số học và ma trận đa tiêu chí không ổn định bằng mã nguồn xác định (Deterministic Logic).
    3. **Không thể truy vết (Lack of Auditability):** Ban Giám đốc và Trưởng phòng kinh doanh không thể phê duyệt một quyết định đầu tư tiền tỷ nếu chỉ nhận được một đoạn text chung chung mà không rõ từng điểm số căn cứ vào dòng nào, trang nào của tài liệu nguồn.
  * Vì vậy, kiến trúc tối ưu là **Tool-Grounded Agentic Workflow**: Agent phân tích ngữ nghĩa và trích xuất dữ kiện, nhưng việc tính toán, kiểm tra ràng buộc cứng và ghi log được thực thi bởi các module nghiệp vụ chuyên biệt.

---

### Câu hỏi 2: Làm sao hệ thống đảm bảo phân biệt được giữa [FACT] (Dữ liệu nguồn) và [INFERENCE] (Suy luận của Agent)?
* **Trả lời:**
  * Hệ thống áp dụng cấu trúc dữ liệu nghiêm ngặt trong module `FactVerificationSkill`:
    * Mọi thông tin thuộc trường `[FACT]` (như số lượng chuỗi, kỳ báo cáo, tính năng khách hàng ghi trong khảo sát, phương thức hỗ trợ yêu cầu) phải có con trỏ trích dẫn `raw_citations` trỏ trực tiếp đến tên tài liệu và năm phát hành.
    * Mọi đánh giá thuộc trường `[INFERENCE]` (như Điểm tương thích giải pháp Fit-Score, Nhận định về lợi thế cạnh tranh, Cảnh báo quá tải On-site) đều phải đi qua thuật toán đối chiếu ma trận và được gắn nhãn rõ ràng trên báo cáo để cấp quản lý nhận diện được đâu là số liệu thực tế, đâu là nhận định của AI.

---

### Câu hỏi 3: Nếu giảng viên cung cấp một bộ dữ liệu mới tại buổi thi có cấu trúc cột hơi khác hoặc thiếu một vài cột thì giải pháp xử lý thế nào?
* **Trả lời:**
  * Module `DataIngestionEngine` đã được thiết kế với cơ chế **Fuzzy Column Matching**:
    * Nhận diện cột không phân biệt chữ hoa/thường, tự động map các biến thể tiếng Việt và tiếng Anh (ví dụ: `name`, `tên địa bàn`, `địa bàn` đều nhận diện là tên; `demanded_features`, `tính năng yêu cầu` đều nhận diện là nhu cầu).
    * Hỗ trợ tự động bóc tách file Excel `.xlsx` thuần túy bằng thư viện chuẩn của Python, không phụ thuộc vào việc máy thi có cài đặt `pandas` hay `openpyxl` hay không.
    * Khi phát hiện thiếu hẳn một cột trọng yếu, Agent không báo lỗi sập chương trình (crash) mà chuyển thành cờ cảnh báo `missing_fields` và kích hoạt luồng **Human-in-the-Loop** để người dùng xử lý.

---

### Câu hỏi 4: Cơ chế phát hiện "Mâu thuẫn dữ liệu" và "Trùng lặp nguồn" hoạt động như thế nào?
* **Trả lời:**
  * **Xử lý trùng lặp nguồn:** Agent phân tích nội dung metadata của báo cáo. Nếu phát hiện ghi chú "dẫn lại nguồn từ..." hoặc tên nguồn trùng với báo cáo đã nạp trước đó, Agent lập tức bỏ qua báo cáo thứ hai và ghi nhận vào log cảnh báo trùng lặp, ngăn chặn việc phóng đại quy mô thị trường ảo.
  * **Phát hiện mâu thuẫn:** Khi có từ 2 nguồn độc lập cùng báo cáo về một địa bàn trong cùng kỳ nhưng chênh lệch số lượng chuỗi bán lẻ vượt quá $30\%$, Agent gắn nhãn `is_data_reliable = False`, hạ điểm tin cậy và tự động gửi cảnh báo lên chốt chặn Human-in-the-Loop để con người kiểm tra tài liệu gốc.

---

### Câu hỏi 5: Giải thích rõ vì sao địa bàn Duyên Hải có quy mô thị trường lớn nhất (120 chuỗi, 190 tỷ) nhưng lại bị loại bỏ?
* **Trả lời:**
  * Đây là minh chứng rõ nhất cho việc khắc phục **Vấn đề số 2 và số 3** trong quy trình cũ:
    1. **Về độ khớp giải pháp:** Khách hàng tại Duyên Hải yêu cầu kho lạnh robotized tự động và phân loại hàng siêu trọng cảng biển — đây là 2 tính năng nằm trong danh mục `unsupported_capabilities` của Hưng Phát. Điểm Fit thực tế là $0.0\%$.
    2. **Về năng lực triển khai:** Khách hàng bắt buộc cam kết hỗ trợ On-site 24/7 tức thì tại kho cảng. Trong khi đó, chính sách công ty nêu rõ đội ngũ chỉ có 4 kỹ sư và chưa có chi nhánh tại chỗ. Ràng buộc cứng `RULE_EXCLUDE_ONSITE_OVERLOAD` lập tức kích hoạt để bảo vệ công ty trước nguy cơ vỡ trận triển khai và đền bù hợp đồng.

---

## 📊 PHẦN 3: TỔNG HỢP CÁC LỆNH CHẠY DÀNH CHO BUỔI BẢO VỆ

| Mục đích | Câu lệnh thực thi trong Terminal |
| :--- | :--- |
| **Chạy Web UI trực tiếp** | `run_web_ui.bat` hoặc `powershell .\run_web_ui.ps1` |
| **Kiểm thử tự động 3 kịch bản** | `python tests/test_cases.py` |
| **Chạy thử file CSV** | `python run_agent.py --data data/sample_territories.csv` |
| **Chạy thử file Excel XLSX** | `python run_agent.py --data data/sample_territories.xlsx` |
| **Chạy bộ dữ liệu mới của Giảng viên** | `python run_agent.py --data "đường_dẫn_file_giảng_viên.json"` |

