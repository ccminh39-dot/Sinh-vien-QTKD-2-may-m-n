import json
import os
from datetime import datetime
from typing import Any, Dict, List

class AuditLogger:
    """
    Module ghi nhật ký truy vết (Traceability & Audit Logging)
    Lưu trữ đầy đủ các bước thực thi, công cụ đã gọi, quy tắc nghiệp vụ đã kiểm tra,
    căn cứ dữ liệu nguồn và quyết định chuyển giao cho con người (HITL).
    """
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        try:
            os.makedirs(self.log_dir, exist_ok=True)
        except Exception:
            pass
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(self.log_dir, f"audit_trace_{self.session_id}.jsonl")
        self.events: List[Dict[str, Any]] = []

    def log_event(self, event_type: str, tool_name: str, inputs: Any, outputs: Any, metadata: Dict[str, Any] = None):
        event = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "event_type": event_type,
            "tool_name": tool_name,
            "inputs": inputs,
            "outputs": outputs,
            "metadata": metadata or {}
        }
        self.events.append(event)
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except Exception:
            # Tren moi truong Serverless nhu Vercel (read-only filesystem), luu tru in-memory
            pass

    def export_summary(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "log_file": self.log_file,
            "total_events": len(self.events),
            "events_by_type": [e["event_type"] for e in self.events]
        }

