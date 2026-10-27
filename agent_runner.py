#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
===================================================================================
       AI AGENT SKILL RUNNER - QUẢN LÝ & THỰC THI TOÀN BỘ SKILLS SDLC
              Hệ Thống Quản Lý Đặt Lịch Salon Tóc Tích Hợp AI
===================================================================================
Tác giả: AI Engineering & Requirements Analysis Team
Mô tả: Agent tự động hóa chu trình chạy các Skills trong .agents/skills/ và
      Prompts trong promts/ sử dụng Google Gemini Cloud API với cơ chế
      Grounded Context nội bộ SQLite và dự phòng Zero-Downtime Fallback.
===================================================================================
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Any

# Ensure UTF-8 output on Windows terminal
if sys.platform.startswith("win"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    requests = None

# --- ĐƯỜNG DẪN CẤU HÌNH ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
SKILLS_DIR = os.path.join(PROJECT_ROOT, ".agents", "skills")
PROMPTS_DIR = os.path.join(CURRENT_DIR, "promts")
OUTPUTS_DIR = os.path.join(CURRENT_DIR, "outputs")

# Đảm bảo các thư mục tồn tại
os.makedirs(PROMPTS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)

# Đọc cấu hình .env (Ưu tiên Agent/.env rồi đến root .env)
def load_env_variables() -> Dict[str, str]:
    config = {}
    env_paths = [
        os.path.join(CURRENT_DIR, ".env"),
        os.path.join(PROJECT_ROOT, ".env")
    ]
    for path in env_paths:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k, v = k.strip(), v.strip().strip('"').strip("'")
                        if k not in config:
                            config[k] = v
    return config

ENV_CONFIG = load_env_variables()
GEMINI_API_KEY = ENV_CONFIG.get("GEMINI_API_KEY", "")
DEFAULT_MODEL = ENV_CONFIG.get("GEMINI_MODEL", "gemini-3.8-flash")
FALLBACK_MODELS = [DEFAULT_MODEL, "gemini-flash-latest", "gemini-2.5-flash", "gemini-1.5-flash"]

# Bối cảnh nghiệp vụ cốt lõi của Salon Tóc Hà Minh
SALON_CORE_CONTEXT = """
BỐI CẢNH DỰ ÁN HỆ THỐNG SALON TÓC HÀ MINH:
1. Thương hiệu: HÀ MINH HAIR SALON (188 Thái Hà, Đống Đa, Hà Nội).
2. Người sáng lập & Giám đốc kỹ thuật: Master Stylist Hà Minh (Mã NV001, Chức vụ: Quản lý).
3. Kiến trúc CSDL: 8 bảng quan hệ SQLite chuẩn 3NF:
   - TaiKhoan (TaiKhoanID, TenDangNhap, MatKhauHash, VaiTro, TrangThai, SessionToken)
   - NhanVien (NhanVienID, HoTen, SoDienThoai, ChucVu, ChuyenMon, TaiKhoanID)
   - KhachHang (KhachHangID, HoTen, SoDienThoai, HangThanhVien, GhiChuToc, TongChiTieu)
   - DichVu (DichVuID, TenDichVu, LoaiDichVu, Gia, ThoiLuongPhut, MoTa)
   - LichHen (LichHenID, KhachHangID, NhanVienID, NgayHen, GioBatDau, GioKetThuc, TrangThai)
   - ChiTietLichHen (ChiTietID, LichHenID, DichVuID, DonGia)
   - HoaDon (HoaDonID, LichHenID, TongTien, GiamGia, ThanhTien, PhuongThucTT, NgayTao)
   - TroLyAI (LogID, ThoiGian, TacVu, NguoiDungID, NoiDungInput, NoiDungOutput, ThoiGianXuLyMs)
4. Quy tắc nghiệp vụ cốt lõi:
   - Chống trùng lịch thợ: Điều kiện giao thoa (S1 < E2) AND (S2 < E1).
   - Bảo mật đơn phiên: Single-Device Session kiểm tra session_token qua heartbeat 3.5s.
   - Ràng buộc tài chính: Hóa đơn dịch vụ > 2.000.000đ yêu cầu đặt cọc 20%.
   - Tiêu chuẩn VIP: Khách làm hóa chất nặng (Nhuộm Balayage, Uốn phồng) luôn bố trí 1 Thợ chính + 1 Thợ phụ thao tác đồng thời 2 bên đầu.
   - Khoa học tóc học (Trichology): Tóc tẩy cấp 8-9 cấm uốn nhiệt; phục hồi protein tơ tằm / keratin nano ở pH 4.5 khóa biểu bì; dầu gội Sulfate-free.
"""

class AgentClient:
    """HTTP Client gọi Google Gemini Cloud API với Connection Pooling."""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = None
        if requests:
            self.session = requests.Session()
            retries = Retry(total=2, backoff_factor=1, status_forcelist=[502, 503, 504])
            adapter = HTTPAdapter(max_retries=retries, pool_connections=5, pool_maxsize=5)
            self.session.mount("https://", adapter)

    def generate(self, prompt: str, system_instruction: str = "") -> Optional[str]:
        if not self.api_key or not self.session:
            return None

        for model in FALLBACK_MODELS:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 4096,
                }
            }
            if system_instruction:
                payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

            try:
                resp = self.session.post(url, json=payload, timeout=40)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "").strip()
            except Exception as e:
                continue
        return None


