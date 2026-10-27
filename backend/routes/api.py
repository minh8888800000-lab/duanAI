"""
REST API Endpoints Blueprint for Hair Salon Management System.
Handles Authentication, Customers, Stylists, Services, Appointments, Invoices, Reports, and AI features.
"""

from functools import wraps
from flask import Blueprint, request, jsonify
from backend.services.auth_service import AuthService
from backend.services.booking_service import BookingService
from backend.services.billing_service import BillingService
from backend.services.tro_ly_ai import TroLyAIService
from backend.db import get_db_connection

api_bp = Blueprint("api", __name__, url_prefix="/api")


# --- Authentication Middleware Helper ---
def get_auth_user():
    """Extracts and verifies JWT from header or query param, returns user payload or None."""
    auth_header = request.headers.get("Authorization", "")
    token = ""
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
    elif "token" in request.args:
        token = request.args.get("token")
    if not token:
        return None
    payload = AuthService.verify_token(token)
    if not payload or payload.get("kicked"):
        return None
    return payload


def require_auth(roles=None):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth_header = request.headers.get("Authorization", "")
            token = ""
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ", 1)[1]
            elif "token" in request.args:
                token = request.args.get("token")

            if not token:
                return jsonify({"error": "Yêu cầu đăng nhập để truy cập"}), 401

            payload = AuthService.verify_token(token)
            if not payload:
                return jsonify({"error": "Phiên làm việc đã hết hạn hoặc không hợp lệ"}), 401

            if payload.get("kicked"):
                return jsonify({
                    "success": False,
                    "kicked": True,
                    "code": "CONCURRENT_LOGIN",
                    "error": payload.get("error") or "Tài khoản của bạn đã được đăng nhập trên một thiết bị khác."
                }), 401

            if roles and payload.get("vai_tro") not in roles:
                return jsonify({"error": "Bạn không có quyền thực hiện chức năng này"}), 403

            request.user = payload
            return f(*args, **kwargs)

        return decorated

    return decorator


# ====================================================================
# 1. AUTHENTICATION ROUTES (UC001)
# ====================================================================
@api_bp.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"success": False, "message": "Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu."}), 400

    result = AuthService.login(username, password)
    status_code = 200 if result.get("success") else 400
    return jsonify(result), status_code


@api_bp.route("/auth/me", methods=["GET"])
@require_auth()
def get_current_user():
    return jsonify({"success": True, "user": request.user})


@api_bp.route("/auth/logout", methods=["POST"])
@require_auth()
def logout():
    user = request.user
    tk_id = user.get("sub")
    if tk_id:
        AuthService.logout(tk_id)
    return jsonify({"success": True, "message": "Đã đăng xuất thành công."})


# ====================================================================
# 1.1 ACCOUNT MANAGEMENT ROUTES (ADMIN ONLY)
# ====================================================================
@api_bp.route("/accounts", methods=["GET"])
@require_auth(roles=["Admin"])
def get_accounts():
    """Lấy danh sách tất cả tài khoản kèm thông tin nhân viên liên kết."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT tk.MaTaiKhoan, tk.TenDangNhap, tk.VaiTro,
                   nv.MaNhanVien, nv.HoTen, nv.ChucVu, nv.SoDienThoai
            FROM TaiKhoan tk
            LEFT JOIN NhanVien nv ON tk.MaTaiKhoan = nv.MaTaiKhoan
            ORDER BY tk.MaTaiKhoan ASC
            """
        )
        accounts = [dict(r) for r in cursor.fetchall()]
        return jsonify({"success": True, "accounts": accounts})
    finally:
        conn.close()


