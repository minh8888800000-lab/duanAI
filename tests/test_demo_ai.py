import sys
import json
import urllib.request

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

def ask_ai(question):
    print("=" * 60)
    print(f"👉 CÂU HỎI: {question}")
    payload = json.dumps({"message": question}).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:5000/api/ai/chat",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"🤖 ĐỘNG CƠ XỬ LÝ: {data.get('model_used')} | Thời gian: {data.get('duration_ms')}ms")
            print(f"💬 TRẢ LỜI:\n{data.get('reply')}\n")
    except Exception as e:
        print(f"Lỗi: {e}")

if __name__ == "__main__":
    ask_ai("Vì sao tóc tẩy cấp độ 8-9 không được uốn nóng Collagen?")
    ask_ai("Bảng giá các dịch vụ uốn và nhuộm tại salon?")
    ask_ai("Hôm nay có thợ nào đang rảnh để cắt tóc không?")