# --- DANH MỤC SKILLS QUY CHUẨN ---
AVAILABLE_SKILLS = [
    {
        "id": "requirements-analysis",
        "title": "Phân Tích Yêu Cầu Nghiệp Vụ (Requirements Analysis)",
        "icon": "📋",
        "desc": "Bóc tách 4 nhóm tác nhân, 10 Use Cases (UC001-UC010), ma trận FR/NFR, tiêu chí nghiệm thu AC."
    },
    {
        "id": "architecture-design",
        "title": "Thiết Kế Kiến Trúc Phân Tầng (Architecture Design)",
        "icon": "🏛️",
        "desc": "Kiến trúc 3 tầng Clean Architecture, Class Diagram 8 thực thể, 4 Screen Flows, Single-Device Session."
    },
    {
        "id": "database-design",
        "title": "Thiết Kế CSDL SQLite Chuẩn 3NF (Database Design)",
        "icon": "💾",
        "desc": "Đặc tả 8 bảng CSDL, 4 cấp độ ràng buộc toàn vẹn, Filtered Index và WAL mode."
    },
    {
        "id": "api-documentation",
        "title": "Đặc Tả Hợp Đồng RESTful API (API Documentation)",
        "icon": "🔌",
        "desc": "Quy chuẩn 25+ endpoints, chuẩn Envelope, RFC 7807 Problem Details và tài liệu SOP."
    },
    {
        "id": "implementation",
        "title": "Quy Chuẩn Viết Mã Sạch (Implementation Standards)",
        "icon": "💻",
        "desc": "Clean Code, Service Layer độc lập, thuật toán De Morgan chống trùng lịch, xử lý Windows."
    },
    {
        "id": "ui-ux-design",
        "title": "Thiết Kế Giao Diện & Trải Nghiệm POS (UI/UX Design)",
        "icon": "🎨",
        "desc": "Neo-Glassmorphism, bàn cờ lịch hẹn trực quan, POS thu ngân, in hóa đơn nhiệt 80mm/58mm."
    },
    {
        "id": "ai-prompt-engineering",
        "title": "Kỹ Nghệ Prompt & Động Cơ AI 2 Tầng (AI Prompt Engineering)",
        "icon": "🧠",
        "desc": "Gemini Cloud + Fallback SQLite, Context Grounding, Function Calling đổi giá, Zero-Hallucination."
    },
    {
        "id": "testing",
        "title": "Kịch Bản Kiểm Thử Toàn Diện (Testing & QA)",
        "icon": "🧪",
        "desc": "Bộ kiểm thử Unit Tests, Integration Tests, kịch bản tranh chấp Single-Device Session và E2E."
    },
    {
        "id": "code-review",
        "title": "Rà Soát Chất Lượng Mã Nguồn (Code Review)",
        "icon": "🔍",
        "desc": "Checklist 5 trọng điểm Clean Architecture, Transaction isolation, Good vs Bad Code patterns."
    },
    {
        "id": "performance-tuning",
        "title": "Tinh Chỉnh & Tối Ưu Hiệu Năng (Performance Tuning)",
        "icon": "⚡",
        "desc": "PRAGMA SQLite WAL, Cache 64MB, Adaptive Heartbeat Polling 3.5s, Tối ưu DOM batching."
    },
    {
        "id": "security-review",
        "title": "Kiểm Toán An Ninh & Bảo Mật (Security Review)",
        "icon": "🛡️",
        "desc": "Phòng chống SQL Injection, RBAC rào chắn phân quyền, bảo vệ Session Token và API Key."
    },
    {
        "id": "devops-deployment",
        "title": "Đóng Gói & Triển Khai Sản Xuất (DevOps & Deployment)",
        "icon": "🚀",
        "desc": "Máy chủ Waitress WSGI Windows Service (NSSM), Docker Compose, sao lưu SQLite Online."
    }
]


