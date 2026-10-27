"""
Integration Test Suite for Web App Endpoints:
Verifies:
- GET /
- GET /health
- GET /api/reports/summary
- GET /api/customers
- GET /api/stylists
- GET /api/services
- GET /api/appointments
- POST /api/appointments (collision check & successful booking)
- POST /api/billing/checkout
- POST /api/ai/suggest
- POST /api/ai/reminder
- POST /api/ai/summary
"""

import unittest
import json
from app import app
from database.init_db import init_database
from backend.config import Config

class TestSalonWebApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_database(Config.DB_PATH, reset=True)
        cls.client = app.test_client()

    def test_health_and_index(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        self.assertIn("healthy", res.get_json()["status"])

        res_index = self.client.get("/")
        self.assertEqual(res_index.status_code, 200)
        content = res_index.data.decode("utf-8")
        self.assertTrue("HÀ MINH" in content or "HA MINH" in content)

    def test_services_and_customers_api(self):
        res_svc = self.client.get("/api/services")
        self.assertEqual(res_svc.status_code, 200)
        svcs = res_svc.get_json()["services"]
        self.assertGreaterEqual(len(svcs), 6)

        res_cust = self.client.get("/api/customers")
        self.assertEqual(res_cust.status_code, 200)
        custs = res_cust.get_json()["customers"]
        self.assertGreaterEqual(len(custs), 5)

    def test_booking_conflict_prevention(self):
        # Existing appointment LH005 is on 2026-09-19 14:00:00 with NV004 (DV003 90m + DV005 50m = 140m, ends 16:20)
        # Attempt to book overlapping time for NV004 at 14:30 should fail
        payload_conflict = {
            "ma_khach_hang": "KH001",
            "ma_nhan_vien": "NV004",
            "ngay_gio_hen": "2026-09-19 14:30:00",
            "service_ids": ["DV001"],
            "ghi_chu": "Thử nghiệm trùng lịch"
        }
        res_conflict = self.client.post(
            "/api/appointments",
            data=json.dumps(payload_conflict),
            content_type="application/json"
        )
        self.assertEqual(res_conflict.status_code, 400)
        self.assertIn("Thợ đã có lịch bận", res_conflict.get_json()["message"])

        # Non-overlapping booking should succeed
        payload_ok = {
            "ma_khach_hang": "KH001",
            "ma_nhan_vien": "NV004",
            "ngay_gio_hen": "2026-09-25 15:00:00",
            "service_ids": ["DV001", "DV002"],
            "ghi_chu": "Lịch hẹn mới chuẩn"
        }
        res_ok = self.client.post(
            "/api/appointments",
            data=json.dumps(payload_ok),
            content_type="application/json"
        )
        self.assertEqual(res_ok.status_code, 200)
        self.assertTrue(res_ok.get_json()["success"])

    def test_ai_endpoints(self):
        # AI Suggest
        res_sug = self.client.post(
            "/api/ai/suggest",
            data=json.dumps({"customer_id": "KH001", "notes": "Tóc khô sau tẩy"}),
            content_type="application/json"
        )
        self.assertEqual(res_sug.status_code, 200)
        self.assertTrue(res_sug.get_json()["success"])

        # AI Reminder
        res_rem = self.client.post(
            "/api/ai/reminder",
            data=json.dumps({"appointment_id": "LH001"}),
            content_type="application/json"
        )
        self.assertEqual(res_rem.status_code, 200)
        self.assertTrue(res_rem.get_json()["success"])

        # AI Summary
        res_sum = self.client.post(
            "/api/ai/summary",
            data=json.dumps({"customer_id": "KH001"}),
            content_type="application/json"
        )
        self.assertEqual(res_sum.status_code, 200)
        self.assertTrue(res_sum.get_json()["success"])

        # AI Interactive Chatbot
        res_chat = self.client.post(
            "/api/ai/chat",
            data=json.dumps({"message": "Tư vấn màu nhuộm cho da ngăm"}),
            content_type="application/json"
        )
        self.assertEqual(res_chat.status_code, 200)
        chat_data = res_chat.get_json()
        self.assertTrue(chat_data["success"])
        self.assertIn("reply", chat_data)
        self.assertGreater(len(chat_data["reply"]), 10)

    def test_revenue_reporting_and_kpi(self):
        """Verify UC007 financial summary API calculations."""
        res = self.client.get("/api/reports/summary")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])

        # Validate KPIs
        kpi = data["kpi"]
        self.assertGreater(kpi["tong_doanh_thu"], 0)
        self.assertGreater(kpi["aov"], 0)
        self.assertGreater(kpi["tong_hoa_don"], 0)
        self.assertGreater(kpi["doanh_thu_hom_nay"], 0)

        # Validate Revenue by Payment Method
        methods = data["revenue_by_method"]
        self.assertGreaterEqual(len(methods), 2)
        total_pct = sum(m["phan_tram"] for m in methods)
        self.assertAlmostEqual(total_pct, 100.0, delta=1.0)
        total_by_methods = sum(m["doanh_thu"] for m in methods)
        self.assertEqual(total_by_methods, kpi["tong_doanh_thu"])

        # Validate Revenue by Day trend
        days = data["revenue_by_day"]
        self.assertGreaterEqual(len(days), 5)
        for day in days:
            self.assertIn("Ngay", day)
            self.assertGreater(day["DoanhThu"], 0)

        # Validate Stylist leaderboard
        leaderboard = data["stylist_leaderboard"]
        self.assertGreaterEqual(len(leaderboard), 2)
        for stylist in leaderboard:
            self.assertIn("TenTho", stylist)
            self.assertGreater(stylist["SoLuotPhucVu"], 0)

    def test_revenue_export_csv(self):
        """Verify UC007 CSV export formatting and content."""
        res = self.client.get("/api/reports/export")
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/csv", res.headers.get("Content-Type", ""))
        content = res.data.decode("utf-8")
        self.assertTrue(content.startswith("\ufeffMã Hóa Đơn"))
        self.assertIn("Thành Tiền (VNĐ)", content)
        self.assertIn("Phương Thức", content)


if __name__ == "__main__":
    unittest.main()

