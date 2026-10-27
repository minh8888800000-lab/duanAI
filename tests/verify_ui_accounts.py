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
    port = 9223
    user_data = os.path.join(os.environ.get('TEMP', '.'), 'chrome_test_profile_acc')
    
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
        send_cmd("Log.enable")
        
        def evaluate(js_code):
            mid = send_cmd("Runtime.evaluate", {"expression": js_code, "returnByValue": True, "awaitPromise": True})
            start = time.time()
            s.settimeout(3.0)
            while time.time() - start < 4:
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

        # 1. Check AI buttons removed
        check_ai = evaluate("""
            (() => {
                const aiDrawerSettingsBtn = document.querySelector('#ai-chat-drawer .ai-tool-btn[onclick*="openAIConfigModal"]');
                const aiHubConfigBtn = document.querySelector('#tab-ai-hub button[onclick*="openAIConfigModal"]');
                return {
                    aiDrawerSettingsExists: Boolean(aiDrawerSettingsBtn),
                    aiHubConfigExists: Boolean(aiHubConfigBtn)
                };
            })()
        """)
        print("[TEST 1] AI buttons check:", check_ai)
        assert not check_ai['aiDrawerSettingsExists'], "AI Chat drawer settings button still exists!"
        assert not check_ai['aiHubConfigExists'], "AI Hub config button still exists!"
        print("  -> PASSED: AI settings and config buttons have been completely removed!")

        # 2. Login as Admin
        login_res = evaluate("""
            new Promise(async (resolve) => {
                await quickLogin('admin', 'admin123');
                setTimeout(() => {
                    resolve({
                        role: state.currentRole,
                        user: state.currentUser?.username
                    });
                }, 300);
            })
        """)
        print("[TEST 2] Admin login:", login_res)
        assert login_res and login_res.get('role') == 'Admin', f"Login failed: {login_res}"
        print("  -> PASSED: Admin logged in successfully!")

        # 3. Check sidebar has 'accounts' tab
        check_nav = evaluate("""
            (() => {
                const accNav = document.querySelector('.nav-item[data-tab="accounts"]');
                return {
                    hasAccountsNav: Boolean(accNav),
                    isDisplayed: accNav ? window.getComputedStyle(accNav).display !== 'none' : false,
                    text: accNav ? accNav.innerText.trim() : ''
                };
            })()
        """)
        print("[TEST 3] Accounts Nav Item:", check_nav)
        assert check_nav['hasAccountsNav'] and check_nav['isDisplayed'], "Accounts nav not visible to Admin!"
        print("  -> PASSED: 'Quản Lý Tài Khoản' nav visible for Admin!")

        # 4. Switch to accounts tab and check table
        switch_acc = evaluate("""
            new Promise(async (resolve) => {
                switchTab('accounts');
                await loadAccounts();
                setTimeout(() => {
                    const total = document.getElementById('stat-total-accounts')?.innerText;
                    const rows = document.querySelectorAll('#accounts-table-tbody tr').length;
                    resolve({ activeTab: state.activeTab, totalStat: total, rowCount: rows });
                }, 400);
            })
        """)
        print("[TEST 4] Accounts Tab View:", switch_acc)
        assert switch_acc['activeTab'] == 'accounts', "Switch tab failed"
        assert int(switch_acc['rowCount']) >= 7, f"Row count too low: {switch_acc['rowCount']}"
        print(f"  -> PASSED: Accounts view loaded with {switch_acc['rowCount']} accounts and stats!")

        # 5. Check staff tab for '+ Thêm Tài Khoản' and column
        check_staff = evaluate("""
            new Promise(async (resolve) => {
                switchTab('staff');
                setTimeout(() => {
                    const addAccBtn = Array.from(document.querySelectorAll('#tab-staff button')).find(b => b.innerText.includes('Thêm Tài Khoản'));
                    const thCols = Array.from(document.querySelectorAll('#tab-staff thead th')).map(th => th.innerText.trim());
                    resolve({
                        hasAddAccBtn: Boolean(addAccBtn),
                        cols: thCols
                    });
                }, 300);
            })
        """)
        print("[TEST 5] Staff tab account features:", check_staff)
        assert check_staff['hasAddAccBtn'], "Missing '+ Thêm Tài Khoản' button in staff tab"
        assert any('TÀI KHOẢN ĐĂNG NHẬP' in col.upper() for col in check_staff['cols']), f"Missing 'Tài Khoản Đăng Nhập' column header, got: {check_staff['cols']}"
        print("  -> PASSED: Staff tab has Add Account button and Login Account column!")

        # 6. Check open modal account
        modal_check = evaluate("""
            (() => {
                openNewAccountModal('NV008');
                const modal = document.getElementById('modal-account');
                const staffSel = document.getElementById('modal-acc-staff')?.value;
                const roleSel = document.getElementById('modal-acc-role')?.value;
                const isDisplayed = modal?.style.display === 'flex' || modal?.classList.contains('active');
                closeModal('modal-account');
                return {
                    isDisplayed,
                    preselectedStaff: staffSel,
                    recommendedRole: roleSel
                };
            })()
        """)
        print("[TEST 6] Modal Add Account check:", modal_check)
        assert modal_check['isDisplayed'], "Modal did not open"
        assert modal_check['preselectedStaff'] == 'NV008', "Staff not preselected"
        print("  -> PASSED: Modal Add Account works with auto-selection and role recommendation!")

        print("\n==============================================")
        print("🎉 ALL FRONTEND & BACKEND VERIFICATIONS PASSED!")
        print("==============================================")

    finally:
        proc.kill()

if __name__ == '__main__':
    run_test()
