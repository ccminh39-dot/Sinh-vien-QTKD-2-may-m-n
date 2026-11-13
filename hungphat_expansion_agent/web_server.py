from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import socketserver
import json
import urllib.parse
import os
import base64
import sys
import traceback

# Đảm bảo import được các module trong package
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from agent.expansion_agent import ExpansionDecisionAgent
from agent.audit_logger import AuditLogger
from agent.data_parsers import DataIngestionEngine
from agent.workflow_engine import WorkflowEngine
import tempfile

PORT = int(os.environ.get("PORT", 8080))

class AgentServerHandler(BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Connection", "close")
        super().end_headers()

    def do_GET(self):
        self.close_connection = True
        url_parsed = urllib.parse.urlparse(self.path)
        if url_parsed.path == "/" or url_parsed.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            index_path = os.path.join(BASE_DIR, "ui", "index.html")
            with open(index_path, "r", encoding="utf-8") as f:
                self.wfile.write(f.read().encode("utf-8"))
        elif url_parsed.path == "/download_sample_csv":
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", "attachment; filename=file_mau_dung_dinh_dang_hungphat.csv")
            self.end_headers()
            csv_path = os.path.join(BASE_DIR, "data", "file_mau_dung_dinh_dang_hungphat.csv")
            with open(csv_path, "rb") as f:
                self.wfile.write(f.read())
        elif url_parsed.path == "/download_sample_xlsx":
            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            self.send_header("Content-Disposition", "attachment; filename=file_mau_dung_dinh_dang_hungphat.xlsx")
            self.end_headers()
            xlsx_path = os.path.join(BASE_DIR, "data", "file_mau_dung_dinh_dang_hungphat.xlsx")
            with open(xlsx_path, "rb") as f:
                self.wfile.write(f.read())
        elif url_parsed.path.startswith("/assets/"):
            file_name = url_parsed.path.replace("/assets/", "")
            file_path = os.path.join(BASE_DIR, "ui", "assets", file_name)
            if os.path.exists(file_path):
                self.send_response(200)
                if file_name.endswith(".jpg") or file_name.endswith(".jpeg"):
                    self.send_header("Content-Type", "image/jpeg")
                elif file_name.endswith(".png"):
                    self.send_header("Content-Type", "image/png")
                else:
                    self.send_header("Content-Type", "application/octet-stream")
                self.end_headers()
                with open(file_path, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "Asset Not Found")
        elif url_parsed.path.startswith("/api/load_preset"):
            query = urllib.parse.parse_qs(url_parsed.query)
            preset_name = query.get("name", ["standard"])[0]
            file_map = {
                "standard": os.path.join(BASE_DIR, "data", "dataset_standard.json"),
                "missing": os.path.join(BASE_DIR, "data", "dataset_missing_info.json"),
                "boundary": os.path.join(BASE_DIR, "data", "dataset_boundary_case.json")
            }
            target_file = file_map.get(preset_name, os.path.join(BASE_DIR, "data", "dataset_standard.json"))
            with open(target_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._send_json({"status": "success", "data": data})
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        url_parsed = urllib.parse.urlparse(self.path)
        if url_parsed.path == "/api/workflow_execute":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                payload = json.loads(body)
                action = payload.get("action", "step_validate") # step_validate, step_cleaning, step_process, step_verify, step_export, run_pipeline
                sheet_url = payload.get("sheet_url", "")
                source_type = payload.get("source_type", "sheets")
                preset_name = payload.get("preset_name", "standard")
                feedback = payload.get("feedback", "")
                force_verify_ok = payload.get("force_verify_ok", False)

                print(f"[API] POST /api/workflow_execute | action={action} | source={source_type}")

                # ==============================================================
                # HÀNH ĐỘNG 1: BƯỚC 1 (SHEETS / INPUT VALIDATION)
                # ==============================================================
                if action == "step_validate":
                    raw_data = None
                    if source_type == "sheets":
                        validation = WorkflowEngine.step_validate_sheets(sheet_url)
                        if not validation.get("ok"):
                            print(f"[API] Sheet validation failed: {validation.get('error')}")
                            self._send_json(validation)
                            return
                        raw_data = validation.get("raw_data")
                    elif source_type == "preset":
                        preset_file = {
                            "standard": os.path.join(BASE_DIR, "data", "dataset_standard.json"),
                            "missing": os.path.join(BASE_DIR, "data", "dataset_missing_info.json"),
                            "boundary": os.path.join(BASE_DIR, "data", "dataset_boundary_case.json")
                        }.get(preset_name, os.path.join(BASE_DIR, "data", "dataset_standard.json"))
                        with open(preset_file, "r", encoding="utf-8") as f:
                            raw_data = json.load(f)
                    elif source_type == "csv_content":
                        csv_text = payload.get("content", "")
                        try:
                            raw_data = DataIngestionEngine.parse_csv_string(csv_text)
                        except Exception as e:
                            self._send_json({"ok": False, "step": "Sheets", "error": f"Báo lỗi định dạng bảng: {str(e)}"})
                            return
                    elif source_type == "xlsx_base64":
                        b64_data = payload.get("content_base64", "")
                        temp_xlsx = os.path.join(tempfile.gettempdir(), "temp_upload.xlsx")
                        with open(temp_xlsx, "wb") as f:
                            f.write(base64.b64decode(b64_data))
                        try:
                            raw_data = DataIngestionEngine.parse_xlsx_file(temp_xlsx)
                        except Exception as e:
                            self._send_json({"ok": False, "step": "Sheets", "error": f"Báo lỗi file Excel: {str(e)}"})
                            return

                    if not raw_data or not raw_data.get("territories"):
                        self._send_json({"ok": False, "step": "Sheets", "error": "Báo lỗi: Không tìm thấy dữ liệu hợp lệ. Yêu cầu nhập đúng link Google Sheets hoặc file theo cấu trúc."})
                        return

                    commentary = WorkflowEngine.generate_commentary_step1(raw_data)
                    self._send_json({
                        "ok": True,
                        "step": "Sheets",
                        "message": f"Nạp thành công {len(raw_data.get('territories', []))} địa bàn!",
                        "raw_data": raw_data,
                        "commentary": commentary
                    })
                    return

                # ==============================================================
                # HÀNH ĐỘNG 2: BƯỚC 2 (CLEANING)
                # ==============================================================
                elif action == "step_cleaning":
                    raw_data = payload.get("raw_data")
                    if not raw_data:
                        self._send_json({"ok": False, "step": "Cleaning", "error": "Thiếu dữ liệu gốc từ Bước 1 để thực hiện Cleaning."})
                        return
                    cleaning_res = WorkflowEngine.step_cleaning(raw_data)
                    self._send_json(cleaning_res)
                    return

                # ==============================================================
                # HÀNH ĐỘNG 3: BƯỚC 3 (PROCESS)
                # ==============================================================
                elif action == "step_process":
                    cleaned_data = payload.get("cleaned_data")
                    if not cleaned_data:
                        self._send_json({"ok": False, "step": "Process", "error": "Thiếu dữ liệu làm sạch từ Bước 2 để xử lý nghiệp vụ."})
                        return
                    process_res = WorkflowEngine.step_process(cleaned_data, feedback=feedback)
                    self._send_json(process_res)
                    return

                # ==============================================================
                # HÀNH ĐỘNG 4: BƯỚC 4 (VERIFY)
                # ==============================================================
                elif action == "step_verify":
                    process_res = payload.get("process_res")
                    if not process_res:
                        self._send_json({"ok": False, "step": "Verify", "error": "Thiếu kết quả tính toán từ Bước 3 để thẩm định."})
                        return

                    if force_verify_ok:
                        # Người dùng bấm Phê duyệt ngoại lệ
                        commentary = WorkflowEngine.generate_commentary_step4(process_res.get("results", {}), False, [])
                        commentary["summary"] = "Chuyên viên đã chủ động phê duyệt ngoại lệ sau khi xem xét các cảnh báo (HITL Approved)."
                        self._send_json({
                            "ok": True,
                            "step": "Verify",
                            "status": "verified_ok",
                            "message": "Phê duyệt ngoại lệ thành công! Sẵn sàng xuất HTML Dashboard.",
                            "commentary": commentary
                        })
                        return

                    verify_res = WorkflowEngine.step_verify(process_res)
                    self._send_json(verify_res)
                    return

                # ==============================================================
                # HÀNH ĐỘNG 5: BƯỚC 5 (XUẤT DASHBOARD & BÁO CÁO)
                # ==============================================================
                elif action == "step_export" or action == "run_pipeline":
                    process_res = payload.get("process_res")
                    if not process_res:
                        # Fallback nếu gọi full pipeline
                        raw_data = payload.get("raw_data")
                        if not raw_data:
                            self._send_json({"ok": False, "step": "Export_Dashboard", "error": "Thiếu dữ liệu để xuất Dashboard."})
                            return
                        c_res = WorkflowEngine.step_cleaning(raw_data)
                        process_res = WorkflowEngine.step_process(c_res["cleaned_data"], feedback=feedback)

                    results = process_res["results"]
                    report_markdown = process_res["report_markdown"]
                    audit_events = process_res["audit_events"]

                    self._send_json({
                        "ok": True,
                        "step": "Export_Dashboard",
                        "status": "completed",
                        "message": "Toàn bộ quy trình hoàn tất! Đã xuất HTML Dashboard và Báo cáo đề xuất.",
                        "territories": [
                            {
                                "id": r["territory"]["id"],
                                "name": r["territory"]["name"],
                                "facts": r["verified_facts"],
                                "fit": r["fit_analysis"],
                                "score": r["score_res"],
                                "is_selected": r in results["selected_territories"]
                            }
                            for r in results["pipeline_results"]
                        ],
                        "selected_top_2": [
                            {
                                "id": s["territory"]["id"],
                                "name": s["territory"]["name"],
                                "score": s["score_res"]["total_score"],
                                "reasons": s["fit_analysis"]["feasibility_assessment"]
                            }
                            for s in results["selected_territories"]
                        ],
                        "report_markdown": report_markdown,
                        "audit_events": audit_events
                    })
                    return

            except Exception as e:
                traceback.print_exc()
                self._send_json({"ok": False, "step": "Sheets", "error": f"Lỗi xử lý: {str(e)}"}, 200)
            return

        elif url_parsed.path == "/api/run":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                payload = json.loads(body)
                dataset_name = payload.get("dataset", "standard")
                feedback = payload.get("feedback", None)

                file_map = {
                    "standard": "data/dataset_standard.json",
                    "missing": "data/dataset_missing_info.json",
                    "boundary": "data/dataset_boundary_case.json"
                }
                target_file = file_map.get(dataset_name, "data/dataset_standard.json")

                logger = AuditLogger()
                agent = ExpansionDecisionAgent(data_file_path=target_file, logger=logger)
                results = agent.run_pipeline()
                report_markdown = agent.generate_management_report(results)

                response_payload = {
                    "status": "success",
                    "dataset": dataset_name,
                    "territories": [
                        {
                            "id": r["territory"]["id"],
                            "name": r["territory"]["name"],
                            "facts": r["verified_facts"],
                            "fit": r["fit_analysis"],
                            "score": r["score_res"],
                            "is_selected": r in results["selected_territories"]
                        }
                        for r in results["pipeline_results"]
                    ],
                    "selected_top_2": [
                        {
                            "id": s["territory"]["id"],
                            "name": s["territory"]["name"],
                            "score": s["score_res"]["total_score"],
                            "reasons": s["fit_analysis"]["feasibility_assessment"]
                        }
                        for s in results["selected_territories"]
                    ],
                    "unselected": [
                        {
                            "id": u["territory"]["id"],
                            "name": u["territory"]["name"],
                            "score": u["score_res"]["total_score"],
                            "is_excluded": u["score_res"]["is_excluded"],
                            "exclusion_reasons": u["score_res"]["exclusion_reasons"]
                        }
                        for u in results["unselected_territories"]
                    ],
                    "report_markdown": report_markdown,
                    "audit_events": logger.events
                }

                self._send_json(response_payload)
            except Exception as e:
                self._send_json({"status": "error", "message": str(e)}, 500)
        else:
            self.send_error(404)

    def _send_json(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

class MultiThreadedServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True

def run_server(port=PORT):
    os.makedirs("ui", exist_ok=True)
    server_address = ("", port)
    httpd = MultiThreadedServer(server_address, AgentServerHandler)
    print(f"[*] Hưng Phát AI Agent Web UI đang chạy tại: http://localhost:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Dừng Web Server.")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
