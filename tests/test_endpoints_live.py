import urllib.request
import json

def test():
    # 1. HTML check
    req = urllib.request.Request('http://127.0.0.1:5000/')
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode('utf-8')
    assert 'HÀ MINH' in html or 'HA MINH' in html, 'Brand not in HTML'
    assert '187.500.000' in html, 'Total revenue not pre-rendered in HTML!'
    assert '41.000.000' in html, 'Today revenue not pre-rendered in HTML!'
    print('1. GET /: OK, Brand HÀ MINH and Pre-rendered Revenue 187.500.000 / 41.000.000 verified in HTML!'.encode('ascii', 'ignore').decode())

    # 2. Reports summary check
    req = urllib.request.Request('http://127.0.0.1:5000/api/reports/summary')
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
    assert res['success'] is True
    kpi = res['kpi']
    print(f"2. GET /api/reports/summary: OK, Tong DT = {kpi['tong_doanh_thu']:,} VND | DT Hom nay = {kpi['doanh_thu_hom_nay']:,} VND | AOV = {kpi['aov']:,} VND")

    # 3. Reports invoices check
    req = urllib.request.Request('http://127.0.0.1:5000/api/reports/invoices')
    with urllib.request.urlopen(req) as resp:
        inv_res = json.loads(resp.read().decode('utf-8'))
    assert inv_res['success'] is True
    print(f"3. GET /api/reports/invoices: OK, Count = {inv_res['count']} invoices")
    assert inv_res['count'] >= 25, 'Expected at least 25 invoices'

    # 4. AI Chatbot check
    payload = json.dumps({'message': 'Chào bạn, cho tôi biết salon của bạn là gì?'}).encode('utf-8')
    req = urllib.request.Request('http://127.0.0.1:5000/api/ai/chat', data=payload, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        ai_res = json.loads(resp.read().decode('utf-8'))
    reply = ai_res.get('reply', '')
    print('4. POST /api/ai/chat: OK, reply length =', len(reply))
    assert 'HÀ MINH' in reply, f'Brand not mentioned by AI: {reply[:100]}'
    print('Brand "HÀ MINH" confirmed in AI response!')

    print("\nALL VERIFICATIONS PASSED 100% PERFECTLY!")

if __name__ == '__main__':
    test()
