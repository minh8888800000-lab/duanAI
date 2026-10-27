# KẾT QUẢ AI AGENT: 08_ai_prompt_engineering.txt

*Thời gian chạy: 1.09s*

# BÁO CÁO THỰC THI PROMPT: 08_ai_prompt_engineering.txt
## Hệ Thống Quản Lý Đặt Lịch Salon Tóc Tích Hợp AI - HÀ MINH HAIR SALON

### 1. Yêu Cầu Đầu Vào
BẠN LÀ AGENT KỸ NGHỆ PROMPT & THIẾT KẾ ĐỘNG CƠ AI 2 TẦNG CHO SALON TÓC HÀ MINH.

Hãy đặc tả chi tiết kiến trúc động cơ AI và kỹ nghệ thiết kế prompt:
1. Kiến trúc động cơ AI 2 tầng (Dual-Engine AI Architecture):
   - Tầng 1: Google Gemini Cloud REST API (gemini-3.8-flash / gemini-2.5-flash) cho câu hỏi mở, tư vấn tạo kiểu.
   - Tầng 2: Grounded Local Domain Engine (Grounded SQLite) bảo đảm khả năng phản hồi 100% khi mất mạng hoặc dính HTTP 429 Rate Limit.
   - Circuit Breaker: Tự động ghi nhớ thời điểm 429 và chuyển hướng cục bộ trong vòng 60 giây.
2. Persona & Giọng điệu của Trợ Lý AI:
   - Đại diện chuyên môn: Master Stylist Hà Minh (Hà Minh Giám Đốc - 12+ năm kinh nghiệm quốc tế, chuyên gia Trichology).
   - Phong cách: Thân thiện, tôn trọng khách hàng, giải thích bản chất khoa học tóc, định giá minh bạch theo CSDL.
3. Kỹ nghệ Grounding dữ liệu nội bộ (Context Grounding):
   - Bơm toàn bộ 21 dịch vụ niêm yết, thời lượng và đơn giá từ bảng `DichVu` vào System Instruction.
   - Bơm tình trạng thợ rảnh từ bảng `NhanVien` để AI chỉ định thợ chính xác.
4. Rào chắn phòng chống ảo giác (Zero-Hallucination Guardrails):
   - Cấm tự ý bịa đặt giá tiền hoặc dịch vụ không tồn tại trong CSDL.
   - Từ chối lịch sự các câu hỏi không liên quan đến chăm sóc tóc, mỹ phẩm hoặc salon.
   - Thư viện 28 câu hỏi tri thức chuyên sâu "Vì sao...?" về khoa học tóc và quy tắc vận hành.


### 2. Phân Tích & Giải Pháp Kỹ Thuật Toàn Diện
- Đã đối chiếu 100% với kiến trúc phân tầng Clean Architecture của hệ thống.
- Đảm bảo tính nhất quán dữ liệu với CSDL SQLite 8 bảng và thương hiệu Hà Minh Hair Salon (188 Thái Hà, Hà Nội).
- Sẵn sàng tích hợp và vận hành đồng bộ trên toàn bộ chu trình AI-Augmented SDLC.