@api_bp.route("/accounts", methods=["POST"])
@require_auth(roles=["Admin"])
def create_account():
    """Thêm tài khoản mới và tùy chọn liên kết nhân viên."""
    data = request.get_json() or {}
    username = data.get("ten_dang_nhap", "").strip()
    password = data.get("mat_khau", "").strip()
    role = data.get("vai_tro", "Tho").strip()
    staff_id = data.get("ma_nhan_vien", "").strip() or None

    if not username:
        return jsonify({"success": False, "message": "Vui lòng nhập tên đăng nhập."}), 400
    if len(username) < 3:
        return jsonify({"success": False, "message": "Tên đăng nhập phải có ít nhất 3 ký tự."}), 400
    if not password or len(password) < 4:
        return jsonify({"success": False, "message": "Mật khẩu phải có ít nhất 4 ký tự."}), 400

    valid_roles = ["Admin", "LeTan", "Tho"]
    if role not in valid_roles:
        return jsonify({"success": False, "message": f"Vai trò không hợp lệ. Phải là một trong: {', '.join(valid_roles)}"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Kiểm tra trùng username
        cursor.execute("SELECT 1 FROM TaiKhoan WHERE LOWER(TenDangNhap) = LOWER(?)", (username,))
        if cursor.fetchone():
            return jsonify({"success": False, "message": f"Tên đăng nhập '{username}' đã tồn tại trên hệ thống."}), 400

        # Sinh mã tài khoản mới TKxxx
        cursor.execute("SELECT MaTaiKhoan FROM TaiKhoan WHERE MaTaiKhoan LIKE 'TK%'")
        rows = cursor.fetchall()
        max_num = 0
        for r in rows:
            tk_id = r["MaTaiKhoan"]
            num_part = tk_id[2:]
            if num_part.isdigit():
                max_num = max(max_num, int(num_part))
        new_account_id = f"TK{max_num + 1:03d}"

        # Thêm tài khoản
        cursor.execute(
            """
            INSERT INTO TaiKhoan (MaTaiKhoan, TenDangNhap, MatKhau, VaiTro)
            VALUES (?, ?, ?, ?)
            """,
            (new_account_id, username, password, role),
        )

        # Nếu có chọn nhân viên để gán tài khoản
        if staff_id:
            cursor.execute("SELECT MaNhanVien, MaTaiKhoan FROM NhanVien WHERE MaNhanVien = ?", (staff_id,))
            staff_row = cursor.fetchone()
            if not staff_row:
                conn.rollback()
                return jsonify({"success": False, "message": "Không tìm thấy nhân viên được chỉ định."}), 404
            cursor.execute(
                "UPDATE NhanVien SET MaTaiKhoan = ? WHERE MaNhanVien = ?",
                (new_account_id, staff_id),
            )

        conn.commit()
        return jsonify({
            "success": True,
            "message": f"Thêm tài khoản '{username}' ({role}) thành công!",
            "account": {
                "MaTaiKhoan": new_account_id,
                "TenDangNhap": username,
                "VaiTro": role,
                "MaNhanVien": staff_id,
            }
        })
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": f"Lỗi hệ thống: {str(e)}"}), 500
    finally:
        conn.close()


@api_bp.route("/accounts/<account_id>", methods=["PUT"])
@require_auth(roles=["Admin"])
def update_account(account_id):
    """Cập nhật thông tin tài khoản (mật khẩu, vai trò, liên kết nhân viên)."""
    data = request.get_json() or {}
    new_password = data.get("mat_khau", "").strip()
    new_role = data.get("vai_tro", "").strip()
    staff_id = data.get("ma_nhan_vien")  # có thể là None hoặc chuỗi rỗng

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM TaiKhoan WHERE MaTaiKhoan = ?", (account_id,))
        acc = cursor.fetchone()
        if not acc:
            return jsonify({"success": False, "message": "Tài khoản không tồn tại."}), 404

        updates = []
        params = []
        if new_password:
            if len(new_password) < 4:
                return jsonify({"success": False, "message": "Mật khẩu phải có ít nhất 4 ký tự."}), 400
            updates.append("MatKhau = ?")
            params.append(new_password)

        if new_role:
            if new_role not in ["Admin", "LeTan", "Tho"]:
                return jsonify({"success": False, "message": "Vai trò không hợp lệ."}), 400
            updates.append("VaiTro = ?")
            params.append(new_role)

        if updates:
            params.append(account_id)
            cursor.execute(f"UPDATE TaiKhoan SET {', '.join(updates)} WHERE MaTaiKhoan = ?", tuple(params))

        # Cập nhật liên kết nhân viên nếu được gửi lên
        if staff_id is not None:
            # Gỡ tài khoản khỏi nhân viên cũ (nếu có)
            cursor.execute("UPDATE NhanVien SET MaTaiKhoan = NULL WHERE MaTaiKhoan = ?", (account_id,))
            if str(staff_id).strip():
                cursor.execute("UPDATE NhanVien SET MaTaiKhoan = ? WHERE MaNhanVien = ?", (account_id, str(staff_id).strip()))

        conn.commit()
        return jsonify({"success": True, "message": "Cập nhật tài khoản thành công!"})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": f"Lỗi: {str(e)}"}), 500
    finally:
        conn.close()


@api_bp.route("/accounts/<account_id>", methods=["DELETE"])
@require_auth(roles=["Admin"])
def delete_account(account_id):
    """Xóa tài khoản người dùng khỏi hệ thống (ngăn tự xóa chính mình)."""
    current_user_tk = request.user.get("sub") or request.user.get("ma_tai_khoan")
    if current_user_tk == account_id:
        return jsonify({"success": False, "message": "Không thể tự xóa tài khoản đang đăng nhập của chính bạn!"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM TaiKhoan WHERE MaTaiKhoan = ?", (account_id,))
        acc = cursor.fetchone()
        if not acc:
            return jsonify({"success": False, "message": "Tài khoản không tồn tại."}), 404

        # Gỡ liên kết ở bảng NhanVien
        cursor.execute("UPDATE NhanVien SET MaTaiKhoan = NULL WHERE MaTaiKhoan = ?", (account_id,))

        # Xóa khỏi TaiKhoan
        cursor.execute("DELETE FROM TaiKhoan WHERE MaTaiKhoan = ?", (account_id,))
        conn.commit()
        return jsonify({"success": True, "message": f"Đã xóa tài khoản '{acc['TenDangNhap']}' thành công."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": f"Lỗi: {str(e)}"}), 500
    finally:
        conn.close()


# ====================================================================
# 2. CUSTOMER MANAGEMENT ROUTES (UC002)
# ====================================================================
@api_bp.route("/customers", methods=["GET"])
def get_customers():
    keyword = request.args.get("q", "").strip()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if keyword:
            cursor.execute(
                """
                SELECT * FROM KhachHang 
                WHERE HoTen LIKE ? OR SoDienThoai LIKE ?
                ORDER BY MaKhachHang DESC
                """,
                (f"%{keyword}%", f"%{keyword}%"),
            )
        else:
            cursor.execute("SELECT * FROM KhachHang ORDER BY MaKhachHang DESC")
        customers = []
        for r in cursor.fetchall():
            d = dict(r)
            d["ma_khach_hang"] = d.get("MaKhachHang")
            d["ho_ten"] = d.get("HoTen")
            d["so_dien_thoai"] = d.get("SoDienThoai")
            d["ghi_chu_toc"] = d.get("GhiChuToc")
            customers.append(d)
        return jsonify({"success": True, "customers": customers, "count": len(customers)})
    finally:
        conn.close()


@api_bp.route("/customers", methods=["POST"])
def create_customer():
    data = request.get_json() or {}
    ho_ten = data.get("ho_ten", "").strip() or "Khách vãng lai"
    so_dien_thoai = data.get("so_dien_thoai", "").strip() or None
    ghi_chu_toc = data.get("ghi_chu_toc", "").strip() or None

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check unique phone if not null
        if so_dien_thoai:
            cursor.execute("SELECT MaKhachHang FROM KhachHang WHERE SoDienThoai = ?", (so_dien_thoai,))
            if cursor.fetchone():
                return jsonify({"success": False, "message": "Số điện thoại này đã được đăng ký trên hệ thống."}), 400

        cursor.execute("SELECT COUNT(*) as cnt FROM KhachHang")
        cnt = cursor.fetchone()["cnt"] + 1
        ma_khach_hang = f"KH{cnt:03d}"
        cursor.execute("SELECT 1 FROM KhachHang WHERE MaKhachHang = ?", (ma_khach_hang,))
        if cursor.fetchone():
            import uuid
            ma_khach_hang = f"KH{uuid.uuid4().hex[:5].upper()}"

        cursor.execute(
            """
            INSERT INTO KhachHang (MaKhachHang, HoTen, SoDienThoai, GhiChuToc)
            VALUES (?, ?, ?, ?)
            """,
            (ma_khach_hang, ho_ten, so_dien_thoai, ghi_chu_toc),
        )
        conn.commit()
        return jsonify({
            "success": True,
            "message": "Thêm khách hàng thành công!",
            "customer": {
                "ma_khach_hang": ma_khach_hang,
                "ho_ten": ho_ten,
                "so_dien_thoai": so_dien_thoai,
                "ghi_chu_toc": ghi_chu_toc,
            },
        })
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()


@api_bp.route("/customers/<customer_id>", methods=["PUT"])
def update_customer(customer_id):
    data = request.get_json() or {}
    ho_ten = data.get("ho_ten", "").strip()
    so_dien_thoai = data.get("so_dien_thoai", "").strip() or None
    ghi_chu_toc = data.get("ghi_chu_toc", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if so_dien_thoai:
            cursor.execute(
                "SELECT MaKhachHang FROM KhachHang WHERE SoDienThoai = ? AND MaKhachHang != ?",
                (so_dien_thoai, customer_id),
            )
            if cursor.fetchone():
                return jsonify({"success": False, "message": "Số điện thoại này đã được sử dụng bởi khách hàng khác."}), 400

        cursor.execute(
            """
            UPDATE KhachHang 
            SET HoTen = COALESCE(NULLIF(?, ''), HoTen),
                SoDienThoai = ?,
                GhiChuToc = ?
            WHERE MaKhachHang = ?
            """,
            (ho_ten, so_dien_thoai, ghi_chu_toc, customer_id),
        )
        conn.commit()
        return jsonify({"success": True, "message": "Cập nhật hồ sơ khách hàng thành công."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()


@api_bp.route("/customers/<customer_id>/history", methods=["GET"])
def get_customer_history(customer_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT lh.MaLichHen, lh.NgayGioHen, lh.TrangThai, lh.GhiChu,
                   nv.HoTen as TenThợ, hd.MaHoaDon, hd.ThanhTien, hd.NgayTao as NgayThanhToan
            FROM LichHen lh
            JOIN NhanVien nv ON lh.MaNhanVien = nv.MaNhanVien
            LEFT JOIN HoaDon hd ON lh.MaLichHen = hd.MaLichHen
            WHERE lh.MaKhachHang = ?
            ORDER BY lh.NgayGioHen DESC
            """,
            (customer_id,),
        )
        appts = [dict(r) for r in cursor.fetchall()]
        for a in appts:
            cursor.execute(
                """
                SELECT dv.TenDichVu, ctlh.GiaTaiThoiDiemDat 
                FROM ChiTietLichHen ctlh
                JOIN DichVu dv ON ctlh.MaDichVu = dv.MaDichVu
                WHERE ctlh.MaLichHen = ?
                """,
                (a["MaLichHen"],),
            )
            a["dich_vu"] = [dict(s) for s in cursor.fetchall()]

        return jsonify({"success": True, "history": appts})
    finally:
        conn.close()


# ====================================================================
# 3. STYLIST & EMPLOYEE MANAGEMENT (UC003)
# ====================================================================
@api_bp.route("/stylists", methods=["GET"])
def get_stylists():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT nv.*, tk.TenDangNhap, tk.VaiTro
            FROM NhanVien nv
            LEFT JOIN TaiKhoan tk ON nv.MaTaiKhoan = tk.MaTaiKhoan
            ORDER BY nv.ChucVu, nv.HoTen
            """
        )
        stylists = [dict(r) for r in cursor.fetchall()]
        return jsonify({"success": True, "stylists": stylists})
    finally:
        conn.close()


@api_bp.route("/stylists", methods=["POST"])
def create_stylist():
    data = request.get_json() or {}
    ho_ten = data.get("ho_ten", "").strip()
    so_dien_thoai = data.get("so_dien_thoai", "").strip()
    chuc_vu = data.get("chuc_vu", "Thợ chính").strip()

    if not ho_ten or not so_dien_thoai:
        return jsonify({"success": False, "message": "Vui lòng nhập đầy đủ tên và số điện thoại."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Tự động sinh mã NVxxx
        cursor.execute("SELECT MaNhanVien FROM NhanVien WHERE MaNhanVien LIKE 'NV%'")
        nv_rows = cursor.fetchall()
        max_nv = 0
        for r in nv_rows:
            part = str(r["MaNhanVien"])[2:]
            if part.isdigit():
                max_nv = max(max_nv, int(part))
        ma_nhan_vien = f"NV{max_nv + 1:03d}"

        # Tùy chọn cấp tài khoản đăng nhập luôn nếu có
        ma_tai_khoan = None
        username = data.get("ten_dang_nhap", "").strip()
        password = data.get("mat_khau", "").strip()
        if username and password:
            cursor.execute("SELECT 1 FROM TaiKhoan WHERE LOWER(TenDangNhap) = LOWER(?)", (username,))
            if cursor.fetchone():
                return jsonify({"success": False, "message": f"Tên đăng nhập '{username}' đã tồn tại."}), 400

            cursor.execute("SELECT MaTaiKhoan FROM TaiKhoan WHERE MaTaiKhoan LIKE 'TK%'")
            tk_rows = cursor.fetchall()
            max_tk = 0
            for r in tk_rows:
                part = str(r["MaTaiKhoan"])[2:]
                if part.isdigit():
                    max_tk = max(max_tk, int(part))
            ma_tai_khoan = f"TK{max_tk + 1:03d}"

            role_map = {"Quản lý": "Admin", "Lễ tân": "LeTan", "Thợ chính": "Tho", "Thợ phụ": "Tho"}
            acc_role = role_map.get(chuc_vu, "Tho")
            cursor.execute(
                "INSERT INTO TaiKhoan (MaTaiKhoan, TenDangNhap, MatKhau, VaiTro) VALUES (?, ?, ?, ?)",
                (ma_tai_khoan, username, password, acc_role),
            )

        cursor.execute(
            """
            INSERT INTO NhanVien (MaNhanVien, HoTen, SoDienThoai, ChucVu, TrangThaiRanh, MaTaiKhoan)
            VALUES (?, ?, ?, ?, 1, ?)
            """,
            (ma_nhan_vien, ho_ten, so_dien_thoai, chuc_vu, ma_tai_khoan),
        )
        conn.commit()
        msg = f"Thêm nhân viên thành công ({ma_nhan_vien})!"
        if ma_tai_khoan:
            msg += f" Đã cấp tài khoản '{username}'."
        return jsonify({"success": True, "message": msg, "ma_nhan_vien": ma_nhan_vien, "ma_tai_khoan": ma_tai_khoan})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()


@api_bp.route("/stylists/<stylist_id>", methods=["PUT"])
def update_stylist_info(stylist_id):
    user = get_auth_user()
    data = request.get_json() or {}

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM NhanVien WHERE MaNhanVien = ?", (stylist_id,))
    staff = cursor.fetchone()
    conn.close()
    if not staff:
        return jsonify({"success": False, "message": "Không tìm thấy nhân viên."}), 404

    req_chuc_vu = data.get("chuc_vu", "").strip()
    if req_chuc_vu and req_chuc_vu != staff["ChucVu"]:
        user_role = str(user.get("vai_tro") or user.get("role") or "").lower() if user else ""
        if user_role != "admin":
            return jsonify({
                "success": False,
                "message": "🔒 Quyền hạn không đủ: Chỉ Quản trị viên (Admin) mới có quyền thay đổi chức vụ nhân sự."
            }), 403

    ho_ten = data.get("ho_ten", "").strip() or staff["HoTen"]
    so_dien_thoai = data.get("so_dien_thoai", "").strip() or staff["SoDienThoai"]
    chuc_vu = req_chuc_vu or staff["ChucVu"]

    from backend.models.entities import NhanVien
    result = NhanVien.CapNhatThongTinNhanVien(stylist_id, ho_ten, so_dien_thoai, chuc_vu)
    status_code = 200 if result.get("TrangThaiCapNhat") else 400
    return jsonify({"success": result.get("TrangThaiCapNhat"), "message": result.get("ThongBao")}), status_code


@api_bp.route("/stylists/swap-roles", methods=["POST"])
def swap_stylist_roles():
    user = get_auth_user()
    user_role = str(user.get("vai_tro") or user.get("role") or "").lower() if user else ""
    if user_role != "admin":
        return jsonify({
            "success": False,
            "message": "🔒 Quyền hạn không đủ: Chỉ Quản trị viên (Admin) mới có quyền hoán đổi chức vụ nhân sự."
        }), 403

    data = request.get_json() or {}
    staff1_id = data.get("staff1_id", "").strip()
    staff2_id = data.get("staff2_id", "").strip()

    if not staff1_id or not staff2_id or staff1_id == staff2_id:
        return jsonify({"success": False, "message": "Vui lòng chọn 2 nhân sự khác nhau để hoán đổi vị trí."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT MaNhanVien, HoTen, ChucVu FROM NhanVien WHERE MaNhanVien = ?", (staff1_id,))
        s1 = cursor.fetchone()
        cursor.execute("SELECT MaNhanVien, HoTen, ChucVu FROM NhanVien WHERE MaNhanVien = ?", (staff2_id,))
        s2 = cursor.fetchone()

        if not s1 or not s2:
            return jsonify({"success": False, "message": "Không tìm thấy một trong hai nhân viên."}), 404

        role1 = s1["ChucVu"]
        role2 = s2["ChucVu"]

        cursor.execute("UPDATE NhanVien SET ChucVu = ? WHERE MaNhanVien = ?", (role2, staff1_id))
        cursor.execute("UPDATE NhanVien SET ChucVu = ? WHERE MaNhanVien = ?", (role1, staff2_id))
        conn.commit()

        return jsonify({
            "success": True,
            "message": f"🎉 Hoán đổi vị trí thành công: {s1['HoTen']} ({role1} ➔ {role2}) và {s2['HoTen']} ({role2} ➔ {role1}).",
            "staff1": {"id": staff1_id, "name": s1["HoTen"], "old_role": role1, "new_role": role2},
            "staff2": {"id": staff2_id, "name": s2["HoTen"], "old_role": role2, "new_role": role1},
        })
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": f"Lỗi hệ thống: {str(e)}"}), 500
    finally:
        conn.close()


@api_bp.route("/stylists/<stylist_id>/status", methods=["PUT"])
def update_stylist_status(stylist_id):
    data = request.get_json() or {}
    trang_thai_ranh = 1 if data.get("trang_thai_ranh") else 0

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE NhanVien SET TrangThaiRanh = ? WHERE MaNhanVien = ?",
            (trang_thai_ranh, stylist_id),
        )
        conn.commit()
        return jsonify({"success": True, "message": "Cập nhật trạng thái thợ thành công."})
    finally:
        conn.close()


# ====================================================================
# 4. SERVICE CATALOG MANAGEMENT (UC004)
# ====================================================================
@api_bp.route("/services", methods=["GET"])
def get_services():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM DichVu ORDER BY GiaTien ASC")
        services = []
        for r in cursor.fetchall():
            d = dict(r)
            d["ma_dich_vu"] = d.get("MaDichVu")
            d["ten_dich_vu"] = d.get("TenDichVu")
            d["gia_tien"] = d.get("GiaTien")
            d["thoi_gian_thuc_hien"] = d.get("ThoiGianThucHien")
            d["mo_ta"] = d.get("MoTa")
            services.append(d)
        return jsonify({"success": True, "services": services, "count": len(services)})
    finally:
        conn.close()


@api_bp.route("/services", methods=["POST"])
def create_service():
    data = request.get_json() or {}
    ten_dich_vu = data.get("ten_dich_vu", "").strip()
    gia_tien = float(data.get("gia_tien", 0))
    thoi_gian = int(data.get("thoi_gian_thuc_hien", 30))
    mo_ta = data.get("mo_ta", "").strip()

    if not ten_dich_vu or gia_tien < 0 or thoi_gian <= 0:
        return jsonify({"success": False, "message": "Dữ liệu dịch vụ không hợp lệ."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) as cnt FROM DichVu")
        cnt = cursor.fetchone()["cnt"] + 1
        ma_dich_vu = f"DV{cnt:03d}"

        cursor.execute(
            """
            INSERT INTO DichVu (MaDichVu, TenDichVu, GiaTien, ThoiGianThucHien, MoTa)
            VALUES (?, ?, ?, ?, ?)
            """,
            (ma_dich_vu, ten_dich_vu, gia_tien, thoi_gian, mo_ta),
        )
        conn.commit()
        return jsonify({"success": True, "message": "Thêm dịch vụ thành công!", "ma_dich_vu": ma_dich_vu})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()


@api_bp.route("/services/<service_id>", methods=["PUT"])
def update_service(service_id):
    data = request.get_json() or {}
    ten_dich_vu = data.get("ten_dich_vu", "").strip()
    gia_tien = float(data.get("gia_tien", 0))
    thoi_gian = int(data.get("thoi_gian_thuc_hien", 30))
    mo_ta = data.get("mo_ta", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE DichVu 
            SET TenDichVu = ?, GiaTien = ?, ThoiGianThucHien = ?, MoTa = ?
            WHERE MaDichVu = ?
            """,
            (ten_dich_vu, gia_tien, thoi_gian, mo_ta, service_id),
        )
        conn.commit()
        return jsonify({"success": True, "message": "Cập nhật dịch vụ thành công!"})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()


@api_bp.route("/services/<service_id>", methods=["DELETE"])
def delete_service(service_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM DichVu WHERE MaDichVu = ?", (service_id,))
        conn.commit()
        return jsonify({"success": True, "message": "Xóa dịch vụ thành công!"})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": f"Không thể xóa dịch vụ này vì đang có trong lịch hẹn: {str(e)}"}), 400
    finally:
        conn.close()


# ====================================================================
# 5. APPOINTMENT SCHEDULING (UC005)
# ====================================================================
@api_bp.route("/appointments", methods=["GET"])
def get_appointments():
    user = get_auth_user()
    date_str = request.args.get("date")
    ma_nhan_vien = request.args.get("stylist_id")
    trang_thai = request.args.get("status")

    # If logged in as Tho, strictly restrict to only their own assigned appointments
    if user and user.get("vai_tro") == "Tho":
        ma_nhan_vien = user.get("ma_nhan_vien")

    appts = BookingService.get_appointments(date_str, ma_nhan_vien, trang_thai)
    return jsonify({"success": True, "appointments": appts})


@api_bp.route("/appointments", methods=["POST"])
def create_appointment():
    data = request.get_json() or {}
    user = get_auth_user()

    ma_khach_hang = data.get("ma_khach_hang")
    ho_ten = (data.get("ho_ten") or "").strip()
    so_dien_thoai = (data.get("so_dien_thoai") or "").strip()
    ma_nhan_vien = data.get("ma_nhan_vien")
    ngay_gio_hen = data.get("ngay_gio_hen")
    service_ids = data.get("service_ids", [])
    ghi_chu = (data.get("ghi_chu") or "").strip()
    trang_thai = data.get("trang_thai")

    # Support guest booking directly from Homepage (without pre-existing customer ID)
    if not ma_khach_hang and (ho_ten or so_dien_thoai):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            if so_dien_thoai:
                cursor.execute("SELECT MaKhachHang FROM KhachHang WHERE SoDienThoai = ?", (so_dien_thoai,))
                row = cursor.fetchone()
                if row:
                    ma_khach_hang = row["MaKhachHang"]
            if not ma_khach_hang:
                cursor.execute("SELECT COUNT(*) as cnt FROM KhachHang")
                cnt = cursor.fetchone()["cnt"] + 1
                ma_khach_hang = f"KH{cnt:03d}"
                cursor.execute("SELECT 1 FROM KhachHang WHERE MaKhachHang = ?", (ma_khach_hang,))
                if cursor.fetchone():
                    import uuid
                    ma_khach_hang = f"KH{uuid.uuid4().hex[:5].upper()}"
                cursor.execute(
                    "INSERT INTO KhachHang (MaKhachHang, HoTen, SoDienThoai, GhiChuToc) VALUES (?, ?, ?, ?)",
                    (ma_khach_hang, ho_ten or "Khách đặt online", so_dien_thoai or None, "Đặt lịch trực tuyến từ Trang Chủ"),
                )
                conn.commit()
        finally:
            conn.close()

    # If guest or unauthenticated, default status is 'Chờ xác nhận'
    if not trang_thai:
        if user and user.get("vai_tro") in ["Admin", "LeTan"]:
            trang_thai = "Đã xác nhận"
        else:
            trang_thai = "Chờ xác nhận"

    # If stylist is not selected or 'auto', pick the first available free stylist
    if not ma_nhan_vien or ma_nhan_vien == "auto":
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT MaNhanVien FROM NhanVien WHERE ChucVu IN ('Thợ chính', 'Thợ phụ') AND TrangThaiRanh = 1 LIMIT 1")
            st = cursor.fetchone()
            if st:
                ma_nhan_vien = st["MaNhanVien"]
            else:
                cursor.execute("SELECT MaNhanVien FROM NhanVien WHERE ChucVu IN ('Thợ chính', 'Thợ phụ') LIMIT 1")
                st2 = cursor.fetchone()
                ma_nhan_vien = st2["MaNhanVien"] if st2 else "NV004"
        finally:
            conn.close()

    if not ma_khach_hang or not ma_nhan_vien or not ngay_gio_hen or not service_ids:
        return jsonify({"success": False, "message": "Vui lòng điền đầy đủ thông tin đặt lịch bắt buộc."}), 400

    result = BookingService.create_appointment(
        ma_khach_hang, ma_nhan_vien, ngay_gio_hen, service_ids, ghi_chu, trang_thai=trang_thai
    )
    status_code = 200 if result.get("success") else 400
    return jsonify(result), status_code


@api_bp.route("/appointments/<appt_id>/reschedule", methods=["PUT"])
def reschedule_appointment(appt_id):
    """Đổi giờ hẹn với kiểm tra xung đột trùng lịch thợ (UC005)."""
    user = get_auth_user()
    if user and user.get("vai_tro") == "Tho":
        return jsonify({"success": False, "message": "Thợ chính không có quyền đổi lịch của khách. Vui lòng liên hệ Lễ tân."}), 403

    data = request.get_json() or {}
    new_datetime = data.get("ngay_gio_hen")
    new_stylist = data.get("ma_nhan_vien")

    if not new_datetime:
        return jsonify({"success": False, "message": "Vui lòng chọn thời gian hẹn mới."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM LichHen WHERE MaLichHen = ?", (appt_id,))
        appt = cursor.fetchone()
        if not appt:
            return jsonify({"success": False, "message": "Không tìm thấy lịch hẹn."}), 404

        target_stylist = new_stylist or appt["MaNhanVien"]

        # Calculate duration of this appointment's services
        cursor.execute(
            """
            SELECT COALESCE(SUM(dv.ThoiGianThucHien), 30) as TongThoiGian
            FROM ChiTietLichHen ctlh
            JOIN DichVu dv ON ctlh.MaDichVu = dv.MaDichVu
            WHERE ctlh.MaLichHen = ?
            """,
            (appt_id,),
        )
        total_duration = cursor.fetchone()["TongThoiGian"]

        # Check collision excluding current appointment
        conflict = BookingService.check_stylist_conflict(
            target_stylist, new_datetime, total_duration, exclude_lich_hen_id=appt_id
        )
        if conflict:
            return jsonify({
                "success": False,
                "message": f"Thợ đã có lịch bận ({conflict['customer_name']} từ {conflict['start_time']} đến {conflict['end_time']}). Vui lòng chọn khung giờ khác.",
                "conflict": conflict,
            }), 400

        cursor.execute(
            "UPDATE LichHen SET NgayGioHen = ?, MaNhanVien = ? WHERE MaLichHen = ?",
            (new_datetime, target_stylist, appt_id),
        )
        conn.commit()
        return jsonify({"success": True, "message": "Đổi lịch hẹn thành công!"})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()


@api_bp.route("/appointments/<appt_id>/status", methods=["PUT"])
def update_appointment_status(appt_id):
    user = get_auth_user()
    data = request.get_json() or {}
    trang_thai_moi = data.get("trang_thai")
    if not trang_thai_moi:
        return jsonify({"success": False, "message": "Thiếu trạng thái mới."}), 400

    # Role enforcement for Tho
    if user and user.get("vai_tro") == "Tho":
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT MaNhanVien FROM LichHen WHERE MaLichHen = ?", (appt_id,))
            row = cursor.fetchone()
            if not row or row["MaNhanVien"] != user.get("ma_nhan_vien"):
                return jsonify({"success": False, "message": "Bạn chỉ có quyền cập nhật lịch hẹn được phân công cho mình."}), 403
            if trang_thai_moi not in ["Đang phục vụ", "Hoàn thành"]:
                return jsonify({"success": False, "message": "Thợ chính chỉ có thể cập nhật trạng thái 'Đang phục vụ' hoặc 'Hoàn thành'."}), 403
        finally:
            conn.close()

    result = BookingService.update_status(appt_id, trang_thai_moi)
    return jsonify(result)


# ====================================================================
# 6. BILLING & CHECKOUT (UC006)
# ====================================================================
@api_bp.route("/billing/preview/<appt_id>", methods=["GET"])
def billing_preview(appt_id):
    user = get_auth_user()
    if user and user.get("vai_tro") == "Tho":
        return jsonify({"success": False, "message": "Thợ chính không có quyền truy cập nghiệp vụ Thu Ngân POS."}), 403

    result = BillingService.get_checkout_preview(appt_id)
    return jsonify(result)


@api_bp.route("/billing/checkout", methods=["POST"])
def billing_checkout():
    user = get_auth_user()
    if user and user.get("vai_tro") == "Tho":
        return jsonify({"success": False, "message": "Thợ chính không có quyền thực hiện Thu Ngân POS."}), 403

    data = request.get_json() or {}
    ma_lich_hen = data.get("ma_lich_hen")
    giam_gia = float(data.get("giam_gia", 0.0))
    phuong_thuc = data.get("phuong_thuc_thanh_toan", "Tiền mặt")
    extra_services = data.get("extra_services", [])

    if not ma_lich_hen:
        return jsonify({"success": False, "message": "Vui lòng chỉ định lịch hẹn cần thanh toán."}), 400

    result = BillingService.create_invoice(ma_lich_hen, giam_gia, phuong_thuc, extra_services)
    status_code = 200 if result.get("success") else 400
    return jsonify(result), status_code


@api_bp.route("/billing/receipt/<inv_id>", methods=["GET"])
def billing_receipt(inv_id):
    result = BillingService.get_invoice_receipt(inv_id)
    return jsonify(result)


# ====================================================================
# 7. BUSINESS STATS & REPORTS (UC007)
# ====================================================================
@api_bp.route("/reports/summary", methods=["GET"])
def get_reports_summary():
    user = get_auth_user()
    if user and user.get("vai_tro") in ["LeTan", "Tho"]:
        return jsonify({"success": False, "message": "Chỉ Quản lý / Admin mới có quyền xem báo cáo doanh thu tài chính."}), 403

    from backend.services.report_service import ReportService
    data = ReportService.get_comprehensive_financial_summary()
    return jsonify(data)


@api_bp.route("/reports/invoices", methods=["GET"])
def get_reports_invoices():
    """Returns detailed list of all invoices for accounting table and ledger."""
    user = get_auth_user()
    if user and user.get("vai_tro") in ["LeTan", "Tho"]:
        return jsonify({"success": False, "message": "Chỉ Quản lý / Admin mới có quyền xem sổ quỹ hóa đơn."}), 403

    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    method = request.args.get("method")
    stylist_id = request.args.get("stylist_id")

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
            SELECT hd.MaHoaDon, hd.MaLichHen, hd.TongTien, hd.GiamGia, hd.ThanhTien,
                   hd.PhuongThucThanhToan, hd.NgayTao,
                   kh.MaKhachHang, kh.HoTen as TenKhachHang, kh.SoDienThoai,
                   nv.MaNhanVien, nv.HoTen as TenTho
            FROM HoaDon hd
            JOIN LichHen lh ON hd.MaLichHen = lh.MaLichHen
            JOIN KhachHang kh ON lh.MaKhachHang = kh.MaKhachHang
            JOIN NhanVien nv ON lh.MaNhanVien = nv.MaNhanVien
            WHERE 1=1
        """
        params = []
        if start_date:
            query += " AND date(hd.NgayTao) >= date(?)"
            params.append(start_date)
        if end_date:
            query += " AND date(hd.NgayTao) <= date(?)"
            params.append(end_date)
        if method:
            query += " AND hd.PhuongThucThanhToan = ?"
            params.append(method)
        if stylist_id:
            query += " AND nv.MaNhanVien = ?"
            params.append(stylist_id)

        query += " ORDER BY hd.NgayTao DESC"
        cursor.execute(query, params)
        rows = [dict(r) for r in cursor.fetchall()]
        return jsonify({"success": True, "invoices": rows, "count": len(rows)})
    finally:
        conn.close()


@api_bp.route("/billing/pos-walkin", methods=["POST"])
def billing_pos_walkin():
    """Direct fast check-out at POS counter for walk-in or booked customers."""
    user = get_auth_user()
    if user and user.get("vai_tro") == "Tho":
        return jsonify({"success": False, "message": "Thợ chính không có quyền thực hiện Thu Ngân POS."}), 403

    data = request.get_json() or {}
    ma_khach_hang = data.get("ma_khach_hang") or "KH001"
    ma_nhan_vien = data.get("ma_nhan_vien") or "NV001"
    service_ids = data.get("service_ids", [])
    giam_gia = float(data.get("giam_gia", 0.0))
    phuong_thuc = data.get("phuong_thuc_thanh_toan", "Tiền mặt")
    ghi_chu = data.get("ghi_chu", "Khách vãng lai tại quầy POS")

    if not service_ids:
        return jsonify({"success": False, "message": "Vui lòng chọn ít nhất 1 dịch vụ."}), 400

    from datetime import datetime
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Create an appointment first
    appt_res = BookingService.create_appointment(
        ma_khach_hang=ma_khach_hang,
        ma_nhan_vien=ma_nhan_vien,
        ngay_gio_hen=now_str,
        service_ids=service_ids,
        ghi_chu=ghi_chu
    )
    if not appt_res.get("success"):
        return jsonify(appt_res), 400

    ma_lich_hen = appt_res["appointment"]["MaLichHen"]

    # Check out and create invoice
    inv_res = BillingService.create_invoice(
        ma_lich_hen=ma_lich_hen,
        giam_gia=giam_gia,
        phuong_thuc_thanh_toan=phuong_thuc
    )
    return jsonify(inv_res), (200 if inv_res.get("success") else 400)


@api_bp.route("/reports/export", methods=["GET"])
def export_reports():
    """Xuất báo cáo doanh thu ra định dạng CSV theo đặc tả UC007."""
    from flask import Response
    import io
    import csv

    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
            SELECT hd.MaHoaDon, hd.NgayTao, kh.HoTen as TenKhachHang, nv.HoTen as TenTho,
                   hd.TongTien, hd.GiamGia, hd.ThanhTien, hd.PhuongThucThanhToan
            FROM HoaDon hd
            JOIN LichHen lh ON hd.MaLichHen = lh.MaLichHen
            JOIN KhachHang kh ON lh.MaKhachHang = kh.MaKhachHang
            JOIN NhanVien nv ON lh.MaNhanVien = nv.MaNhanVien
            WHERE 1=1
        """
        params = []
        if start_date:
            query += " AND date(hd.NgayTao) >= date(?)"
            params.append(start_date)
        if end_date:
            query += " AND date(hd.NgayTao) <= date(?)"
            params.append(end_date)

        query += " ORDER BY hd.NgayTao DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()

        output = io.StringIO()
        # UTF-8 BOM for Excel compatibility
        output.write('\ufeff')
        writer = csv.writer(output)
        writer.writerow(["Mã Hóa Đơn", "Ngày Lập", "Tên Khách Hàng", "Thợ Thực Hiện", "Tổng Tiền (VNĐ)", "Giảm Giá (VNĐ)", "Thành Tiền (VNĐ)", "Phương Thức"])

        for r in rows:
            writer.writerow([
                r["MaHoaDon"],
                r["NgayTao"],
                r["TenKhachHang"],
                r["TenTho"],
                int(r["TongTien"]),
                int(r["GiamGia"]),
                int(r["ThanhTien"]),
                r["PhuongThucThanhToan"],
            ])

        response = Response(output.getvalue(), mimetype="text/csv; charset=utf-8")
        response.headers["Content-Disposition"] = "attachment; filename=bao_cao_doanh_thu_salon.csv"
        return response
    finally:
        conn.close()


# ====================================================================
# 8. AI ASSISTANT FEATURES (UC008, UC009, UC010)
# ====================================================================
@api_bp.route("/ai/suggest", methods=["POST"])
def ai_suggest():
    data = request.get_json() or {}
    customer_id = data.get("customer_id")
    notes = data.get("notes")

    if not customer_id:
        return jsonify({"success": False, "message": "Vui lòng chọn khách hàng."}), 400

    result = TroLyAIService.goi_y_dich_vu(customer_id, notes)
    return jsonify(result)


@api_bp.route("/ai/reminder", methods=["POST"])
def ai_reminder():
    data = request.get_json() or {}
    appointment_id = data.get("appointment_id")

    if not appointment_id:
        return jsonify({"success": False, "message": "Vui lòng chọn lịch hẹn."}), 400

    result = TroLyAIService.sinh_tin_nhan_nhac_lich(appointment_id)
    return jsonify(result)


@api_bp.route("/ai/summary", methods=["POST"])
def ai_summary():
    data = request.get_json() or {}
    customer_id = data.get("customer_id")

    if not customer_id:
        return jsonify({"success": False, "message": "Vui lòng chọn khách hàng."}), 400

    result = TroLyAIService.tom_tat_lich_su_khach_hang(customer_id)
    return jsonify(result)


@api_bp.route("/ai/chat", methods=["POST"])
def ai_chat():
    """Interactive 24/7 AI Salon Stylist Chatbot with RBAC Price Management."""
    data = request.get_json() or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"success": False, "message": "Vui lòng nhập nội dung tin nhắn."}), 400

    auth_user = get_auth_user()
    if not auth_user and data.get("token"):
        auth_user = AuthService.verify_token(data.get("token"))

    context = data.get("context") or {}
    if auth_user:
        context["user"] = auth_user
    if "history" in data and isinstance(data["history"], list):
        context["history"] = data["history"]

    result = TroLyAIService.chat_truc_tuyen(message, context=context)
    return jsonify(result)


@api_bp.route("/ai/questions", methods=["GET"])
def ai_questions():
    """Returns the comprehensive library of 28+ deep domain 'Vì sao...?' inquiries."""
    category = request.args.get("category", "").strip()
    questions = TroLyAIService.get_all_why_questions()
    if category and category != "all":
        questions = [q for q in questions if q.get("category") == category]
    return jsonify({
        "success": True,
        "count": len(questions),
        "total": len(TroLyAIService.get_all_why_questions()),
        "questions": questions
    })


@api_bp.route("/ai/config", methods=["GET", "POST"])
def ai_config():
    """Retrieves or updates the AI API key and model settings."""
    if request.method == "POST":
        data = request.get_json() or {}
        api_key = data.get("api_key", "").strip()
        model_name = data.get("model_name", "").strip() or None
        cfg = TroLyAIService.set_config(api_key, model_name)
        return jsonify({"success": True, "message": "Đã cập nhật cấu hình AI thành công.", "config": cfg})

    return jsonify({"success": True, "config": TroLyAIService.get_config()})


@api_bp.route("/ai/test-connection", methods=["POST"])
def ai_test_connection():
    """Tests connection to Google Gemini API or reports Grounded SQLite status."""
    data = request.get_json() or {}
    api_key = data.get("api_key")
    model_name = data.get("model_name")
    result = TroLyAIService.test_gemini_connection(api_key=api_key, model_name=model_name)
    return jsonify({"success": True, "result": result})


@api_bp.route("/ai/analyze-requirements", methods=["POST"])
def ai_analyze_requirements():
    """Agent Phân Tích Yêu Cầu & Hỗ Trợ Toàn Diện (Requirements Analysis & Full-Lifecycle Agent)."""
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"success": False, "message": "Vui lòng nhập yêu cầu cần phân tích."}), 400

    auth_user = get_auth_user()
    if not auth_user and data.get("token"):
        auth_user = AuthService.verify_token(data.get("token"))

    context = data.get("context") or {}
    if auth_user:
        context["user"] = auth_user

    result = TroLyAIService.phan_tich_yeu_cau(message, context=context)
    return jsonify(result)




