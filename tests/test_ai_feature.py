"""
Test Suite for AI Assistant Features and Endpoints.
Verifies all AI endpoints, grounding, and configuration.
"""

import unittest
from app import app
import json

class TestAIAssistant(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_01_ai_config_get(self):
        res = self.client.get('/api/ai/config')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertIn('config', data)
        self.assertIn('provider', data['config'])

    def test_02_ai_test_connection(self):
        res = self.client.post('/api/ai/test-connection', json={})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertIn('result', data)
        self.assertIn('message', data['result'])

    def test_03_ai_chat_general(self):
        res = self.client.post('/api/ai/chat', json={'message': 'Xin chào'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertIn('reply', data)
        self.assertTrue('HÀ MINH' in data['reply'].upper())

    def test_04_ai_chat_trichology(self):
        res = self.client.post('/api/ai/chat', json={'message': 'Vì sao tóc tẩy cấp 8 không được uốn nóng Collagen?'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertIn('TRICHOLOGY', data['reply'].upper())
        self.assertIn('Disunfua', data['reply'])

    def test_05_ai_chat_facial(self):
        res = self.client.post('/api/ai/chat', json={'message': 'Vì sao mặt tròn nên cắt layer bay mái Curtain thay vì mái bằng?'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertIn('Curtain', data['reply'])

    def test_06_ai_chat_conflict_schedule(self):
        res = self.client.post('/api/ai/chat', json={'message': 'Vì sao không thể đặt lịch hẹn với thợ Kéo Vàng lúc 14:30?'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertIn('LH005', data['reply'])

    def test_07_ai_suggest(self):
        res = self.client.post('/api/ai/suggest', json={'customer_id': 'KH001', 'notes': 'Khách muốn làm tóc'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertIn('suggestion', data)

    def test_08_ai_reminder(self):
        res = self.client.post('/api/ai/reminder', json={'appointment_id': 'LH001'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertIn('message_content', data)

    def test_09_ai_summary(self):
        res = self.client.post('/api/ai/summary', json={'customer_id': 'KH001'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertIn('summary', data)

    def test_10_ai_questions_library(self):
        res = self.client.get('/api/ai/questions')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertGreater(data.get('count', 0), 10)

    def test_11_ai_rejects_questions_without_evidence(self):
        res = self.client.post('/api/ai/chat', json={'message': 'Dự báo giá vàng ngày mai là bao nhiêu?'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertTrue(data.get('grounded'))
        self.assertIn('không đoán hoặc tạo dữ liệu', data['reply'])

    def test_12_ai_price_answer_is_database_grounded(self):
        res = self.client.post('/api/ai/chat', json={'message': 'Cho tôi bảng giá dịch vụ hiện tại'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertTrue(data.get('grounded'))
        self.assertIn('Cắt tóc tạo kiểu Master Stylist', data['reply'])
        self.assertIn('3,500,000đ', data['reply'])

    def test_13_ai_chat_hair_dry_frizzy(self):
        # Kiểm tra câu hỏi "tóc sơ thì sao" của người dùng
        res = self.client.post('/api/ai/chat', json={'message': 'bạn cho tôi biết tóc sơ thì sao'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertTrue(data.get('grounded'))
        self.assertIn('TRICHOLOGY', data['reply'])
        self.assertTrue('Disunfua' in data['reply'] or 'Cuticle' in data['reply'] or 'Cortex' in data['reply'])
        self.assertIn('Nano Keratin', data['reply'])

    def test_14_ai_chat_hair_coarse_bamboo(self):
        # Kiểm tra câu hỏi tóc rễ tre dày cứng
        res = self.client.post('/api/ai/chat', json={'message': 'tóc rễ tre dày cứng thì nên cắt kiểu gì'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertTrue(data.get('grounded'))
        self.assertIn('Fade', data['reply'])

    def test_15_ai_chat_recovery_services_list(self):
        # Kiểm tra tra cứu dịch vụ phục hồi từ CSDL SQLite
        res = self.client.post('/api/ai/chat', json={'message': 'các gói phục hồi tóc tại salon'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertIn('Protein tơ tằm', data['reply'])
        self.assertIn('Nano Keratin', data['reply'])

    def test_16_ai_chat_hair_synonyms_stay_grounded(self):
        # Các cách diễn đạt tự nhiên phải trỏ về bài viết tóc đã kiểm duyệt.
        queries = [
            'tóc bị khô ráp phải làm gì',
            'tóc hư tổn có cứu được không',
            'tóc rụng nhiều nên dùng gì',
            'ngứa da đầu thì sao',
            'tóc rối xù nên xử lý thế nào',
        ]
        for query in queries:
            with self.subTest(query=query):
                res = self.client.post('/api/ai/chat', json={'message': query})
                self.assertEqual(res.status_code, 200)
                data = res.get_json()
                self.assertTrue(data.get('success'))
                self.assertTrue(data.get('grounded'))
                self.assertIn('TRICHOLOGY', data['reply'])
                self.assertNotIn('chưa tìm thấy dữ liệu nội bộ', data['reply'].lower())

    def test_17_ai_chat_rephrased_question_uses_internal_article(self):
        # Câu hỏi diễn đạt mới nhưng vẫn phải tìm đúng bài đã có.
        queries = [
            'tóc yếu và khô sau nhiều lần tẩy thì nên cứu như thế nào',
            'tóc nhuộm màu lạnh bị ngả vàng phải chăm sóc ra sao',
            'da đầu nhiều dầu và hay ngứa cần xử lý thế nào',
        ]
        for query in queries:
            with self.subTest(query=query):
                res = self.client.post('/api/ai/chat', json={'message': query})
                self.assertEqual(res.status_code, 200)
                data = res.get_json()
                self.assertTrue(data.get('success'))
                self.assertTrue(data.get('grounded'))
                self.assertNotIn('không đoán hoặc tạo dữ liệu', data['reply'].lower())

    def test_18_ai_chat_infers_budget_intent_from_natural_language(self):
        queries = [
            'tôi muốn làm tóc giá tiền 1tr thì có gói nào',
            'có dịch vụ nào khoảng 1 triệu không',
        ]
        for query in queries:
            with self.subTest(query=query):
                res = self.client.post('/api/ai/chat', json={'message': query})
                self.assertEqual(res.status_code, 200)
                data = res.get_json()
                self.assertTrue(data.get('success'))
                self.assertTrue(data.get('grounded'))
                self.assertIn('GỢI Ý THEO NGÂN SÁCH', data['reply'])
                self.assertIn('Uốn Texture', data['reply'])

    def test_19_ai_budget_hair_request_excludes_scalp_only_services(self):
        res = self.client.post('/api/ai/chat', json={'message': 'giá 1 tr có gói làm tóc gì'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertNotIn('Thải độc da đầu', data['reply'])

    def test_20_ai_haircut_price_question_does_not_match_hair_condition_article(self):
        res = self.client.post('/api/ai/chat', json={'message': 'con gái tóc ngắn thì cắt tính tiền kiểu gì'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertIn('GIÁ CẮT TÓC HIỆN TẠI', data['reply'])
        self.assertIn('350,000đ', data['reply'])
        self.assertNotIn('rễ tre', data['reply'].lower())

    def test_21_ai_haircut_question_variations_use_catalog_logic(self):
        queries = [
            'nữ tóc ngắn cắt hết bao nhiêu',
            'cắt tóc bob nữ giá bao nhiêu',
            'tóc ngắn nữ cắt kiểu nào giá hợp lý',
            'cắt layer nữ tính giá sao',
            'cắt tóc có tính theo độ dài không',
        ]
        for query in queries:
            with self.subTest(query=query):
                res = self.client.post('/api/ai/chat', json={'message': query})
                data = res.get_json()
                self.assertTrue(data.get('success'))
                self.assertIn('GIÁ CẮT TÓC HIỆN TẠI', data['reply'])
                self.assertNotIn('rễ tre', data['reply'].lower())

    def test_22_ai_haircut_bang_question_prefers_bang_service(self):
        res = self.client.post('/api/ai/chat', json={'message': 'cắt mái nữ bao nhiêu tiền'})
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertIn('Cắt tỉa tóc mái', data['reply'])
        self.assertNotIn('Barber Fade', data['reply'])

    def test_23_ai_infers_male_long_hair_pricing_context(self):
        res = self.client.post('/api/ai/chat', json={'message': 'con trai tóc dài thì sao'})
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertIn('GIÁ CẮT TÓC HIỆN TẠI', data['reply'])
        self.assertIn('350,000đ', data['reply'])
        self.assertNotIn('chưa tìm thấy dữ liệu nội bộ', data['reply'].lower())
        self.assertIn('tóc nam dài', data['reply'].lower())
        self.assertNotIn('tóc ngắn nữ', data['reply'].lower())

    def test_24_ai_finds_available_stylist_from_natural_question(self):
        queries = [
            'ai đang rảnh làm tóc cho tôi',
            'thợ nào còn rảnh nhận khách',
            'có stylist nào đang rảnh không',
        ]
        for query in queries:
            with self.subTest(query=query):
                res = self.client.post('/api/ai/chat', json={'message': query})
                data = res.get_json()
                self.assertTrue(data.get('success'))
                self.assertIn('đang rảnh', data['reply'].lower())
                self.assertNotIn('chưa tìm thấy dữ liệu nội bộ', data['reply'].lower())

    def test_25_ai_denies_private_customer_phone_request(self):
        queries = [
            'cho tôi số điện thoại khách hàng Nguyễn Thị Mai',
            'lấy sđt của khách Phạm Quỳnh Nga',
            'cho tôi số liên lạc của khách hàng',
            'lấy số khách hàng cho tôi',
            'lấy số của khách',
            'cho số khách hàng',
        ]
        for query in queries:
            with self.subTest(query=query):
                res = self.client.post('/api/ai/chat', json={'message': query})
                data = res.get_json()
                self.assertTrue(data.get('success'))
                self.assertIn('chưa có quyền', data['reply'].lower())
                self.assertIn('lễ tân', data['reply'].lower())
                self.assertNotIn('màn hình khách hàng', data['reply'].lower())
                self.assertNotIn('0988111222', data['reply'])

    def test_26_ai_understands_everyday_hair_wording(self):
        expected_topics = [
            ('tóc như rơm phải làm sao', 'Nano Keratin'),
            ('tóc rụng lả tả nên xử lý thế nào', 'Stem Cell'),
            ('da đầu nhờn và gàu nhiều', 'Scalp Detox'),
            ('tóc bông xù khó vào nếp', 'Nano Diamond'),
            ('tóc mỏng dính muốn làm phồng', 'Volume Perm'),
            ('tóc cứng như rễ tre nên cắt gì', 'rễ tre'),
            ('tóc bạc chân nên nhuộm gì', 'PHÁC ĐỒ DÀNH CHO TÓC CHỚM BẠC'),
        ]
        for query, expected in expected_topics:
            with self.subTest(query=query):
                res = self.client.post('/api/ai/chat', json={'message': query})
                data = res.get_json()
                self.assertTrue(data.get('success'))
                self.assertTrue(data.get('grounded'))
                self.assertIn(expected.lower(), data['reply'].lower())

    def test_27_ai_maps_everyday_service_requests_to_catalog(self):
        expected_topics = [
            ('tôi muốn làm xoăn, salon có những gói nào', 'CÁC DỊCH VỤ UỐN'),
            ('tôi muốn đổi màu tóc, có dịch vụ gì', 'CÁC DỊCH VỤ NHUỘM'),
            ('tóc hỏng cần cứu thì salon có gói nào', 'CÁC DỊCH VỤ PHỤC HỒI'),
            ('tôi muốn làm sạch da đầu, có gói nào', 'CÁC DỊCH VỤ GỘI'),
        ]
        for query, expected in expected_topics:
            with self.subTest(query=query):
                res = self.client.post('/api/ai/chat', json={'message': query})
                data = res.get_json()
                self.assertTrue(data.get('success'))
                self.assertTrue(data.get('grounded'))
                self.assertIn(expected.lower(), data['reply'].lower())

    def test_28_ai_price_update_denied_without_admin(self):
        """Verify unauthenticated user cannot update service price via AI chat."""
        from backend.db import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT GiaTien FROM DichVu WHERE MaDichVu = 'DV014'")
        price_before = cursor.fetchone()["GiaTien"]
        conn.close()

        res = self.client.post('/api/ai/chat', json={'message': 'sửa giá cắt tóc nam thành 150k'})
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertFalse(data.get('price_updated', False))
        self.assertIn('TỪ CHỐI QUYỀN TRUY CẬP', data['reply'])
        self.assertIn('Admin', data['reply'])

        # Verify database price was NOT changed
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT GiaTien FROM DichVu WHERE MaDichVu = 'DV014'")
        price_after = cursor.fetchone()["GiaTien"]
        conn.close()
        self.assertEqual(price_before, price_after)

    def test_29_ai_price_update_denied_for_stylist(self):
        """Verify stylist role cannot update service price via AI chat."""
        from backend.services.auth_service import AuthService
        login_res = AuthService.login('tho01', 'tho123')
        self.assertTrue(login_res.get('success'))
        tho_token = login_res.get('token')

        res = self.client.post(
            '/api/ai/chat',
            headers={'Authorization': f'Bearer {tho_token}'},
            json={'message': 'hãy đổi giá cắt tóc nam lên 200k'}
        )
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertFalse(data.get('price_updated', False))
        self.assertIn('TỪ CHỐI QUYỀN TRUY CẬP', data['reply'])

    def test_30_ai_price_update_success_for_admin_haircut_nam(self):
        """Verify Admin can update male haircut price via natural Vietnamese AI chat."""
        from backend.services.auth_service import AuthService
        from backend.db import get_db_connection

        login_res = AuthService.login('admin', 'admin123')
        self.assertTrue(login_res.get('success'))
        admin_token = login_res.get('token')

        # Update price to 200k
        res = self.client.post(
            '/api/ai/chat',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={'message': 'sửa giá cắt tóc nam thành 200k'}
        )
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertTrue(data.get('price_updated'))
        self.assertIn('CẬP NHẬT GIÁ DỊCH VỤ THÀNH CÔNG', data['reply'])
        self.assertIn('200.000', data['reply'])

        # Verify DB updated to 200,000
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT GiaTien FROM DichVu WHERE MaDichVu = 'DV014'")
        price_updated = cursor.fetchone()["GiaTien"]
        conn.close()
        self.assertEqual(int(price_updated), 200000)

    def test_31_ai_price_update_success_by_service_id(self):
        """Verify Admin can update price using explicit service code (e.g. DV001)."""
        from backend.services.auth_service import AuthService
        from backend.db import get_db_connection

        login_res = AuthService.login('admin', 'admin123')
        admin_token = login_res.get('token')

        res = self.client.post(
            '/api/ai/chat',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={'message': 'cập nhật giá DV001 thành 380000'}
        )
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertTrue(data.get('price_updated'))
        self.assertIn('380.000', data['reply'])

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT GiaTien FROM DichVu WHERE MaDichVu = 'DV001'")
        price_updated = cursor.fetchone()["GiaTien"]
        conn.close()
        self.assertEqual(int(price_updated), 380000)

    def test_32_ai_price_update_prompt_missing_price(self):
        """Verify Admin receives helpful prompt if price amount is omitted."""
        from backend.services.auth_service import AuthService

        login_res = AuthService.login('admin', 'admin123')
        admin_token = login_res.get('token')

        res = self.client.post(
            '/api/ai/chat',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={'message': 'tôi muốn sửa giá cắt tóc nam'}
        )
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertFalse(data.get('price_updated', False))
        self.assertIn('Bạn muốn điều chỉnh mức giá mới thành bao nhiêu', data['reply'])

    def test_33_ai_stylist_status_denied_for_guest(self):
        """Verify unauthenticated user cannot change stylist availability status."""
        res = self.client.post('/api/ai/chat', json={'message': 'chuyển thợ Kéo Vàng sang bận'})
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertFalse(data.get('data_updated', False))
        self.assertIn('TỪ CHỐI QUYỀN TRUY CẬP', data['reply'])

    def test_34_ai_stylist_status_success_for_letan(self):
        """Verify LeTan role can change stylist status via AI chat."""
        from backend.services.auth_service import AuthService
        from backend.db import get_db_connection

        login_res = AuthService.login('letan01', 'letan123')
        token = login_res['token']

        res = self.client.post(
            '/api/ai/chat',
            headers={'Authorization': f'Bearer {token}'},
            json={'message': 'chuyển thợ Kéo Vàng sang rảnh'}
        )
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertTrue(data.get('data_updated'))
        self.assertIn('ĐÃ CẬP NHẬT TRẠNG THÁI THỢ THÀNH CÔNG', data['reply'])
        self.assertIn('ĐANG RẢNH', data['reply'])

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT TrangThaiRanh FROM NhanVien WHERE MaNhanVien = 'NV004'")
        status = cursor.fetchone()["TrangThaiRanh"]
        conn.close()
        self.assertEqual(status, 1)

    def test_35_ai_cancel_appointment_denied_for_guest(self):
        """Verify guest cannot cancel salon appointment."""
        res = self.client.post('/api/ai/chat', json={'message': 'hủy lịch hẹn LH011'})
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertFalse(data.get('data_updated', False))
        self.assertIn('TỪ CHỐI QUYỀN TRUY CẬP', data['reply'])

    def test_36_ai_cancel_appointment_success_for_admin(self):
        """Verify Admin can cancel appointment via AI chat."""
        from backend.services.auth_service import AuthService
        from backend.db import get_db_connection

        login_res = AuthService.login('admin', 'admin123')
        token = login_res['token']

        res = self.client.post(
            '/api/ai/chat',
            headers={'Authorization': f'Bearer {token}'},
            json={'message': 'hủy lịch hẹn LH011'}
        )
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertTrue(data.get('data_updated'))
        self.assertIn('ĐÃ HỦY LỊCH HẸN THÀNH CÔNG', data['reply'])

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT TrangThai FROM LichHen WHERE MaLichHen = 'LH011'")
        status = cursor.fetchone()["TrangThai"]
        conn.close()
        self.assertEqual(status, 'Đã hủy')

    def test_37_ai_checkout_appointment_denied_for_guest(self):
        """Verify guest cannot execute POS checkout via AI chat."""
        res = self.client.post('/api/ai/chat', json={'message': 'thanh toán lịch hẹn LH012 giảm giá 50k'})
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertFalse(data.get('data_updated', False))
        self.assertIn('TỪ CHỐI QUYỀN TRUY CẬP', data['reply'])

    def test_38_ai_update_hair_note_success_for_stylist(self):
        """Verify stylist can update customer hair profile via AI chat."""
        from backend.services.auth_service import AuthService
        from backend.db import get_db_connection

        login_res = AuthService.login('tho01', 'tho123')
        token = login_res['token']

        res = self.client.post(
            '/api/ai/chat',
            headers={'Authorization': f'Bearer {token}'},
            json={'message': 'cập nhật chất tóc khách Nguyễn Thị Mai là tóc tơ mảnh phục hồi keratin nano'}
        )
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertTrue(data.get('data_updated'))
        self.assertIn('ĐÃ CẬP NHẬT HỒ SƠ CHẤT TÓC THÀNH CÔNG', data['reply'])

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT GhiChuToc FROM KhachHang WHERE MaKhachHang = 'KH001'")
        note = cursor.fetchone()["GhiChuToc"]
        conn.close()
        self.assertIn('keratin nano', note)

    def test_39_ai_add_service_rbac(self):
        """Verify receptionist cannot add services, but Admin can add services via AI."""
        from backend.services.auth_service import AuthService
        from backend.db import get_db_connection

        # LeTan should be denied
        letan_tok = AuthService.login('letan01', 'letan123')['token']
        res_lt = self.client.post(
            '/api/ai/chat',
            headers={'Authorization': f'Bearer {letan_tok}'},
            json={'message': 'thêm dịch vụ Cắt tóc trẻ em giá 120k thời gian 30 phút'}
        )
        self.assertIn('TỪ CHỐI QUYỀN TRUY CẬP', res_lt.get_json()['reply'])

        # Admin should succeed
        admin_tok = AuthService.login('admin', 'admin123')['token']
        res_ad = self.client.post(
            '/api/ai/chat',
            headers={'Authorization': f'Bearer {admin_tok}'},
            json={'message': 'thêm dịch vụ Cắt tóc trẻ em VIP giá 120k thời gian 30 phút'}
        )
        data_ad = res_ad.get_json()
        self.assertTrue(data_ad.get('success'))
        self.assertTrue(data_ad.get('data_updated'))
        self.assertIn('ĐÃ THÊM DỊCH VỤ MỚI THÀNH CÔNG', data_ad['reply'])
        self.assertIn('120.000', data_ad['reply'])

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM DichVu WHERE TenDichVu LIKE '%Cắt tóc trẻ em VIP%'")
        new_svc = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(new_svc)
        self.assertEqual(int(new_svc['GiaTien']), 120000)

    def test_40_ai_promotion_rbac(self):
        """Verify only Admin can promote apprentice to main stylist via AI chat."""
        from backend.services.auth_service import AuthService
        from backend.db import get_db_connection

        # Guest should be denied
        res_guest = self.client.post('/api/ai/chat', json={'message': 'cho Thảo Vy lên thợ chính'})
        self.assertIn('TỪ CHỐI QUYỀN TRUY CẬP', res_guest.get_json()['reply'])

        # LeTan should be denied
        letan_tok = AuthService.login('letan01', 'letan123')['token']
        res_lt = self.client.post(
            '/api/ai/chat',
            headers={'Authorization': f'Bearer {letan_tok}'},
            json={'message': 'cho Thảo Vy lên thợ chính'}
        )
        self.assertIn('TỪ CHỐI QUYỀN TRUY CẬP', res_lt.get_json()['reply'])

        # Admin should succeed
        admin_tok = AuthService.login('admin', 'admin123')['token']
        res_ad = self.client.post(
            '/api/ai/chat',
            headers={'Authorization': f'Bearer {admin_tok}'},
            json={'message': 'cho Thảo Vy lên thợ chính'}
        )
        data_ad = res_ad.get_json()
        self.assertTrue(data_ad.get('success'))
        self.assertTrue(data_ad.get('data_updated'))
        self.assertIn('QUYẾT ĐỊNH THĂNG CHỨC THÀNH CÔNG', data_ad['reply'])
        self.assertIn('Vũ Thảo Vy', data_ad['reply'])
        self.assertIn('Thợ chính', data_ad['reply'])

        # Verify DB updated
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ChucVu FROM NhanVien WHERE MaNhanVien = 'NV007'")
        new_chuc_vu = cursor.fetchone()["ChucVu"]
        conn.close()
        self.assertEqual(new_chuc_vu, 'Thợ chính')

    def test_41_ai_and_api_role_swap_and_change(self):
        """Verify Admin can change roles and swap positions between staff, while Guest is blocked."""
        from backend.services.auth_service import AuthService
        from backend.db import get_db_connection

        admin_tok = AuthService.login('admin', 'admin123')['token']

        # 1. AI general inquiry about swapping multiple roles
        res_inquiry = self.client.post(
            '/api/ai/chat',
            headers={'Authorization': f'Bearer {admin_tok}'},
            json={'message': 'muốn ở quán lý thợ đấy đổi được nhiều vị trí cho nhau vào'}
        )
        data_inquiry = res_inquiry.get_json()
        self.assertTrue(data_inquiry.get('success'))
        self.assertIn('CÁC CÁCH ĐỔI VỊ TRÍ & HOÁN ĐỔI NHÂN SỰ', data_inquiry['reply'])
        self.assertIn('Hoán Đổi Vị Trí', data_inquiry['reply'])

        # 2. AI swap execution
        res_swap = self.client.post(
            '/api/ai/chat',
            headers={'Authorization': f'Bearer {admin_tok}'},
            json={'message': 'hoán đổi vị trí của Thảo Vy và Tuấn Anh'}
        )
        data_swap = res_swap.get_json()
        self.assertTrue(data_swap.get('success'))
        self.assertTrue(data_swap.get('data_updated'))
        self.assertIn('HOÁN ĐỔI VỊ TRÍ NHÂN SỰ THÀNH CÔNG', data_swap['reply'])

        # 3. REST endpoint swap-roles RBAC
        res_guest_swap = self.client.post(
            '/api/stylists/swap-roles',
            json={'staff1_id': 'NV007', 'staff2_id': 'NV008'}
        )
        self.assertEqual(res_guest_swap.status_code, 403)

        res_admin_swap = self.client.post(
            '/api/stylists/swap-roles',
            headers={'Authorization': f'Bearer {admin_tok}'},
            json={'staff1_id': 'NV007', 'staff2_id': 'NV008'}
        )
        self.assertEqual(res_admin_swap.status_code, 200)
        self.assertTrue(res_admin_swap.get_json().get('success'))

        # Reset back for clean state
        conn = get_db_connection()
        conn.execute("UPDATE NhanVien SET ChucVu = 'Thợ phụ' WHERE MaNhanVien IN ('NV007', 'NV008')")
        conn.commit()
        conn.close()

    def test_42_semantic_natural_language_intent_and_rbac_across_all_roles(self):
        """
        Comprehensive test for deep natural language intent understanding:
        1. Price update via slang ('cắt nam 180 cành', 'hạ uốn collagen còn 1 củ 2') with RBAC.
        2. Staff role promotion via nicknames ('con bé Vy cắt cứng rồi cho nó làm thợ đi').
        3. Swapping positions via colloquial phrase ('tráo vị trí của Vy với Tuấn Anh').
        4. Staff status toggle ('báo ku Phong bận nha', 'Kéo Vàng rảnh tay rồi đấy').
        5. Verify that unauthorized roles get intelligent acknowledgment + clear RBAC explanation.
        """
        from backend.services.auth_service import AuthService
        from backend.db import get_db_connection

        admin_tok = AuthService.login('admin', 'admin123')['token']
        letan_tok = AuthService.login('letan01', 'letan123')['token']

        # ---------------------------------------------------------
        # SCENARIO 1: PRICE UPDATE WITH SLANG ('cành', 'củ')
        # ---------------------------------------------------------
        # 1.1 Guest says 'cắt nam 180 cành' -> AI understands intent (DV014 to 180.000đ) but safely denies
        res_guest_price = self.client.post('/api/ai/chat', json={'message': 'cắt nam 180 cành'})
        data_gp = res_guest_price.get_json()
        self.assertTrue(data_gp.get('success'))
        self.assertFalse(data_gp.get('price_updated', False))
        self.assertIn('TỪ CHỐI QUYỀN TRUY CẬP', data_gp['reply'])
        self.assertIn('Cắt Barber phong cách Fade nghệ thuật', data_gp['reply'])
        self.assertIn('180.000 đ', data_gp['reply'])

        # 1.2 Admin says 'cắt nam 180 cành' -> AI understands and executes
        res_ad_price = self.client.post(
            '/api/ai/chat',
            headers={'Authorization': f'Bearer {admin_tok}'},
            json={'message': 'cắt nam 180 cành'}
        )
        data_ap = res_ad_price.get_json()
        self.assertTrue(data_ap.get('success'))
        self.assertTrue(data_ap.get('price_updated'))
        self.assertIn('CẬP NHẬT GIÁ DỊCH VỤ THÀNH CÔNG', data_ap['reply'])
        self.assertIn('180.000 đ', data_ap['reply'])

        # Check DB
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT GiaTien FROM DichVu WHERE MaDichVu = 'DV014'")
        self.assertEqual(int(cur.fetchone()['GiaTien']), 180000)

        # 1.3 Admin says 'hạ uốn collagen còn 1 củ 2' -> Compound price slang (1.200.000đ)
        res_ad_uon = self.client.post(
            '/api/ai/chat',
            headers={'Authorization': f'Bearer {admin_tok}'},
            json={'message': 'hạ uốn collagen còn 1 củ 2'}
        )
        data_uon = res_ad_uon.get_json()
        self.assertTrue(data_uon.get('success'))
        self.assertTrue(data_uon.get('price_updated'))
        self.assertIn('1.200.000 đ', data_uon['reply'])

        cur.execute("SELECT GiaTien FROM DichVu WHERE MaDichVu = 'DV002'")
        self.assertEqual(int(cur.fetchone()['GiaTien']), 1200000)

        # ---------------------------------------------------------
        # SCENARIO 2: PROMOTION / ROLE CHANGE VIA NATURAL PHRASES
        # ---------------------------------------------------------
        # 2.1 Receptionist says 'con bé Vy cắt cứng rồi cho nó làm thợ đi' -> AI acknowledges intent, denies
        res_lt_promo = self.client.post(
            '/api/ai/chat',
            headers={'Authorization': f'Bearer {letan_tok}'},
            json={'message': 'con bé Vy cắt cứng rồi cho nó làm thợ đi'}
        )
        data_lt = res_lt_promo.get_json()
        self.assertIn('TỪ CHỐI QUYỀN TRUY CẬP', data_lt['reply'])
        self.assertIn('Vũ Thảo Vy', data_lt['reply'])
        self.assertIn('Thợ chính', data_lt['reply'])

        # 2.2 Admin says 'con bé Vy cắt cứng rồi cho nó làm thợ đi' -> AI promotes Vy to Thợ chính
        res_ad_promo = self.client.post(
            '/api/ai/chat',
            headers={'Authorization': f'Bearer {admin_tok}'},
            json={'message': 'con bé Vy cắt cứng rồi cho nó làm thợ đi'}
        )
        data_ad_promo = res_ad_promo.get_json()
        self.assertTrue(data_ad_promo.get('success'))
        self.assertTrue(data_ad_promo.get('data_updated'))
        self.assertIn('Vũ Thảo Vy', data_ad_promo['reply'])
        self.assertIn('Thợ chính', data_ad_promo['reply'])

        cur.execute("SELECT ChucVu FROM NhanVien WHERE MaNhanVien = 'NV007'")
        self.assertEqual(cur.fetchone()['ChucVu'], 'Thợ chính')

        # 2.3 Admin says 'bữa nay cho Tuấn Anh ra quầy làm lễ tân' -> AI assigns Tuấn Anh to Lễ tân
        res_ad_tuan = self.client.post(
            '/api/ai/chat',
            headers={'Authorization': f'Bearer {admin_tok}'},
            json={'message': 'bữa nay cho Tuấn Anh ra quầy làm lễ tân'}
        )
        data_tuan = res_ad_tuan.get_json()
        self.assertTrue(data_tuan.get('success'))
        self.assertTrue(data_tuan.get('data_updated'))
        self.assertIn('Bùi Tuấn Anh', data_tuan['reply'])
        self.assertIn('Lễ tân', data_tuan['reply'])

        cur.execute("SELECT ChucVu FROM NhanVien WHERE MaNhanVien = 'NV008'")
        self.assertEqual(cur.fetchone()['ChucVu'], 'Lễ tân')

        # ---------------------------------------------------------
        # SCENARIO 3: SWAP POSITIONS VIA NATURAL PHRASE
        # ---------------------------------------------------------
        # 3.1 Guest says 'tráo vị trí của Vy với Tuấn Anh' -> AI understands both entities, safely denies
        res_guest_sw = self.client.post(
            '/api/ai/chat',
            json={'message': 'tráo vị trí của Vy với Tuấn Anh'}
        )
        data_gsw = res_guest_sw.get_json()
        self.assertIn('TỪ CHỐI QUYỀN TRUY CẬP', data_gsw['reply'])
        self.assertIn('Vũ Thảo Vy', data_gsw['reply'])
        self.assertIn('Bùi Tuấn Anh', data_gsw['reply'])

        # 3.2 Admin says 'tráo vị trí của Vy với Tuấn Anh' -> AI swaps their roles
        res_ad_sw = self.client.post(
            '/api/ai/chat',
            headers={'Authorization': f'Bearer {admin_tok}'},
            json={'message': 'tráo vị trí của Vy với Tuấn Anh'}
        )
        data_ad_sw = res_ad_sw.get_json()
        self.assertTrue(data_ad_sw.get('success'))
        self.assertTrue(data_ad_sw.get('data_updated'))
        self.assertIn('HOÁN ĐỔI VỊ TRÍ NHÂN SỰ THÀNH CÔNG', data_ad_sw['reply'])

        cur.execute("SELECT ChucVu FROM NhanVien WHERE MaNhanVien = 'NV007'")
        self.assertEqual(cur.fetchone()['ChucVu'], 'Lễ tân')
        cur.execute("SELECT ChucVu FROM NhanVien WHERE MaNhanVien = 'NV008'")
        self.assertEqual(cur.fetchone()['ChucVu'], 'Thợ chính')

        # ---------------------------------------------------------
        # SCENARIO 4: STYLIST AVAILABILITY STATUS TOGGLE
        # ---------------------------------------------------------
        # 4.1 Guest says 'báo ku Phong bận nha' -> AI understands, denies guest
        res_g_busy = self.client.post('/api/ai/chat', json={'message': 'báo ku Phong bận nha'})
        self.assertIn('TỪ CHỐI QUYỀN TRUY CẬP', res_g_busy.get_json()['reply'])

        # 4.2 Receptionist says 'báo ku Phong bận nha' -> AI marks Phong as busy
        res_lt_busy = self.client.post(
            '/api/ai/chat',
            headers={'Authorization': f'Bearer {letan_tok}'},
            json={'message': 'báo ku Phong bận nha'}
        )
        data_lt_busy = res_lt_busy.get_json()
        self.assertTrue(data_lt_busy.get('success'))
        self.assertTrue(data_lt_busy.get('data_updated'))
        self.assertIn('ĐANG BẬN', data_lt_busy['reply'])

        cur.execute("SELECT TrangThaiRanh FROM NhanVien WHERE MaNhanVien = 'NV006'")
        self.assertEqual(int(cur.fetchone()['TrangThaiRanh']), 0)

        # 4.3 Receptionist says 'Kéo Vàng rảnh tay rồi đấy' -> AI marks Kéo Vàng as available
        res_lt_free = self.client.post(
            '/api/ai/chat',
            headers={'Authorization': f'Bearer {letan_tok}'},
            json={'message': 'Kéo Vàng rảnh tay rồi đấy'}
        )
        data_lt_free = res_lt_free.get_json()
        self.assertTrue(data_lt_free.get('success'))
        self.assertTrue(data_lt_free.get('data_updated'))
        self.assertIn('ĐANG RẢNH', data_lt_free['reply'])

        cur.execute("SELECT TrangThaiRanh FROM NhanVien WHERE MaNhanVien = 'NV004'")
        self.assertEqual(int(cur.fetchone()['TrangThaiRanh']), 1)

        # Cleanup test state back to defaults
        conn.execute("UPDATE DichVu SET GiaTien = 200000 WHERE MaDichVu = 'DV014'")
        conn.execute("UPDATE DichVu SET GiaTien = 1850000 WHERE MaDichVu = 'DV002'")
        conn.execute("UPDATE NhanVien SET ChucVu = 'Thợ phụ' WHERE MaNhanVien IN ('NV007', 'NV008')")
        conn.execute("UPDATE NhanVien SET TrangThaiRanh = 1 WHERE MaNhanVien IN ('NV004', 'NV006')")
        conn.commit()
        conn.close()

if __name__ == '__main__':
    unittest.main()
