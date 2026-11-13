import csv
import json
import os
import re
import urllib.request
import urllib.error
import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, Any, List

def remove_accents(input_str: str) -> str:
    """Chuyển đổi chuỗi tiếng Việt có dấu thành không dấu để so khớp linh hoạt"""
    if not input_str:
        return ""
    s = input_str.lower()
    s = re.sub(r'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', s)
    s = re.sub(r'[èéẹẻẽêềếệểễ]', 'e', s)
    s = re.sub(r'[ìíịỉĩ]', 'i', s)
    s = re.sub(r'[òóọỏõôồốộổỗơờớợởỡ]', 'o', s)
    s = re.sub(r'[ùúụủũưừứựửữ]', 'u', s)
    s = re.sub(r'[ỳýỵỷỹ]', 'y', s)
    s = re.sub(r'[đ]', 'd', s)
    return s.strip()

class DataIngestionEngine:
    """
    Module hỗ trợ đa dạng định dạng đầu vào:
    - Google Sheets URL (tự động fetch qua gviz tq API & export CSV API)
    - File CSV nội bộ (hỗ trợ phân cách phẩy, chấm phẩy, tab)
    - File XLSX (phân tích thuần túy qua zipfile + XML của Python)
    - File JSON
    """

    @staticmethod
    def parse_google_sheets_url(sheet_url: str) -> Dict[str, Any]:
        """
        Chuyển đổi URL Google Sheets thành URL xuất CSV và tải dữ liệu về
        Hỗ trợ đa dạng định dạng link:
        - Link thông thường: https://docs.google.com/spreadsheets/d/{ID}/edit...
        - Link xuất bản Web: https://docs.google.com/spreadsheets/d/e/{ID}/pubhtml hoặc pub?output=csv
        - Link chia sẻ Google Drive: https://drive.google.com/file/d/{ID}/view...
        """
        sheet_url = sheet_url.strip().strip('"').strip("'")
        
        # Trích xuất Sheet ID & GID
        sheet_id = None
        is_pub = False
        
        if "/spreadsheets/d/e/" in sheet_url:
            match_pub = re.search(r"/spreadsheets/d/e/([a-zA-Z0-9-_]+)", sheet_url)
            if match_pub:
                sheet_id = match_pub.group(1)
                is_pub = True
        elif "/spreadsheets/d/" in sheet_url:
            match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", sheet_url)
            if match:
                sheet_id = match.group(1)
        elif "drive.google.com/file/d/" in sheet_url:
            match_drive = re.search(r"drive\.google\.com/file/d/([a-zA-Z0-9-_]+)", sheet_url)
            if match_drive:
                sheet_id = match_drive.group(1)
        else:
            # Tìm ID dạng chuỗi ký tự dài
            match_raw = re.search(r"([a-zA-Z0-9-_]{20,})", sheet_url)
            if match_raw:
                sheet_id = match_raw.group(1)

        if not sheet_id:
            raise ValueError(
                "Không nhận diện được ID Google Sheets từ liên kết. "
                "Vui lòng cung cấp link dạng: https://docs.google.com/spreadsheets/d/{ID}..."
            )

        gid_match = re.search(r"[#&?]gid=([0-9]+)", sheet_url)
        gid = gid_match.group(1) if gid_match else "0"

        # Danh sách endpoint tải CSV theo thứ tự ưu tiên
        candidate_urls = []
        if is_pub:
            candidate_urls.append(f"https://docs.google.com/spreadsheets/d/e/{sheet_id}/pub?output=csv&gid={gid}")
            candidate_urls.append(f"https://docs.google.com/spreadsheets/d/e/{sheet_id}/pub?output=csv")
        else:
            # 1. Google Visualization Query API (ít bị redirect sang màn hình đăng nhập nhất đối với link Anyone with link)
            candidate_urls.append(f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&gid={gid}")
            # 2. Export trực tiếp dạng CSV
            candidate_urls.append(f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}")
            candidate_urls.append(f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv")

        last_error = None
        for candidate in candidate_urls:
            try:
                req = urllib.request.Request(
                    candidate,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                        "Accept": "text/csv,text/plain,*/*"
                    }
                )
                with urllib.request.urlopen(req, timeout=12) as response:
                    csv_bytes = response.read()
                    csv_text = csv_bytes.decode("utf-8", errors="replace")

                    # Kiểm tra nếu Google trả về trang HTML đăng nhập
                    if "<!DOCTYPE html>" in csv_text or "<html" in csv_text or "accounts.google.com" in csv_text:
                        last_error = PermissionError(
                            "Trang tính Google Sheets này CHƯA ĐƯỢC BẬT QUYỀN CHIA SẺ CÔNG KHAI! "
                            "Cách bật quyền: Mở Google Sheet -> Bấm nút 'Chia sẻ' (Share) màu xanh ở góc phải trên -> "
                            "Tại mục 'Quyền truy cập chung', đổi thành 'Bất kỳ ai có đường liên kết' (Quyền: Người xem)."
                        )
                        continue

                    # Parse nội dung CSV
                    parsed = DataIngestionEngine.parse_csv_string(csv_text)
                    if parsed.get("territories"):
                        return parsed

            except urllib.error.HTTPError as http_err:
                if http_err.code in [401, 403]:
                    last_error = PermissionError(
                        "Google từ chối truy cập (HTTP 401/403): Trang tính chưa được chia sẻ công khai. "
                        "Vui lòng vào Google Sheet -> 'Chia sẻ' -> Đổi thành 'Bất kỳ ai có đường liên kết'."
                    )
                elif http_err.code == 404:
                    last_error = ValueError("Không tìm thấy trang tính (HTTP 404). Vui lòng kiểm tra lại ID đường link.")
                else:
                    last_error = RuntimeError(f"Lỗi kết nối máy chủ Google Sheets (HTTP {http_err.code}): {http_err.reason}")
            except Exception as e:
                last_error = e

        if last_error:
            raise last_error
        raise ValueError("Không thể trích xuất dữ liệu từ link Google Sheets được cung cấp.")

    @staticmethod
    def parse_csv_file(file_path: str) -> Dict[str, Any]:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            csv_text = f.read()
        return DataIngestionEngine.parse_csv_string(csv_text)

    @staticmethod
    def parse_csv_string(csv_text: str) -> Dict[str, Any]:
        if not csv_text or not csv_text.strip():
            raise ValueError("Nội dung bảng dữ liệu rỗng.")

        # Xóa BOM UTF-8 nếu có
        csv_text = csv_text.lstrip("\ufeff").strip()
        lines = [line.strip() for line in csv_text.splitlines() if line.strip()]
        if not lines:
            raise ValueError("Không tìm thấy dòng dữ liệu nào.")

        # Tự động nhận diện dấu phân cách: Tab (\t), Phẩy (,), hoặc Chấm phẩy (;)
        first_line = lines[0]
        tab_count = first_line.count("\t")
        comma_count = first_line.count(",")
        semi_count = first_line.count(";")

        delimiter = ","
        if tab_count > comma_count and tab_count > semi_count:
            delimiter = "\t"
        elif semi_count > comma_count and semi_count > tab_count:
            delimiter = ";"

        # Tìm dòng tiêu đề (Header row) thông minh
        header_idx = 0
        for i in range(min(5, len(lines))):
            test_line_norm = remove_accents(lines[i])
            if any(k in test_line_norm for k in ["dia ban", "name", "ten", "ma", "id", "chuoi", "retail", "khu vuc"]):
                header_idx = i
                break

        # Đọc dữ liệu với DictReader hoặc Positional fallback
        reader_lines = lines[header_idx:]
        reader = csv.reader(reader_lines, delimiter=delimiter)
        raw_rows = list(reader)
        if not raw_rows:
            raise ValueError("Không có dòng dữ liệu hợp lệ sau tiêu đề.")

        header_row = [c.strip() for c in raw_rows[0]]
        data_rows = raw_rows[1:]

        # Tạo ánh xạ cột thông minh
        col_map = {}
        for idx, col in enumerate(header_row):
            norm_col = remove_accents(col).replace("_", " ").replace("-", " ")
            if any(k in norm_col for k in ["ma dia ban", "id", "stt", "code", "ma"]):
                col_map.setdefault("id", idx)
            elif any(k in norm_col for k in ["ten dia ban", "dia ban", "khu vuc", "vung", "ten", "name", "territory"]):
                col_map.setdefault("name", idx)
            elif any(k in norm_col for k in ["so chuoi", "chuoi ban le", "chuoi", "retail", "stores", "chains"]):
                col_map.setdefault("retail_count", idx)
            elif any(k in norm_col for k in ["tang truong", "growth"]):
                col_map.setdefault("growth", idx)
            elif any(k in norm_col for k in ["dung luong", "quy mo", "gia tri", "market val", "value"]):
                col_map.setdefault("market_val", idx)
            elif any(k in norm_col for k in ["tinh nang", "nhu cau", "features", "demanded"]):
                col_map.setdefault("features", idx)
            elif any(k in norm_col for k in ["ho tro", "support", "yeu cau ho tro"]):
                col_map.setdefault("support", idx)
            elif any(k in norm_col for k in ["doi thu", "competitor"]):
                col_map.setdefault("competitor", idx)
            elif any(k in norm_col for k in ["thi phan", "share"]):
                col_map.setdefault("competitor_share", idx)
            elif any(k in norm_col for k in ["nhuoc diem", "diem yeu", "weakness"]):
                col_map.setdefault("competitor_weakness", idx)
            elif any(k in norm_col for k in ["nguon", "source"]):
                col_map.setdefault("source", idx)
            elif any(k in norm_col for k in ["ky", "nam", "period", "thoi gian"]):
                col_map.setdefault("period", idx)
            elif any(k in norm_col for k in ["ghi chu", "note"]):
                col_map.setdefault("note", idx)

        # Fallback theo vị trí mặc định nếu thiếu tiêu đề
        if "name" not in col_map:
            col_map["name"] = 1 if len(header_row) > 1 else 0
        if "id" not in col_map:
            col_map["id"] = 0
        if "retail_count" not in col_map:
            col_map["retail_count"] = 2 if len(header_row) > 2 else -1
        if "features" not in col_map:
            col_map["features"] = 3 if len(header_row) > 3 else -1
        if "support" not in col_map:
            col_map["support"] = 4 if len(header_row) > 4 else -1

        territories = []
        for row_idx, row in enumerate(data_rows, 1):
            if not row or not any(row):
                continue

            def get_val(key: str, default: str = "") -> str:
                idx = col_map.get(key, -1)
                if 0 <= idx < len(row):
                    return row[idx].strip()
                return default

            tid = get_val("id") or f"TERR_{row_idx:02d}"
            name = get_val("name") or f"Địa bàn {row_idx}"
            
            # Xử lý số lượng chuỗi
            retail_count_raw = get_val("retail_count", "0")
            try:
                digits = re.sub(r"[^\d]", "", retail_count_raw)
                retail_count = int(digits) if digits else 0
            except ValueError:
                retail_count = 0

            growth_raw = get_val("growth", "15%")
            market_val = get_val("market_val", "N/A")
            source = get_val("source", "Báo cáo ngành B2B Retail")
            period = get_val("period", "2024")
            note = get_val("note", "")

            # Xử lý đối thủ
            comp_name = get_val("competitor", "")
            comp_share = get_val("competitor_share", "20%")
            comp_weakness = get_val("competitor_weakness", "Chậm hỗ trợ kỹ thuật")
            competitors = []
            if comp_name and comp_name.lower() not in ["none", "không", "thiếu", "n/a", ""]:
                competitors.append({
                    "name": comp_name,
                    "market_share": comp_share,
                    "weakness": comp_weakness,
                    "strength": "N/A"
                })

            # Xử lý tính năng yêu cầu & yêu cầu hỗ trợ
            features_raw = get_val("features", "Quản lý tồn kho đa kênh thời gian thực, Tối ưu lộ trình lấy hàng")
            features = [f.strip() for f in re.split(r"[,;|]", features_raw) if f.strip()]
            support_req = get_val("support", "Remote Support 8/5")

            territories.append({
                "id": tid,
                "name": name,
                "market_reports": [
                    {
                        "source": source,
                        "period": period,
                        "retail_chains_count": retail_count,
                        "estimated_market_value_vnd": market_val,
                        "annual_growth_rate": growth_raw,
                        "note": note
                    }
                ],
                "competitors": competitors,
                "customer_demands": {
                    "key_feature_requests": features,
                    "support_requirement": support_req if support_req.lower() not in ["none", "không", "n/a", ""] else None
                }
            })

        if not territories:
            raise ValueError("Không đọc được dữ liệu địa bàn nào từ bảng cung cấp.")

        return DataIngestionEngine._wrap_with_company_profile(territories)

    @staticmethod
    def parse_xlsx_file(file_path: str) -> Dict[str, Any]:
        """
        Trích xuất file XLSX (Excel) bằng zipfile và XML parser có sẵn của Python
        Không cần cài thêm thư viện bên ngoài như openpyxl hay pandas.
        """
        with zipfile.ZipFile(file_path, 'r') as z:
            # 1. Đọc shared strings
            shared_strings = []
            if 'xl/sharedStrings.xml' in z.namelist():
                tree = ET.fromstring(z.read('xl/sharedStrings.xml'))
                ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                for si in tree.findall('ns:si', ns):
                    t = si.find('ns:t', ns)
                    shared_strings.append(t.text if t is not None and t.text else "")

            # 2. Đọc sheet1.xml
            sheet_tree = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
            ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            
            rows_data = []
            for row in sheet_tree.findall('.//ns:row', ns):
                row_vals = []
                for c in row.findall('ns:c', ns):
                    cell_type = c.attrib.get('t', '')
                    val = ""
                    if cell_type == 's':
                        v = c.find('ns:v', ns)
                        if v is not None and v.text and v.text.isdigit():
                            idx = int(v.text)
                            val = shared_strings[idx] if idx < len(shared_strings) else ""
                    elif cell_type == 'inlineStr':
                        t = c.find('.//ns:t', ns)
                        if t is not None and t.text:
                            val = t.text
                    else:
                        v = c.find('ns:v', ns)
                        if v is not None and v.text:
                            val = v.text
                    row_vals.append(val)
                if any(row_vals):
                    rows_data.append(row_vals)

        if not rows_data:
            raise ValueError("File Excel trống hoặc không có dữ liệu tại Sheet1.")

        headers = [h.strip() for h in rows_data[0]]
        csv_rows = []
        csv_rows.append(",".join(f'"{h}"' for h in headers))
        for row in rows_data[1:]:
            padded = row + [""] * (len(headers) - len(row))
            csv_rows.append(",".join(f'"{c}"' for c in padded[:len(headers)]))

        return DataIngestionEngine.parse_csv_string("\n".join(csv_rows))

    @staticmethod
    def _wrap_with_company_profile(territories: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "company_profile": {
                "name": "Công ty Cổ phần Giải pháp Công nghệ Hưng Phát",
                "solution_name": "HP-WMS (Quản lý kho thông minh cho bán lẻ)",
                "core_capabilities": [
                    "Quản lý tồn kho đa kênh thời gian thực (Omnichannel Inventory)",
                    "Tối ưu lộ trình lấy hàng bằng mã vạch/QR",
                    "Tích hợp sàn TMĐT và phần mềm bán hàng POS thông dụng",
                    "Báo cáo cảnh báo hạn dùng và dự báo nhập hàng cơ bản"
                ],
                "unsupported_capabilities": [
                    "Tự động hóa kho lạnh robotized (Automated Cold-Chain Robotics)",
                    "Hệ thống phân loại tự động siêu trọng (Heavy Sorting Automation)"
                ],
                "deployment_capacity": {
                    "max_parallel_expansions": 1,
                    "max_onsite_support_teams": 1,
                    "available_engineers": 4,
                    "policy": "Chỉ chấp nhận địa bàn yêu cầu hỗ trợ on-site tối đa 2 kỹ sư/tuần hoặc chuyển đổi được sang hình thức Remote Support 8/5. Không mở rộng vào địa bàn bắt buộc cam kết On-site 24/7 tức thì khi chưa có chi nhánh."
                }
            },
            "evaluation_criteria": {
                "weights": {
                    "market_size_and_growth": 0.25,
                    "solution_fit": 0.30,
                    "competitive_advantage": 0.20,
                    "operational_feasibility": 0.25
                },
                "exclusion_rules": [
                    {
                        "id": "RULE_EXCLUDE_ONSITE_OVERLOAD",
                        "description": "Loại bỏ ngay địa bàn bắt buộc hỗ trợ On-site 24/7 vượt quá năng lực đội ngũ Hưng Phát.",
                        "condition": "onsite_requirement_exceeds_capacity == true"
                    },
                    {
                        "id": "RULE_MINIMUM_FIT_SCORE",
                        "description": "Điểm khớp giải pháp (solution_fit) phải đạt tối thiểu 60/100.",
                        "condition": "solution_fit_score < 60"
                    }
                ]
            },
            "territories": territories
        }
