"""
Script to generate ultra-high revenue seed data for HA MINH HAIR SALON.
Total revenue > 185,000,000 VND with realistic VIP services, multiple appointments,
and strict mathematical integrity: ThanhTien = TongTien - GiamGia.
"""

import os

SEED_PATH = os.path.join(os.path.dirname(__file__), "seed.sql")

def generate_high_revenue_seed():
    seed_sql = """-- ====================================================================
-- BỘ DỮ LIỆU MẪU HÀ MINH HAIR SALON - DOANH THU CỰC CAO (VIP HIGH-END REVENUE)
-- TỔNG DOANH THU: > 185 TRIỆU ĐỒNG | ĐẦY ĐỦ 8 BẢNG & RÀNG BUỘC TOÀN VẸN
-- ====================================================================

PRAGMA foreign_keys = ON;

-- --------------------------------------------------------------------
-- 1. BẢNG TAIKHOAN
-- --------------------------------------------------------------------
INSERT OR REPLACE INTO TaiKhoan (MaTaiKhoan, TenDangNhap, MatKhau, VaiTro) VALUES
('TK001', 'admin', 'admin123', 'Admin'),
('TK002', 'letan01', 'letan123', 'LeTan'),
('TK003', 'letan02', 'letan123', 'LeTan'),
('TK004', 'tho01', 'tho123', 'Tho'),
('TK005', 'tho02', 'tho123', 'Tho'),
('TK006', 'tho03', 'tho123', 'Tho'),
('TK007', 'tho04', 'tho123', 'Tho');

-- --------------------------------------------------------------------
-- 2. BẢNG NHANVIEN
-- --------------------------------------------------------------------
INSERT OR REPLACE INTO NhanVien (MaNhanVien, HoTen, SoDienThoai, ChucVu, TrangThaiRanh, MaTaiKhoan) VALUES
('NV001', 'Hà Minh Giám Đốc', '0901234567', 'Quản lý', 1, 'TK001'),
('NV002', 'Lê Thị Thu Ngân', '0912345678', 'Lễ tân', 1, 'TK002'),
('NV003', 'Nguyễn Hoàng Yến Nhi', '0913555777', 'Lễ tân', 1, 'TK003'),
('NV004', 'Nguyễn Văn Kéo Vàng', '0923456789', 'Thợ chính', 0, 'TK004'),
('NV005', 'Phạm Minh Tóc Mây', '0934567890', 'Thợ chính', 1, 'TK005'),
('NV006', 'Đỗ Hải Phong', '0945678901', 'Thợ chính', 0, 'TK006'),
('NV007', 'Vũ Thảo Vy', '0956789012', 'Thợ phụ', 1, 'TK007'),
('NV008', 'Bùi Tuấn Anh', '0967890123', 'Thợ phụ', 1, NULL);

-- --------------------------------------------------------------------
-- 3. BẢNG KHACHHANG (15 Khách VIP & Khách vãng lai)
-- --------------------------------------------------------------------
INSERT OR REPLACE INTO KhachHang (MaKhachHang, HoTen, SoDienThoai, GhiChuToc) VALUES
('KH001', 'Nguyễn Thị Mai', '0988111222', 'Khách VIP Diamond: Tóc tơ mảnh, da đầu dầu nhạy cảm, thích làm combo phục hồi Keratin định kỳ'),
('KH002', 'Lê Văn Hùng', '0977222333', 'Doanh nhân VIP: Tóc rễ tre dày cứng, cắt phom Side Part Fade vuốt clay mờ, chu kỳ 2 tuần/lần'),
('KH003', 'Phạm Quỳnh Nga', '0966333444', 'Nghệ sĩ VIP: Tóc đã tẩy bạch kim level 9. CẢNH BÁO: Chỉ dùng thuốc nhuộm hữu cơ & Olaplex VIP'),
('KH004', 'Trần Bảo Anh', '0955444555', 'Khách VIP Gold: Thích phong cách uốn layer lơi sóng nước bồng bềnh chuẩn Hàn Quốc'),
('KH005', 'Khách vãng lai VIP 01', NULL, 'Khách vãng lai làm combo cắt gội massage hoàng gia tại quầy'),
('KH006', 'Đặng Hoàng Yến', '0944888999', 'Khách VIP Platinum: Tóc xoăn xù tự nhiên, duỗi cúp phục hồi Collagen & Scalp Detox'),
('KH007', 'Vũ Đức Nam', '0933777888', 'Giám đốc công ty: Uốn Texture phồng chân tóc và nhuộm nâu lạnh sang trọng'),
('KH008', 'Bùi Ngọc Linh', '0922666777', 'Khách VIP: Tóc dài dày khỏe, chu kỳ làm hóa chất uốn nhuộm 2 tháng/lần'),
('KH009', 'Hoàng Thu Trang', '0911555666', 'Beauty Blogger: Da đầu nhạy cảm, thích các tông màu Balayage khói thời thượng'),
('KH010', 'Khách vãng lai VIP 02', NULL, 'Khách nam ghé trải nghiệm dịch vụ Barber Fade & Uốn tóc nam'),
('KH011', 'Ngô Thanh Vân', '0909887766', 'Doanh nhân thời trang: Cắt Bob sắc sảo phối liệu trình Bọc Protein tơ tằm thượng hạng'),
('KH012', 'Phan Minh Khang', '0908776655', 'Ca sĩ trẻ: Tóc nam Two-Block uốn sóng rủ Hàn Quốc kết hợp nhuộm xám khói'),
('KH013', 'Đỗ Cẩm Tú', '0907665544', 'Khách VIP: Cần phục hồi chuyên sâu cấp tốc cho tóc hư tổn sau tẩy'),
('KH014', 'Dương Quốc Bảo', '0906554433', 'Nhà đầu tư: Cắt Barber Fade doanh nhân, gội massage bấm huyệt đả thông kinh lạc'),
('KH015', 'Khách vãng lai VIP 03', NULL, 'Khách nữ làm dịch vụ gội dưỡng sinh hoàng gia thư giãn'),
('KH016', 'Đỗ Mỹ Linh', '0912334455', 'Hoa hậu / VIP Royal: Tóc dài nguyên bản uốn lơi sóng nước nhẹ, bảo dưỡng định kỳ bằng Tế bào gốc Stem Cell'),
('KH017', 'Nguyễn Trọng Hoàng', '0913445566', 'Cầu thủ bóng đá: Tóc nam cắt Mullet Fade cá tính, uốn Texture giữ nếp khi vận động thể thao'),
('KH018', 'Trần Mai Phương', '0914556677', 'MC Truyền hình: Tóc mỏng xẹp, cần dịch vụ Duỗi phồng chân tóc Volume Perm kết hợp uốn đuôi cúp'),
('KH019', 'Lê Bảo Châu', '0915667788', 'Fashionista: Tóc tẩy Airtouch tông xám tro khói, rất nhạy cảm nhiệt độ, chỉ sấy mát và bọc Protein'),
('KH020', 'Vũ Hoàng Yến', '0916778899', 'Nữ doanh nhân: Tóc chớm bạc chân, định kỳ nhuộm thảo dược che phủ bạc và gội dưỡng sinh Hoàng Cung'),
('KH021', 'Phạm Quốc Cường', '0917889900', 'Doanh nhân: Tóc thưa rụng vùng đỉnh đầu, đang theo liệu trình Thải độc Scalp Detox kết hợp cấy tinh chất'),
('KH022', 'Đinh Thu Hà', '0918990011', 'Khách VIP: Tóc bông xù dày cứng, thường duỗi phủ bóng Nano Diamond kết hợp cắt phom layer Hàn Quốc'),
('KH023', 'Khách vãng lai VIP 04', NULL, 'Khách đặt qua hotline làm gói Gội thảo mộc 24 vị và sấy tạo kiểu dạ tiệc'),
('KH024', 'Trương Gia Huy', '0919001122', 'Kiến trúc sư: Tóc nam rẽ ngôi 7/3, cắt Barber Fade cổ điển kết hợp cạo râu khăn nóng'),
('KH025', 'Tô Khánh Linh', '0920112233', 'Sinh viên đại học: Tóc khô đuôi do tự nhuộm tại nhà, cần cắt tỉa layer và phục hồi Plex Bond Builder');

-- --------------------------------------------------------------------
-- 4. BẢNG DICHVU (22 Dịch vụ cao cấp & Bảng giá chuẩn Salon VIP)
-- --------------------------------------------------------------------
INSERT OR REPLACE INTO DichVu (MaDichVu, TenDichVu, GiaTien, ThoiGianThucHien, MoTa) VALUES
('DV001', 'Cắt tóc tạo kiểu Master Stylist', 350000, 45, 'Thiết kế phom chuẩn nhân trắc học, thợ chính tạo kiểu, sấy vuốt sáp tạo nếp'),
('DV002', 'Uốn sóng bung Collagen Nano VIP', 1850000, 120, 'Uốn sóng bung bồng bềnh công nghệ Nano Collagen Nhật Bản khóa ẩm biểu bì'),
('DV003', 'Nhuộm Balayage / Ombre Thiết Kế VIP', 2800000, 150, 'Kỹ thuật nhuộm khối nghệ thuật đa tầng ánh sáng, thuốc nhuộm hữu cơ châu Âu'),
('DV004', 'Tẩy tóc an toàn Olaplex No.1 & No.2', 1500000, 90, 'Liệu trình nâng tone an toàn chuẩn thế giới, bảo toàn 100% cấu trúc tủy tóc'),
('DV005', 'Cấy phục hồi cấu trúc Nano Keratin VIP', 2200000, 75, 'Cấy tinh chất Keratin nguyên chất vào lõi tóc, chữa lành tức thì tóc cháy chẻ ngọn'),
('DV006', 'Gội đầu dưỡng sinh Đông Y Hoàng Gia', 350000, 60, 'Gội nước canh thảo dược 18 vị, massage bấm huyệt cổ vai gáy, đắp mặt nạ ngọc trai'),
('DV007', 'Duỗi phủ bóng gương Nano Diamond', 2400000, 130, 'Duỗi tóc mềm mại tự nhiên, phủ lớp màng bóng kim cương lấp lánh phản chiếu'),
('DV008', 'Uốn Texture phồng chân tóc nam VIP', 850000, 60, 'Tạo độ phồng tơi tự nhiên chuẩn phong cách idol Hàn Quốc cho tóc nam'),
('DV009', 'Thải độc da đầu bùn khoáng hữu cơ', 650000, 50, 'Làm sạch sâu nang chân tóc, loại bỏ gàu mảng và bã nhờn tích tụ lâu năm'),
('DV010', 'Cắt tỉa tóc mái & Sấy phồng phom Hàn', 200000, 20, 'Cắt phom mái bay/mái thưa hack tuổi kết hợp sấy phồng định hình'),
('DV011', 'Bọc Protein tơ tằm tái sinh tóc nát', 3200000, 90, 'Cấp cứu cấp tốc cho mái tóc hư tổn nặng nề do hóa chất tẩy uốn nhiều lần'),
('DV012', 'Liệu trình thải độc Scalp Detox', 1200000, 50, 'Thanh lọc độc tố chân tóc, bổ sung dưỡng chất kích thích mọc tóc dày khỏe'),
('DV013', 'Sấy tạo kiểu dạ tiệc & Sự kiện VIP', 600000, 40, 'Tạo sóng nước Hollywood sang trọng bồng bềnh giữ nếp suốt 24 giờ'),
('DV014', 'Cắt Barber phong cách Fade nghệ thuật', 450000, 45, 'Kỹ thuật Fade trắng mờ Skinfade sắc nét từng milimet cho quý ông'),
('DV015', 'Uốn sóng Hippie / Butterfly lơi Hàn Quốc', 1950000, 110, 'Kỹ thuật uốn lơi bướm bay bồng bềnh tự nhiên không khô ráp, giữ nếp 6-8 tháng'),
('DV016', 'Nhuộm French Airtouch Highlight cao cấp', 3500000, 180, 'Kỹ thuật sấy tách lớp sợi tóc tơ vi điểm của Pháp, tạo hiệu ứng phản quang đa chiều'),
('DV017', 'Phục hồi tế bào gốc thực vật Stem Cell VIP', 2600000, 70, 'Công nghệ tế bào gốc tái sinh nang tóc teo nhỏ, kích hoạt tế bào mầm tóc phát triển dày mượt'),
('DV018', 'Gội đầu dưỡng sinh Hoàng Cung Thảo Mộc 24 vị', 450000, 75, 'Xông hơi thảo dược, ngâm chân muối hồng Himalaya, massage bấm huyệt đả thông 12 đường kinh lạc'),
('DV019', 'Duỗi phồng chân tóc Volume Perm Hàn Quốc', 950000, 60, 'Tạo độ phồng tự nhiên cho đỉnh đầu, khắc phục triệt để tình trạng đầu bẹp hoặc tóc xẹp lép'),
('DV020', 'Phục hồi cấp cứu Plex Bond Builder Pro', 1600000, 50, 'Tái tạo liên kết disunfua lưu huỳnh đứt gãy sau tẩy uốn nặng, phục hồi độ đàn hồi sợi tóc'),
('DV021', 'Nhuộm Nâu Tây Ánh Khói Mật Ong Glossy', 1750000, 90, 'Tông nâu tây nâng 2 tone da châu Á, phủ dưỡng chất Glossy phản chiếu ánh sáng óng ả'),
('DV022', 'Cắt & Tạo kiểu Mullet Layer Wolfcut thời thượng', 400000, 45, 'Phom cắt Wolfcut bay bổng cá tính, tôn góc nghiêng khuôn mặt cho nam và nữ');
"""

    # Invoices mapped to appointments LH001-LH004, and LH011-LH033
    invoices_data = [
        # (MaHoaDon, MaLichHen, MaKhach, MaTho, NgayTao, Services, GiamGia, PhuongThuc)
        ("HD001", "LH001", "KH001", "NV004", "2026-09-08 11:00:00", [("DV001", 350000), ("DV005", 2200000), ("DV012", 1200000)], 250000, "Chuyển khoản"), # 3750k - 250k = 3500k
        ("HD002", "LH002", "KH002", "NV006", "2026-09-09 15:30:00", [("DV014", 450000), ("DV008", 850000), ("DV006", 350000), ("DV012", 1200000), ("DV005", 2200000)], 550000, "Thẻ"), # 5050k - 550k = 4500k
        ("HD003", "LH003", "KH003", "NV005", "2026-09-10 11:45:00", [("DV003", 2800000), ("DV004", 1500000), ("DV011", 3200000)], 500000, "Chuyển khoản"), # 7500k - 500k = 7000k
        ("HD004", "LH004", "KH004", "NV004", "2026-09-10 16:30:00", [("DV001", 350000), ("DV002", 1850000), ("DV005", 2200000), ("DV012", 1200000)], 600000, "Thẻ"), # 5600k - 600k = 5000k
        ("HD005", "LH011", "KH006", "NV005", "2026-09-11 12:00:00", [("DV007", 2400000), ("DV005", 2200000), ("DV011", 3200000)], 800000, "Chuyển khoản"), # 7800k - 800k = 7000k
        ("HD006", "LH012", "KH007", "NV006", "2026-09-11 17:30:00", [("DV014", 450000), ("DV008", 850000), ("DV006", 350000), ("DV011", 3200000), ("DV012", 1200000)], 550000, "Chuyển khoản"), # 6050k - 550k = 5500k
        ("HD007", "LH013", "KH008", "NV004", "2026-09-12 11:30:00", [("DV002", 1850000), ("DV003", 2800000), ("DV004", 1500000), ("DV005", 2200000)], 850000, "Thẻ"), # 8350k - 850k = 7500k
        ("HD008", "LH014", "KH005", "NV007", "2026-09-12 14:15:00", [("DV006", 350000), ("DV009", 650000), ("DV012", 1200000)], 200000, "Tiền mặt"), # 2200k - 200k = 2000k
        ("HD009", "LH015", "KH009", "NV005", "2026-09-13 12:30:00", [("DV003", 2800000), ("DV004", 1500000), ("DV011", 3200000), ("DV005", 2200000), ("DV012", 1200000)], 900000, "Chuyển khoản"), # 10900k - 900k = 10000k
        ("HD010", "LH016", "KH010", "NV006", "2026-09-13 16:00:00", [("DV014", 450000), ("DV008", 850000), ("DV006", 350000), ("DV005", 2200000)], 350000, "Tiền mặt"), # 3850k - 350k = 3500k
        ("HD011", "LH017", "KH011", "NV004", "2026-09-14 11:00:00", [("DV001", 350000), ("DV011", 3200000), ("DV003", 2800000), ("DV005", 2200000)], 550000, "Chuyển khoản"), # 8550k - 550k = 8000k
        ("HD012", "LH018", "KH012", "NV006", "2026-09-14 15:45:00", [("DV014", 450000), ("DV008", 850000), ("DV003", 2800000), ("DV004", 1500000), ("DV005", 2200000)], 800000, "Thẻ"), # 7800k - 800k = 7000k
        ("HD013", "LH019", "KH013", "NV005", "2026-09-15 12:00:00", [("DV011", 3200000), ("DV005", 2200000), ("DV007", 2400000), ("DV002", 1850000), ("DV012", 1200000)], 850000, "Chuyển khoản"), # 10850k - 850k = 10000k
        ("HD014", "LH020", "KH014", "NV006", "2026-09-15 16:30:00", [("DV014", 450000), ("DV006", 350000), ("DV009", 650000), ("DV012", 1200000), ("DV008", 850000)], 500000, "Tiền mặt"), # 3500k - 500k = 3000k
        ("HD015", "LH021", "KH001", "NV004", "2026-09-16 11:30:00", [("DV002", 1850000), ("DV003", 2800000), ("DV005", 2200000), ("DV011", 3200000)], 1050000, "Thẻ"), # 10050k - 1050k = 9000k
        ("HD016", "LH022", "KH003", "NV005", "2026-09-16 16:00:00", [("DV003", 2800000), ("DV004", 1500000), ("DV011", 3200000), ("DV005", 2200000), ("DV007", 2400000)], 1100000, "Chuyển khoản"), # 12100k - 1100k = 11000k
        ("HD017", "LH023", "KH004", "NV004", "2026-09-17 11:00:00", [("DV002", 1850000), ("DV005", 2200000), ("DV003", 2800000), ("DV012", 1200000)], 1050000, "Chuyển khoản"), # 8050k - 1050k = 7000k
        ("HD018", "LH024", "KH002", "NV006", "2026-09-17 14:30:00", [("DV014", 450000), ("DV008", 850000), ("DV012", 1200000), ("DV005", 2200000), ("DV011", 3200000)], 900000, "Thẻ"), # 7900k - 900k = 7000k
        ("HD019", "LH025", "KH007", "NV007", "2026-09-17 17:00:00", [("DV006", 350000), ("DV009", 650000), ("DV012", 1200000), ("DV001", 350000)], 550000, "Tiền mặt"), # 2550k - 550k = 2000k
        ("HD020", "LH026", "KH011", "NV005", "2026-09-18 10:30:00", [("DV003", 2800000), ("DV004", 1500000), ("DV011", 3200000), ("DV007", 2400000), ("DV005", 2200000)], 1100000, "Chuyển khoản"), # 12100k - 1100k = 11000k
        ("HD021", "LH027", "KH012", "NV006", "2026-09-18 14:45:00", [("DV014", 450000), ("DV008", 850000), ("DV003", 2800000), ("DV005", 2200000), ("DV011", 3200000)], 1000000, "Thẻ"), # 9500k - 1000k = 8500k
        ("HD022", "LH028", "KH013", "NV004", "2026-09-18 18:00:00", [("DV011", 3200000), ("DV005", 2200000), ("DV012", 1200000), ("DV002", 1850000)], 950000, "Chuyển khoản"), # 8450k - 950k = 7500k
        # Hôm nay (2026-09-19): 5 hóa đơn VIP hoàn thành trong ngày mang về hơn 41 triệu doanh thu!
        ("HD023", "LH029", "KH006", "NV004", "2026-09-19 10:00:00", [("DV002", 1850000), ("DV005", 2200000), ("DV011", 3200000), ("DV012", 1200000), ("DV007", 2400000)], 1350000, "Chuyển khoản"), # 10850k - 1350k = 9500k
        ("HD024", "LH030", "KH008", "NV005", "2026-09-19 11:30:00", [("DV003", 2800000), ("DV004", 1500000), ("DV005", 2200000), ("DV011", 3200000)], 1200000, "Thẻ"), # 9700k - 1200k = 8500k
        ("HD025", "LH031", "KH014", "NV006", "2026-09-19 13:00:00", [("DV014", 450000), ("DV008", 850000), ("DV006", 350000), ("DV012", 1200000), ("DV009", 650000)], 500000, "Tiền mặt"), # 3500k - 500k = 3000k
        ("HD026", "LH032", "KH009", "NV004", "2026-09-19 14:45:00", [("DV003", 2800000), ("DV005", 2200000), ("DV011", 3200000), ("DV002", 1850000)], 1050000, "Chuyển khoản"), # 10050k - 1050k = 9000k
        ("HD027", "LH033", "KH003", "NV005", "2026-09-19 16:15:00", [("DV003", 2800000), ("DV004", 1500000), ("DV011", 3200000), ("DV007", 2400000), ("DV005", 2200000)], 1100000, "Chuyển khoản"), # 12100k - 1100k = 11000k
    ]

    # Crucial appointments required for unit tests:
    # LH005: NV004 on 2026-09-19 14:00:00, "Đang phục vụ", DV003 (150m) + DV005 (75m), ends 17:45 -> triggers collision for 14:30
    # LH006: NV006 on 2026-09-19 14:30:00, "Đang phục vụ"
    # LH007: NV005 on 2026-09-19 16:30:00, "Đã xác nhận", EXACTLY 2 details, NO invoice -> tests cascade delete
    special_appts = [
        ("LH005", "KH003", "NV004", "2026-09-19 14:00:00", "Đang phục vụ", "Nhuộm Balayage VIP + Phục hồi Keratin"),
        ("LH006", "KH007", "NV006", "2026-09-19 14:30:00", "Đang phục vụ", "Cắt Fade nghệ thuật + Gội hoàng gia"),
        ("LH007", "KH008", "NV005", "2026-09-19 16:30:00", "Đã xác nhận", "Uốn Collagen + Phục hồi Keratin"),
        ("LH008", "KH005", "NV007", "2026-09-19 17:00:00", "Đã xác nhận", "Gội đầu dưỡng sinh thư giãn"),
        ("LH009", "KH009", "NV004", "2026-09-20 09:30:00", "Chờ xác nhận", "Khách VIP muốn tư vấn nhuộm xám khói"),
        ("LH010", "KH010", "NV006", "2026-09-18 11:00:00", "Đã hủy", "Khách bận lịch đột xuất xin dời sang tuần sau"),
        ("LH034", "KH002", "NV004", "2026-09-20 16:30:00", "Đã xác nhận", "Cắt Master Stylist & Thải độc da đầu"),
        ("LH035", "KH015", "NV007", "2026-09-20 18:00:00", "Đã xác nhận", "Gội đầu dưỡng sinh hoàng gia ca tối"),
    ]

    seed_sql += "\n-- --------------------------------------------------------------------\n"
    seed_sql += "-- 5. BẢNG LICHHEN (35 Cuộc hẹn trải rộng từ 08/09 đến 20/09)\n"
    seed_sql += "-- --------------------------------------------------------------------\n"
    seed_sql += "INSERT OR REPLACE INTO LichHen (MaLichHen, MaKhachHang, MaNhanVien, NgayGioHen, TrangThai, GhiChu) VALUES\n"
    
    lh_rows = []
    for inv in invoices_data:
        lh_rows.append(f"('{inv[1]}', '{inv[2]}', '{inv[3]}', '{inv[4]}', 'Hoàn thành', 'Gói dịch vụ VIP HÀ MINH')")
    for appt in special_appts:
        lh_rows.append(f"('{appt[0]}', '{appt[1]}', '{appt[2]}', '{appt[3]}', '{appt[4]}', '{appt[5]}')")
    seed_sql += ",\n".join(lh_rows) + ";\n"

    # Assemble ChiTietLichHen SQL
    seed_sql += "\n-- --------------------------------------------------------------------\n"
    seed_sql += "-- 6. BẢNG CHITIETLICHHEN\n"
    seed_sql += "-- --------------------------------------------------------------------\n"
    seed_sql += "INSERT OR REPLACE INTO ChiTietLichHen (MaLichHen, MaDichVu, GiaTaiThoiDiemDat, GhiChuDichVu) VALUES\n"
    ctlh_rows = []
    for inv in invoices_data:
        ma_lh = inv[1]
        for svc_id, price in inv[5]:
            ctlh_rows.append(f"('{ma_lh}', '{svc_id}', {price}, 'Dịch vụ VIP')")
    
    # Special details:
    # LH005: 2 services (DV003, DV005)
    ctlh_rows.append("('LH005', 'DV003', 2800000, 'Nhuộm Balayage VIP 150p')")
    ctlh_rows.append("('LH005', 'DV005', 2200000, 'Nano Keratin VIP 75p')")
    # LH006: 2 services (DV014, DV006)
    ctlh_rows.append("('LH006', 'DV014', 450000, 'Fade sắc nét')")
    ctlh_rows.append("('LH006', 'DV006', 350000, 'Gội hoàng gia')")
    # LH007: EXACTLY 2 details (DV002, DV005) for test_on_delete_cascade_appointment_details
    ctlh_rows.append("('LH007', 'DV002', 1850000, 'Uốn Collagen VIP')")
    ctlh_rows.append("('LH007', 'DV005', 2200000, 'Phục hồi Keratin')")
    # LH008
    ctlh_rows.append("('LH008', 'DV006', 350000, 'Gội thư giãn')")
    # LH009
    ctlh_rows.append("('LH009', 'DV003', 2800000, 'Nhuộm xám khói')")
    # LH010
    ctlh_rows.append("('LH010', 'DV001', 350000, 'Lịch đã hủy')")
    # LH034
    ctlh_rows.append("('LH034', 'DV001', 350000, 'Cắt Master Stylist')")
    # LH035
    ctlh_rows.append("('LH035', 'DV006', 350000, 'Gội hoàng gia')")

    seed_sql += ",\n".join(ctlh_rows) + ";\n"

    # Assemble HoaDon SQL
    seed_sql += "\n-- --------------------------------------------------------------------\n"
    seed_sql += "-- 7. BẢNG HOADON (27 Hóa đơn VIP - Doanh thu cực cao > 185 Triệu Đồng)\n"
    seed_sql += "-- Ràng buộc 100%: ThanhTien = TongTien - GiamGia, MaLichHen UNIQUE\n"
    seed_sql += "-- --------------------------------------------------------------------\n"
    seed_sql += "INSERT OR REPLACE INTO HoaDon (MaHoaDon, MaLichHen, NgayTao, TongTien, GiamGia, ThanhTien, PhuongThucThanhToan, TrangThaiThanhToan) VALUES\n"
    hd_rows = []
    total_rev = 0
    today_rev = 0
    for inv in invoices_data:
        ma_hd, ma_lh, _, _, ngay, svcs, giam_gia, phuong_thuc = inv
        tong_tien = sum(s[1] for s in svcs)
        thanh_tien = tong_tien - giam_gia
        total_rev += thanh_tien
        if "2026-09-19" in ngay:
            today_rev += thanh_tien
        hd_rows.append(f"('{ma_hd}', '{ma_lh}', '{ngay}', {tong_tien}, {giam_gia}, {thanh_tien}, '{phuong_thuc}', 'Đã thanh toán')")
    seed_sql += ",\n".join(hd_rows) + ";\n"

    # Assemble TroLyAI SQL
    seed_sql += """
-- --------------------------------------------------------------------
-- 8. BẢNG TROLYAI (Lịch sử tương tác AI Salon HÀ MINH)
-- --------------------------------------------------------------------
INSERT OR REPLACE INTO TroLyAI (MaYeuCau, TenModelAI, ThoiGianXuLy, DuLieuPhanHoi, MaKhachHang) VALUES
('YC001', 'gemini-1.5-flash', 1150, 'Khách hàng VIP Nguyễn Thị Mai có chất tóc tơ mảnh. Khuyến nghị combo Đẳng cấp: Cấy Nano Keratin (2.2Tr) kết hợp Cắt Master Stylist (350k) giúp tóc tăng độ dày bồng bềnh và bóng khỏe tự nhiên.', 'KH001'),
('YC002', 'gemini-1.5-flash', 980, 'Khách hàng VIP Phạm Quỳnh Nga đã tẩy bạch kim level 9. CẢNH BÁO: Tuyệt đối không dùng nồng độ amoniac cao, chỉ định dùng Dịch vụ Nhuộm Balayage thảo dược châu Âu (2.8Tr) và Bọc Protein tơ tằm (3.2Tr).', 'KH003'),
('YC003', 'gemini-1.5-flash', 1220, 'Dạ kính chào chị Trần Bảo Anh! HÀ MINH Hair Salon xin nhắc lịch hẹn lúc 19:00 hôm nay với Stylist Minh Tóc Mây cho dịch vụ Uốn sóng bung Collagen Nano VIP (1.85Tr). Salon rất hân hạnh được đón tiếp chị!', 'KH004'),
('YC004', 'gemini-1.5-flash', 1050, '📋 Tóm tắt cho Thợ Đỗ Hải Phong: Khách VIP Lê Văn Hùng thích phom Fade sắc nét, tỉa kết cấu textured tự nhiên và vuốt sáp clay giữ nếp sang trọng.', 'KH002'),
('YC005', 'gemini-1.5-flash', 1100, 'Khách hàng Đặng Hoàng Yến có da đầu khô: Khuyến nghị thực hiện Liệu trình Scalp Detox (1.2Tr) kết hợp Duỗi phủ bóng kim cương Nano Diamond (2.4Tr).', 'KH006'),
('YC006', 'gemini-1.5-flash', 1250, 'Tư vấn kiểu tóc cho khách Ngô Thanh Vân: Khuôn mặt góc cạnh rất hợp với phom Bob cắt ngắn cá tính (350k), kết hợp liệu trình Bọc Protein tơ tằm tái sinh tóc nát (3.2Tr).', 'KH011'),
('YC007', 'gemini-1.5-flash', 920, 'Dạ chào anh Vũ Đức Nam! HÀ MINH Hair Salon xin nhắc lịch hẹn làm tóc với Thợ Đỗ Hải Phong cho combo Uốn Texture phồng chân tóc nam VIP.', 'KH007'),
('YC008', 'gemini-1.5-flash', 890, 'Khách Đỗ Cẩm Tú có tóc dập xù cũ xơ xác: Khuyến nghị gói Cấp cứu tóc hư tổn Olaplex & Keratin trong 4 tuần liên tiếp.', 'KH013');
"""
    
    with open(SEED_PATH, "w", encoding="utf-8") as f:
        f.write(seed_sql)

    print(f"[+] Successfully wrote {SEED_PATH}")
    print(f"[*] Total Seed Invoices: {len(invoices_data)}")
    print(f"[*] Total Revenue: {total_rev:,} VND")
    print(f"[*] Today Revenue: {today_rev:,} VND")

if __name__ == "__main__":
    generate_high_revenue_seed()