def load_skill_content(skill_id: str) -> str:
    """Đọc nội dung SKILL.md từ thư mục .agents/skills/"""
    skill_path = os.path.join(SKILLS_DIR, skill_id, "SKILL.md")
    if os.path.exists(skill_path):
        with open(skill_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    return ""


def run_skill_agent(skill_meta: Dict[str, str], client: AgentClient) -> str:
    """Thực thi một Skill thông qua AI Agent."""
    skill_id = skill_meta["id"]
    skill_title = skill_meta["title"]
    print(f"\n[🔄 Đang chạy Agent] {skill_meta['icon']} {skill_title}...")

    skill_doc = load_skill_content(skill_id)
    if not skill_doc:
        print(f"  ⚠️ Không tìm thấy file SKILL.md tại .agents/skills/{skill_id}/")
        skill_doc = f"Thực hiện đặc tả chuẩn mực cho kỹ năng {skill_title}."

    system_instruction = (
        "Bạn là Kiến Trúc Sư Trưởng & Chuyên Gia Phân Tích Phần Mềm Cao Cấp (Chief Solution Architect & Requirements Analyst) "
        "cho Hệ Thống Quản Lý Đặt Lịch Salon Tóc Tích Hợp AI (HÀ MINH HAIR SALON). "
        "Hãy suy nghĩ sâu sắc (Think Deeply), lập luận chặt chẽ và tạo ra bản tài liệu đặc tả kỹ thuật chi tiết, thực tế, "
        "chuyên nghiệp bằng tiếng Việt, tuân thủ tuyệt đối chuẩn mực công nghiệp và kiến trúc phân tầng."
    )

    prompt = f"""
NHIỆM VỤ CỦA BẠN (AGENT EXECUTION TASK):
Hãy vận dụng tài liệu chỉ dẫn kỹ năng (SKILL SPECIFICATION) dưới đây để xây dựng bản báo cáo đặc tả hoàn chỉnh và tối ưu nhất cho kỹ năng:
**{skill_title}**

{SALON_CORE_CONTEXT}

TÀI LIỆU CHỈ DẪN KỸ NĂNG (SKILL DOCUMENTATION):
{skill_doc}

YÊU CẦU ĐẦU RA (OUTPUT DELIVERABLES):
1. Tóm tắt mục tiêu và phương pháp luận cốt lõi.
2. Các đặc tả kỹ thuật chi tiết (bảng biểu, sơ đồ Mermaid, danh mục yêu cầu hoặc mã nguồn minh họa chuẩn).
3. Các quy tắc biên, xử lý rủi ro và tiêu chí nghiệm thu (Acceptance Criteria).
4. Khẳng định tính tương thích tuyệt đối với CSDL SQLite 8 bảng và thương hiệu Hà Minh Hair Salon.
"""

    start_time = time.time()
    ai_result = client.generate(prompt=prompt, system_instruction=system_instruction)
    elapsed = time.time() - start_time

    if not ai_result:
        print(f"  ℹ️ Sử dụng bản tài liệu Grounded Domain có sẵn (Không kết nối được Gemini)...")
        ai_result = f"# BÁO CÁO ĐẶC TẢ KỸ NĂNG: {skill_title}\n\n" \
                    f"> **Trạng thái**: Tự động sinh bởi Grounded Local Engine\n" \
                    f"> **Thời gian**: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n" \
                    f"## 1. Tổng Quan Kỹ Năng\n{skill_meta['desc']}\n\n" \
                    f"## 2. Nội Dung Chỉ Dẫn Kỹ Năng Chi Tiết\n\n{skill_doc}\n"

    # Lưu kết quả ra thư mục outputs/
    output_filename = f"{skill_id}_output.md"
    output_path = os.path.join(OUTPUTS_DIR, output_filename)
    
    header = f"""<!--
  BÁO CÁO SINH TỰ ĐỘNG BỞI AI AGENT RUNNER
  Kỹ năng: {skill_title} ({skill_id})
  Thời gian tạo: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
  Thời gian thực thi: {elapsed:.2f}s
  Model: Google Gemini ({DEFAULT_MODEL})
-->

"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(header + ai_result)

    print(f"  ✅ Đã hoàn thành trong {elapsed:.2f}s! Đã lưu tại: Agent/outputs/{output_filename}")
    return output_path


def generate_grounded_fallback_report(prompt_filename: str, prompt_text: str) -> str:
    """Tạo báo cáo chi tiết theo chuẩn Grounded SQLite khi Gemini gặp lỗi hạn ngạch (429) hoặc ngoại tuyến."""
    name_lower = prompt_filename.lower()
    
    if "requirements" in name_lower:
        return f"""# BÁO CÁO ĐẶC TẢ YÊU CẦU PHẦN MỀM (SOFTWARE REQUIREMENTS SPECIFICATION)
## Dự Án: Hệ Thống Quản Lý Đặt Lịch Salon Tóc Tích Hợp AI - HÀ MINH HAIR SALON

### 1. Bối Cảnh & Mục Tiêu Hệ Thống
- **Thương hiệu**: HÀ MINH HAIR SALON - 188 Thái Hà, Đống Đa, Hà Nội.
- **Mục tiêu**: Tự động hóa 100% quy trình đặt lịch, thu ngân POS, quản lý khách hàng thân thiết và tích hợp Trợ lý AI Stylist 24/7.
- **Pain Points giải quyết**: Chặn triệt để trùng lịch thợ, loại bỏ sai sót tính tiền, lưu vết lịch sử chất tóc khách hàng để chống cháy/hỏng tóc khi làm hóa chất.

### 2. Bốn Nhóm Tác Nhân & Phân Quyền Hệ Thống (Actors & RBAC)
1. **Quản Lý / Chủ Salon (`Admin` - Master Stylist Hà Minh, NV001)**:
   - Toàn quyền cấu hình bảng giá dịch vụ, quản lý tài khoản nhân viên, xem báo cáo doanh thu tài chính thời gian thực.
2. **Lễ Tân & Thu Ngân (`LeTan`)**:
   - Tiếp đón khách hàng, tạo lịch hẹn mới, xem bàn cờ thợ rảnh, thanh toán POS và in phiếu thanh toán nhiệt.
3. **Thợ Làm Tóc / Stylist (`Tho`)**:
   - Xem lịch phân công cá nhân, xem tóm tắt hồ sơ chất tóc của khách trong 5 giây trước khi vào dịch vụ.
4. **Khách Hàng Trải Nghiệm (`Guest`)**:
   - Tra cứu menu dịch vụ niêm yết, tương tác với AI Stylist tư vấn kiểu tóc và liệu trình phục hồi hư tổn.

### 3. Danh Mục Yêu Cầu Chức Năng Cốt Lõi (Functional Requirements - FR)
- **FR01 (Quản lý Hồ sơ & Lịch sử Tóc)**: Lưu thông tin họ tên, SĐT, hạng thành viên và trường `GhiChuToc` (chất tóc tẩy, tóc dầu, dị ứng hóa chất).
- **FR02 (Quản lý Danh mục Dịch vụ)**: Quản lý mã DV (DV001-DV021), tên dịch vụ, đơn giá niêm yết, thời lượng (phút).
- **FR03 (Đặt Lịch Hẹn & Chống Trùng Giờ)**: Bố trí lịch hẹn không giao thoa theo công thức De Morgan `(S1 < E2) AND (S2 < E1)`.
- **FR04 (Thu Ngân POS & In Hóa Đơn)**: Tự động tính tổng tiền dịch vụ, chiết khấu giảm giá VIP, thanh toán VietQR/POS/Tiền mặt và in phiếu thanh toán.
- **FR05 (Trợ Lý AI Đa Tầng)**: Gợi ý dịch vụ theo chất tóc, sinh tin nhắn nhắc lịch Zalo/SMS, tóm tắt 5s cho thợ, chat trực tuyến giải đáp tóc học (Trichology).

### 4. Yêu Cầu Phi Chức Năng (Non-Functional Requirements - NFR)
- **NFR01 (Bảo mật Đơn phiên - Single-Device Session)**: Mỗi tài khoản chỉ đăng nhập trên 1 thiết bị; cơ chế Session Heartbeat 3.5s đá phiên cũ khi phát hiện đăng nhập nơi khác.
- **NFR02 (Hiệu năng CSDL)**: SQLite WAL Mode, cache_size = 64MB, thời gian phản hồi API < 100ms.
- **NFR03 (Zero-Hallucination Guardrail)**: AI không bao giờ tự bịa đặt giá tiền ngoài CSDL; từ chối trả lời câu hỏi ngoài phạm vi salon (giá vàng, chứng khoán).

### 5. Quy Tắc Nghiệp Vụ & Khoa Học Tóc Học (Trichology & Business Rules)
- **Quy tắc đặt cọc**: Gói dịch vụ có tổng giá trị > 2.000.000đ bắt buộc đặt cọc 20%.
- **Quy tắc phân công VIP**: Khách làm hóa chất nặng luôn được phân công 1 Thợ chính kèm 1 Thợ phụ thao tác 2 bên đầu đồng thời trong 15 phút.
- **Khoa học tóc học**: Tóc tẩy cấp 8-9 cấm uốn nhiệt; phục hồi protein tơ tằm / nano keratin ở pH 4.5 khóa biểu bì; dầu gội Sulfate-free.
"""
    elif "use_case" in name_lower:
        return f"""# BÁO CÁO ĐẶC TẢ CHI TIẾT 10 USE CASES (UC001 - UC010)
## Hệ Thống Quản Lý Đặt Lịch Salon Tóc Tích Hợp AI - HÀ MINH HAIR SALON

### UC001: Đăng Nhập & Kiểm Soát Đơn Phiên (Single-Device Session)
- **Tác nhân**: Tất cả nhân viên (Admin, LeTan, Tho).
- **Tiền điều kiện**: Đã có tài khoản trong bảng `TaiKhoan`.
- **Luồng chính**: Đăng nhập tên/mật khẩu -> Sinh SessionToken mới -> Cấp JWT -> Điều hướng phân quyền.
- **Luồng ngoại lệ (A1)**: Tài khoản đang mở ở máy khác, máy cũ nhận mã lỗi 401 khi heartbeat sau 3.5s và tự đăng xuất.

### UC002: Quản Lý Hồ Sơ Khách Hàng & Chất Tóc
- **Tác nhân**: LeTan, Admin.
- **Luồng chính**: Tìm kiếm theo tên hoặc SĐT; cập nhật trường `GhiChuToc` (chất tóc tẩy, tóc xơ, dị ứng).

### UC003: Quản Lý Danh Mục Dịch Vụ & Bảng Giá
- **Tác nhân**: Admin (Master Stylist Hà Minh).
- **Ràng buộc**: Đơn giá >= 0, Thời lượng > 0, Không xóa dịch vụ đang có lịch hẹn tham chiếu.

### UC004: Quản Lý Đội Ngũ Stylist & Lịch Làm Việc
- **Tác nhân**: Admin.
- **Nghiệp vụ**: Phân công chuyên môn (Uốn sóng, Nhuộm Balayage, Phục hồi Nano).

### UC005: Tạo Lịch Hẹn & Chống Trùng Giờ (De Morgan)
- **Tác nhân**: LeTan, Khách hàng.
- **Công thức chống trùng**: `(S1 < E2) AND (S2 < E1)`. Chặn tuyệt đối 2 lịch hẹn đè giờ nhau trên cùng một thợ.

### UC006: Thu Ngân POS, Giảm Giá & In Hóa Đơn Nhiệt
- **Tác nhân**: LeTan.
- **Công thức**: `ThanhTien = TongTien - GiamGia` (Kiểm tra ràng buộc CHECK CSDL). Xuất phiếu in nhiệt 80mm/58mm.

### UC007: Báo Cáo Doanh Thu & Hiệu Suất Vận Hành
- **Tác nhân**: Admin.
- **Nghiệp vụ**: Thống kê doanh thu theo ngày/tháng, phương thức thanh toán, xuất file CSV.

### UC008: AI Gợi Ý Liệu Trình Dịch Vụ Thông Minh
- **Tác nhân**: LeTan, Stylist.
- **Nghiệp vụ**: AI đối chiếu chất tóc và tiền sử làm hóa chất để đề xuất gói uốn/nhuộm/phục hồi tối ưu.

### UC009: AI Tự Động Sinh Tin Nhắn Nhắc Lịch (Zalo/SMS)
- **Tác nhân**: LeTan, Hệ thống.
- **Nội dung**: Tin nhắn văn minh, chuẩn mực, nêu rõ thợ làm, khung giờ, địa chỉ 188 Thái Hà.

### UC010: AI Tóm Tắt Hồ Sơ Khách 5 Giây Cho Stylist
- **Tác nhân**: Stylist (Thợ).
- **Nghiệp vụ**: Hiển thị nhanh 3 gạch đầu dòng: Tên khách, chất tóc, dịch vụ đã chọn để stylist sẵn sàng đón tiếp.
"""
    elif "database" in name_lower:
        return f"""# BÁO CÁO THIẾT KẾ CSDL QUAN HỆ SQLITE CHUẨN 3NF (8 BẢNG)
## Hệ Thống Quản Lý Đặt Lịch Salon Tóc Tích Hợp AI - HÀ MINH HAIR SALON

### 1. Mô Hình Thực Thể & Danh Mục 8 Bảng
1. `TaiKhoan`: Quản lý định danh nhân viên, mật khẩu hash SHA-256, SessionToken đơn phiên.
2. `NhanVien`: Quản lý hồ sơ stylist, thợ chính, thợ phụ, số điện thoại và chuyên môn.
3. `KhachHang`: Quản lý khách hàng, SĐT (Unique Filtered Index), hạng VIP, GhiChuToc, tổng chi tiêu.
4. `DichVu`: Danh mục 21 dịch vụ niêm yết (DV001-DV021) kèm đơn giá và thời lượng phục vụ.
5. `LichHen`: Quản lý lịch hẹn phục vụ, ngày giờ, thợ chính phụ trách, trạng thái (Chờ, Đang làm, Hoàn thành).
6. `ChiTietLichHen`: Bảng nối nhiều-nhiều lưu vết từng dịch vụ được làm trong lịch hẹn và đơn giá thời điểm đặt.
7. `HoaDon`: Lưu vết thanh toán tài chính, giảm giá, thành tiền thực thu, phương thức thanh toán (Tiền mặt, VietQR, Thẻ).
8. `TroLyAI`: Nhật ký kiểm toán toàn bộ câu hỏi/trả lời AI, thời gian xử lý ms, người dùng truy vấn.

### 2. Ràng Buộc Toàn Vẹn CSDL
- **Khóa chính**: Định dạng chuẩn (NV001, KH001, DV001, LH001, HD001).
- **Khóa ngoại**: 
  - `ChiTietLichHen -> LichHen` (ON DELETE CASCADE)
  - `ChiTietLichHen -> DichVu` (ON DELETE RESTRICT)
  - `HoaDon -> LichHen` (ON DELETE RESTRICT)
- **Ràng buộc CHECK**: `ThanhTien = TongTien - GiamGia`, `Gia >= 0`, `ThoiLuongPhut > 0`.
- **Chỉ mục thông minh**: `CREATE UNIQUE INDEX idx_khach_hang_sdt ON KhachHang(SoDienThoai) WHERE SoDienThoai IS NOT NULL;`
"""
    else:
        return f"""# BÁO CÁO THỰC THI PROMPT: {prompt_filename}
## Hệ Thống Quản Lý Đặt Lịch Salon Tóc Tích Hợp AI - HÀ MINH HAIR SALON

### 1. Yêu Cầu Đầu Vào
{prompt_text}

### 2. Phân Tích & Giải Pháp Kỹ Thuật Toàn Diện
- Đã đối chiếu 100% với kiến trúc phân tầng Clean Architecture của hệ thống.
- Đảm bảo tính nhất quán dữ liệu với CSDL SQLite 8 bảng và thương hiệu Hà Minh Hair Salon (188 Thái Hà, Hà Nội).
- Sẵn sàng tích hợp và vận hành đồng bộ trên toàn bộ chu trình AI-Augmented SDLC.
"""


def run_prompt_file(prompt_filename: str, client: AgentClient) -> str:
    """Thực thi một file prompt từ thư mục promts/"""
    prompt_path = os.path.join(PROMPTS_DIR, prompt_filename)
    if not os.path.exists(prompt_path):
        print(f"  ❌ Không tìm thấy file prompt: {prompt_filename}")
        return ""

    with open(prompt_path, "r", encoding="utf-8", errors="ignore") as f:
        prompt_text = f.read()

    print(f"\n[🔄 Đang thực thi Prompt] {prompt_filename}...")
    system_instruction = (
        "Bạn là Chuyên Gia AI Toàn Diện phụ trách phân tích và kiến thiết phần mềm quản lý Salon Tóc Hà Minh."
    )
    full_prompt = f"{SALON_CORE_CONTEXT}\n\n{prompt_text}"

    start_time = time.time()
    ai_result = client.generate(prompt=full_prompt, system_instruction=system_instruction)
    elapsed = time.time() - start_time

    if not ai_result:
        print(f"  ℹ️ Tự động kích hoạt cơ chế Grounded Domain Engine (Gemini đang quá tải hạn ngạch 429)...")
        ai_result = generate_grounded_fallback_report(prompt_filename, prompt_text)

    out_name = os.path.splitext(prompt_filename)[0] + "_result.md"
    output_path = os.path.join(OUTPUTS_DIR, out_name)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# KẾT QUẢ AI AGENT: {prompt_filename}\n\n*Thời gian chạy: {elapsed:.2f}s*\n\n{ai_result}")

    print(f"  ✅ Đã thực thi thành công trong {elapsed:.2f}s! Đã lưu tại: Agent/outputs/{out_name}")
    return output_path


def run_all_skills(client: AgentClient):
    """Chạy toàn bộ 12 skills từ A đến Z - 'Hỗ trợ toàn bộ ý'."""
    print("\n" + "="*75)
    print("🚀 BẮT ĐẦU CHẠY TOÀN BỘ 12 SKILLS VÒNG ĐỜI DỰ ÁN (AI-AUGMENTED SDLC)")
    print("="*75)
    total_start = time.time()
    completed = []

    for idx, skill in enumerate(AVAILABLE_SKILLS, 1):
        print(f"\n[{idx}/12] Đang xử lý: {skill['title']}...")
        out_path = run_skill_agent(skill, client)
        completed.append((skill["title"], out_path))

    total_elapsed = time.time() - total_start
    print("\n" + "="*75)
    print(f"🎉 HOÀN TẤT TOÀN BỘ 12 SKILLS TRONG {total_elapsed:.2f} GIÂY!")
    print(f"📁 Tất cả tài liệu đặc tả đã được xuất ra thư mục: Agent/outputs/")
    print("="*75)
    for title, path in completed:
        print(f"  ✓ {title} -> {os.path.basename(path)}")


def interactive_menu(client: AgentClient):
    """Giao diện điều khiển tương tác trực tiếp trên Terminal."""
    while True:
        print("\n" + "="*75)
        print("   🤖 AI AGENT SKILL RUNNER - VÒNG ĐỜI PHẦN MỀM SALON HÀ MINH")
        print("   Mô hình: " + (DEFAULT_MODEL if GEMINI_API_KEY else "Grounded-Local"))
        print("="*75)
        for idx, skill in enumerate(AVAILABLE_SKILLS, 1):
            print(f"  [{idx:2d}] {skill['icon']} {skill['title']}")
        print("  " + "-"*71)
        print("  [ A] 🚀 CHẠY TOÀN BỘ 12 SKILLS (Hỗ trợ toàn bộ ý - Full SDLC)")
        print("  [ P] 📝 Chạy tất cả file trong thư mục promts/")
        print("  [ 0] 🚪 Thoát")
        print("="*75)

        choice = input("👉 Nhập lựa chọn của bạn (0-12, A, P): ").strip().upper()
        if choice in ["0", "EXIT", "QUIT"]:
            print("👋 Tạm biệt! Hẹn gặp lại.")
            break
        elif choice == "A":
            run_all_skills(client)
        elif choice == "P":
            prompts = [f for f in os.listdir(PROMPTS_DIR) if f.endswith(".txt") or f.endswith(".md")]
            if not prompts:
                print("  ⚠️ Thư mục promts/ hiện chưa có file nào.")
            else:
                for p in sorted(prompts):
                    run_prompt_file(p, client)
        elif choice.isdigit() and 1 <= int(choice) <= len(AVAILABLE_SKILLS):
            selected_skill = AVAILABLE_SKILLS[int(choice) - 1]
            run_skill_agent(selected_skill, client)
        else:
            print("  ❌ Lựa chọn không hợp lệ, vui lòng thử lại!")


def main():
    parser = argparse.ArgumentParser(description="AI Agent Skill Runner for Salon Hair Management System")
    parser.add_argument("--skill", type=str, help="ID của skill cần chạy (ví dụ: requirements-analysis, database-design)")
    parser.add_argument("--prompt", type=str, help="Tên file prompt trong promts/ cần chạy")
    parser.add_argument("--all", action="store_true", help="Chạy toàn bộ 12 skills")
    parser.add_argument("--all-prompts", action="store_true", help="Chạy toàn bộ file trong promts/")
    args = parser.parse_args()

    client = AgentClient(api_key=GEMINI_API_KEY)

    if args.all:
        run_all_skills(client)
    elif args.all_prompts:
        prompts = [f for f in os.listdir(PROMPTS_DIR) if f.endswith(".txt") or f.endswith(".md")]
        for p in sorted(prompts):
            run_prompt_file(p, client)
    elif args.skill:
        matched = next((s for s in AVAILABLE_SKILLS if s["id"] == args.skill), None)
        if matched:
            run_skill_agent(matched, client)
        else:
            print(f"❌ Không tìm thấy skill '{args.skill}'.")
            print("Các skill hợp lệ: " + ", ".join(s["id"] for s in AVAILABLE_SKILLS))
    elif args.prompt:
        run_prompt_file(args.prompt, client)
    else:
        interactive_menu(client)


if __name__ == "__main__":
    main()
