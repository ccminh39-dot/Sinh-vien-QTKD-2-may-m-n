import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional
from .config import GEMINI_API_KEY, DEFAULT_GEMINI_MODEL

class GeminiLLMEngine:
    """
    Module tích hợp mô hình Gemini AI vào HP-Expansion-Agent.
    - Sử dụng trực tiếp REST API của Google Generative AI (không cần cài thêm thư viện ngoài).
    - Tuân thủ quy tắc đề bài: Không bịa đặt số liệu ngoài tài liệu (Strict Grounding).
    - Có cơ chế Fallback tự động sang Rule-based Engine nếu mất kết nối mạng.
    """
    def __init__(self, api_key: str = GEMINI_API_KEY, model_name: str = DEFAULT_GEMINI_MODEL):
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"

    def generate_strategic_commentary(self, context_summary: str) -> Optional[str]:
        """
        Sinh nhận định chiến lược kinh doanh chuyên sâu cho Trưởng phòng PTKD
        """
        prompt = f"""Bạn là Cố vấn Chiến lược Cấp cao kiêm Trợ lý AI cho Công ty Hưng Phát (giải pháp HP-WMS cho chuỗi bán lẻ).
Dưới đây là tóm tắt kết quả phân tích 4 địa bàn từ dữ liệu thẩm định:

{context_summary}

QUY TẮC BẮT BUỘC (ĐỀ THI AI301):
1. TUYỆT ĐỐI không bịa đặt số liệu thị trường mới ngoài các dữ kiện đã cung cấp.
2. Phân biệt rõ số liệu thực tế trong tài liệu [FACT] và suy luận kinh doanh [INFERENCE].
3. Giải thích ngắn gọn tại sao Top 2 địa bàn được chọn là quyết định tối ưu với nguồn lực triển khai hiện tại (chỉ phục vụ 1 đợt, tối đa 4 kỹ sư).

Hãy viết một đoạn "Nhận Định Chiến Lược Dành Cho Trưởng Phòng Phát Triển Kinh Doanh" (khoảng 3-4 đoạn súc tích, văn phong quản trị kinh doanh chuyên nghiệp, có bullet points)."""

        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1024
            }
        }

        try:
            req = urllib.request.Request(
                self.base_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=12) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                candidates = res_data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
        except Exception as e:
            # Fallback sang nhận định có cấu trúc nếu offline / lỗi mạng
            return None

        return None

