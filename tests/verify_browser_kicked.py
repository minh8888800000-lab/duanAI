import subprocess
import json
import time
import os
import urllib.request
import socket
import base64
import struct
import sys

sys.stdout.reconfigure(encoding='utf-8')

def run_test():
    chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
    port = 9224
    user_data = os.path.join(os.environ.get('TEMP', '.'), 'chrome_test_profile_kicked')
    
    proc = subprocess.Popen([
        chrome_path,
        '--headless=new',
        f'--remote-debugging-port={port}',
        f'--user-data-dir={user_data}',
        '--disable-gpu',
        '--no-first-run',
        '--no-default-browser-check',
        'http://127.0.0.1:5000/'
    ])
    
    time.sleep(2)
    
    try:
        res = urllib.request.urlopen(f'http://127.0.0.1:{port}/json')
        targets = json.loads(res.read().decode())
        page_target = next((t for t in targets if t.get('type') == 'page'), None)
        assert page_target, "No page target found in Chrome"
        
        ws_url = page_target['webSocketDebuggerUrl']
        from urllib.parse import urlparse
        u = urlparse(ws_url)
        s = socket.socket()
        s.connect((u.hostname, u.port))
        
        key = base64.b64encode(os.urandom(16)).decode()
        handshake = (
            f"GET {u.path} HTTP/1.1\r\n"
            f"Host: {u.hostname}:{u.port}\r\n"
            f"Upgrade: websocket\r\n"
            f"Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            f"Sec-WebSocket-Version: 13\r\n\r\n"
        )
        s.sendall(handshake.encode())
        resp = s.recv(4096).decode(errors='ignore')
        assert "101" in resp, f"WebSocket handshake failed: {resp}"
        
        msg_id = [1]
        def send_cmd(method, params=None):
            mid = msg_id[0]
            msg_id[0] += 1
            payload = json.dumps({"id": mid, "method": method, "params": params or {}}).encode()
            length = len(payload)
            frame = bytearray([0x81])
            mask = os.urandom(4)
            if length < 126:
                frame.append(0x80 | length)
            elif length <= 65535:
                frame.append(0x80 | 126)
                frame.extend(struct.pack('>H', length))
            else:
                frame.append(0x80 | 127)
                frame.extend(struct.pack('>Q', length))
            frame.extend(mask)
            masked_payload = bytearray(b ^ mask[i % 4] for i, b in enumerate(payload))
            frame.extend(masked_payload)
            s.sendall(frame)
            return mid

        def read_frame():
            header = s.recv(2)
            if not header or len(header) < 2: return None
            b1, b2 = header[0], header[1]
            length = b2 & 0x7f
            if length == 126:
                length = struct.unpack('>H', s.recv(2))[0]
            elif length == 127:
                length = struct.unpack('>Q', s.recv(8))[0]
            data = bytearray()
            while len(data) < length:
                chunk = s.recv(length - len(data))
                if not chunk: break
                data.extend(chunk)
            return data.decode(errors='ignore')

        send_cmd("Runtime.enable")
        
        def evaluate(js_code):
            mid = send_cmd("Runtime.evaluate", {"expression": js_code, "returnByValue": True, "awaitPromise": True})
            start = time.time()
            s.settimeout(4.0)
            while time.time() - start < 5:
                try:
                    f = read_frame()
                    if f:
                        d = json.loads(f)
                        if d.get('id') == mid:
                            res = d.get('result', {}).get('result', {})
                            if 'value' in res:
                                return res['value']
                            return res
                except socket.timeout:
                    break
            return None

        time.sleep(1)

        # 1. Trình duyệt A đăng nhập admin
        login_res = evaluate("""
            new Promise(async (resolve) => {
                await quickLogin('admin', 'admin123');
                setTimeout(() => {
                    resolve({
                        role: state.currentRole,
                        user: state.currentUser?.username,
                        heartbeatRunning: Boolean(sessionHeartbeatTimer)
                    });
                }, 400);
            })
        """)
        print("[TEST 1] Browser A Logged in:", login_res)
        assert login_res['role'] == 'Admin', "Login failed"
        assert login_res['heartbeatRunning'], "Heartbeat should be running!"
        print("  -> PASSED: Browser A logged in and heartbeat is actively monitoring session!")

        # 2. Thiết bị B (máy khác) đăng nhập qua API
        req_b = urllib.request.Request(
            'http://127.0.0.1:5000/api/auth/login',
            data=json.dumps({'username': 'admin', 'password': 'admin123'}).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req_b) as resp_b:
            data_b = json.loads(resp_b.read().decode('utf-8'))
        assert data_b.get('success'), f"Device B login failed: {data_b}"
        print("[TEST 2] Device B logged in externally. Device A session is now invalid.")

        # 3. Chờ 4 giây để heartbeat của Browser A tự động kích hoạt
        print("  Waiting 4.5 seconds for Browser A heartbeat to detect concurrent login...")
        time.sleep(4.5)

        # 4. Kiểm tra trạng thái Browser A: modal-session-kicked hiển thị và state bị xóa
        kicked_check = evaluate("""
            (() => {
                const modal = document.getElementById('modal-session-kicked');
                const isModalVisible = modal && (modal.style.display === 'flex' || modal.classList.contains('active'));
                const hasToken = Boolean(state.authToken || localStorage.getItem('salon_auth_token'));
                const hasUser = Boolean(state.currentUser);
                const guestView = document.getElementById('view-guest-home')?.style.display !== 'none';
                return {
                    isModalVisible,
                    hasToken,
                    hasUser,
                    guestView
                };
            })()
        """)
        print("[TEST 3] Browser A Kicked State:", kicked_check)
        assert kicked_check['isModalVisible'], "Kicked modal should be displayed!"
        assert not kicked_check['hasToken'], "Auth token must be cleared!"
        assert not kicked_check['hasUser'], "Current user must be cleared!"
        assert kicked_check['guestView'], "Must be returned to guest view!"
        print("  -> PASSED: Browser A was automatically kicked out! Alert modal popped up and session was terminated!")

        print("\n=======================================================")
        print("🎉 SINGLE DEVICE CONCURRENT LOGIN VERIFICATION PASSED!")
        print("=======================================================")

    finally:
        proc.kill()

if __name__ == '__main__':
    run_test()
