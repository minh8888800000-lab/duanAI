# -*- coding: utf-8 -*-
import sys
import io
import urllib.request
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
sys.path.insert(0, os.path.abspath('.'))

from backend.services.auth_service import AuthService
from backend.db import get_db_connection

def send_chat(msg, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    payload = json.dumps({'message': msg}, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request('http://127.0.0.1:5000/api/ai/chat', data=payload, headers=headers)
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read().decode('utf-8'))

print("=== 1. Test Khách Vãng Lai (Không có token / Không có quyền) ===")
r1 = send_chat("sửa giá cắt tóc nam thành 150k")
print("Price updated:", r1.get('price_updated'))
print("Reply:", r1['reply'][:120] + "...")

print("\n=== 2. Test Lễ Tân (Có token nhưng vai trò LeTan) ===")
letan_tok = AuthService.login('letan01', 'letan123')['token']
r2 = send_chat("đổi giá cắt tóc nam lên 180k", token=letan_tok)
print("Price updated:", r2.get('price_updated'))
print("Reply:", r2['reply'][:120] + "...")

print("\n=== 3. Test Admin (Có token vai trò Admin -> CÓ QUYỀN) ===")
admin_tok = AuthService.login('admin', 'admin123')['token']
r3 = send_chat("sửa giá cắt tóc nam thành 200k", token=admin_tok)
print("Price updated:", r3.get('price_updated'))
print("Reply:\n", r3['reply'])

conn = get_db_connection()
c = conn.cursor()
c.execute("SELECT MaDichVu, TenDichVu, GiaTien FROM DichVu WHERE MaDichVu = 'DV014'")
print("\n[DB Result Sau Khi Admin Sửa]:", dict(c.fetchone()))
conn.close()
