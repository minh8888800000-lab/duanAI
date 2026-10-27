import subprocess
import json
import time
import os
import urllib.request
import socket
import base64
import hashlib
import struct

def run_chrome_test():
    chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
    port = 9222
    user_data = os.path.join(os.environ.get('TEMP', '.'), 'chrome_test_profile')
    
    # Launch Chrome
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
        # Get targets
        res = urllib.request.urlopen(f'http://127.0.0.1:{port}/json')
        targets = json.loads(res.read().decode())
        print(f"Found {len(targets)} targets")
        page_target = None
        for t in targets:
            if t.get('type') == 'page':
                page_target = t
                break
        
        if not page_target:
            print("No page target found!")
            return

        ws_url = page_target['webSocketDebuggerUrl']
        print("WebSocket URL:", ws_url)
        
        # Connect to websocket
        # ws_url looks like ws://127.0.0.1:9222/devtools/page/...
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
        if " 101 " not in resp and "101 WebSocket" not in resp:
            print("WebSocket handshake failed:", resp)
            return
        
        print("WebSocket connected!")
        
        # Helper to send WS frame
        msg_id = [1]
        def send_cmd(method, params=None):
            mid = msg_id[0]
            msg_id[0] += 1
            payload = json.dumps({"id": mid, "method": method, "params": params or {}}).encode()
            length = len(payload)
            frame = bytearray([0x81]) # FIN + text
            # Mask bit must be 1 for client -> server
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
            if not header or len(header) < 2:
                return None
            b1, b2 = header[0], header[1]
            length = b2 & 0x7f
            if length == 126:
                length = struct.unpack('>H', s.recv(2))[0]
            elif length == 127:
                length = struct.unpack('>Q', s.recv(8))[0]
            data = bytearray()
            while len(data) < length:
                chunk = s.recv(length - len(data))
                if not chunk:
                    break
                data.extend(chunk)
            return data.decode(errors='ignore')

        # Enable Console and Runtime
        send_cmd("Runtime.enable")
        send_cmd("Log.enable")
        send_cmd("Page.enable")
        
        # Read initial events for 2 seconds
        s.settimeout(2.0)
        start_time = time.time()
        while time.time() - start_time < 3:
            try:
                frame_data = read_frame()
                if frame_data:
                    data = json.loads(frame_data)
                    if data.get('method') == 'Runtime.exceptionThrown':
                        print("\n[EXCEPTION THROWN]:", json.dumps(data, indent=2, ensure_ascii=False))
                    elif data.get('method') == 'Runtime.consoleAPICalled':
                        print("\n[CONSOLE]:", data['params']['type'], [arg.get('value', arg.get('description')) for arg in data['params']['args']])
            except socket.timeout:
                break
            except Exception as e:
                pass
        
        # Now test calling openLoginModal()
        print("\n--- Evaluating openLoginModal() ---")
        mid_login = send_cmd("Runtime.evaluate", {"expression": "openLoginModal()", "returnByValue": True})
        # Test calling scrollToGuestBooking()
        print("\n--- Evaluating scrollToGuestBooking() ---")
        mid_booking = send_cmd("Runtime.evaluate", {"expression": "scrollToGuestBooking()", "returnByValue": True})
        
        # Read responses
        start_time = time.time()
        while time.time() - start_time < 3:
            try:
                frame_data = read_frame()
                if frame_data:
                    data = json.loads(frame_data)
                    if data.get('id') in (mid_login, mid_booking):
                        print(f"Eval result (id={data.get('id')}):", json.dumps(data, indent=2, ensure_ascii=False))
                    elif data.get('method') == 'Runtime.exceptionThrown':
                        print("\n[EXCEPTION THROWN]:", json.dumps(data, indent=2, ensure_ascii=False))
                    elif data.get('method') == 'Runtime.consoleAPICalled':
                        print("\n[CONSOLE]:", data['params']['type'], [arg.get('value', arg.get('description')) for arg in data['params']['args']])
            except socket.timeout:
                break
            except Exception as e:
                pass
                
        # Also check DOM state of modal-login and scroll position
        mid_check = send_cmd("Runtime.evaluate", {
            "expression": "({ modalDisplay: document.getElementById('modal-login')?.style.display, modalOffset: document.getElementById('modal-login')?.getBoundingClientRect(), scrollY: window.scrollY })",
            "returnByValue": True
        })
        time.sleep(0.5)
        try:
            while True:
                f = read_frame()
                if not f: break
                d = json.loads(f)
                if d.get('id') == mid_check:
                    print("DOM Check:", json.dumps(d.get('result', {}).get('result', {}).get('value', {}), indent=2))
                    break
        except:
            pass

    finally:
        proc.kill()

if __name__ == '__main__':
    run_chrome_test()
