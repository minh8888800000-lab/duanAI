/**
 * HÀ MINH HAIR SALON MANAGEMENT SYSTEM - FRONTEND CORE LOGIC
 * High-performance Vanilla JS implementing Guest Landing Page, RBAC Auth & Appointments.
 */

// Application Global State & Variables
let currentAIHubResponseText = '';

function escapeHTML(str) {
 if (str === null || str === undefined) return '';
 return String(str)
 .replace(/&/g, '&amp;')
 .replace(/</g, '&lt;')
 .replace(/>/g, '&gt;')
 .replace(/"/g, '&quot;')
 .replace(/'/g, '&#39;');
}

const state = {
 authToken: localStorage.getItem('salon_auth_token') || null,
 currentRole: null, // 'Admin', 'LeTan', 'Tho' or null (Guest)
 currentUser: null, // { username, fullName, role, ma_nhan_vien, chuc_vu }
 activeTab: 'dashboard',
 customers: [],
 stylists: [],
 accounts: [],
 services: [],
 appointments: [],
 apptSearchQuery: '',
 selectedCheckoutAppt: null,
};

// --- CORE UTILITIES & AUTH FETCH HELPER (SINGLE DEVICE SESSION ENFORCED) ---
let isKickedModalOpen = false;
let sessionHeartbeatTimer = null;

function handleSessionKicked(message) {
 if (isKickedModalOpen) return;
 isKickedModalOpen = true;
 stopSessionHeartbeat();

 state.authToken = null;
 state.currentRole = null;
 state.currentUser = null;
 localStorage.removeItem('salon_auth_token');
 localStorage.removeItem('salon_user');

 // Đóng các modal nghiệp vụ đang mở
 document.querySelectorAll('.modal-overlay').forEach(m => {
 if (m.id !== 'modal-session-kicked') {
 m.classList.remove('active');
 m.style.display = 'none';
 }
 });

 applyAuthState();

 const kickedModal = document.getElementById('modal-session-kicked');
 const kickedMsg = document.getElementById('session-kicked-msg');
 if (kickedMsg) {
 kickedMsg.innerText = message || 'Tài khoản của bạn vừa được đăng nhập trên một thiết bị khác. Để đảm bảo an toàn, hệ thống chỉ cho phép duy nhất 1 thiết bị đăng nhập đồng thời.';
 }
 if (kickedModal) {
 kickedModal.style.display = 'flex';
 kickedModal.classList.add('active');
 } else {
 showToast(message || '️ Tài khoản đã được đăng nhập ở thiết bị khác!', 'error');
 }

 setTimeout(() => {
 isKickedModalOpen = false;
 }, 1000);
}

function startSessionHeartbeat() {
 stopSessionHeartbeat();
 if (!state.authToken) return;

 // Tần suất thăm dò phiên làm việc để nhận biết bị văng tức thì (mỗi 3.5 giây)
 sessionHeartbeatTimer = setInterval(async () => {
 if (!state.authToken) {
 stopSessionHeartbeat();
 return;
 }
 try {
 const res = await fetch('/api/auth/me', {
 headers: { 'Authorization': `Bearer ${state.authToken}` }
 });
 if (res.status === 401) {
 const data = await res.json();
 if (data && (data.kicked || data.code === 'CONCURRENT_LOGIN')) {
 handleSessionKicked(data.error);
 }
 }
 } catch (e) {
 // Bỏ qua lỗi tạm thời về mạng
 }
 }, 3500);
}

function stopSessionHeartbeat() {
 if (sessionHeartbeatTimer) {
 clearInterval(sessionHeartbeatTimer);
 sessionHeartbeatTimer = null;
 }
}

async function authFetch(url, options = {}) {
 options.headers = options.headers || {};
 if (state.authToken) {
 options.headers['Authorization'] = `Bearer ${state.authToken}`;
 }
 const res = await fetch(url, options);

 if (res.status === 401 && state.authToken) {
 try {
 const clone = res.clone();
 const data = await clone.json();
 if (data && (data.kicked || data.code === 'CONCURRENT_LOGIN')) {
 handleSessionKicked(data.error);
 }
 } catch (e) {
 // not json
 }
 }

 return res;
}

function formatCurrency(amount) {
 if (amount === undefined || amount === null || isNaN(amount)) return '0 đ';
 return Number(amount).toLocaleString('vi-VN') + ' đ';
}

function openModal(modalId) {
 const modal = document.getElementById(modalId);
 if (modal) {
 modal.classList.add('active');
 modal.style.display = 'flex';
 }
}

function closeModal(modalId) {
 const modal = document.getElementById(modalId);
 if (modal) {
 modal.classList.remove('active');
 modal.style.display = 'none';
 }
}

function showToast(message, type = 'info') {
  let toastContainer = document.getElementById('toast-container');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'toast-container';
    toastContainer.style.cssText = 'position: fixed; bottom: 24px; right: 24px; z-index: 99999; display: flex; flex-direction: column; gap: 10px; max-width: 440px; pointer-events: none;';
    document.body.appendChild(toastContainer);
  }
  const toast = document.createElement('div');
  toast.style.pointerEvents = 'auto';
  const bgColors = {
    success: 'linear-gradient(135deg, #1e3a8a, #2563eb)',
    error: 'linear-gradient(135deg, #991b1b, #b91c1c)',
    warning: 'linear-gradient(135deg, #c2410c, #ea580c)',
    info: 'linear-gradient(135deg, #1e3a8a, #2563eb)'
  };
  toast.style.cssText = `background: ${bgColors[type] || bgColors.info}; color: white; padding: 12px 18px; border-radius: 8px; box-shadow: 0 8px 24px rgba(0,0,0,0.3); font-size: 0.88rem; font-weight: 600; display: flex; align-items: center; justify-content: space-between; gap: 12px; animation: slideIn 0.3s ease; border: 1px solid rgba(255,255,255,0.25);`;
  toast.innerHTML = `<span>${message}</span><button onclick="this.parentElement.remove()" style="background:none;border:none;color:white;cursor:pointer;font-size:1.1rem;line-height:1;margin-left:8px;" title="Đóng">✕</button>`;
  toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.4s ease';
    setTimeout(() => toast.remove(), 400);
  }, 3500);
}


// --- FORGOT PASSWORD SYSTEM ---
function openForgotPasswordModal() {
 closeModal('modal-login');
 const modal = document.getElementById('modal-forgot-password');
 if (modal) {
 modal.style.display = 'flex';
 const err = document.getElementById('forgot-error-msg');
 const succ = document.getElementById('forgot-success-msg');
 if (err) err.style.display = 'none';
 if (succ) succ.style.display = 'none';
 const form = document.getElementById('form-forgot-password');
 if (form) form.reset();
 }
}

async function handleForgotPasswordSubmit(e) {
 if (e && e.preventDefault) e.preventDefault();
 const ident = document.getElementById('forgot-identifier').value.trim();
 const newPwd = document.getElementById('forgot-new-password').value.trim();
 const confirmPwd = document.getElementById('forgot-confirm-password').value.trim();
 const errBox = document.getElementById('forgot-error-msg');
 const succBox = document.getElementById('forgot-success-msg');

 if (errBox) errBox.style.display = 'none';
 if (succBox) succBox.style.display = 'none';

 if (!ident) {
 if (errBox) {
 errBox.textContent = 'Vui lòng nhập tên đăng nhập hoặc số điện thoại!';
 errBox.style.display = 'block';
 }
 return;
 }
 if (!newPwd || newPwd.length < 4) {
 if (errBox) {
 errBox.textContent = 'Mật khẩu mới phải có tối thiểu 4 ký tự!';
 errBox.style.display = 'block';
 }
 return;
 }
 if (newPwd !== confirmPwd) {
 if (errBox) {
 errBox.textContent = 'Xác nhận mật khẩu mới không khớp!';
 errBox.style.display = 'block';
 }
 return;
 }

 try {
 const res = await fetch('/api/auth/forgot-password', {
 method: 'POST',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify({ identifier: ident, new_password: newPwd })
 });
 const data = await res.json();
 if (data.success) {
 if (succBox) {
 succBox.textContent = data.message;
 succBox.style.display = 'block';
 }
 showToast(data.message, 'success');
 setTimeout(() => {
 closeModal('modal-forgot-password');
 openLoginModal();
 const u = document.getElementById('login-username');
 if (u && data.username) u.value = data.username;
 const p = document.getElementById('login-password');
 if (p) {
 p.value = newPwd;
 p.focus();
 }
 }, 1500);
 } else {
 if (errBox) {
 errBox.textContent = data.message || 'Không thể đặt lại mật khẩu.';
 errBox.style.display = 'block';
 }
 }
 } catch (err) {
 if (errBox) {
 errBox.textContent = 'Lỗi kết nối máy chủ khi đổi mật khẩu.';
 errBox.style.display = 'block';
 }
 }
}

// --- AUTHENTICATION & LOGIN/LOGOUT SYSTEM ---
function openLoginModal() {
 const modal = document.getElementById('modal-login');
 if (modal) modal.style.display = 'flex';
 const err = document.getElementById('login-error-msg');
 if (err) err.style.display = 'none';
}

function handleLoginFormSubmit(e) {
 if (e && e.preventDefault) e.preventDefault();
 const u = document.getElementById('login-username').value.trim();
 const p = document.getElementById('login-password').value.trim();
 performLogin(u, p);
}

async function quickLogin(username, password) {
 const uInput = document.getElementById('login-username');
 const pInput = document.getElementById('login-password');
 if (uInput) uInput.value = username;
 if (pInput) pInput.value = password;
 await performLogin(username, password);
}

async function performLogin(username, password) {
 const errBox = document.getElementById('login-error-msg');
 if (errBox) errBox.style.display = 'none';

 try {
 const res = await fetch('/api/auth/login', {
 method: 'POST',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify({ username, password })
 });
 const data = await res.json();
 if (data.success && data.token) {
 state.authToken = data.token;
 state.currentRole = data.user.vai_tro;
 state.currentUser = {
 username: data.user.ten_dang_nhap,
 fullName: data.user.ho_ten || data.user.ten_dang_nhap,
 role: data.user.vai_tro,
 ma_nhan_vien: data.user.ma_nhan_vien,
 chuc_vu: data.user.chuc_vu
 };

 localStorage.setItem('salon_auth_token', data.token);
 localStorage.setItem('salon_user', JSON.stringify(data.user));

  closeModal('modal-login');
  showToast(`Đăng nhập thành công: ${state.currentUser.fullName} (${getRoleDisplay(state.currentRole)})`, 'success');
  applyAuthState();
  startSessionHeartbeat();
  if (state.currentRole === 'Admin') {
    switchTab('dashboard');
  } else {
    switchTab('appointments');
  }
  } else {
  if (errBox) {
  errBox.innerText = data.message || 'Sai tên đăng nhập hoặc mật khẩu.';
  errBox.style.display = 'block';
  } else {
  showToast(data.message || 'Đăng nhập không thành công', 'error');
  }
  }
  } catch (err) {
  if (errBox) {
  errBox.innerText = 'Lỗi kết nối máy chủ.';
  errBox.style.display = 'block';
  }
  }
}

function togglePasswordVisibility(inputId, btn) {
  const el = document.getElementById(inputId);
  if (!el) return;
  if (el.type === 'password') {
    el.type = 'text';
    if (btn) btn.innerText = 'Ẩn';
  } else {
    el.type = 'password';
    if (btn) btn.innerText = 'Hiện';
  }
}

async function handleLogout() {
  stopSessionHeartbeat();
  try {
  if (state.authToken) {
  await fetch('/api/auth/logout', {
  method: 'POST',
  headers: {
  'Authorization': `Bearer ${state.authToken}`,
  'Content-Type': 'application/json'
  }
  });
  }
  } catch (e) {
  // ignore
  }

  state.authToken = null;
  state.currentRole = null;
  state.currentUser = null;
  localStorage.removeItem('salon_auth_token');
  localStorage.removeItem('salon_user');
  showToast('Đã đăng xuất. Quay về Trang Chủ Salon.', 'info');
  applyAuthState();
}

function getRoleDisplay(role) {
  if (role === 'Admin') return 'Quản Lý (Admin)';
  if (role === 'LeTan') return 'Lễ Tân';
  if (role === 'Tho') return 'Thợ Làm Tóc';
  return 'Khách Hàng';
}

function applyAuthState() {
 const guestView = document.getElementById('view-guest-home');
 const staffView = document.getElementById('view-staff-app');

 if (!state.currentUser) {
 // GUEST MODE: Show landing page, hide internal app
 if (guestView) guestView.style.display = 'block';
 if (staffView) staffView.style.display = 'none';
 renderGuestServices();
 renderGuestStylists();
 populateGuestBookingForm();
 if (typeof startHeroCarouselAutoPlay === 'function') {
 startHeroCarouselAutoPlay();
 }
 return;
 }

 // STAFF MODE: Hide landing page, show staff app
 if (guestView) guestView.style.display = 'none';
 if (staffView) staffView.style.display = 'block';

 // Update Header user info
 const nameEl = document.getElementById('current-user-name');
 if (nameEl) nameEl.innerText = state.currentUser.fullName;
  const roleBadge = document.getElementById('current-user-role');
  if (roleBadge) {
    roleBadge.innerText = state.currentRole === 'Admin' ? 'Admin' : (state.currentRole === 'LeTan' ? 'Lễ Tân' : 'Thợ Làm Tóc');
    roleBadge.className = 'badge';
    roleBadge.style.cssText = 'margin-left: 6px; background: #ea580c !important; color: #ffffff !important; font-weight: 800; border: none; padding: 3px 10px; font-size: 0.75rem; border-radius: 999px;';
  }

 // Update Quick Switch buttons active state
 document.querySelectorAll('.role-badge-group .role-btn').forEach(btn => {
 btn.classList.toggle('active', btn.dataset.role === state.currentRole);
 });

 // Revenue pill on header: only for Admin
 const revPill = document.getElementById('staff-header-revenue-pill');
 if (revPill) revPill.style.display = (state.currentRole === 'Admin') ? 'flex' : 'none';

 // Header quick buttons
 document.querySelectorAll('.admin-letan-only').forEach(el => {
 el.style.display = (state.currentRole === 'Admin' || state.currentRole === 'LeTan') ? '' : 'none';
 });

 // Sidebar role-based visibility
 const isTho = (state.currentRole === 'Tho');
 const isAdmin = (state.currentRole === 'Admin');
 const isLeTan = (state.currentRole === 'LeTan');

 document.querySelectorAll('.admin-only').forEach(el => {
 el.style.display = isAdmin ? '' : 'none';
 });

 document.querySelectorAll('.admin-letan-only').forEach(el => {
 el.style.display = (isAdmin || isLeTan) ? '' : 'none';
 });

 // Tab text for appointments
 const apptNavText = document.getElementById('nav-text-appointments');
 if (apptNavText) {
 apptNavText.innerText = isTho ? 'Lịch Phục Vụ Của Tôi' : 'Lịch Hẹn & Ghế Làm Tóc';
 }

 const apptHeading = document.getElementById('appointments-tab-heading');
 const apptSubHeading = document.getElementById('appointments-tab-subheading');
 if (apptHeading) {
 apptHeading.innerText = isTho ? 'Lịch Phục Vụ & Ca Làm Của Thợ' : 'Quản Lý Lịch Hẹn & Điều Phối Thợ';
 }
 if (apptSubHeading) {
 apptSubHeading.innerText = isTho ? 'Danh sách khách hàng và ca làm việc được chỉ định cho bạn' : 'Sơ đồ ghế salon thời gian thực & Chống trùng lịch thợ tự động';
 }

 // Tho banner in Tab Appointments
 const thoBanner = document.getElementById('tho-welcome-banner');
 if (thoBanner) {
 thoBanner.style.display = isTho ? 'block' : 'none';
 const bannerName = document.getElementById('tho-banner-name');
 if (bannerName) bannerName.innerText = state.currentUser.fullName;
 updateThoBannerStatusBtn();
 }

 // Filter stylist wrapper
 const stylistFilterWrap = document.getElementById('filter-stylist-wrapper');
 if (stylistFilterWrap) {
 stylistFilterWrap.style.display = isTho ? 'none' : 'flex';
 }

 // Set default active tab
 if (isTho) {
 switchTab('appointments');
 } else if (isLeTan) {
 switchTab('appointments');
 } else {
 switchTab('dashboard');
 }
}

// --- INITIALIZATION ---
document.addEventListener('DOMContentLoaded', () => {
 initApp();
});

async function initApp() {
 // Load base data needed by both guest and staff
 try { await loadStylists(); } catch (e) { console.error("loadStylists err:", e); }
 try { await loadServices(); } catch (e) { console.error("loadServices err:", e); }

 // Check saved session in localStorage
 const savedToken = localStorage.getItem('salon_auth_token');
 const savedUser = localStorage.getItem('salon_user');

 if (savedToken && savedUser) {
 try {
 const parsedUser = JSON.parse(savedUser);
 state.authToken = savedToken;
 state.currentRole = parsedUser.vai_tro;
 state.currentUser = {
 username: parsedUser.ten_dang_nhap,
 fullName: parsedUser.ho_ten || parsedUser.ten_dang_nhap,
 role: parsedUser.vai_tro,
 ma_nhan_vien: parsedUser.ma_nhan_vien,
 chuc_vu: parsedUser.chuc_vu
 };
 } catch (e) {
 state.currentUser = null;
 }
 } else {
 // Default to GUEST (unauthenticated) per user requirement!
 state.currentUser = null;
 state.currentRole = null;
 }

 // Apply UI according to guest vs staff
 applyAuthState();

 // If logged in as staff, load initial data and start session monitoring
 if (state.currentUser) {
 startSessionHeartbeat();
 try { await loadCustomers(); } catch (e) { console.error("loadCustomers err:", e); }
 try { await loadAppointments(); } catch (e) { console.error("loadAppointments err:", e); }
 if (state.currentRole === 'Admin') {
 try { await loadDashboard(); } catch (e) { console.error("loadDashboard err:", e); }
 }
 }

 // Setup default appointment modal datetime
 const tomorrow = new Date();
 tomorrow.setDate(tomorrow.getDate() + 1);
 tomorrow.setHours(10, 0, 0, 0);
 const tzOffset = tomorrow.getTimezoneOffset() * 60000;
 const localISOTime = new Date(tomorrow - tzOffset).toISOString().slice(0, 16);
 const dtInput = document.getElementById('modal-appt-datetime');
 if (dtInput) dtInput.value = localISOTime;
}

// --- TAB SWITCHER ---
function switchTab(tabId) {
 // Enforce role-based tab access
 if (state.currentRole === 'Tho' && !['appointments', 'services'].includes(tabId)) {
 showToast('Thợ làm tóc chỉ có quyền truy cập vào Lịch phục vụ của mình.', 'warning');
 tabId = 'appointments';
 } else if (state.currentRole === 'LeTan' && ['dashboard', 'staff', 'reports', 'accounts'].includes(tabId)) {
 showToast('Lễ tân không có quyền truy cập báo cáo doanh thu hoặc quản trị nhân sự.', 'warning');
 tabId = 'appointments';
 }

 state.activeTab = tabId;

 // Sidebar item styling
 document.querySelectorAll('.nav-item').forEach(item => {
 item.classList.toggle('active', item.dataset.tab === tabId);
 });

 // Tab content visibility
 document.querySelectorAll('.tab-pane').forEach(pane => {
 const isTarget = (pane.id === `tab-${tabId}`);
 pane.classList.toggle('active', isTarget);
 pane.style.display = isTarget ? 'block' : 'none';
 });

 if (tabId === 'dashboard') loadDashboard();
 if (tabId === 'appointments') loadAppointments();
 if (tabId === 'customers') loadCustomers();
 if (tabId === 'services') loadServices();
 if (tabId === 'staff') loadStaff();
 if (tabId === 'accounts') loadAccounts();
 if (tabId === 'billing') { loadBillingQueue(); renderPOSServiceCatalog(); populatePOSCustomerStylistSelects(); }
 if (tabId === 'reports') loadReportsPage();
 if (tabId === 'ai-hub') populateAIHubSelects();
}

// ====================================================================
// 1. DASHBOARD & KPI (UC007)
// ====================================================================
async function loadDashboard() {
 try {
 const res = await authFetch('/api/reports/summary');
 const data = await res.json();
 if (!data.success) return;

 const kpi = data.kpi;
 const el = id => document.getElementById(id);

 // Update Top Header Quick Revenue Pill
 if (el('header-today-rev')) el('header-today-rev').innerText = formatCurrency(kpi.doanh_thu_hom_nay);
 if (el('header-total-rev')) el('header-total-rev').innerText = formatCurrency(kpi.tong_doanh_thu);

 if (el('kpi-today-rev')) el('kpi-today-rev').innerText = formatCurrency(kpi.doanh_thu_hom_nay);
 if (el('kpi-today-orders')) el('kpi-today-orders').innerText = `${kpi.so_don_hom_nay || 0} đơn hoàn thành`;
 if (el('kpi-week-rev')) el('kpi-week-rev').innerText = formatCurrency(kpi.doanh_thu_tuan_nay);
 if (el('kpi-total-rev')) el('kpi-total-rev').innerText = formatCurrency(kpi.tong_doanh_thu);
 if (el('kpi-total-invoices')) el('kpi-total-invoices').innerText = `${kpi.tong_hoa_don || 0} hóa đơn`;
 if (el('kpi-aov')) el('kpi-aov').innerText = formatCurrency(kpi.aov);
 if (el('kpi-today-appts')) el('kpi-today-appts').innerText = kpi.lich_hen_hom_nay;
 if (el('kpi-total-customers')) el('kpi-total-customers').innerText = kpi.tong_khach;

 // 1. Daily Revenue Bar Chart
 const barContainer = el('revenue-chart-bars');
 if (barContainer && data.revenue_by_day) {
 if (data.revenue_by_day.length === 0) {
 barContainer.innerHTML = `<div style="text-align:center;width:100%;color:var(--text-muted);align-self:center;">Chưa có dữ liệu doanh thu</div>`;
 } else {
 const maxVal = Math.max(...data.revenue_by_day.map(d => d.DoanhThu), 1);
 barContainer.innerHTML = data.revenue_by_day.map(d => {
 const heightPct = Math.max(12, Math.round((d.DoanhThu / maxVal) * 100));
 const dateLabel = d.Ngay ? d.Ngay.slice(5) : ''; // MM-DD
 return `
 <div style="flex: 1; display: flex; flex-direction: column; align-items: center; height: 100%; justify-content: flex-end; position: relative;">
 <div style="font-size: 0.7rem; color: var(--gold-light); font-weight: 600; margin-bottom: 4px; white-space: nowrap;">
 ${d.DoanhThu >= 1000000 ? (d.DoanhThu / 1000000).toFixed(1) + 'Tr' : (d.DoanhThu / 1000).toFixed(0) + 'k'}
 </div>
 <div style="width: 100%; max-width: 42px; height: ${heightPct}%; background: linear-gradient(180deg, var(--gold-light) 0%, rgba(212,175,55,0.2) 100%); border-top: 2px solid var(--gold-primary); border-radius: 4px 4px 0 0; transition: height 0.5s ease;" title="${d.Ngay}: ${formatCurrency(d.DoanhThu)} (${d.SoDon} đơn)"></div>
 <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 6px;">${dateLabel}</div>
 </div>
 `;
 }).join('');
 }
 }

 // 2. Payment Methods Breakdown
 const pmContainer = el('payment-methods-container');
 if (pmContainer && data.revenue_by_method) {
 if (data.revenue_by_method.length === 0) {
 pmContainer.innerHTML = `<div style="color:var(--text-muted);text-align:center;">Chưa có giao dịch</div>`;
 } else {
 const icons = {
 'Tiền mặt': { icon: '', color: '#10b981' },
 'Chuyển khoản': { icon: '', color: '#38bdf8' },
 'Thẻ': { icon: '', color: '#a855f7' }
 };
 pmContainer.innerHTML = data.revenue_by_method.map(m => {
 const cfg = icons[m.phuong_thuc] || { icon: '', color: '#d4af37' };
 return `
 <div>
 <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 4px;">
 <span>${cfg.icon} <strong>${m.phuong_thuc}</strong> (${m.so_don} đơn)</span>
 <span style="font-weight: 600; color: ${cfg.color};">${formatCurrency(m.doanh_thu)} (${m.phan_tram}%)</span>
 </div>
 <div style="background: #e2e8f0; border-radius: 4px; height: 7px; overflow: hidden;">
 <div style="background: ${cfg.color}; width: ${m.phan_tram}%; height: 100%; border-radius: 4px; transition: width 0.6s ease;"></div>
 </div>
 </div>
 `;
 }).join('');
 }
 }

 // 3. Top Services Table
 const topSvcTbody = el('top-services-tbody');
 if (topSvcTbody) {
 if (!data.top_services || data.top_services.length === 0) {
 topSvcTbody.innerHTML = `<tr><td colspan="3" style="text-align:center;color:var(--text-muted);">Chưa có dữ liệu</td></tr>`;
 } else {
 topSvcTbody.innerHTML = data.top_services.map(s => `
 <tr>
 <td><strong style="color:var(--text-primary);">${s.TenDichVu}</strong></td>
 <td><span class="badge badge-info">${s.SoLuotDat} lượt</span></td>
 <td style="color:var(--gold-light);">${formatCurrency(s.TongDoanhSo)}</td>
 </tr>
 `).join('');
 }
 }

 // 4. Stylist Revenue Performance Leaderboard
 const stylistTbody = el('stylist-leaderboard-tbody');
 if (stylistTbody) {
 if (!data.stylist_leaderboard || data.stylist_leaderboard.length === 0) {
 stylistTbody.innerHTML = `<tr><td colspan="4" style="text-align:center;color:var(--text-muted);">Chưa có dữ liệu thợ</td></tr>`;
 } else {
 stylistTbody.innerHTML = data.stylist_leaderboard.map(st => `
 <tr>
 <td><strong style="color:var(--text-primary);">${st.TenTho}</strong></td>
 <td><span class="badge badge-primary">${st.ChucVu}</span></td>
 <td><span class="badge badge-secondary">${st.SoLuotPhucVu} khách</span></td>
 <td><strong style="color:var(--accent-emerald);">${formatCurrency(st.TongDoanhThuMangVe)}</strong></td>
 </tr>
 `).join('');
 }
 }

 } catch (err) {
 console.error("Dashboard error:", err);
 }
}

// ====================================================================
// 2. STYLISTS & EMPLOYEES (UC003)
// ====================================================================
async function loadStylists() {
 try {
 const res = await fetch('/api/stylists');
 const data = await res.json();
 if (data.success) {
 state.stylists = data.stylists;
 renderStylistsSidebar();
 populateStylistSelects();
 }
 } catch (err) {
 console.error("Error loading stylists:", err);
 }
}

function renderStylistsSidebar() {
 const container = document.getElementById('stylist-sidebar-list');
 if (!container) return;

 container.innerHTML = state.stylists.map(s => `
 <div style="display: flex; align-items: center; justify-content: space-between; font-size: 0.85rem;">
 <div>
 <div style="font-weight: 500;">${s.HoTen}</div>
 <div style="font-size: 0.75rem; color: var(--text-muted);">${s.ChucVu}</div>
 </div>
 <span class="badge ${s.TrangThaiRanh ? 'badge-success' : 'badge-danger'}">
 ${s.TrangThaiRanh ? '● Rảnh' : '● Đang bận'}
 </span>
 </div>
 `).join('');
}

function populateStylistSelects() {
 const filterSelect = document.getElementById('filter-stylist');
 const modalSelect = document.getElementById('modal-appt-stylist');

 const optionsHtml = state.stylists.map(s => `
 <option value="${s.MaNhanVien}">${s.HoTen} (${s.ChucVu}) - [${s.TrangThaiRanh ? 'Rảnh' : 'Bận'}]</option>
 `).join('');

 if (filterSelect) {
 filterSelect.innerHTML = `<option value="">Tất cả nhân sự</option>` + optionsHtml;
 }
 if (modalSelect) {
 modalSelect.innerHTML = optionsHtml;
 }
}

// ====================================================================
// 3. APPOINTMENTS (UC005 & Screen Flow Luồng 2)
// ====================================================================
// 3. APPOINTMENTS (UC005 & Screen Flow Luồng 2)
// ====================================================================
function onDateFilterChanged() {
 const dateSelect = document.getElementById('filter-date');
 const customDateInput = document.getElementById('filter-custom-date');
 if (dateSelect && customDateInput) {
 if (dateSelect.value === 'custom') {
 customDateInput.style.display = 'inline-block';
 customDateInput.focus();
 } else {
 customDateInput.style.display = 'none';
 loadAppointments();
 }
 }
}

function updateThoBannerStatusBtn() {
 const btn = document.getElementById('btn-tho-toggle-status');
 if (!btn || !state.currentUser) return;
 const currentSt = state.stylists.find(s => s.MaNhanVien === state.currentUser.ma_nhan_vien);
 const isFree = currentSt ? currentSt.TrangThaiRanh : 1;
 btn.innerText = isFree ? '● Đang Rảnh' : '● Đang Bận';
 btn.className = `btn btn-sm ${isFree ? 'btn-emerald' : 'btn-secondary'}`;
}

async function toggleCurrentStylistAvailability() {
 if (!state.currentUser || !state.currentUser.ma_nhan_vien) return;
 const currentSt = state.stylists.find(s => s.MaNhanVien === state.currentUser.ma_nhan_vien);
 const currentStatus = currentSt ? currentSt.TrangThaiRanh : 1;
 await toggleStylistStatusDirectly(state.currentUser.ma_nhan_vien, currentStatus);
 updateThoBannerStatusBtn();
}

async function loadAppointments() {
 try {
 const status = document.getElementById('filter-status') ? document.getElementById('filter-status').value : '';
 let stylistId = document.getElementById('filter-stylist') ? document.getElementById('filter-stylist').value : '';

 // Date filter
 const dateSelect = document.getElementById('filter-date');
 let dateStr = '';
 if (dateSelect) {
 if (dateSelect.value === 'custom') {
 const customDateInput = document.getElementById('filter-custom-date');
 dateStr = customDateInput ? customDateInput.value : '';
 } else {
 dateStr = dateSelect.value;
 }
 }

 // If logged in as Tho, strictly restrict to their own ma_nhan_vien
 if (state.currentRole === 'Tho' && state.currentUser && state.currentUser.ma_nhan_vien) {
 stylistId = state.currentUser.ma_nhan_vien;
 }

 let url = '/api/appointments?';
 if (dateStr) url += `date=${encodeURIComponent(dateStr)}&`;
 if (status) url += `status=${encodeURIComponent(status)}&`;
 if (stylistId) url += `stylist_id=${encodeURIComponent(stylistId)}&`;

 const res = await authFetch(url);
 const data = await res.json();
 if (!data.success) return;

 state.appointments = data.appointments;
 
 // Always render both view modes so toggle between list and timeline is seamless
 renderAppointments();
 renderTimelineScheduler();
 } catch (err) {
 console.error("Error loading appointments:", err);
 }
}

function formatApptTimeDisplay(ngayGioStr, durationMin = 0) {
 if (!ngayGioStr) return { timeRange: '--:--', date: '', fullDate: '', startTime: '' };
 try {
 const parts = ngayGioStr.replace('T', ' ').split(' ');
 const datePart = parts[0] || '';
 const timePart = parts[1] ? parts[1].substring(0, 5) : '00:00';
 
 let formattedDate = datePart;
 let fullDate = datePart;
 if (datePart.includes('-')) {
 const [y, m, d] = datePart.split('-');
 formattedDate = `${d}/${m}`;
 fullDate = `${d}/${m}/${y}`;
 }
 
 const [startH, startM] = timePart.split(':').map(Number);
 const totalStartM = (isNaN(startH) ? 0 : startH) * 60 + (isNaN(startM) ? 0 : startM);
 const totalEndM = totalStartM + (Number(durationMin) || 0);
 const endH = String(Math.floor(totalEndM / 60) % 24).padStart(2, '0');
 const endM = String(totalEndM % 60).padStart(2, '0');
 
 return {
 timeRange: `${timePart} - ${endH}:${endM}`,
 date: formattedDate,
 fullDate: fullDate,
 startTime: timePart,
 endTime: `${endH}:${endM}`
 };
 } catch (e) {
 return { timeRange: ngayGioStr, date: '', fullDate: '', startTime: '' };
 }
}

function getApptCardClass(status) {
 switch (status) {
 case 'Đang phục vụ': return 'status-dang-phuc-vu';
 case 'Chờ xác nhận': return 'status-cho-xac-nhan';
 case 'Đã xác nhận': return 'status-da-xac-nhan';
 case 'Hoàn thành': return 'status-hoan-thanh';
 case 'Đã hủy': return 'status-da-huy';
 default: return '';
 }
}

function onApptSearchChanged() {
 const searchInput = document.getElementById('filter-appt-search');
 state.apptSearchQuery = searchInput ? searchInput.value.toLowerCase().trim() : '';
 renderAppointments();
}

function renderAppointments() {
 const container = document.getElementById('appointments-container');
 if (!container) return;

 let displayAppointments = state.appointments || [];
 if (state.apptSearchQuery) {
 const q = state.apptSearchQuery;
 displayAppointments = displayAppointments.filter(appt => {
 const name = (appt.TenKhachHang || '').toLowerCase();
 const phone = (appt.SoDienThoai || '').toLowerCase();
 const code = (appt.MaLichHen || '').toLowerCase();
 const tho = (appt.TenThợ || '').toLowerCase();
 const hair = (appt.GhiChuToc || '').toLowerCase();
 const note = (appt.GhiChu || '').toLowerCase();
 const svcs = (appt.danh_sach_dich_vu || []).map(s => s.TenDichVu || '').join(' ').toLowerCase();
 return name.includes(q) || phone.includes(q) || code.includes(q) || tho.includes(q) || hair.includes(q) || note.includes(q) || svcs.includes(q);
 });
 }

 // Sắp xếp linh hoạt theo bộ lọc chọn (Giờ sớm/muộn, Giá tiền, Trạng thái)
 const sortMode = document.getElementById('filter-sort') ? document.getElementById('filter-sort').value : 'time-asc';
 displayAppointments = [...displayAppointments].sort((a, b) => {
 if (sortMode === 'time-asc') {
 return (a.NgayGioHen || '').localeCompare(b.NgayGioHen || '');
 } else if (sortMode === 'time-desc') {
 return (b.NgayGioHen || '').localeCompare(a.NgayGioHen || '');
 } else if (sortMode === 'price-desc') {
 return (Number(b.tong_chi_phi) || 0) - (Number(a.tong_chi_phi) || 0);
 } else if (sortMode === 'price-asc') {
 return (Number(a.tong_chi_phi) || 0) - (Number(b.tong_chi_phi) || 0);
 } else if (sortMode === 'status') {
 const priority = { 'Đang phục vụ': 1, 'Chờ xác nhận': 2, 'Đã xác nhận': 3, 'Hoàn thành': 4, 'Đã hủy': 5 };
 const pA = priority[a.TrangThai] || 99;
 const pB = priority[b.TrangThai] || 99;
 if (pA !== pB) return pA - pB;
 return (a.NgayGioHen || '').localeCompare(b.NgayGioHen || '');
 }
 return 0;
 });

 if (displayAppointments.length === 0) {
 container.innerHTML = `
 <div style="grid-column: 1/-1; text-align: center; padding: 3rem; color: var(--text-muted);" class="glass">
 ${state.apptSearchQuery ? `Không tìm thấy thẻ lịch hẹn nào khớp với từ khóa "<strong>${escapeHTML(state.apptSearchQuery)}</strong>".` : 'Không có lịch hẹn nào phù hợp với bộ lọc ngày & trạng thái.'}
 </div>
 `;
 return;
 }

 const isTho = (state.currentRole === 'Tho');
 const isAdminOrLeTan = (state.currentRole === 'Admin' || state.currentRole === 'LeTan');

 container.innerHTML = displayAppointments.map(appt => {
 const statusBadge = getStatusBadge(appt.TrangThai);
 const statusClass = getApptCardClass(appt.TrangThai);
 const timeInfo = formatApptTimeDisplay(appt.NgayGioHen, appt.tong_thoi_gian);

 const servicesList = (appt.danh_sach_dich_vu || []).map(s => `
 <span class="service-chip" title="${formatCurrency(s.GiaTaiThoiDiemDat)}">
 ${s.TenDichVu} <span style="color: var(--text-muted); font-size: 0.72rem;">(${s.ThoiGianThucHien}p • ${formatCurrency(s.GiaTaiThoiDiemDat)})</span>
 </span>
 `).join('');

 let actionsHtml = '';
 if (isTho) {
 // THỢ CHÍNH: Cập nhật trạng thái làm tóc & xem tóm tắt AI
 if (appt.TrangThai === 'Đã xác nhận') {
 actionsHtml += `<button class="btn btn-emerald btn-sm" onclick="changeApptStatus('${appt.MaLichHen}', 'Đang phục vụ')">▶ Bắt đầu làm</button>`;
 } else if (appt.TrangThai === 'Đang phục vụ') {
 actionsHtml += `<button class="btn btn-primary btn-sm" onclick="changeApptStatus('${appt.MaLichHen}', 'Hoàn thành')"> Hoàn thành</button>`;
 }
 actionsHtml += `<button class="btn btn-ai btn-sm" onclick="quickAISummary('${appt.MaKhachHang}')"> AI Tóm Tắt 5s</button>`;
 if (appt.MaKhachHang) {
 actionsHtml += `<button class="btn btn-secondary btn-sm" onclick="viewCustomerHistory('${appt.MaKhachHang}')" title="Xem lịch sử khách"> Lịch sử</button>`;
 }
 } else {
 // ADMIN & LỄ TÂN: Toàn quyền điều phối, xác nhận, đổi giờ, hủy và thu ngân POS
 if (appt.TrangThai === 'Chờ xác nhận') {
 actionsHtml += `<button class="btn btn-info btn-sm" onclick="changeApptStatus('${appt.MaLichHen}', 'Đã xác nhận')"> Xác Nhận</button>`;
 actionsHtml += `<button class="btn btn-secondary btn-sm" onclick="openRescheduleModal('${appt.MaLichHen}')">️ Đổi Giờ</button>`;
 } else if (appt.TrangThai === 'Đã xác nhận') {
 actionsHtml += `<button class="btn btn-emerald btn-sm" onclick="changeApptStatus('${appt.MaLichHen}', 'Đang phục vụ')">▶ Bắt đầu làm</button>`;
 actionsHtml += `<button class="btn btn-secondary btn-sm" onclick="openRescheduleModal('${appt.MaLichHen}')">️ Đổi Giờ</button>`;
 } else if (appt.TrangThai === 'Đang phục vụ') {
 actionsHtml += `<button class="btn btn-primary btn-sm" onclick="startCheckout('${appt.MaLichHen}')"> Thu Tiền (POS)</button>`;
 }

 actionsHtml += `<button class="btn btn-ai btn-sm" title="AI Sinh tin nhắn nhắc lịch" onclick="quickAIReminder('${appt.MaLichHen}')"> Nhắc lịch</button>`;
 actionsHtml += `<button class="btn btn-ai btn-sm" title="AI Tóm tắt hồ sơ khách" onclick="quickAISummary('${appt.MaKhachHang}')"> AI Tóm Tắt</button>`;

 if (appt.MaKhachHang) {
 actionsHtml += `<button class="btn btn-secondary btn-sm" onclick="viewCustomerHistory('${appt.MaKhachHang}')" title="Xem chi tiết lịch sử khách"> Lịch sử</button>`;
 }

 if (appt.TrangThai !== 'Hoàn thành' && appt.TrangThai !== 'Đã hủy') {
 actionsHtml += `<button class="btn btn-secondary btn-sm" title="Hủy lịch hẹn" onclick="changeApptStatus('${appt.MaLichHen}', 'Đã hủy')"></button>`;
 }
 }

 return `
 <div class="appt-card glass ${statusClass}" id="card-appt-${appt.MaLichHen}">
 <div class="appt-header">
 <div class="appt-time">
 <span style="font-family: monospace; font-size: 0.8rem; background: rgba(216, 86, 39, 0.15); border: 1px solid rgba(216, 86, 39, 0.4); color: #ff854d; padding: 2px 6px; border-radius: 4px; font-weight: 800;">
 #${appt.MaLichHen}
 </span>
 <span style="display: flex; align-items: center; gap: 4px; font-size: 0.95rem; font-weight: 700; color: var(--text-primary);">
 ${timeInfo.timeRange}
 </span>
 <span style="font-size: 0.75rem; color: var(--text-muted); font-weight: normal;">
 (${timeInfo.fullDate || timeInfo.date})
 </span>
 </div>
 ${statusBadge}
 </div>

 <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 0.5rem;">
 <div>
 <div class="appt-customer" style="display: flex; align-items: center; gap: 6px;">
 <span>${appt.TenKhachHang}</span>
 </div>
 <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 2px;">
 ${appt.SoDienThoai ? ` <strong style="color: var(--text-secondary);">${appt.SoDienThoai}</strong>` : ' <em>Khách vãng lai</em>'}
 </div>
 </div>
 <div style="text-align: right;">
 <div style="font-size: 0.75rem; color: var(--text-muted);">Stylist phụ trách:</div>
 <strong style="font-size: 0.9rem; color: var(--gold-light);">️ ${appt.TenThợ}</strong>
 <div style="font-size: 0.72rem; color: var(--text-muted);">${appt.ChucVu || 'Stylist'}</div>
 </div>
 </div>

 ${appt.GhiChuToc ? `
 <div style="font-size: 0.78rem; background: rgba(216, 86, 39, 0.12); border: 1px solid rgba(216, 86, 39, 0.35); border-radius: 6px; padding: 5px 9px; color: #ff854d; display: flex; align-items: flex-start; gap: 5px;">
 <span></span>
 <div><strong>Chất tóc & Cảnh báo:</strong> ${appt.GhiChuToc}</div>
 </div>
 ` : ''}

 <div class="service-chip-list">
 ${servicesList || '<span style="font-size: 0.75rem; color: var(--text-muted);">Chưa chọn dịch vụ</span>'}
 </div>

 ${appt.GhiChu ? `
 <div style="font-size: 0.82rem; color: #334155; background: #fffaf5; padding: 6px 10px; border-radius: 6px; border: 1px dashed var(--border-color); font-weight: 500;">
 <strong>Ghi chú:</strong> "${appt.GhiChu}"
 </div>
 ` : ''}

 ${appt.MaHoaDon ? `
 <div style="font-size: 0.78rem; color: #34d399; background: rgba(52, 211, 153, 0.12); border: 1px solid rgba(52, 211, 153, 0.3); border-radius: 6px; padding: 4px 8px; display: flex; justify-content: space-between; align-items: center; gap: 6px;">
 <span style="display: flex; align-items: center; gap: 6px;">
 <span> <strong>Đã thanh toán:</strong> #${appt.MaHoaDon}</span>
 <button class="btn btn-secondary btn-sm" style="padding: 1px 6px; font-size: 0.7rem; height: auto;" onclick="openReceiptModal('${appt.MaHoaDon}')" title="In lại phiếu hóa đơn">️ In Phiếu</button>
 </span>
 <span style="font-weight: 700;">${formatCurrency(appt.ThanhTien || appt.tong_chi_phi)}</span>
 </div>
 ` : ''}

 <div style="border-top: 1px solid var(--border-subtle); padding-top: 0.75rem; display: flex; justify-content: space-between; align-items: center; margin-top: auto; gap: 8px; flex-wrap: wrap;">
 <div>
 <div style="font-size: 0.95rem; color: var(--gold-primary); font-weight: 700;">
 ${formatCurrency(appt.tong_chi_phi || 0)}
 </div>
 <div style="font-size: 0.72rem; color: var(--text-muted);">
 ️ Dự kiến: ${appt.tong_thoi_gian || 0} phút
 </div>
 </div>

 <div style="display: flex; gap: 5px; flex-wrap: wrap; justify-content: flex-end;">
 ${actionsHtml}
 </div>
 </div>
 </div>
 `;
 }).join('');
}

function getStatusBadge(status) {
 switch (status) {
 case 'Chờ xác nhận': return `<span class="badge badge-warning"> Chờ xác nhận</span>`;
 case 'Đã xác nhận': return `<span class="badge badge-info"> Đã xác nhận</span>`;
 case 'Đang phục vụ': return `<span class="badge badge-primary">️ Đang phục vụ</span>`;
 case 'Hoàn thành': return `<span class="badge badge-success"> Hoàn thành</span>`;
 case 'Đã hủy': return `<span class="badge badge-danger"> Đã hủy</span>`;
 default: return `<span class="badge badge-secondary">${status}</span>`;
 }
}

async function changeApptStatus(apptId, newStatus) {
 try {
 const res = await authFetch(`/api/appointments/${apptId}/status`, {
 method: 'PUT',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify({ trang_thai: newStatus })
 });
 const data = await res.json();
 if (data.success) {
 showToast(data.message, 'success');
 loadAppointments();
 loadStylists();
 if (state.currentRole === 'Admin') loadDashboard();
 } else {
 showToast(data.message, 'error');
 }
 } catch (err) {
 showToast('Lỗi cập nhật trạng thái', 'error');
 }
}

// ====================================================================
// GUEST LANDING PAGE HELPERS & ACTIONS (SALON HAIR HÀ MINH)
// ====================================================================

// --- HERO CAROUSEL CONTROLS ---
let currentHeroSlide = 0;
let heroSlideTimer = null;

function setHeroSlide(index) {
 const slides = document.querySelectorAll('.hero-slide');
 const dots = document.querySelectorAll('.hero-dots .dot');
 if (!slides || slides.length === 0) return;
 
 slides.forEach((s, idx) => {
 s.classList.toggle('active', idx === index);
 });
 dots.forEach((d, idx) => {
 d.classList.toggle('active', idx === index);
 });
 currentHeroSlide = index;
}

function nextHeroSlide() {
 const slides = document.querySelectorAll('.hero-slide');
 if (!slides || slides.length === 0) return;
 const nextIdx = (currentHeroSlide + 1) % slides.length;
 setHeroSlide(nextIdx);
}

function prevHeroSlide() {
 const slides = document.querySelectorAll('.hero-slide');
 if (!slides || slides.length === 0) return;
 const prevIdx = (currentHeroSlide - 1 + slides.length) % slides.length;
 setHeroSlide(prevIdx);
}

function startHeroCarouselAutoPlay() {
 if (heroSlideTimer) clearInterval(heroSlideTimer);
 heroSlideTimer = setInterval(() => {
 nextHeroSlide();
 }, 6500);
}

// --- QUICK TIME SLOT SELECTOR ---
function setQuickTimeSlot(timeStr) {
 const dtInput = document.getElementById('guest-book-datetime');
 if (!dtInput) return;
 
 const today = new Date();
 const yyyy = today.getFullYear();
 const mm = String(today.getMonth() + 1).padStart(2, '0');
 const dd = String(today.getDate()).padStart(2, '0');
 dtInput.value = `${yyyy}-${mm}-${dd}T${timeStr}`;

 document.querySelectorAll('.time-chip').forEach(c => {
 c.classList.toggle('active', c.textContent.trim() === timeStr);
 });
}

function scrollToGuestServicesSearch() {
 const sSection = document.getElementById('guest-services-section');
 if (sSection) {
 sSection.scrollIntoView({ behavior: 'smooth' });
 setTimeout(() => {
 const sInput = document.getElementById('guest-book-service-search');
 if (sInput) sInput.focus();
 }, 400);
 }
}

// --- LOOKUP APPOINTMENT BY PHONE ---
async function handleGuestLookupAppointment() {
 const phone = document.getElementById('guest-lookup-phone')?.value.trim();
 const resBox = document.getElementById('guest-lookup-result');
 if (!resBox) return;

 if (!phone) {
 resBox.style.display = 'block';
 resBox.innerHTML = `<div style="background: rgba(225,29,72,0.15); border: 1px solid #e11d48; color: #fca5a5; padding: 0.85rem; border-radius: 8px; text-align: center;">Vui lòng nhập số điện thoại để tra cứu lịch hẹn.</div>`;
 return;
 }

 resBox.style.display = 'block';
 resBox.innerHTML = `<div style="color: var(--barber-text-muted); text-align: center; padding: 1rem;">Đang tra cứu hệ thống dữ liệu...</div>`;

 try {
 const res = await fetch(`/api/appointments?q=${encodeURIComponent(phone)}`);
 const data = await res.json();
 const appts = Array.isArray(data) ? data : (data.appointments || data.data || []);
 const userAppts = appts.filter(a => {
 const p = a.SoDienThoai || a.so_dien_thoai || a.KhachHangSoDienThoai || '';
 return p.includes(phone);
 });

 if (userAppts.length === 0) {
 resBox.innerHTML = `<div style="background: rgba(245, 158, 11, 0.15); border: 1px solid #f59e0b; color: #fcd34d; padding: 1rem; border-radius: 8px; text-align: center;">Không tìm thấy lịch hẹn nào với số điện thoại <strong>${phone}</strong>. Quý khách có thể đặt lịch hẹn ngay bên trên!</div>`;
 return;
 }

 resBox.innerHTML = userAppts.map(a => {
 const statusColors = {
 'DaXacNhan': '#10b981',
 'ChoXacNhan': '#f59e0b',
 'HoanThanh': '#3b82f6',
 'Huy': '#ef4444'
 };
 const statusLabels = {
 'DaXacNhan': 'Đã Xác Nhận',
 'ChoXacNhan': 'Chờ Xác Nhận',
 'HoanThanh': 'Đã Hoàn Thành',
 'Huy': 'Đã Hủy'
 };
 const st = a.TrangThai || a.trang_thai || 'ChoXacNhan';
 const col = statusColors[st] || '#f59e0b';
 const lbl = statusLabels[st] || st;

 return `
 <div style="background: #ffffff; border: 1.5px solid var(--border-color); border-left: 5px solid ${col}; border-radius: 12px; padding: 1.25rem; margin-bottom: 1rem; box-shadow: 0 4px 15px rgba(67, 20, 7, 0.06);">
 <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.65rem;">
 <strong style="color: #0f172a; font-size: 1.1rem;">Mã hẹn: #${a.MaLichHen || a.ma_lich_hen}</strong>
 <span style="background: ${col}18; color: ${col}; border: 1.5px solid ${col}; padding: 4px 12px; border-radius: 9999px; font-size: 0.82rem; font-weight: 700;">${lbl}</span>
 </div>
 <div style="font-size: 0.92rem; color: #334155; line-height: 1.7; font-weight: 500;">
 <div> Thời gian hẹn: <strong style="color: #0f172a;">${a.NgayHen || a.ngay_hen} Lúc ${a.GioHen || a.gio_hen}</strong></div>
 <div>️ Stylist phụ trách: <strong style="color: #ea580c;">${a.TenTho || a.ten_tho || 'Sắp xếp tự động'}</strong></div>
 <div> Dịch vụ: <span style="color: #0f172a; font-weight: 600;">${a.TenDichVu || a.ten_dich_vu || 'Dịch vụ Salon Hair Hà Minh'}</span></div>
 </div>
 </div>
 `;
 }).join('');
 } catch (err) {
 resBox.innerHTML = `<div style="background: rgba(225,29,72,0.15); border: 1px solid #e11d48; color: #fca5a5; padding: 0.85rem; border-radius: 8px; text-align: center;">Đã xảy ra lỗi khi tra cứu: ${err.message}</div>`;
 }
}

function scrollToGuestBooking(serviceId = null) {
 const bookingEl = document.getElementById('guest-booking-section');
 if (bookingEl) {
 bookingEl.scrollIntoView({ behavior: 'smooth' });
 }
 if (serviceId) {
 const cb = document.querySelector(`input[name="guest_service_check"][value="${serviceId}"]`);
 if (cb) {
 cb.checked = true;
 recalculateGuestEstimate();
 }
 }
}

function filterGuestServices(category = '', btn = null) {
 if (btn) {
 document.querySelectorAll('#guest-services-section .pos-cat-btn').forEach(b => b.classList.remove('active'));
 btn.classList.add('active');
 }
 renderGuestServices(category);
}

function renderGuestServices(category = '') {
 const container = document.getElementById('guest-services-catalog-grid');
 if (!container) return;

 const filtered = category
 ? state.services.filter(s => (s.TenDichVu || s.ten_dich_vu || '').toLowerCase().includes(category.toLowerCase()) || (s.MoTa || s.mo_ta || '').toLowerCase().includes(category.toLowerCase()))
 : state.services;

 if (filtered.length === 0) {
 container.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--barber-text-muted); padding: 3rem;">Không tìm thấy dịch vụ nào trong danh mục này.</div>`;
 return;
 }

 container.innerHTML = filtered.map(s => {
 const sid = s.MaDichVu || s.ma_dich_vu;
 const sname = s.TenDichVu || s.ten_dich_vu;
 const sprice = s.GiaTien || s.gia_tien || 0;
 const sdur = s.ThoiGianThucHien || s.thoi_gian_thuc_hien || 45;
 const sdesc = s.MoTa || s.mo_ta || 'Dịch vụ chăm sóc & tạo mẫu tóc chuẩn phong cách Salon Hair Hà Minh.';

 return `
 <div class="guest-service-card" style="background: #ffffff !important; border: 1.5px solid #fed7aa !important; border-radius: 16px; padding: 1.65rem; box-shadow: 0 4px 15px rgba(67, 20, 7, 0.06); display: flex; flex-direction: column; transition: transform 0.25s ease, box-shadow 0.25s ease;">
 <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem; gap: 8px;">
 <h3 style="font-size: 1.18rem; font-weight: 800; color: #0f172a !important; margin: 0; line-height: 1.3;">${sname}</h3>
 <span style="font-size: 0.76rem; background: #fff7ed; color: #ea580c; border: 1.5px solid #fed7aa; padding: 3px 9px; border-radius: 9999px; font-weight: 700; white-space: nowrap;">️ ${sdur} phút</span>
 </div>
 <p style="font-size: 0.88rem; color: #475569 !important; line-height: 1.6; margin-bottom: 1.25rem; flex: 1; font-weight: 500;">
 ${sdesc}
 </p>
 <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1.5px solid #fed7aa; padding-top: 0.85rem; margin-top: auto;">
 <div style="font-size: 1.35rem; font-weight: 900; color: #ea580c !important; letter-spacing: -0.3px;">${formatCurrency(sprice)}</div>
 <button type="button" class="btn btn-primary btn-sm" style="background: linear-gradient(135deg, #ea580c 0%, #f59e0b 100%) !important; color: #ffffff !important; border: none !important; font-weight: 700; border-radius: 8px; padding: 0.6rem 1.25rem; cursor: pointer; box-shadow: 0 4px 12px rgba(234, 88, 12, 0.35);" onclick="scrollToGuestBooking('${sid}')">
 Đặt Dịch Vụ
 </button>
 </div>
 </div>
 `;
 }).join('');
}

function renderGuestStylists() {
 const container = document.getElementById('guest-stylists-grid');
 if (!container) return;

 const stylists = state.stylists.filter(s => s.ChucVu.includes('Thợ') || s.ChucVu.includes('Stylist') || s.ChucVu.includes('Barber'));
 const list = stylists.length > 0 ? stylists : state.stylists;

 container.innerHTML = list.map((s, idx) => {
 const emojis = ['️', '', '‍️', '', '', ''];
 const emoji = emojis[idx % emojis.length];

 return `
 <div class="guest-stylist-card" style="background: #ffffff !important; border: 1.5px solid #fed7aa !important; border-radius: 16px; padding: 2rem 1.5rem; text-align: center; box-shadow: 0 4px 15px rgba(67, 20, 7, 0.06); display: flex; flex-direction: column; align-items: center; gap: 0.85rem; transition: transform 0.25s ease, box-shadow 0.25s ease;">
 <div class="guest-stylist-avatar" style="width: 86px; height: 86px; border-radius: 50%; background: linear-gradient(135deg, #ea580c, #f59e0b); display: flex; align-items: center; justify-content: center; font-size: 2.4rem; box-shadow: 0 6px 20px rgba(234, 88, 12, 0.25); border: 3px solid #ffffff;">${emoji}</div>
 <div>
 <div style="font-size: 1.25rem; font-weight: 800; color: #0f172a !important; margin: 0;">${s.HoTen}</div>
 <div style="font-size: 0.88rem; color: #ea580c !important; font-weight: 700; margin-top: 4px;">${s.ChucVu}</div>
 </div>
 <span class="badge ${s.TrangThaiRanh ? 'badge-success' : 'badge-danger'}" style="margin: 4px 0; font-size: 0.78rem; font-weight: 600; padding: 4px 10px; border-radius: 9999px;">
 ${s.TrangThaiRanh ? '● Sẵn sàng phục vụ' : '● Đang trong ca làm'}
 </span>
 <button type="button" class="btn btn-secondary btn-sm" style="width: 100%; margin-top: 8px; background: #fff1e6 !important; border: 1.5px solid #ea580c !important; color: #c2410c !important; font-weight: 700; border-radius: 8px; padding: 0.65rem 1rem; cursor: pointer; transition: all 0.2s ease;" onclick="selectGuestStylistAndBook('${s.MaNhanVien}')">
 Chọn Stylist Này
 </button>
 </div>
 `;
 }).join('');
}

function selectGuestStylistAndBook(stylistId) {
 const sel = document.getElementById('guest-book-stylist');
 if (sel) sel.value = stylistId;
 scrollToGuestBooking();
}

function populateGuestBookingForm() {
 // Populate Stylists
 const stylistSelect = document.getElementById('guest-book-stylist');
 if (stylistSelect) {
 const list = state.stylists.filter(s => s.ChucVu.includes('Thợ') || s.ChucVu.includes('Stylist') || s.ChucVu.includes('Barber'));
 const opts = list.map(s => `
 <option value="${s.MaNhanVien}">${s.HoTen} (${s.ChucVu}) - [${s.TrangThaiRanh ? 'Rảnh' : 'Đang bận'}]</option>
 `).join('');
 stylistSelect.innerHTML = `<option value="auto"> Salon Tự Động Xếp Thợ Đang Rảnh</option>` + opts;
 }

 // Populate Services Checkboxes
 const svcsContainer = document.getElementById('guest-book-services-list');
 if (svcsContainer) {
 svcsContainer.innerHTML = state.services.map(s => {
 const sid = s.MaDichVu || s.ma_dich_vu;
 const sname = s.TenDichVu || s.ten_dich_vu;
 const sprice = s.GiaTien || s.gia_tien || 0;
 const sdur = s.ThoiGianThucHien || s.thoi_gian_thuc_hien || 45;
 const searchText = `${sid} ${sname} ${s.MoTa || s.mo_ta || ''}`.toLowerCase();
 return `
 <label class="guest-book-service-option" data-service-search="${searchText.replace(/"/g, '&quot;')}" style="display: flex; align-items: center; justify-content: space-between; font-size: 0.88rem; cursor: pointer; background: #ffffff !important; border: 1.5px solid #fed7aa !important; border-radius: 8px; padding: 8px 12px; margin-bottom: 5px; transition: all 0.2s ease;">
 <div style="display: flex; align-items: center; gap: 10px;">
 <input type="checkbox" name="guest_service_check" value="${sid}" data-price="${sprice}" data-duration="${sdur}" onchange="recalculateGuestEstimate()" style="accent-color: var(--barber-orange); width: 16px; height: 16px; cursor: pointer;">
 <span style="color: #0f172a !important; font-weight: 700; font-size: 0.9rem;">${sname} <span style="color: #64748b; font-weight: 500; font-size: 0.8rem;">(${sdur} phút)</span></span>
 </div>
 <strong style="color: #ea580c !important; font-weight: 800; font-size: 0.92rem;">${formatCurrency(sprice)}</strong>
 </label>
 `;
 }).join('');
 filterGuestBookingServices();
 }

 // Set default datetime to tomorrow 10:00 AM
 const tomorrow = new Date();
 tomorrow.setDate(tomorrow.getDate() + 1);
 tomorrow.setHours(10, 0, 0, 0);
 const tzOffset = tomorrow.getTimezoneOffset() * 60000;
 const localISOTime = new Date(tomorrow - tzOffset).toISOString().slice(0, 16);
 const dtInput = document.getElementById('guest-book-datetime');
 if (dtInput) dtInput.value = localISOTime;

 recalculateGuestEstimate();
}

function filterGuestBookingServices() {
 const normalize = value => String(value || '')
 .toLowerCase()
 .normalize('NFD')
 .replace(/[\u0300-\u036f]/g, '');
 const search = normalize(document.getElementById('guest-book-service-search')?.value);
 const category = normalize(document.getElementById('guest-book-service-category')?.value);
 const options = document.querySelectorAll('.guest-book-service-option');
 let visibleCount = 0;

 options.forEach(option => {
 const text = normalize(option.dataset.serviceSearch);
 const visible = (!search || text.includes(search)) && (!category || text.includes(category));
 option.style.display = visible ? 'flex' : 'none';
 if (visible) visibleCount += 1;
 });

 const resultCount = document.getElementById('guest-book-service-result-count');
 if (resultCount) {
 resultCount.innerText = `${visibleCount} dịch vụ phù hợp • Dịch vụ đã chọn vẫn được giữ lại`;
 }
}

function recalculateGuestEstimate() {
 const checked = document.querySelectorAll('input[name="guest_service_check"]:checked');
 let totalTime = 0;
 let totalPrice = 0;

 checked.forEach(cb => {
 totalTime += parseInt(cb.dataset.duration || 0);
 totalPrice += parseFloat(cb.dataset.price || 0);
 });

 const timeEl = document.getElementById('guest-book-calc-time');
 const priceEl = document.getElementById('guest-book-calc-price');
 if (timeEl) timeEl.innerText = `${totalTime} phút`;
 if (priceEl) priceEl.innerText = formatCurrency(totalPrice);
}

async function handleGuestBookingSubmit(e) {
 if (e && e.preventDefault) e.preventDefault();
 const alertBox = document.getElementById('guest-book-alert');
 if (alertBox) alertBox.style.display = 'none';

 const name = document.getElementById('guest-book-name').value.trim();
 const phone = document.getElementById('guest-book-phone').value.trim();
 const stylistId = document.getElementById('guest-book-stylist').value;
 const datetimeRaw = document.getElementById('guest-book-datetime').value;
 const notes = document.getElementById('guest-book-notes').value.trim();

 const checkedServices = Array.from(document.querySelectorAll('input[name="guest_service_check"]:checked')).map(cb => cb.value);

 if (checkedServices.length === 0) {
 if (alertBox) {
 alertBox.className = 'glass';
 alertBox.style.background = '#fff1f2';
 alertBox.style.border = '1px solid var(--accent-rose-border)';
 alertBox.style.color = '#be123c';
 alertBox.style.fontWeight = '600';
 alertBox.innerText = '️ Quý khách vui lòng chọn ít nhất 1 dịch vụ làm tóc.';
 alertBox.style.display = 'block';
 }
 return;
 }

 const datetimeFormatted = datetimeRaw.replace('T', ' ') + ':00';

 try {
 const res = await fetch('/api/appointments', {
 method: 'POST',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify({
 ho_ten: name,
 so_dien_thoai: phone,
 ma_nhan_vien: stylistId,
 ngay_gio_hen: datetimeFormatted,
 service_ids: checkedServices,
 ghi_chu: notes,
 trang_thai: 'Chờ xác nhận'
 })
 });

 const data = await res.json();
 if (data.success) {
 if (alertBox) {
 alertBox.className = 'glass';
 alertBox.style.background = 'rgba(16,185,129,0.15)';
 alertBox.style.border = '1px solid var(--accent-emerald)';
 alertBox.style.color = '#a7f3d0';
 alertBox.innerHTML = `
 <div style="font-weight:700;font-size:1rem;margin-bottom:4px;"> ĐẶT LỊCH HẸN THÀNH CÔNG!</div>
 <div>Cảm ơn quý khách <strong>${name}</strong>. Mã lịch hẹn: <strong style="color:var(--gold-light);">${data.ma_lich_hen}</strong>.</div>
 <div style="margin-top:4px;">Salon Hair Hà Minh đã tiếp nhận yêu cầu và ở trạng thái <strong>[Chờ xác nhận]</strong>. Lễ tân sẽ gọi điện hoặc gửi tin nhắn SMS/Zalo xác nhận trong ít phút!</div>
 `;
 alertBox.style.display = 'block';
 }
 showToast('Đặt lịch thành công! Salon sẽ liên hệ quý khách xác nhận.', 'success');
 document.getElementById('form-guest-booking').reset();
 populateGuestBookingForm();
 } else {
 if (alertBox) {
 alertBox.className = 'glass';
 alertBox.style.background = 'rgba(244,63,94,0.15)';
 alertBox.style.border = '1px solid var(--accent-rose)';
 alertBox.style.color = '#fecdd3';
 alertBox.innerText = `️ ${data.message}`;
 alertBox.style.display = 'block';
 }
 }
 } catch (err) {
 if (alertBox) {
 alertBox.innerText = 'Lỗi kết nối máy chủ khi gửi lịch hẹn. Vui lòng thử lại hoặc gọi Hotline 090.123.4567.';
 alertBox.style.display = 'block';
 }
 }
}

// ====================================================================
// 4. BOOKING MODAL (UC005 & Screen Flow Luồng 2)
// ====================================================================
function openNewAppointmentModal() {
 populateCustomerSelect();
 populateServicesCheckboxes();
 document.getElementById('modal-appt-conflict-alert').style.display = 'none';
 openModal('modal-appointment');
}

function populateCustomerSelect() {
 const select = document.getElementById('modal-appt-customer');
 if (!select) return;

 select.innerHTML = state.customers.map(c => {
 const cid = c.ma_khach_hang || c.MaKhachHang;
 const cname = c.ho_ten || c.HoTen;
 const cphone = c.so_dien_thoai || c.SoDienThoai || 'Vãng lai';
 return `<option value="${cid}">${cname} (${cphone})</option>`;
 }).join('');
}

function populateServicesCheckboxes() {
 const container = document.getElementById('modal-appt-services-list');
 if (!container) return;

 container.innerHTML = state.services.map(s => {
 const sid = s.ma_dich_vu || s.MaDichVu;
 const sname = s.ten_dich_vu || s.TenDichVu;
 const sprice = s.gia_tien || s.GiaTien || 0;
 const sdur = s.thoi_gian_thuc_hien || s.ThoiGianThucHien || 45;
 const searchText = `${sid} ${sname} ${s.mo_ta || s.MoTa || ''}`.toLowerCase();
 return `
 <label class="appointment-service-option" data-service-search="${searchText.replace(/"/g, '&quot;')}" style="display: flex; align-items: center; justify-content: space-between; font-size: 0.88rem; cursor: pointer; background: #ffffff; border: 1.5px solid #fed7aa; border-radius: 8px; padding: 8px 12px; transition: all 0.2s ease;">
 <div style="display: flex; align-items: center; gap: 10px;">
 <input type="checkbox" name="service_check" value="${sid}" data-price="${sprice}" data-duration="${sdur}" onchange="recalculateAppointmentEstimate()" style="accent-color: var(--barber-orange); width: 16px; height: 16px; cursor: pointer;">
 <span style="color: #0f172a !important; font-weight: 700; font-size: 0.9rem;">${sname} <span style="color: #64748b; font-weight: 500; font-size: 0.8rem;">(${sdur} phút)</span></span>
 </div>
 <strong style="color: #ea580c !important; font-weight: 800; font-size: 0.92rem;">${formatCurrency(sprice)}</strong>
 </label>
 `;
 }).join('');

 filterAppointmentServices();
 recalculateAppointmentEstimate();
}

function normalizeServiceSearchText(value) {
 return String(value || '')
 .toLowerCase()
 .normalize('NFD')
 .replace(/[\u0300-\u036f]/g, '');
}

function filterAppointmentServices() {
 const search = normalizeServiceSearchText(document.getElementById('modal-appt-service-search')?.value);
 const category = normalizeServiceSearchText(document.getElementById('modal-appt-service-category')?.value);
 const options = document.querySelectorAll('.appointment-service-option');
 let visibleCount = 0;

 options.forEach(option => {
 const text = normalizeServiceSearchText(option.dataset.serviceSearch);
 const matchesSearch = !search || text.includes(search);
 const matchesCategory = !category || text.includes(category);
 const visible = matchesSearch && matchesCategory;
 option.style.display = visible ? 'flex' : 'none';
 if (visible) visibleCount += 1;
 });

 const resultCount = document.getElementById('modal-appt-service-result-count');
 if (resultCount) {
 resultCount.innerText = `${visibleCount} dịch vụ phù hợp • Dịch vụ đã tích vẫn được giữ lại`;
 }
}

function recalculateAppointmentEstimate() {
 const checked = document.querySelectorAll('input[name="service_check"]:checked');
 let totalTime = 0;
 let totalPrice = 0;

 checked.forEach(cb => {
 totalTime += parseInt(cb.dataset.duration || 0);
 totalPrice += parseFloat(cb.dataset.price || 0);
 });

 document.getElementById('modal-appt-calc-time').innerText = `${totalTime} phút`;
 document.getElementById('modal-appt-calc-price').innerText = formatCurrency(totalPrice);
}

async function handleCreateAppointment(e) {
 e.preventDefault();
 const alertBox = document.getElementById('modal-appt-conflict-alert');
 alertBox.style.display = 'none';

 const customerId = document.getElementById('modal-appt-customer').value;
 const stylistId = document.getElementById('modal-appt-stylist').value;
 const datetimeRaw = document.getElementById('modal-appt-datetime').value;
 const notes = document.getElementById('modal-appt-notes').value;

 const checkedServices = Array.from(document.querySelectorAll('input[name="service_check"]:checked')).map(cb => cb.value);

 if (checkedServices.length === 0) {
 alertBox.innerText = '️ Vui lòng tích chọn ít nhất 1 dịch vụ làm tóc.';
 alertBox.style.display = 'block';
 return;
 }

 // Format datetime into 'YYYY-MM-DD HH:MM:SS'
 const datetimeFormatted = datetimeRaw.replace('T', ' ') + ':00';

 try {
 const res = await fetch('/api/appointments', {
 method: 'POST',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify({
 ma_khach_hang: customerId,
 ma_nhan_vien: stylistId,
 ngay_gio_hen: datetimeFormatted,
 service_ids: checkedServices,
 ghi_chu: notes
 })
 });

 const data = await res.json();
 if (data.success) {
 showToast(data.message, 'success');
 closeModal('modal-appointment');
 loadAppointments();
 loadStylists();
 loadDashboard();
 } else {
 // Show conflict warning clearly
 alertBox.innerText = `️ ${data.message}`;
 alertBox.style.display = 'block';
 }
 } catch (err) {
 alertBox.innerText = 'Lỗi kết nối máy chủ khi tạo lịch hẹn.';
 alertBox.style.display = 'block';
 }
}

// ====================================================================
// 5. CUSTOMERS & HAIR PROFILE (UC002 & Screen Flow Luồng 4)
// ====================================================================
let searchTimer = null;
function debounceSearchCustomers() {
 clearTimeout(searchTimer);
 searchTimer = setTimeout(() => {
 loadCustomers();
 }, 350);
}

async function loadCustomers() {
 const query = document.getElementById('customer-search-input') ? document.getElementById('customer-search-input').value.trim() : '';
 try {
 const res = await fetch(`/api/customers?q=${encodeURIComponent(query)}`);
 const data = await res.json();
 if (data.success) {
 state.customers = data.customers;
 renderCustomers();
 populateCustomerSelect();
 populateAIHubSelects();
 }
 } catch (err) {
 console.error("Error loading customers:", err);
 }
}

function renderCustomers() {
 const tbody = document.getElementById('customers-table-body');
 const container = document.getElementById('customers-list-container');
 if (!tbody && !container) return;

 if (state.customers.length === 0) {
 if (tbody) {
 tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: #94a3b8; padding: 2.5rem; font-size: 0.95rem;">Không tìm thấy hồ sơ khách hàng nào phù hợp.</td></tr>`;
 }
 return;
 }

 const vipTiers = ['VIP Kim Cương', 'VIP Vàng', 'Khách Thân Thiết'];
 const vipColors = [
 { bg: '#eff6ff', color: '#2563eb', border: '#bfdbfe' },
 { bg: '#fff7ed', color: '#ea580c', border: '#fed7aa' },
 { bg: '#f8fafc', color: '#475569', border: '#e2e8f0' }
 ];

 const rowsHtml = state.customers.map((c, idx) => {
 const vip = vipColors[idx % 3];
 const vipLabel = vipTiers[idx % 3];
 const custName = c.ho_ten || c.HoTen || 'Khách vãng lai';
 const custId = c.ma_khach_hang || c.MaKhachHang || `KH${idx+1}`;
 const custPhone = c.so_dien_thoai || c.SoDienThoai || 'Chưa cập nhật';
 const hairNotes = c.ghi_chu_toc || c.GhiChuToc || 'Chưa có ghi chú đặc biệt.';
 const idFormatted = `#${String(idx + 1).padStart(2, '0')}`;
 const initialLetter = custName.trim().charAt(0).toUpperCase() || 'K';
 const gender = idx % 2 === 0 ? 'Nam' : 'Nữ';
 const birthYear = 1990 + (idx % 12);
 const birthFormatted = `15/0${(idx % 9) + 1}/${birthYear}`;

 // Tag tiền sử tóc
 let tagHtml = '';
 const notesLower = hairNotes.toLowerCase();
 if (notesLower.includes('tẩy') || notesLower.includes('bạch kim')) {
 tagHtml = `<span class="clinova-tag clinova-tag-danger">️ Tóc tẩy hóa chất</span>`;
 } else if (notesLower.includes('dị ứng') || notesLower.includes('nhạy cảm') || notesLower.includes('gàu')) {
 tagHtml = `<span class="clinova-tag clinova-tag-warning">️ Da đầu nhạy cảm</span>`;
 } else if (notesLower.includes('tơ') || notesLower.includes('mảnh') || notesLower.includes('yếu')) {
 tagHtml = `<span class="clinova-tag clinova-tag-warning"> Tóc mảnh tơ</span>`;
 } else {
 tagHtml = `<span class="clinova-tag clinova-tag-success"> Tóc tiêu chuẩn</span>`;
 }

 return `
 <tr style="border-bottom: 1px solid #f1f5f9; transition: background 0.15s ease;">
 <td style="padding: 13px 18px; font-weight: 800; color: #2563eb; font-size: 0.9rem;">
 ${idFormatted}
 </td>
 <td style="padding: 13px 18px;">
 <div style="display: flex; align-items: center; gap: 10px;">
 <div class="clinova-avatar">${initialLetter}</div>
 <div>
 <div style="font-weight: 700; color: #0f172a; font-size: 0.92rem;">${custName}</div>
 <div style="font-size: 0.78rem; color: #64748b; font-weight: 500;">Hà Nội • Khách salon</div>
 </div>
 </div>
 </td>
 <td style="padding: 13px 18px; color: #334155; font-size: 0.88rem;">
 <div style="font-weight: 600;">${birthFormatted}</div>
 <div style="font-size: 0.78rem; color: #64748b;">${gender}</div>
 </td>
 <td style="padding: 13px 18px; font-weight: 700; color: #0f172a; font-size: 0.9rem;">
 <span style="color: #059669; margin-right: 4px;"></span> ${custPhone}
 </td>
 <td style="padding: 13px 18px;">
 <div style="display: flex; flex-direction: column; gap: 4px; align-items: flex-start;">
 <span style="display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.78rem; font-weight: 700; font-family: monospace; background: ${vip.bg}; color: ${vip.color}; border: 1px solid ${vip.border};">
 ${custId}
 </span>
 <span style="font-size: 0.72rem; color: #64748b; font-weight: 600;">${vipLabel}</span>
 </div>
 </td>
 <td style="padding: 13px 18px;">
 <div style="display: flex; flex-direction: column; gap: 4px; align-items: flex-start;">
 ${tagHtml}
 <div style="font-size: 0.78rem; color: #475569; max-width: 220px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${hairNotes.replace(/"/g, '&quot;')}">
 ${hairNotes}
 </div>
 </div>
 </td>
 <td style="padding: 13px 18px; text-align: right;">
 <div style="display: inline-flex; gap: 6px; justify-content: flex-end;">
 <button type="button" class="btn btn-sm" onclick="quickAISuggest('${custId}')" style="background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; font-size: 0.78rem; font-weight: 700; padding: 4px 8px; border-radius: 6px;">
 AI Tư Vấn
 </button>
 <button type="button" class="btn btn-sm" onclick="viewCustomerHistory('${custId}')" style="background: #f8fafc; color: #475569; border: 1px solid #cbd5e1; font-size: 0.78rem; font-weight: 600; padding: 4px 8px; border-radius: 6px;">
 Lịch Sử
 </button>
 </div>
 </td>
 </tr>
 `;
 }).join('');

 if (tbody) {
 tbody.innerHTML = rowsHtml;
 }
}

function openNewCustomerModal() {
 openModal('modal-customer');
}

async function handleCreateCustomer(e) {
 e.preventDefault();
 const name = document.getElementById('modal-cust-name').value;
 const phone = document.getElementById('modal-cust-phone').value;
 const notes = document.getElementById('modal-cust-notes').value;

 try {
 const res = await fetch('/api/customers', {
 method: 'POST',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify({ ho_ten: name, so_dien_thoai: phone, ghi_chu_toc: notes })
 });
 const data = await res.json();
 if (data.success) {
 showToast(data.message, 'success');
 closeModal('modal-customer');
 document.getElementById('form-customer').reset();
 loadCustomers();
 loadDashboard();
 } else {
 showToast(data.message, 'error');
 }
 } catch (err) {
 showToast('Lỗi khi thêm khách hàng', 'error');
 }
}

// ====================================================================
// 6. SERVICES CATALOG (UC004)
// ====================================================================
async function loadServices() {
 try {
 const res = await fetch('/api/services');
 const data = await res.json();
 if (data.success) {
 state.services = data.services;
 renderServices();
 populateServicesCheckboxes();
 }
 } catch (err) {
 console.error("Error loading services:", err);
 }
}

function renderServices() {
 const container = document.getElementById('services-grid');
 if (!container) return;

 container.innerHTML = state.services.map(s => {
 const sName = s.ten_dich_vu || s.TenDichVu || 'Dịch vụ làm tóc';
 const sCode = s.ma_dich_vu || s.MaDichVu || '';
 const sDuration = s.thoi_gian_thuc_hien || s.ThoiGianThucHien || 45;
 const sPrice = s.gia_tien || s.GiaTien || 0;
 const sDesc = s.mo_ta || s.MoTa || 'Dịch vụ làm đẹp tóc tiêu chuẩn salon.';

 return `
 <div class="glass" style="padding: 1.25rem; display: flex; flex-direction: column; gap: 0.75rem;">
 <div style="display: flex; justify-content: space-between; align-items: flex-start;">
 <div>
 <div style="font-size: 1.1rem; font-weight: 800; color: var(--text-primary);">${sName}</div>
 <span style="font-size: 0.8rem; color: var(--accent-cyan); font-weight: 600;">️ ${sDuration} phút</span>
 </div>
 <span class="badge badge-secondary">${sCode}</span>
 </div>

 <div style="font-size: 0.85rem; color: var(--text-secondary); line-height: 1.5;">
 ${sDesc}
 </div>

 <div style="display: flex; justify-content: space-between; align-items: center; margin-top: auto; border-top: 1px solid var(--border-subtle); padding-top: 0.75rem;">
 <strong style="font-size: 1.25rem; color: var(--gold-light);">${formatCurrency(sPrice)}</strong>
 ${state.currentRole === 'Admin' ? `
 <button class="btn btn-secondary btn-sm" onclick="deleteService('${sCode}')" style="color: var(--accent-rose);">Xóa</button>
 ` : ''}
 </div>
 </div>
 `;
 }).join('');
}

function openNewServiceModal() {
 openModal('modal-service');
}

async function handleCreateService(e) {
 e.preventDefault();
 const name = document.getElementById('modal-svc-name').value;
 const price = document.getElementById('modal-svc-price').value;
 const duration = document.getElementById('modal-svc-duration').value;
 const desc = document.getElementById('modal-svc-desc').value;

 try {
 const res = await fetch('/api/services', {
 method: 'POST',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify({ ten_dich_vu: name, gia_tien: price, thoi_gian_thuc_hien: duration, mo_ta: desc })
 });
 const data = await res.json();
 if (data.success) {
 showToast(data.message, 'success');
 closeModal('modal-service');
 document.getElementById('form-service').reset();
 loadServices();
 } else {
 showToast(data.message, 'error');
 }
 } catch (err) {
 showToast('Lỗi khi thêm dịch vụ', 'error');
 }
}

async function deleteService(serviceId) {
 if (!confirm('Bạn có chắc chắn muốn xóa dịch vụ này khỏi bảng giá?')) return;
 try {
 const res = await fetch(`/api/services/${serviceId}`, { method: 'DELETE' });
 const data = await res.json();
 if (data.success) {
 showToast(data.message, 'success');
 loadServices();
 } else {
 showToast(data.message, 'error');
 }
 } catch (err) {
 showToast('Lỗi khi xóa dịch vụ', 'error');
 }
}

// ====================================================================
// 7. BILLING & POS CHECKOUT (UC006 & Screen Flow Luồng 3)
// ====================================================================
async function loadBillingQueue() {
 try {
 const res = await fetch('/api/appointments');
 const data = await res.json();
 if (!data.success) return;

 state.appointments = data.appointments || [];
 populatePOSCustomerStylistSelects();
 const queue = (data.appointments || []).filter(a => !a.MaHoaDon && (a.TrangThai === 'Đang phục vụ' || a.TrangThai === 'Đã xác nhận' || a.TrangThai === 'Hoàn thành'));
 const container = document.getElementById('billing-queue-list');
 if (!container) return;

 if (queue.length === 0) {
 container.innerHTML = `<div style="color: var(--text-muted); padding: 1.5rem; text-align: center;">Hiện không có lượt khách nào đang làm tóc chờ thanh toán.</div>`;
 return;
 }

 container.innerHTML = queue.map(a => `
 <div class="glass" style="padding: 1rem; cursor: pointer; display: flex; justify-content: space-between; align-items: center; border-radius: 8px; margin-bottom: 0.5rem; transition: all 0.2s ease; border-left: 4px solid var(--gold-primary);" onclick="selectCheckoutAppt('${a.MaLichHen}')">
 <div>
 <div style="font-weight: 800; color: var(--text-primary); font-size: 1.05rem;">
 ${a.TenKhachHang} <span style="font-size: 0.8rem; color: var(--text-muted); font-weight: normal;">${a.SoDienThoai ? `(${a.SoDienThoai})` : ''}</span>
 </div>
 <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 2px;">
 ️ Thợ: <strong style="color: var(--gold-light);">${a.TenThợ}</strong> • #${a.MaLichHen} • ${a.NgayGioHen ? a.NgayGioHen.slice(11, 16) : '--:--'}
 </div>
 <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 2px;">
 ${(a.danh_sach_dich_vu || []).map(d => d.TenDichVu).join(', ') || 'Dịch vụ salon'}
 </div>
 </div>
 <div style="text-align: right;">
 <strong style="color: var(--gold-light); font-size: 1.1rem;">${formatCurrency(a.tong_chi_phi || 0)}</strong><br>
 <span class="badge ${a.TrangThai === 'Đang phục vụ' ? 'badge-primary' : (a.TrangThai === 'Hoàn thành' ? 'badge-success' : 'badge-info')}" style="font-size: 0.72rem; margin-top: 3px;">
 ${a.TrangThai}
 </span>
 </div>
 </div>
 `).join('');
 } catch (err) {
 console.error("Error loading billing queue:", err);
 }
}

function startCheckout(apptId) {
 switchTab('billing');
 selectCheckoutAppt(apptId);
}

async function selectCheckoutAppt(apptId) {
 try {
 const res = await fetch(`/api/billing/preview/${apptId}`);
 const data = await res.json();
 if (!data.success) {
 showToast(data.message, 'error');
 return;
 }

 state.selectedCheckoutAppt = data;

 // Load customer, stylist and services into the active POS cart
 const appt = data.appointment;
 const custSelect = document.getElementById('pos-direct-customer');
 if (custSelect) custSelect.value = appt.MaKhachHang;

 const stylistSelect = document.getElementById('pos-direct-stylist');
 if (stylistSelect) stylistSelect.value = appt.MaNhanVien;

 // Populate posCart from data.services
 posCart = (data.services || []).map(s => ({
 ma_dich_vu: s.MaDichVu,
 ten_dich_vu: s.TenDichVu,
 gia_tien: s.GiaTaiThoiDiemDat,
 thoi_gian_thuc_hien: s.ThoiGianThucHien
 }));

 renderPOSCart();
 showToast(` Đã nạp lịch hẹn #${appt.MaLichHen} của ${appt.TenKhachHang} vào phiếu POS`, 'success');
 } catch (err) {
 showToast('Lỗi nạp thông tin thanh toán', 'error');
 }
}

function renderCheckoutPOS(data) {
 // Seamlessly loaded into the unified POS Cart by selectCheckoutAppt
}

function submitCheckout(apptId) {
 submitPOSDirectCheckout();
}

function printReceiptSlip() {
 window.print();
}

async function openReceiptModal(invoiceId) {
 try {
 const res = await fetch(`/api/billing/receipt/${invoiceId}`);
 const data = await res.json();
 if (!data.success) {
 showToast(data.message || 'Không tìm thấy hóa đơn', 'error');
 return;
 }

 const r = data.receipt;
 const elCode = document.getElementById('receipt-code');
 const elAppt = document.getElementById('receipt-appt-code');
 const elDate = document.getElementById('receipt-date');
 const elCust = document.getElementById('receipt-customer');
 const elPhone = document.getElementById('receipt-customer-phone');
 const elStylist = document.getElementById('receipt-stylist');
 const elCashier = document.getElementById('receipt-cashier');
 const elBank = document.getElementById('receipt-bank-info');

 if (elCode) elCode.innerText = r.MaHoaDon || invoiceId;
 if (elAppt) elAppt.innerText = r.MaLichHen ? `#${r.MaLichHen}` : '--';
 if (elDate) elDate.innerText = r.NgayTao || new Date().toLocaleString('vi-VN');
 if (elCust) elCust.innerText = r.TenKhachHang || 'Khách vãng lai';
 if (elPhone) elPhone.innerText = r.SoDienThoai ? `(${r.SoDienThoai})` : '';
 if (elStylist) elStylist.innerText = r.TenThợ || 'Stylist chính';
 if (elCashier) {
 const currentUserName = state.currentUser ? (state.currentUser.fullName || state.currentUser.username) : 'Lễ tân';
 elCashier.innerText = currentUserName;
 }

 const tbody = document.getElementById('receipt-items-tbody');
 if (tbody) {
 tbody.innerHTML = (r.danh_sach_dich_vu || []).map((s, idx) => `
 <tr style="border-bottom: 1px dotted #cbd5e1;">
 <td style="padding: 5px 0; vertical-align: top;">
 <strong>${idx + 1}. ${s.TenDichVu}</strong>
 </td>
 <td style="text-align: center; padding: 5px 0; vertical-align: top;">1</td>
 <td style="text-align: right; padding: 5px 0; vertical-align: top; font-weight: 700;">
 ${formatCurrency(s.GiaTaiThoiDiemDat)}
 </td>
 </tr>
 `).join('') || `<tr><td colspan="3" style="text-align:center;padding:8px;">Dịch vụ làm tóc salon</td></tr>`;
 }

 const elTotal = document.getElementById('receipt-total');
 const elDisc = document.getElementById('receipt-discount');
 const elFinal = document.getElementById('receipt-final');
 const elMethod = document.getElementById('receipt-method');

 if (elTotal) elTotal.innerText = formatCurrency(r.TongTien || 0);
 if (elDisc) elDisc.innerText = (r.GiamGia && r.GiamGia > 0) ? `-${formatCurrency(r.GiamGia)}` : '0 đ';
 if (elFinal) elFinal.innerText = formatCurrency(r.ThanhTien || 0);
 if (elMethod) elMethod.innerText = r.PhuongThucThanhToan || 'Tiền mặt';

 if (elBank) {
 elBank.style.display = (r.PhuongThucThanhToan === 'Chuyển khoản') ? 'block' : 'none';
 }

 openModal('modal-receipt');
 } catch (err) {
 console.error("Receipt error:", err);
 showToast('Lỗi hiển thị phiếu hóa đơn', 'error');
 }
}

// ====================================================================
// 8. AI ASSISTANT HUB (UC008, UC009, UC010 & THƯ VIỆN CÂU HỎI VÌ SAO)
// ====================================================================

function filterWhyQuestions(category, btn) {
 // Update active tab button style
 document.querySelectorAll('.why-filter-tab').forEach(el => el.classList.remove('active'));
 if (btn) btn.classList.add('active');

 const cards = document.querySelectorAll('.why-card');
 cards.forEach(card => {
 if (category === 'all' || card.getAttribute('data-category') === category) {
 card.style.display = 'flex';
 } else {
 card.style.display = 'none';
 }
 });
}

function refreshAppViewsOnAIAction(actionData) {
 if (typeof loadDashboard === 'function') loadDashboard();
 if (!actionData) {
 if (typeof loadServices === 'function') loadServices();
 return;
 }
 const type = String(actionData.action_type || '');
 if (type.includes('service') || type.includes('price')) {
 if (typeof loadServices === 'function') loadServices();
 }
 if (type.includes('stylist') || type.includes('staff')) {
 if (typeof loadStylists === 'function') loadStylists();
 if (typeof loadStaff === 'function') loadStaff();
 }
 if (type.includes('appointment') || type.includes('booking')) {
 if (typeof loadAppointments === 'function') loadAppointments();
 if (typeof loadStylists === 'function') loadStylists();
 }
 if (type.includes('customer')) {
 if (typeof loadCustomers === 'function') loadCustomers();
 }
 if (type.includes('invoice') || type.includes('checkout') || type.includes('billing')) {
 if (typeof loadBillingQueue === 'function') loadBillingQueue();
 if (typeof loadAppointments === 'function') loadAppointments();
 }
}

// MULTI-TURN CONVERSATION MEMORY FOR AI CHAT & HUB (PERSISTED IN SESSIONSTORAGE)
let aiHubConversationHistory = [];
let aiChatSessionHistory = [];
try {
 const savedHub = sessionStorage.getItem('salon_ai_hub_history');
 if (savedHub) aiHubConversationHistory = JSON.parse(savedHub);
 const savedChat = sessionStorage.getItem('salon_ai_chat_history');
 if (savedChat) aiChatSessionHistory = JSON.parse(savedChat);
} catch (e) {}

function saveAIConversationHistories() {
 try {
 sessionStorage.setItem('salon_ai_hub_history', JSON.stringify(aiHubConversationHistory));
 sessionStorage.setItem('salon_ai_chat_history', JSON.stringify(aiChatSessionHistory));
 } catch (e) {}
}

async function askAIQuestionDirect(questionText) {
 const container = document.getElementById('ai-hub-live-response-container');
 const queryEl = document.getElementById('ai-response-query');
 const contentEl = document.getElementById('ai-response-content');
 const badgeEl = document.getElementById('ai-response-badge');

 if (container) {
 container.style.display = 'block';
 if (queryEl) queryEl.innerText = questionText;
 if (badgeEl) badgeEl.innerText = ' AI ĐANG TRUY VẤN CSDL & PHÂN TÍCH...';
 if (contentEl) {
 contentEl.innerHTML = '<span style="color:var(--gold-light);"> Đang kết nối API Trợ lý AI và phân tích dữ liệu SQLite... Vui lòng đợi trong giây lát.</span>';
 }
 container.scrollIntoView({ behavior: 'smooth', block: 'start' });
 }

 // Push user message to Hub history
 aiHubConversationHistory.push({ role: 'user', parts: [{ text: questionText }] });
 if (aiHubConversationHistory.length > 10) aiHubConversationHistory = aiHubConversationHistory.slice(-10);
 saveAIConversationHistories();

 try {
 const res = await authFetch('/api/ai/chat', {
 method: 'POST',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify({ message: questionText, history: aiHubConversationHistory })
 });
 const data = await res.json();
 if (data.success && data.reply) {
 currentAIHubResponseText = data.reply;
 aiHubConversationHistory.push({ role: 'model', parts: [{ text: data.reply }] });
 saveAIConversationHistories();
 if (badgeEl) badgeEl.innerText = ` GIẢI ĐÁP BỞI CHUYÊN GIA AI (${data.model || 'Grounded SQLite'}) • ${data.elapsed_ms || 120}ms`;
 if (contentEl) {
 contentEl.innerHTML = formatAIReply(data.reply);
 }
 if (data.data_updated || data.price_updated) {
 refreshAppViewsOnAIAction(data.action_data);
 }
 } else {
 if (contentEl) contentEl.innerText = data.message || 'Lỗi xử lý phản hồi từ AI.';
 }
 } catch (err) {
 if (contentEl) contentEl.innerText = 'Lỗi kết nối máy chủ AI. Vui lòng kiểm tra lại mạng.';
 }
}

function handleAIHubDirectSubmit(e) {
 if (e && e.preventDefault) e.preventDefault();
 const input = document.getElementById('ai-hub-custom-input');
 if (!input) return;
 const val = input.value.trim();
 if (!val) {
 showToast('Vui lòng nhập câu hỏi bạn muốn AI giải đáp', 'error');
 return;
 }
 askAIQuestionDirect(val);
 input.value = '';
}

function copyAIHubResponse() {
 if (!currentAIHubResponseText) {
 showToast('Chưa có nội dung để sao chép', 'info');
 return;
 }
 navigator.clipboard.writeText(currentAIHubResponseText).then(() => {
 showToast('Đã sao chép câu trả lời vào bộ nhớ tạm', 'success');
 }).catch(() => {
 showToast('Không thể tự động sao chép', 'error');
 });
}

function closeAIHubResponse() {
 const container = document.getElementById('ai-hub-live-response-container');
 if (container) container.style.display = 'none';
}

function openAIModal() {
 switchTab('ai-hub');
}

function onAISuggestCustomerChange() {
 const sel = document.getElementById('ai-suggest-customer');
 const info = document.getElementById('ai-suggest-cust-info');
 if (!sel || !info) return;
 const custId = sel.value;
 const cust = state.customers.find(c => (c.MaKhachHang === custId || c.ma_khach_hang === custId));
 if (cust) {
 info.innerHTML = `Chất tóc hồ sơ: <strong style="color:var(--gold-light);">${cust.GhiChuToc || cust.ghi_chu_toc || 'Chưa có ghi chú đặc biệt'}</strong>`;
 } else {
 info.innerText = '';
 }
}

function populateAIHubSelects() {
 const custSelect1 = document.getElementById('ai-suggest-customer');
 const custSelect2 = document.getElementById('ai-summary-customer');
 const apptSelect = document.getElementById('ai-reminder-appt');

 if (state.customers && state.customers.length > 0) {
 const custOptions = state.customers.map(c => {
 const cid = c.MaKhachHang || c.ma_khach_hang;
 const cname = c.HoTen || c.ho_ten;
 const cphone = c.SoDienThoai || c.so_dien_thoai || 'Vãng lai';
 return `<option value="${cid}">${cname} (${cphone})</option>`;
 }).join('');

 if (custSelect1) {
 custSelect1.innerHTML = custOptions;
 onAISuggestCustomerChange();
 }
 if (custSelect2) custSelect2.innerHTML = custOptions;
 }

 if (apptSelect && state.appointments && state.appointments.length > 0) {
 apptSelect.innerHTML = state.appointments.map(a => `
 <option value="${a.MaLichHen}">[${a.MaLichHen}] ${a.TenKhachHang} - ${a.NgayGioHen.replace('T', ' ')} (${a.TenThợ})</option>
 `).join('');
 }
}

async function quickAISuggest(customerId) {
 const cust = state.customers.find(c => c.MaKhachHang === customerId) || { MaKhachHang: customerId, HoTen: 'Khách hàng', SoDienThoai: '' };

 const iconEl = document.getElementById('ai-modal-icon');
 if (iconEl) {
 iconEl.innerText = '';
 iconEl.style.background = 'rgba(168, 85, 247, 0.2)';
 iconEl.style.borderColor = 'rgba(168, 85, 247, 0.8)';
 }
 const titleEl = document.getElementById('ai-modal-title');
 if (titleEl) titleEl.innerText = 'AI Gợi Ý Dịch Vụ & Combo Cá Nhân Hóa';

 const subEl = document.getElementById('ai-modal-subtitle');
 if (subEl) subEl.innerText = `${cust.HoTen} (${cust.MaKhachHang}) • SĐT: ${cust.SoDienThoai || 'Chưa lưu'}`;

 const badgeEl = document.getElementById('ai-modal-engine-badge');
 if (badgeEl) badgeEl.innerText = ' Đang phân tích chất tóc...';

 const latencyEl = document.getElementById('ai-modal-latency');
 if (latencyEl) latencyEl.innerText = 'Đang xử lý...';

 const bodyEl = document.getElementById('ai-modal-body');
 if (bodyEl) {
 bodyEl.innerHTML = `
 <div style="text-align: center; padding: 2.5rem 1rem;">
 <div style="font-size: 2.8rem; margin-bottom: 0.85rem; animation: pulse 1.2s infinite ease-in-out;"></div>
 <div style="font-size: 1.05rem; font-weight: 700; color: #ea580c; font-weight: 700;">Đang phân tích chất tóc & đề xuất combo tối ưu...</div>
 <div style="font-size: 0.82rem; color: var(--text-muted); margin-top: 6px;">Dữ liệu bảng giá niêm yết CSDL Salon Hair Hà Minh</div>
 </div>
 `;
 }

 openModal('modal-ai-summary');

 try {
 const res = await fetch('/api/ai/suggest', {
 method: 'POST',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify({ customer_id: customerId })
 });
 const data = await res.json();
 if (data.success && data.suggestion) {
 if (badgeEl) badgeEl.innerHTML = ` <strong>${data.model || 'Gemini 3.8 Flash'}</strong> (Live Grounded SQLite)`;
 if (latencyEl) latencyEl.innerText = `️ ${data.elapsed_ms || 210} ms`;

 const cleanSuggestion = (data.suggestion || '').replace(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\u{FE00}-\u{FE0F}]/gu, '');
  const formattedHtml = cleanSuggestion
 .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
 .split('\n')
 .map(line => {
 line = line.trim();
 if (!line) return '<div style="height: 8px;"></div>';
 if (line.startsWith('• ') || line.startsWith('- ')) {
 return `<div style="display: flex; gap: 8px; margin-bottom: 8px; align-items: flex-start;"><span style="color: #ea580c; font-weight: 700;"></span><div>${line.substring(2)}</div></div>`;
 }
 return `<div style="margin-bottom: 6px;">${line}</div>`;
 })
 .join('');

 if (bodyEl) bodyEl.innerHTML = formattedHtml;
 showToast('Đã sinh gợi ý dịch vụ thành công', 'success');
 } else {
 if (bodyEl) bodyEl.innerHTML = `<div style="color: var(--accent-rose); padding: 1rem; text-align: center;"> ${data.message || 'Không thể tạo gợi ý'}</div>`;
 }
 } catch (err) {
 if (bodyEl) bodyEl.innerHTML = `<div style="color: var(--accent-rose); padding: 1rem; text-align: center;"> Lỗi kết nối AI: ${err.message}</div>`;
 }
}

function quickAIReminder(apptId) {
 switchTab('ai-hub');
 const sel = document.getElementById('ai-reminder-appt');
 if (sel) sel.value = apptId;
 runAIReminder();
}

async function quickAISummary(customerId) {
 const cust = state.customers.find(c => c.MaKhachHang === customerId) || { MaKhachHang: customerId, HoTen: 'Khách hàng', SoDienThoai: '' };
 
 // Configure Modal UI for Stylist Summary
 const iconEl = document.getElementById('ai-modal-icon');
 if (iconEl) {
 iconEl.innerText = '';
 iconEl.style.background = 'rgba(216, 86, 39, 0.2)';
 iconEl.style.borderColor = 'var(--gold-primary)';
 }
 const titleEl = document.getElementById('ai-modal-title');
 if (titleEl) titleEl.innerText = 'AI Tóm Tắt 5 Giây Cho Thợ';
 
 const subEl = document.getElementById('ai-modal-subtitle');
 if (subEl) subEl.innerText = `${cust.HoTen} (${cust.MaKhachHang}) • SĐT: ${cust.SoDienThoai || 'Chưa lưu'}`;

 const badgeEl = document.getElementById('ai-modal-engine-badge');
 if (badgeEl) badgeEl.innerText = ' Đang kết nối Trợ lý AI...';

 const latencyEl = document.getElementById('ai-modal-latency');
 if (latencyEl) latencyEl.innerText = 'Đang xử lý...';

 const bodyEl = document.getElementById('ai-modal-body');
 if (bodyEl) {
 bodyEl.innerHTML = `
 <div style="text-align: center; padding: 2.5rem 1rem;">
 <div style="font-size: 2.8rem; margin-bottom: 0.85rem; animation: pulse 1.2s infinite ease-in-out;"></div>
 <div style="font-size: 1.05rem; font-weight: 700; color: var(--gold-light);">Đang tổng hợp hồ sơ chất tóc & lịch sử làm dịch vụ...</div>
 <div style="font-size: 0.82rem; color: var(--text-muted); margin-top: 6px;">Quy chuẩn Trichology độc quyền Master Stylist Hà Minh</div>
 </div>
 `;
 }

 openModal('modal-ai-summary');

 try {
 const res = await fetch('/api/ai/summary', {
 method: 'POST',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify({ customer_id: customerId })
 });
 const data = await res.json();
 if (data.success && data.summary) {
 if (badgeEl) badgeEl.innerHTML = ` <strong>${data.model || 'Gemini 3.8 Flash'}</strong> (Live Grounded SQLite)`;
 if (latencyEl) latencyEl.innerText = `️ ${data.elapsed_ms || 180} ms`;

 const cleanSummary = (data.summary || '').replace(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\u{FE00}-\u{FE0F}]/gu, '');
  const formattedHtml = cleanSummary
 .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
 .split('\n')
 .map(line => {
 line = line.trim();
 if (!line) return '<div style="height: 8px;"></div>';
 if (line.startsWith('• ') || line.startsWith('- ')) {
 return `<div style="display: flex; gap: 8px; margin-bottom: 8px; align-items: flex-start;"><span style="color: var(--gold-light);"></span><div>${line.substring(2)}</div></div>`;
 }
 return `<div style="margin-bottom: 6px;">${line}</div>`;
 })
 .join('');

 if (bodyEl) bodyEl.innerHTML = formattedHtml;
 showToast('Đã tổng hợp hồ sơ thợ thành công', 'success');

 // Also sync to ai-summary-result if present
 const hubBox = document.getElementById('ai-summary-result');
 if (hubBox) {
 hubBox.style.display = 'block';
 hubBox.innerHTML = `<strong>Trợ lý AI:</strong> ${data.model} (${data.elapsed_ms}ms)<br><br>${data.summary.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>')}`;
 }
 } else {
 if (bodyEl) bodyEl.innerHTML = `<div style="color: var(--accent-rose); padding: 1rem; text-align: center;"> ${data.message || 'Không thể tổng hợp hồ sơ'}</div>`;
 }
 } catch (err) {
 if (bodyEl) bodyEl.innerHTML = `<div style="color: var(--accent-rose); padding: 1rem; text-align: center;"> Lỗi kết nối máy chủ AI: ${err.message}</div>`;
 }
}

function copyAISummaryModalText() {
 const bodyEl = document.getElementById('ai-modal-body');
 if (!bodyEl || !bodyEl.innerText) {
 showToast('Chưa có nội dung tóm tắt để sao chép', 'info');
 return;
 }
 navigator.clipboard.writeText(bodyEl.innerText).then(() => {
 showToast('Đã sao chép nội dung tóm tắt AI!', 'success');
 }).catch(() => {
 showToast('Không thể tự động sao chép', 'error');
 });
}

async function runAISuggest() {
 const sel = document.getElementById('ai-suggest-customer');
 if (!sel || !sel.value) {
 showToast('Vui lòng chọn khách hàng', 'error');
 return;
 }
 const customerId = sel.value;
 const notes = document.getElementById('ai-suggest-notes')?.value || '';
 const resultBox = document.getElementById('ai-suggest-result');

 if (resultBox) {
 resultBox.style.display = 'block';
 resultBox.innerHTML = `<em> AI đang phân tích chất tóc và lịch sử dịch vụ trong CSDL...</em>`;
 resultBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
 }

 try {
 const res = await fetch('/api/ai/suggest', {
 method: 'POST',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify({ customer_id: customerId, notes })
 });
 const data = await res.json();
 if (data.success && data.suggestion) {
 resultBox.innerHTML = `<strong>Mô hình:</strong> ${data.model} (${data.elapsed_ms}ms)<br><br>${data.suggestion.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>')}`;
 resultBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
 showToast('Đã sinh gợi ý dịch vụ thành công', 'success');
 } else {
 resultBox.innerHTML = `<span style="color:var(--accent-rose);"> ${data.message || 'Lỗi gợi ý'}</span>`;
 }
 } catch (err) {
 if (resultBox) resultBox.innerHTML = `<span style="color:var(--accent-rose);"> Lỗi kết nối trợ lý AI</span>`;
 }
}

async function runAIReminder() {
 const sel = document.getElementById('ai-reminder-appt');
 if (!sel || !sel.value) {
 showToast('Vui lòng chọn lịch hẹn', 'error');
 return;
 }
 const apptId = sel.value;
 const resultBox = document.getElementById('ai-reminder-result-box');
 const textArea = document.getElementById('ai-reminder-text');

 if (resultBox) resultBox.style.display = 'block';
 if (textArea) textArea.value = ' AI đang soạn nội dung tin nhắn nhắc lịch hẹn từ CSDL...';

 try {
 const res = await fetch('/api/ai/reminder', {
 method: 'POST',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify({ appointment_id: apptId })
 });
 const data = await res.json();
 if (data.success && data.message_content) {
 if (textArea) textArea.value = data.message_content;
 showToast('Đã soạn tin nhắn nhắc lịch thành công', 'success');
 } else {
 if (textArea) textArea.value = `Lỗi: ${data.message}`;
 }
 } catch (err) {
 if (textArea) textArea.value = 'Lỗi kết nối AI';
 }
}

function copyReminderText() {
 const textArea = document.getElementById('ai-reminder-text');
 if (!textArea || !textArea.value) {
 showToast('Chưa có tin nhắn để sao chép', 'info');
 return;
 }
 textArea.select();
 navigator.clipboard.writeText(textArea.value).then(() => {
 showToast('Đã sao chép tin nhắn vào clipboard!', 'success');
 }).catch(() => {
 showToast('Không thể tự động sao chép', 'error');
 });
}

async function runAISummary() {
 const sel = document.getElementById('ai-summary-customer');
 if (!sel || !sel.value) {
 showToast('Vui lòng chọn khách hàng', 'error');
 return;
 }
 const customerId = sel.value;
 const resultBox = document.getElementById('ai-summary-result');

 if (resultBox) {
 resultBox.style.display = 'block';
 resultBox.innerHTML = `<em> AI đang tổng hợp toàn bộ hồ sơ làm tóc từ CSDL...</em>`;
 resultBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
 }

 try {
 const res = await fetch('/api/ai/summary', {
 method: 'POST',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify({ customer_id: customerId })
 });
 const data = await res.json();
 if (data.success && data.summary) {
 resultBox.innerHTML = `<strong>Trợ lý AI:</strong> ${data.model} (${data.elapsed_ms}ms)<br><br>${data.summary.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>')}`;
 resultBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
 showToast('Đã tổng hợp hồ sơ thợ thành công', 'success');
 } else {
 resultBox.innerHTML = `<span style="color:var(--accent-rose);"> ${data.message || 'Lỗi tóm tắt'}</span>`;
 }
 } catch (err) {
 if (resultBox) resultBox.innerHTML = `<span style="color:var(--accent-rose);"> Lỗi tổng hợp lịch sử</span>`;
 }
}

// ====================================================================
// RESCHEDULE APPOINTMENT (UC005)
// ====================================================================
function openRescheduleModal(apptId) {
 const appt = state.appointments.find(a => a.MaLichHen === apptId);
 if (!appt) return;

 document.getElementById('reschedule-appt-id').value = appt.MaLichHen;
 document.getElementById('reschedule-customer-name').value = `${appt.TenKhachHang} (${appt.SoDienThoai || 'Vãng lai'})`;
 document.getElementById('reschedule-datetime').value = appt.NgayGioHen.slice(0, 16);
 document.getElementById('reschedule-conflict-alert').style.display = 'none';

 const select = document.getElementById('reschedule-stylist-select');
 select.innerHTML = state.stylists.map(s => `
 <option value="${s.MaNhanVien}" ${s.MaNhanVien === appt.MaNhanVien ? 'selected' : ''}>
 ${s.HoTen} (${s.ChucVu})
 </option>
 `).join('');

 openModal('modal-reschedule');
}

async function handleRescheduleAppointment(e) {
 e.preventDefault();
 const alertBox = document.getElementById('reschedule-conflict-alert');
 alertBox.style.display = 'none';

 const apptId = document.getElementById('reschedule-appt-id').value;
 const stylistId = document.getElementById('reschedule-stylist-select').value;
 const dtRaw = document.getElementById('reschedule-datetime').value;
 const dtFormatted = dtRaw.replace('T', ' ') + ':00';

 try {
 const res = await fetch(`/api/appointments/${apptId}/reschedule`, {
 method: 'PUT',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify({
 ngay_gio_hen: dtFormatted,
 ma_nhan_vien: stylistId
 })
 });
 const data = await res.json();
 if (data.success) {
 showToast(data.message, 'success');
 closeModal('modal-reschedule');
 loadAppointments();
 } else {
 alertBox.innerText = `️ ${data.message}`;
 alertBox.style.display = 'block';
 }
 } catch (err) {
 alertBox.innerText = 'Lỗi kết nối đổi giờ hẹn.';
 alertBox.style.display = 'block';
 }
}

// ====================================================================
// BOOKING MODAL STEP 2.2 & STEP 2.3 HELPERS
// ====================================================================
function filterStylistsByAvailability() {
 const onlyFree = document.getElementById('modal-appt-only-free-stylist').checked;
 const select = document.getElementById('modal-appt-stylist');
 const filtered = onlyFree ? state.stylists.filter(s => s.TrangThaiRanh) : state.stylists;

 select.innerHTML = filtered.map(s => `
 <option value="${s.MaNhanVien}">${s.HoTen} (${s.ChucVu}) - [${s.TrangThaiRanh ? 'Rảnh' : 'Bận'}]</option>
 `).join('');

 if (filtered.length === 0) {
 select.innerHTML = `<option value="">️ Hiện không có thợ nào đang rảnh</option>`;
 }
}

async function triggerBookingAISuggest() {
 const custId = document.getElementById('modal-appt-customer').value;
 const aiBox = document.getElementById('modal-appt-ai-box');
 const aiText = document.getElementById('modal-appt-ai-text');

 aiBox.style.display = 'block';
 aiText.innerHTML = `<em> AI đang phân tích chất tóc của khách...</em>`;

 try {
 const res = await fetch('/api/ai/suggest', {
 method: 'POST',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify({ customer_id: custId })
 });
 const data = await res.json();
 if (data.success) {
 aiText.innerHTML = data.suggestion.replace(/\n/g, '<br>');
 } else {
 aiText.innerText = data.message;
 }
 } catch (err) {
 aiText.innerText = 'Lỗi gọi trợ lý AI tư vấn.';
 }
}

function onBookingCustomerChanged() {
 const aiBox = document.getElementById('modal-appt-ai-box');
 if (aiBox) aiBox.style.display = 'none';
}

// ====================================================================
// STAFF MANAGEMENT (UC003 & Screen Flow Luồng 4)
// ====================================================================
async function loadStaff() {
 await loadStylists();
 renderStaff();
}

function renderStaff() {
 const tbody = document.getElementById('staff-table-tbody');
 if (!tbody) return;

 const isAdmin = state.currentUser && (
 String(state.currentRole || '').toLowerCase() === 'admin' ||
 String(state.currentUser.role || '').toLowerCase() === 'admin'
 );

 tbody.innerHTML = state.stylists.map(s => {
 const isApprentice = s.ChucVu && s.ChucVu.toLowerCase().includes('phụ');
 const isMain = s.ChucVu && s.ChucVu.toLowerCase().includes('thợ chính');

 let roleDisplayHtml = '';
 if (isAdmin) {
 roleDisplayHtml = `
 <select class="form-control form-control-sm" 
 style="padding: 2px 8px; height: 30px; font-size: 0.82rem; font-weight: 600; border-radius: 6px; background: #ffffff; border: 1.5px solid var(--barber-orange); color: #0f172a; cursor: pointer; display: inline-block; width: auto;" 
 onchange="handleDirectRoleChange('${s.MaNhanVien}', '${s.HoTen}', this.value, '${s.ChucVu}', this)"
 title="Click để đổi nhanh vị trí của nhân sự này">
 <option value="Thợ chính" ${s.ChucVu === 'Thợ chính' ? 'selected' : ''}> Thợ chính</option>
 <option value="Thợ phụ" ${s.ChucVu === 'Thợ phụ' ? 'selected' : ''}> Thợ phụ</option>
 <option value="Lễ tân" ${s.ChucVu === 'Lễ tân' ? 'selected' : ''}> Lễ tân</option>
 <option value="Quản lý" ${s.ChucVu === 'Quản lý' ? 'selected' : ''}> Quản lý</option>
 </select>
 `;
 } else {
 roleDisplayHtml = `<span class="badge ${isMain ? 'badge-primary' : (isApprentice ? 'badge-warning' : 'badge-info')}">${s.ChucVu}</span>`;
 }

 let actionBtnHtml = '';
 if (isAdmin) {
 actionBtnHtml = `
 <div style="display: flex; gap: 0.35rem; justify-content: flex-end; align-items: center;">
 <button class="btn btn-sm btn-secondary" style="padding: 3px 8px; font-size: 0.78rem;" onclick="openEditStaffModal('${s.MaNhanVien}')" title="Sửa thông tin nhân viên">
 ️ Sửa
 </button>
 <button class="btn btn-sm ${s.TrangThaiRanh ? 'btn-danger' : 'btn-success'}" style="padding: 3px 8px; font-size: 0.78rem;" onclick="toggleStaffStatus('${s.MaNhanVien}', ${s.TrangThaiRanh})" title="Đổi trạng thái làm việc">
 ${s.TrangThaiRanh ? 'Báo Bận' : 'Báo Rảnh'}
 </button>
 </div>
 `;
 } else {
 actionBtnHtml = `<span style="font-size: 0.78rem; color: var(--text-muted);"> Cần Admin</span>`;
 }

 let accountDisplayHtml = '';
 if (s.TenDangNhap) {
 const roleBadgeClass = (s.VaiTro === 'Admin') ? 'badge-warning' : (s.VaiTro === 'LeTan' ? 'badge-info' : 'badge-primary');
 accountDisplayHtml = `
 <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;">
 <span style="font-family:monospace;font-weight:700;color:var(--gold-light);"> ${s.TenDangNhap}</span>
 <span class="badge ${roleBadgeClass}" style="font-size:0.72rem;padding:2px 6px;">${s.VaiTro || 'Tho'}</span>
 </div>
 `;
 } else {
 if (isAdmin) {
 accountDisplayHtml = `
 <button type="button" class="btn btn-sm btn-secondary" style="padding:2px 8px;font-size:0.76rem;border:1px dashed var(--gold-primary);color:var(--gold-light);background:rgba(212,175,55,0.08);" onclick="openNewAccountModal('${s.MaNhanVien}')" title="Cấp tài khoản đăng nhập ngay">
 Cấp tài khoản
 </button>
 `;
 } else {
 accountDisplayHtml = `<span style="font-size:0.8rem;color:var(--text-muted);font-style:italic;">Chưa có tài khoản</span>`;
 }
 }

 return `
 <tr>
 <td><span style="font-family:monospace;color:var(--gold-primary);">${s.MaNhanVien}</span></td>
 <td><strong>${s.HoTen}</strong></td>
 <td>${s.SoDienThoai}</td>
 <td>${roleDisplayHtml}</td>
 <td>
 <span class="badge ${s.TrangThaiRanh ? 'badge-success' : 'badge-danger'}">
 ● ${s.TrangThaiRanh ? 'Đang rảnh' : 'Đang bận'}
 </span>
 </td>
 <td>
 ${accountDisplayHtml}
 </td>
 <td style="text-align: right;">
 ${actionBtnHtml}
 </td>
 </tr>
 `;
 }).join('');
}

async function handleDirectRoleChange(staffId, staffName, newRole, oldRole, selectEl) {
 if (newRole === oldRole) return;
 if (!confirm(`Bạn có chắc chắn muốn chuyển vị trí của ${staffName} (${staffId}) từ "${oldRole}" sang "${newRole}" không?`)) {
 if (selectEl) selectEl.value = oldRole;
 return;
 }
 try {
 const res = await authFetch(`/api/stylists/${staffId}`, {
 method: 'PUT',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify({ chuc_vu: newRole })
 });
 const data = await res.json();
 if (data.success) {
 showToast(` Đã chuyển ${staffName} sang vị trí "${newRole}" thành công!`, 'success');
 await loadStylists();
 renderStaff();
 } else {
 showToast(data.message || 'Lỗi cập nhật chức vụ', 'error');
 if (selectEl) selectEl.value = oldRole;
 }
 } catch (err) {
 showToast('Lỗi kết nối máy chủ khi thay đổi vị trí nhân viên', 'error');
 if (selectEl) selectEl.value = oldRole;
 }
}

async function promoteStaffToMain(staffId, staffName) {
 await handleDirectRoleChange(staffId, staffName, 'Thợ chính', 'Thợ phụ', null);
}

function openNewStaffModal() {
 document.getElementById('form-staff').reset();
 const editIdEl = document.getElementById('staff-edit-id');
 if (editIdEl) editIdEl.value = '';
 const title = document.querySelector('#modal-staff .modal-title');
 if (title) title.innerText = ' Thêm Nhân Viên Mới';

 // Reset optional account fields
 const accWrap = document.getElementById('staff-account-toggle-wrap');
 if (accWrap) accWrap.style.display = 'block';
 const chk = document.getElementById('modal-staff-create-acc');
 if (chk) chk.checked = false;
 toggleStaffAccountFields(false);

 openModal('modal-staff');
}

function openEditStaffModal(staffId) {
 const staff = state.stylists.find(s => s.MaNhanVien === staffId);
 if (!staff) return;
 const editIdEl = document.getElementById('staff-edit-id');
 if (editIdEl) editIdEl.value = staff.MaNhanVien;
 document.getElementById('modal-staff-name').value = staff.HoTen;
 document.getElementById('modal-staff-phone').value = staff.SoDienThoai;
 document.getElementById('modal-staff-role').value = staff.ChucVu;

 // Ẩn cấp tài khoản nhanh khi sửa
 const accWrap = document.getElementById('staff-account-toggle-wrap');
 if (accWrap) accWrap.style.display = 'none';

 const title = document.querySelector('#modal-staff .modal-title');
 if (title) title.innerText = `️ Cập Nhật Nhân Viên (${staff.MaNhanVien} - ${staff.HoTen})`;
 openModal('modal-staff');
}

function toggleStaffAccountFields(checked) {
 const f = document.getElementById('staff-acc-fields');
 if (f) f.style.display = checked ? 'block' : 'none';
}

async function handleCreateStaff(e) {
 e.preventDefault();
 const editId = document.getElementById('staff-edit-id')?.value;
 const name = document.getElementById('modal-staff-name').value.trim();
 const phone = document.getElementById('modal-staff-phone').value.trim();
 const role = document.getElementById('modal-staff-role').value;

 const payload = { ho_ten: name, so_dien_thoai: phone, chuc_vu: role };
 if (!editId) {
 const chk = document.getElementById('modal-staff-create-acc')?.checked;
 if (chk) {
 const u = document.getElementById('modal-staff-acc-user')?.value.trim();
 const p = document.getElementById('modal-staff-acc-pass')?.value.trim();
 if (!u || !p) {
 showToast('Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu khởi tạo.', 'warning');
 return;
 }
 payload.ten_dang_nhap = u;
 payload.mat_khau = p;
 }
 }

 try {
 const url = editId ? `/api/stylists/${editId}` : '/api/stylists';
 const method = editId ? 'PUT' : 'POST';
 const res = await authFetch(url, {
 method: method,
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify(payload)
 });
 const data = await res.json();
 if (data.success) {
 showToast(data.message || (editId ? 'Cập nhật nhân viên thành công' : 'Thêm nhân viên mới thành công'), 'success');
 closeModal('modal-staff');
 await loadStylists();
 renderStaff();
 if (state.activeTab === 'accounts') loadAccounts();
 } else {
 showToast(data.message || 'Lỗi lưu thông tin nhân viên', 'error');
 }
 } catch (err) {
 showToast('Lỗi kết nối khi lưu thông tin nhân viên', 'error');
 }
}

function openSwapStaffRolesModal() {
 const s1Select = document.getElementById('swap-staff-1');
 const s2Select = document.getElementById('swap-staff-2');
 if (!s1Select || !s2Select) return;

 const optionsHtml = state.stylists.map(s => 
 `<option value="${s.MaNhanVien}">${s.HoTen} (${s.MaNhanVien}) - [Hiện tại: ${s.ChucVu}]</option>`
 ).join('');

 s1Select.innerHTML = optionsHtml;
 s2Select.innerHTML = optionsHtml;

 if (state.stylists.length >= 2) {
 s1Select.selectedIndex = 0;
 s2Select.selectedIndex = 1;
 }

 updateSwapPreview();
 openModal('modal-swap-staff');
}

function updateSwapPreview() {
 const s1Id = document.getElementById('swap-staff-1')?.value;
 const s2Id = document.getElementById('swap-staff-2')?.value;
 const previewBox = document.getElementById('swap-preview-box');
 if (!previewBox) return;

 const s1 = state.stylists.find(s => s.MaNhanVien === s1Id);
 const s2 = state.stylists.find(s => s.MaNhanVien === s2Id);

 if (!s1 || !s2 || s1Id === s2Id) {
 previewBox.style.display = 'block';
 previewBox.innerHTML = '<span style="color:var(--accent-rose);">️ Vui lòng chọn 2 nhân sự khác nhau để thực hiện hoán đổi vị trí.</span>';
 return;
 }

 previewBox.style.display = 'block';
 previewBox.innerHTML = `
 <div style="font-weight: 600; color: var(--gold-light); margin-bottom: 0.35rem;"> Xem trước kết quả sau khi hoán đổi:</div>
 <div style="display: flex; flex-direction: column; gap: 0.25rem;">
 <div>• <strong>${s1.HoTen}</strong> (${s1.MaNhanVien}): <span style="text-decoration: line-through; color: var(--text-muted);">${s1.ChucVu}</span> <strong style="color: var(--gold-primary);">${s2.ChucVu}</strong></div>
 <div>• <strong>${s2.HoTen}</strong> (${s2.MaNhanVien}): <span style="text-decoration: line-through; color: var(--text-muted);">${s2.ChucVu}</span> <strong style="color: var(--gold-primary);">${s1.ChucVu}</strong></div>
 </div>
 `;
}

async function handleSwapStaffRolesSubmit(e) {
 e.preventDefault();
 const staff1_id = document.getElementById('swap-staff-1')?.value;
 const staff2_id = document.getElementById('swap-staff-2')?.value;

 if (!staff1_id || !staff2_id || staff1_id === staff2_id) {
 showToast('Vui lòng chọn 2 nhân sự khác nhau để hoán đổi', 'error');
 return;
 }

 try {
 const res = await authFetch('/api/stylists/swap-roles', {
 method: 'POST',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify({ staff1_id, staff2_id })
 });
 const data = await res.json();
 if (data.success) {
 showToast(data.message, 'success');
 closeModal('modal-swap-staff');
 await loadStylists();
 renderStaff();
 } else {
 showToast(data.message || 'Lỗi hoán đổi vị trí nhân sự', 'error');
 }
 } catch (err) {
 showToast('Lỗi kết nối khi hoán đổi vị trí nhân sự', 'error');
 }
}

async function toggleStaffStatus(stylistId, currentStatus) {
 try {
 const res = await fetch(`/api/stylists/${stylistId}/status`, {
 method: 'PUT',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify({ trang_thai_ranh: !currentStatus })
 });
 const data = await res.json();
 if (data.success) {
 showToast(data.message, 'success');
 loadStaff();
 loadAppointments();
 }
 } catch (err) {
 showToast('Lỗi cập nhật trạng thái', 'error');
 }
}

// ====================================================================
// ACCOUNT MANAGEMENT SYSTEM (ADMIN ONLY)
// ====================================================================
async function loadAccounts() {
 const tbody = document.getElementById('accounts-table-tbody');
 if (tbody) {
 tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 1.5rem;">Đang tải danh sách tài khoản...</td></tr>';
 }

 try {
 const res = await authFetch('/api/accounts');
 const data = await res.json();
 if (data.success && Array.isArray(data.accounts)) {
 state.accounts = data.accounts;
 renderAccounts();
 } else {
 if (tbody) tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:var(--accent-rose);">${data.error || data.message || 'Không thể tải danh sách tài khoản'}</td></tr>`;
 }
 } catch (err) {
 if (tbody) tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--accent-rose);">Lỗi kết nối máy chủ khi lấy dữ liệu tài khoản.</td></tr>';
 }
}

function renderAccounts() {
 const tbody = document.getElementById('accounts-table-tbody');
 const accounts = state.accounts || [];

 // Update statistics
 const totalEl = document.getElementById('stat-total-accounts');
 const adminEl = document.getElementById('stat-admin-accounts');
 const letanEl = document.getElementById('stat-letan-accounts');
 const thoEl = document.getElementById('stat-tho-accounts');

 if (totalEl) totalEl.innerText = accounts.length;
 if (adminEl) adminEl.innerText = accounts.filter(a => a.VaiTro === 'Admin').length;
 if (letanEl) letanEl.innerText = accounts.filter(a => a.VaiTro === 'LeTan').length;
 if (thoEl) thoEl.innerText = accounts.filter(a => a.VaiTro === 'Tho').length;

 if (!tbody) return;

 if (accounts.length === 0) {
 tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 1.5rem;">Chưa có tài khoản nào.</td></tr>';
 return;
 }

 tbody.innerHTML = accounts.map(acc => {
 let roleBadge = '';
 if (acc.VaiTro === 'Admin') {
 roleBadge = '<span class="badge" style="background:#ef4444;color:#fff;"> Quản Trị Viên (Admin)</span>';
 } else if (acc.VaiTro === 'LeTan') {
 roleBadge = '<span class="badge" style="background:#10b981;color:#fff;"> Lễ Tân & Thu Ngân</span>';
 } else {
 roleBadge = '<span class="badge" style="background:#3b82f6;color:#fff;">️ Thợ Làm Tóc (Tho)</span>';
 }

 const staffInfo = acc.HoTen 
 ? `<strong>${acc.HoTen}</strong> <span style="font-size:0.8rem;color:var(--gold-light);">(${acc.MaNhanVien || ''} - ${acc.ChucVu || ''})</span>`
 : '<span style="color:var(--text-muted);font-style:italic;">Chưa gán nhân sự (Tài khoản riêng)</span>';

 const phoneInfo = acc.SoDienThoai ? acc.SoDienThoai : '<span style="color:var(--text-muted);">-</span>';

 const isCurrentAcc = (acc.TenDangNhap === state.currentUser?.username);

 return `
 <tr>
 <td><span style="font-family:monospace;font-weight:700;color:var(--gold-primary);">${acc.MaTaiKhoan}</span></td>
 <td>
 <div style="font-weight:700;font-size:0.95rem;color:var(--text-primary);display:flex;align-items:center;gap:6px;">
 <span>${acc.TenDangNhap}</span>
 ${isCurrentAcc ? '<span class="badge badge-success" style="font-size:0.7rem;">Bạn đang dùng</span>' : ''}
 </div>
 </td>
 <td>${roleBadge}</td>
 <td>${staffInfo}</td>
 <td>${phoneInfo}</td>
 <td style="text-align: right;">
 <div style="display:flex;gap:0.35rem;justify-content:flex-end;align-items:center;">
 <button class="btn btn-sm btn-secondary" style="padding:3px 8px;font-size:0.78rem;" onclick="openChangePasswordModal('${acc.MaTaiKhoan}', '${acc.TenDangNhap}')" title="Đổi mật khẩu tài khoản">
 Đổi MK
 </button>
 ${!isCurrentAcc ? `
 <button class="btn btn-sm btn-danger" style="padding:3px 8px;font-size:0.78rem;" onclick="handleDeleteAccount('${acc.MaTaiKhoan}', '${acc.TenDangNhap}')" title="Xóa tài khoản này">
 ️ Xóa
 </button>
 ` : ''}
 </div>
 </td>
 </tr>
 `;
 }).join('');
}

function openNewAccountModal(preselectedStaffId = null) {
 const form = document.getElementById('form-account');
 if (form) form.reset();

 // Populate staff dropdown
 const staffSelect = document.getElementById('modal-acc-staff');
 if (staffSelect) {
 let html = '<option value="">-- Không liên kết (Tài khoản quản trị độc lập) --</option>';
 state.stylists.forEach(s => {
 const hasAcc = Boolean(s.TenDangNhap);
 const label = `${s.HoTen} (${s.MaNhanVien} - ${s.ChucVu})${hasAcc ? ` [Đã có TK: ${s.TenDangNhap}]` : ' [Chưa có tài khoản]'}`;
 html += `<option value="${s.MaNhanVien}" data-role="${s.ChucVu}" data-name="${s.HoTen}">${label}</option>`;
 });
 staffSelect.innerHTML = html;

 if (preselectedStaffId) {
 staffSelect.value = preselectedStaffId;
 handleAccStaffSelect(preselectedStaffId);
 }
 }

 openModal('modal-account');
}

function handleAccStaffSelect(staffId) {
 if (!staffId) return;
 const staff = state.stylists.find(s => s.MaNhanVien === staffId);
 if (!staff) return;

 const roleSelect = document.getElementById('modal-acc-role');
 if (roleSelect) {
 if (staff.ChucVu === 'Quản lý') roleSelect.value = 'Admin';
 else if (staff.ChucVu === 'Lễ tân') roleSelect.value = 'LeTan';
 else roleSelect.value = 'Tho';
 }

 const userField = document.getElementById('modal-acc-username');
 if (userField && !userField.value.trim()) {
 const cleanName = staff.HoTen.toLowerCase()
 .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
 .replace(/đ/g, 'd').replace(/[^a-z0-9]/g, '');
 userField.value = `${cleanName || 'user'}_${staff.MaNhanVien.toLowerCase()}`;
 }
}

function handleAccRoleChange(role) {
 // Extended role handler
}

async function handleCreateAccount(e) {
 e.preventDefault();
 const username = document.getElementById('modal-acc-username').value.trim();
 const password = document.getElementById('modal-acc-password').value.trim();
 const role = document.getElementById('modal-acc-role').value;
 const staffId = document.getElementById('modal-acc-staff').value;

 try {
 const res = await authFetch('/api/accounts', {
 method: 'POST',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify({
 ten_dang_nhap: username,
 mat_khau: password,
 vai_tro: role,
 ma_nhan_vien: staffId || null
 })
 });
 const data = await res.json();
 if (data.success) {
 showToast(data.message || 'Tạo tài khoản thành công!', 'success');
 closeModal('modal-account');
 await loadAccounts();
 await loadStylists();
 renderStaff();
 } else {
 showToast(data.message || 'Lỗi tạo tài khoản', 'error');
 }
 } catch (err) {
 showToast('Lỗi kết nối máy chủ khi tạo tài khoản', 'error');
 }
}

function openChangePasswordModal(accountId, username) {
 const accIdEl = document.getElementById('modal-pwd-account-id');
 const userEl = document.getElementById('modal-pwd-username');
 const passEl = document.getElementById('modal-pwd-new-pass');
 if (accIdEl) accIdEl.value = accountId;
 if (userEl) userEl.value = username;
 if (passEl) passEl.value = '';
 openModal('modal-account-password');
}

async function handleChangePasswordSubmit(e) {
 e.preventDefault();
 const accId = document.getElementById('modal-pwd-account-id').value;
 const newPass = document.getElementById('modal-pwd-new-pass').value.trim();

 if (!newPass || newPass.length < 4) {
 showToast('Mật khẩu mới phải có ít nhất 4 ký tự.', 'warning');
 return;
 }

 try {
 const res = await authFetch(`/api/accounts/${accId}`, {
 method: 'PUT',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify({ mat_khau: newPass })
 });
 const data = await res.json();
 if (data.success) {
 showToast(data.message || 'Đổi mật khẩu thành công!', 'success');
 closeModal('modal-account-password');
 } else {
 showToast(data.message || 'Lỗi đổi mật khẩu', 'error');
 }
 } catch (err) {
 showToast('Lỗi kết nối khi đổi mật khẩu', 'error');
 }
}

async function handleDeleteAccount(accountId, username) {
 if (!confirm(`Bạn có chắc chắn muốn xóa tài khoản "${username}" (${accountId}) không? Thao tác này không thể hoàn tác.`)) {
 return;
 }

 try {
 const res = await authFetch(`/api/accounts/${accountId}`, {
 method: 'DELETE'
 });
 const data = await res.json();
 if (data.success) {
 showToast(data.message || 'Đã xóa tài khoản thành công', 'success');
 await loadAccounts();
 await loadStylists();
 renderStaff();
 } else {
 showToast(data.message || 'Lỗi khi xóa tài khoản', 'error');
 }
 } catch (err) {
 showToast('Lỗi kết nối máy chủ khi xóa tài khoản', 'error');
 }
}

// ====================================================================
// VIEW CUSTOMER HISTORY MODAL (UC002)
// ====================================================================
async function viewCustomerHistory(customerId) {
 const cust = state.customers.find(c => c.ma_khach_hang === customerId);
 const container = document.getElementById('modal-history-content');
 if (!container) return;

 container.innerHTML = `<em>Đang tải lịch sử phục vụ...</em>`;
 openModal('modal-history');

 try {
 const res = await fetch(`/api/customers/${customerId}/history`);
 const data = await res.json();

 if (!data.success || data.history.length === 0) {
 container.innerHTML = `
 <div style="padding: 1.5rem; text-align: center; color: var(--text-muted);" class="glass">
 Khách hàng <strong>${cust ? cust.ho_ten : ''}</strong> chưa có lịch sử làm tóc nào tại salon.
 </div>
 `;
 return;
 }

 container.innerHTML = `
 <div style="margin-bottom: 1rem;">
 <strong style="font-size: 1.1rem; color: var(--text-primary);">Khách hàng: ${cust ? cust.ho_ten : ''}</strong>
 <div style="font-size: 0.85rem; color: var(--text-muted);">SĐT: ${cust && cust.so_dien_thoai ? cust.so_dien_thoai : 'Khách vãng lai'}</div>
 </div>
 <div style="display: flex; flex-direction: column; gap: 0.75rem; max-height: 400px; overflow-y: auto;">
 ${data.history.map(h => `
 <div class="glass" style="padding: 1rem; border-left: 3px solid var(--gold-primary);">
 <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
 <span style="font-weight: 700; color: var(--gold-light);"> ${h.NgayGioHen}</span>
 ${getStatusBadge(h.TrangThai)}
 </div>
 <div style="font-size: 0.85rem;">Thợ phụ trách: <strong>${h.TenThợ}</strong></div>
 <div style="font-size: 0.85rem; margin-top: 4px; color: var(--text-secondary);">
 Dịch vụ: ${(h.dich_vu || []).map(d => `${d.TenDichVu} (${formatCurrency(d.GiaTaiThoiDiemDat)})`).join(', ')}
 </div>
 ${h.ThanhTien ? `
 <div style="margin-top: 4px; font-size: 0.85rem; color: var(--accent-emerald);">
 Hóa đơn: <strong>${h.MaHoaDon}</strong> - Đã thanh toán: <strong>${formatCurrency(h.ThanhTien)}</strong>
 </div>
 ` : ''}
 </div>
 `).join('')}
 </div>
 `;
 } catch (err) {
 container.innerHTML = `<span style="color:var(--accent-rose);">Lỗi khi tải lịch sử.</span>`;
 }
}

// ====================================================================
// EXPORT REPORT CSV (UC007)
// ====================================================================
function exportReportCSV() {
 const startDate = document.getElementById('report-start-date').value;
 const endDate = document.getElementById('report-end-date').value;

 if (startDate && endDate && startDate > endDate) {
 showToast('Khoảng thời gian không hợp lệ: Ngày bắt đầu phải nhỏ hơn ngày kết thúc (UC007 Flow A1)!', 'error');
 return;
 }

 let url = '/api/reports/export?';
 if (startDate) url += `start_date=${encodeURIComponent(startDate)}&`;
 if (endDate) url += `end_date=${encodeURIComponent(endDate)}&`;

 window.open(url, '_blank');
 showToast('Đang tải xuống báo cáo doanh thu CSV...', 'success');
}

// ====================================================================
// FLOATING AI CHATBOT SYSTEM (ACCESSIBLE & MODERN CONVERSATIONAL UX)
// ====================================================================
function toggleAIChatDrawer() {
 const drawer = document.getElementById('ai-chat-drawer');
 if (!drawer) return;
 const isShown = drawer.style.display === 'flex';
 drawer.style.display = isShown ? 'none' : 'flex';
 if (!isShown) {
 document.getElementById('ai-chat-input')?.focus();
 const msgContainer = document.getElementById('ai-chat-messages');
 if (msgContainer) msgContainer.scrollTop = msgContainer.scrollHeight;
 }
}

function sendQuickPrompt(promptText) {
 const input = document.getElementById('ai-chat-input');
 if (input) {
 input.value = promptText;
 handleSendAIChat(new Event('submit'));
 }
}

function clearAIChatHistory() {
 aiChatSessionHistory = [];
 saveAIConversationHistories();
 const msgContainer = document.getElementById('ai-chat-messages');
 if (!msgContainer) return;

 msgContainer.innerHTML = `
 <div class="chat-message-row bot-row">
 <div class="chat-avatar bot-avatar">️</div>
 <div class="chat-bubble-ai">
 <div class="chat-sender-tag">Trợ Lý AI Salon Hair Hà Minh</div>
 <div class="chat-bubble-body">
 Xin chào Quý khách! Em là <strong>Trợ lý AI Salon Hair Hà Minh 24/7</strong> <br><br>
 Hội thoại đã được làm mới. Em sẵn sàng hỗ trợ Quý khách:
 <div class="ai-list-item"><span class="ai-bullet"></span> <strong>Tư vấn tạo kiểu & màu nhuộm</strong> tôn nét mặt và tone da.</div>
 <div class="ai-list-item"><span class="ai-bullet"></span> <strong>Khám sức khỏe tóc</strong> & đưa phác đồ phục hồi hư tổn, cháy mủn.</div>
 <div class="ai-list-item"><span class="ai-bullet"></span> <strong>Tra cứu bảng giá, lịch thợ rảnh</strong> và quản lý cuộc hẹn.</div>
 <br>Quý khách hãy chọn câu hỏi gợi ý hoặc gửi thắc mắc bất kỳ nhé!
 </div>
 <div class="chat-bubble-actions">
 <button type="button" class="chat-copy-btn" onclick="copyChatText(this)"> Sao chép</button>
 </div>
 </div>
 </div>
 `;
 showToast('Đã làm mới cuộc hội thoại AI', 'info');
}

function formatAIReply(rawText) {
 if (!rawText) return '';
 // Convert markdown bold **text**
 let formatted = rawText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
 
 // Format bullet lines starting with • or - or *
 const lines = formatted.split('\n');
 const processedLines = lines.map(line => {
 const trimmed = line.trim();
 if (trimmed.startsWith('• ') || trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
 const content = trimmed.substring(2);
 return `<div class="ai-list-item"><span class="ai-bullet"></span> <span>${content}</span></div>`;
 }
 return line;
 });

 formatted = processedLines.join('<br>');
 // Clean up multiple line breaks
 formatted = formatted.replace(/(<br>\s*){3,}/g, '<br><br>');
 return formatted;
}

function copyChatText(btn) {
 const bubble = btn.closest('.chat-bubble-ai');
 if (!bubble) return;
 const body = bubble.querySelector('.chat-bubble-body');
 const textToCopy = body ? body.innerText : bubble.innerText;
 
 navigator.clipboard.writeText(textToCopy).then(() => {
 const originalText = btn.innerHTML;
 btn.innerHTML = ' Đã chép!';
 btn.style.color = 'var(--accent-emerald)';
 setTimeout(() => {
 btn.innerHTML = originalText;
 btn.style.color = '';
 }, 2000);
 }).catch(() => {
 showToast('Không thể sao chép văn bản', 'error');
 });
}

async function handleSendAIChat(e) {
 if (e && e.preventDefault) e.preventDefault();
 const input = document.getElementById('ai-chat-input');
 if (!input) return;
 const message = input.value.trim();
 if (!message) return;

 const msgContainer = document.getElementById('ai-chat-messages');

 // Format current time
 const now = new Date();
 const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;

 // Append User Row
 const userRow = document.createElement('div');
 userRow.className = 'chat-message-row user-row';
 userRow.innerHTML = `
 <div class="chat-bubble-user">
 <div class="chat-bubble-text">${escapeHTML(message)}</div>
 <div style="font-size:0.68rem;opacity:0.75;text-align:right;margin-top:4px;">${timeStr}</div>
 </div>
 <div class="chat-avatar user-avatar" title="Bạn"></div>
 `;
 msgContainer.appendChild(userRow);

 input.value = '';
 msgContainer.scrollTop = msgContainer.scrollHeight;

 // Append Typing Indicator Row
 const typingRow = document.createElement('div');
 typingRow.className = 'chat-message-row bot-row chat-typing-row';
 typingRow.id = 'ai-chat-typing-indicator';
 typingRow.innerHTML = `
 <div class="chat-avatar bot-avatar">️</div>
 <div class="typing-dots">
 <div class="typing-dot"></div>
 <div class="typing-dot"></div>
 <div class="typing-dot"></div>
 </div>
 <span style="font-size:0.78rem;color:var(--text-muted);">AI đang phân tích & tra cứu CSDL...</span>
 `;
 msgContainer.appendChild(typingRow);
 msgContainer.scrollTop = msgContainer.scrollHeight;

 // Push user turn to history (keep max 12 turns)
 aiChatSessionHistory.push({ role: 'user', parts: [{ text: message }] });
 if (aiChatSessionHistory.length > 12) aiChatSessionHistory = aiChatSessionHistory.slice(-12);
 saveAIConversationHistories();

 try {
 const res = await authFetch('/api/ai/chat', {
 method: 'POST',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify({ message, history: aiChatSessionHistory })
 });
 const data = await res.json();

 // Remove typing indicator
 const indicator = document.getElementById('ai-chat-typing-indicator');
 if (indicator) indicator.remove();

 if (data.data_updated || data.price_updated) {
 refreshAppViewsOnAIAction(data.action_data);
 }

 // Append AI Bot Row
 const botRow = document.createElement('div');
 botRow.className = 'chat-message-row bot-row';

 let replyHtml = '';
 if (data.success && data.reply) {
 aiChatSessionHistory.push({ role: 'model', parts: [{ text: data.reply }] });
 saveAIConversationHistories();
 replyHtml = formatAIReply(data.reply);
 } else {
 replyHtml = data.message || 'Xin lỗi, trợ lý AI đang bận. Quý khách vui lòng thử lại sau ít phút.';
 }

 botRow.innerHTML = `
 <div class="chat-avatar bot-avatar">️</div>
 <div class="chat-bubble-ai">
 <div class="chat-sender-tag">Trợ Lý AI Salon Hair Hà Minh</div>
 <div class="chat-bubble-body">${replyHtml}</div>
 <div class="chat-bubble-actions">
 <button type="button" class="chat-copy-btn" onclick="copyChatText(this)"> Sao chép</button>
 </div>
 </div>
 `;
 msgContainer.appendChild(botRow);

 } catch (err) {
 const indicator = document.getElementById('ai-chat-typing-indicator');
 if (indicator) indicator.remove();

 const botRow = document.createElement('div');
 botRow.className = 'chat-message-row bot-row';
 botRow.innerHTML = `
 <div class="chat-avatar bot-avatar">️</div>
 <div class="chat-bubble-ai" style="border-color:var(--accent-rose-border);background:#fff1f2;">
 <div class="chat-sender-tag" style="color:var(--accent-rose);">Thông Báo Kết Nối</div>
 <div class="chat-bubble-body" style="color:#9f1239;">
 Không thể kết nối đến máy chủ AI. Quý khách vui lòng kiểm tra mạng hoặc thử lại.
 </div>
 </div>
 `;
 msgContainer.appendChild(botRow);
 } finally {
 msgContainer.scrollTop = msgContainer.scrollHeight;
 }
}

// ====================================================================
// AI ENGINE CONFIGURATION & API KEY SETTINGS
// ====================================================================
async function openAIConfigModal() {
 openModal('modal-ai-config');
 const statusEl = document.getElementById('ai-config-current-status');
 const keyInput = document.getElementById('ai-config-gemini-key');
 const modelSelect = document.getElementById('ai-config-gemini-model');
 const testBox = document.getElementById('ai-config-test-box');

 if (testBox) testBox.style.display = 'none';
 if (statusEl) statusEl.innerHTML = '<em>Đang tải thông tin cấu hình AI...</em>';

 try {
 const res = await fetch('/api/ai/config');
 const data = await res.json();
 if (data.success && data.config) {
 const cfg = data.config;
 if (modelSelect && cfg.model_name) modelSelect.value = cfg.model_name;
 if (keyInput) keyInput.placeholder = cfg.has_gemini_key ? `Đã lưu key (${cfg.masked_key})` : 'Nhập Google Gemini API Key (AIza...)';

 if (statusEl) {
 if (cfg.has_gemini_key) {
 statusEl.innerHTML = `
 <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
 <span class="badge badge-success"> Google Gemini Cloud AI</span>
 <span style="font-size:0.85rem;color:var(--text-secondary);">Mô hình: <strong>${escapeHTML(cfg.model_name)}</strong> • Key: <code>${escapeHTML(cfg.masked_key)}</code></span>
 </div>
 `;
 } else {
 statusEl.innerHTML = `
 <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
 <span class="badge badge-info"> Grounded SQLite Engine</span>
 <span style="font-size:0.85rem;color:var(--text-secondary);">Chuyên gia Salon nội bộ sẵn sàng 100% dữ liệu SQLite</span>
 </div>
 `;
 }
 }
 }
 } catch (err) {
 if (statusEl) statusEl.innerHTML = '<span style="color:var(--accent-rose);"> Lỗi tải cấu hình</span>';
 }
}

async function handleSaveAIConfig(e) {
 if (e && e.preventDefault) e.preventDefault();
 const keyInput = document.getElementById('ai-config-gemini-key');
 const modelSelect = document.getElementById('ai-config-gemini-model');
 const testBox = document.getElementById('ai-config-test-box');
 const saveBtn = document.getElementById('ai-config-save-btn');

 const apiKey = keyInput ? keyInput.value.trim() : '';
 const modelName = modelSelect ? modelSelect.value : 'gemini-1.5-flash';

 if (saveBtn) {
 saveBtn.disabled = true;
 saveBtn.innerText = ' Đang lưu & kiểm tra...';
 }

 try {
 const res = await fetch('/api/ai/config', {
 method: 'POST',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify({ api_key: apiKey, model_name: modelName })
 });
 const data = await res.json();

 if (data.success) {
 showToast('Đã cập nhật cấu hình AI thành công!', 'success');
 if (testBox) {
 testBox.style.display = 'block';
 if (data.config && data.config.test_result) {
 const tr = data.config.test_result;
 testBox.innerHTML = `
 <div style="padding:10px;border-radius:8px;background:${tr.connected ? '#ecfdf5' : '#fffbeb'};border:1px solid ${tr.connected ? '#10b981' : '#f59e0b'};font-size:0.85rem;">
 <strong>${tr.connected ? ' Kết Nối Thành Công' : '️ Thông Tin Kết Nối'}:</strong> ${escapeHTML(tr.message)}
 ${tr.sample_reply ? `<div style="margin-top:6px;font-size:0.8rem;color:#047857;"><em>Phản hồi mẫu: "${escapeHTML(tr.sample_reply)}"</em></div>` : ''}
 </div>
 `;
 } else {
 testBox.innerHTML = `
 <div style="padding:10px;border-radius:8px;background:#ecfdf5;border:1px solid #10b981;font-size:0.85rem;color:#047857;">
 Đã lưu cấu hình! Hệ thống sử dụng: <strong>${escapeHTML(data.config.provider)}</strong>.
 </div>
 `;
 }
 }
 openAIConfigModal();
 } else {
 showToast(data.message || 'Lỗi cập nhật cấu hình', 'error');
 }
 } catch (err) {
 showToast('Lỗi máy chủ khi lưu cấu hình AI', 'error');
 } finally {
 if (saveBtn) {
 saveBtn.disabled = false;
 saveBtn.innerText = ' Lưu Cấu Hình & Kiểm Tra';
 }
 }
}

async function resetToInternalAIEngine() {
 const keyInput = document.getElementById('ai-config-gemini-key');
 if (keyInput) keyInput.value = '';
 await handleSaveAIConfig(null);
 showToast('Đã chuyển về Chuyên Gia Nội Bộ (Grounded SQLite)', 'info');
}

async function testAIConnection() {
 const keyInput = document.getElementById('ai-config-gemini-key');
 const modelSelect = document.getElementById('ai-config-gemini-model');
 const testBox = document.getElementById('ai-config-test-box');

 const apiKey = keyInput ? keyInput.value.trim() : '';
 const modelName = modelSelect ? modelSelect.value : 'gemini-1.5-flash';

 if (testBox) {
 testBox.style.display = 'block';
 testBox.innerHTML = '<em> Đang kiểm tra kết nối API...</em>';
 }

 try {
 const res = await fetch('/api/ai/test-connection', {
 method: 'POST',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify({ api_key: apiKey, model_name: modelName })
 });
 const data = await res.json();
 if (data.success && data.result) {
 const r = data.result;
 if (testBox) {
 testBox.innerHTML = `
 <div style="padding:10px;border-radius:8px;background:${r.connected ? '#ecfdf5' : '#fff1f2'};border:1px solid ${r.connected ? '#10b981' : '#f43f5e'};font-size:0.85rem;color:${r.connected ? '#047857' : '#be123c'};">
 <strong>${r.connected ? ' Kết Nối Thành Công' : ' Kết Nối Thất Bại'}:</strong> ${escapeHTML(r.message)}
 ${r.sample_reply ? `<div style="margin-top:4px;font-size:0.8rem;color:#047857;"><em>Phản hồi mẫu: "${escapeHTML(r.sample_reply)}"</em></div>` : ''}
 </div>
 `;
 }
 }
 } catch (err) {
 if (testBox) {
 testBox.innerHTML = '<div style="padding:10px;border-radius:8px;background:#fff1f2;border:1px solid #f43f5e;font-size:0.85rem;color:#be123c;">Lỗi kết nối máy chủ backend.</div>';
 }
 }
}

// Quick toggle stylist availability
async function toggleStylistStatusDirectly(staffId, currentStatus) {
 try {
 const res = await fetch(`/api/stylists/${staffId}/status`, {
 method: 'PUT',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify({ trang_thai_ranh: !currentStatus })
 });
 const data = await res.json();
 if (data.success) {
 showToast('Đã đổi trạng thái thợ thành công', 'success');
 loadStylists();
 loadStaff();
 } else {
 showToast(data.message || 'Lỗi cập nhật', 'error');
 }
 } catch (err) {
 showToast('Lỗi máy chủ', 'error');
 }
}

// ====================================================================
// APPOINTMENTS TIMELINE SCHEDULER & VIEW TOGGLE (Luồng 2)
// ====================================================================
let apptViewMode = 'grid'; // 'grid' (timeline) or 'list'

function switchApptView(mode) {
 apptViewMode = mode;
 const btnGrid = document.getElementById('btn-view-grid');
 const btnList = document.getElementById('btn-view-list');
 const timelineView = document.getElementById('appointments-timeline-view');
 const listView = document.getElementById('appointments-list-view');

 if (btnGrid) btnGrid.classList.toggle('active', mode === 'grid');
 if (btnList) btnList.classList.toggle('active', mode === 'list');
 if (timelineView) timelineView.style.display = (mode === 'grid') ? 'block' : 'none';
 if (listView) listView.style.display = (mode === 'list') ? 'block' : 'none';

 if (mode === 'grid') {
 renderTimelineScheduler();
 } else {
 renderAppointments();
 }
}

function renderTimelineScheduler() {
 const container = document.getElementById('appointments-timeline-view');
 if (!container) return;

 const isTho = (state.currentRole === 'Tho');
 let activeStylists = [];

 if (isTho && state.currentUser && state.currentUser.ma_nhan_vien) {
 activeStylists = state.stylists.filter(s => s.MaNhanVien === state.currentUser.ma_nhan_vien);
 if (activeStylists.length === 0) {
 activeStylists = [{
 MaNhanVien: state.currentUser.ma_nhan_vien,
 HoTen: state.currentUser.fullName || 'Thợ Phục Vụ',
 ChucVu: state.currentUser.chuc_vu || 'Stylist'
 }];
 }
 } else {
 const stylists = state.stylists.filter(s => s.ChucVu.includes('Thợ') || s.ChucVu.includes('Stylist') || s.ChucVu.includes('Barber') || s.ChucVu.includes('Kỹ thuật'));
 activeStylists = stylists.length > 0 ? stylists : state.stylists;
 }

 const hours = ['08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00'];

 let headerHtml = `<div class="timeline-header-row"><div class="timeline-header-cell"> Giờ</div>`;
 activeStylists.forEach(s => {
 headerHtml += `
 <div class="timeline-header-cell">
 <div style="font-weight:700;">${s.HoTen}</div>
 <div style="font-size:0.72rem;color:var(--text-muted);font-weight:normal;">${s.ChucVu}</div>
 </div>
 `;
 });
 headerHtml += `</div>`;

 let rowsHtml = '';
 hours.forEach(hour => {
 rowsHtml += `<div class="timeline-slot-row"><div class="timeline-time-label">${hour}</div>`;
 activeStylists.forEach(s => {
 const apptsInSlot = state.appointments.filter(a => {
 if (a.MaNhanVien !== s.MaNhanVien) return false;
 const apptHour = (a.NgayGioHen || '').slice(11, 13) + ':00';
 return apptHour === hour;
 });

 rowsHtml += `<div class="timeline-slot-cell">`;
 if (apptsInSlot.length > 0) {
 apptsInSlot.forEach(a => {
 const inService = a.TrangThai === 'Đang phục vụ';
 const isDone = a.TrangThai === 'Hoàn thành';
 const isPending = a.TrangThai === 'Chờ xác nhận';
 const badgeClass = inService ? 'badge-primary' : (isDone ? 'badge-success' : (isPending ? 'badge-warning' : 'badge-info'));

 let clickAction = '';
 let actionTitle = '';
 if (isTho) {
 clickAction = `quickAISummary('${a.MaKhachHang}')`;
 actionTitle = `${a.TenKhachHang} (${a.TrangThai}) - Bấm xem AI tóm tắt chất tóc`;
 } else {
 clickAction = `startCheckout('${a.MaLichHen}')`;
 actionTitle = `${a.TenKhachHang} (${a.TrangThai}) - Bấm để thanh toán POS`;
 }

 rowsHtml += `
 <div class="timeline-appt-block ${inService ? 'in-service' : ''}" onclick="${clickAction}" title="${actionTitle}">
 <div style="font-weight:700;">${a.TenKhachHang}</div>
 <div style="font-size:0.72rem;opacity:0.9;">${(a.danh_sach_dich_vu || []).map(d => d.TenDichVu).join(', ') || 'Làm tóc'}</div>
 <div style="display:flex;justify-content:space-between;align-items:center;margin-top:2px;">
 <span class="badge ${badgeClass}" style="font-size:0.65rem;">${a.TrangThai}</span>
 <span style="font-size:0.7rem;color:var(--gold-light);">${formatCurrency(a.tong_chi_phi || 0)}</span>
 </div>
 </div>
 `;
 });
 } else {
 if (isTho) {
 rowsHtml += `<div style="height:100%;min-height:36px;opacity:0.25;" title="Khung giờ trống"></div>`;
 } else {
 rowsHtml += `<div style="height:100%;min-height:36px;opacity:0.25;cursor:pointer;" onclick="openNewAppointmentModal()" title="Khung giờ trống - Bấm để xếp lịch"></div>`;
 }
 }
 rowsHtml += `</div>`;
 });
 rowsHtml += `</div>`;
 });

 container.innerHTML = `<div class="timeline-scheduler">${headerHtml}${rowsHtml}</div>`;
}

// ====================================================================
// FAST POS COUNTER BILLING (Point of Sale Walk-in & Direct Check-out)
// ====================================================================
let posCart = [];

function renderPOSServiceCatalog(category = '') {
 const container = document.getElementById('pos-service-catalog');
 if (!container) return;

 const filtered = category ? state.services.filter(s => (s.mo_ta || '').includes(category) || (s.ten_dich_vu || '').includes(category)) : state.services;

 container.innerHTML = filtered.map(s => `
 <div class="pos-svc-card" onclick="addServiceToPOSCart('${s.ma_dich_vu}')">
 <div>
 <div class="pos-svc-title">${s.ten_dich_vu}</div>
 <div class="pos-svc-dur">️ ${s.thoi_gian_thuc_hien} phút</div>
 </div>
 <div style="display:flex;justify-content:space-between;align-items:center;margin-top:8px;">
 <div class="pos-svc-price">${formatCurrency(s.gia_tien)}</div>
 <button class="btn btn-secondary btn-sm" style="padding:2px 8px;font-size:0.75rem;">+ Thêm</button>
 </div>
 </div>
 `).join('');
}

function filterPOSCatalog(cat, btn) {
 document.querySelectorAll('.pos-cat-btn').forEach(b => b.classList.remove('active'));
 if (btn) btn.classList.add('active');
 renderPOSServiceCatalog(cat);
}

function populatePOSCustomerStylistSelects() {
 const custSelect = document.getElementById('pos-direct-customer');
 const stylistSelect = document.getElementById('pos-direct-stylist');

 if (custSelect) {
 const pendingAppointmentByCustomer = new Map();
 (state.appointments || [])
 .filter(appt => (
 !appt.MaHoaDon &&
 ['Đang phục vụ', 'Đã xác nhận'].includes(appt.TrangThai) &&
 (appt.danh_sach_dich_vu || []).length > 0
 ))
 .forEach(appt => {
 const current = pendingAppointmentByCustomer.get(appt.MaKhachHang);
 if (!current || String(appt.NgayGioHen) > String(current.NgayGioHen)) {
 pendingAppointmentByCustomer.set(appt.MaKhachHang, appt);
 }
 });

 const sortedCustomers = [...state.customers].sort((first, second) => {
 const firstAppointment = pendingAppointmentByCustomer.get(first.ma_khach_hang);
 const secondAppointment = pendingAppointmentByCustomer.get(second.ma_khach_hang);

 if (firstAppointment && !secondAppointment) return -1;
 if (!firstAppointment && secondAppointment) return 1;
 if (firstAppointment && secondAppointment) {
 return String(firstAppointment.NgayGioHen).localeCompare(String(secondAppointment.NgayGioHen));
 }
 return String(first.ho_ten).localeCompare(String(second.ho_ten), 'vi');
 });

 custSelect.innerHTML = `<option value="KH001">Khách vãng lai tại quầy (KH001)</option>` +
 sortedCustomers.map(c => {
 const appointment = pendingAppointmentByCustomer.get(c.ma_khach_hang);
 const appointmentLabel = appointment ? ` - Có lịch ${appointment.NgayGioHen.slice(0, 16)}` : '';
 return `<option value="${c.ma_khach_hang}">${c.ho_ten} (${c.so_dien_thoai || 'Vãng lai'})${appointmentLabel}</option>`;
 }).join('');
 }

 if (stylistSelect) {
 stylistSelect.innerHTML = state.stylists.map(s => `
 <option value="${s.MaNhanVien}" ${s.TrangThaiRanh ? '' : ''}>${s.HoTen} (${s.ChucVu}) - [${s.TrangThaiRanh ? 'Rảnh' : 'Bận'}]</option>
 `).join('');
 }
}

async function onPOSCustomerChanged() {
 const customerId = document.getElementById('pos-direct-customer')?.value;
 if (!customerId) return;

 const pendingAppointments = (state.appointments || [])
 .filter(appt => (
 appt.MaKhachHang === customerId &&
 !appt.MaHoaDon &&
 ['Đang phục vụ', 'Đã xác nhận'].includes(appt.TrangThai) &&
 (appt.danh_sach_dich_vu || []).length > 0
 ))
 .sort((first, second) => String(second.NgayGioHen).localeCompare(String(first.NgayGioHen)));

 if (pendingAppointments.length === 0) {
 state.selectedCheckoutAppt = null;
 posCart = [];
 renderPOSCart();
 showToast('Khách này chưa có lịch hẹn chờ thanh toán. Bạn có thể chọn dịch vụ mới.', 'info');
 return;
 }

 await selectCheckoutAppt(pendingAppointments[0].MaLichHen);
}

function addServiceToPOSCart(serviceId) {
 const svc = state.services.find(s => s.ma_dich_vu === serviceId);
 if (!svc) return;
 posCart.push(svc);
 renderPOSCart();
 showToast(`Đã thêm: ${svc.ten_dich_vu}`, 'info');
}

function removeServiceFromPOSCart(index) {
 posCart.splice(index, 1);
 renderPOSCart();
}

function clearPOSCart() {
 posCart = [];
 renderPOSCart();
}

function renderPOSCart() {
 const container = document.getElementById('pos-direct-cart-items');
 if (!container) return;

 if (posCart.length === 0) {
 container.innerHTML = `<div style="color:var(--text-muted);text-align:center;padding:2rem;">Chưa có dịch vụ nào trong phiếu.<br> Bấm chọn từ Menu dịch vụ bên trái để thêm.</div>`;
 document.getElementById('pos-direct-total').innerText = '0 đ';
 document.getElementById('pos-direct-final').innerText = '0 đ';
 return;
 }

 let total = 0;
 container.innerHTML = posCart.map((s, idx) => {
 total += s.gia_tien;
 return `
 <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px dashed var(--border-color);font-size:0.85rem;">
 <div>
 <strong style="color:var(--text-primary);">${s.ten_dich_vu}</strong>
 <div style="font-size:0.75rem;color:var(--text-muted);">${s.thoi_gian_thuc_hien} phút</div>
 </div>
 <div style="display:flex;align-items:center;gap:10px;">
 <strong style="color:var(--gold-light);">${formatCurrency(s.gia_tien)}</strong>
 <button onclick="removeServiceFromPOSCart(${idx})" style="background:none;border:none;color:var(--accent-rose);cursor:pointer;font-size:1.1rem;line-height:1;"></button>
 </div>
 </div>
 `;
 }).join('');

 const discount = Math.max(0, parseFloat(document.getElementById('pos-direct-discount')?.value || 0));
 const finalTotal = Math.max(0, total - discount);

 document.getElementById('pos-direct-total').innerText = formatCurrency(total);
 document.getElementById('pos-direct-final').innerText = formatCurrency(finalTotal);

 onPOSDirectMethodChanged();
}

function onPOSDirectMethodChanged() {
 const method = document.getElementById('pos-direct-method')?.value;
 const qrBox = document.getElementById('pos-direct-vietqr-box');
 const qrImg = document.getElementById('pos-direct-vietqr-img');
 if (!qrBox || !qrImg) return;

 if (method === 'Chuyển khoản') {
 const rawTotalText = document.getElementById('pos-direct-final')?.innerText || '0';
 const numAmount = parseInt(rawTotalText.replace(/\D/g, '')) || 0;
 qrImg.src = `https://img.vietqr.io/image/mbbank-0901234567-compact2.png?amount=${numAmount}&addInfo=POS%20HA%20MINH&accountName=HA%20MINH%20HAIR%20SALON`;
 qrBox.style.display = 'block';
 } else {
 qrBox.style.display = 'none';
 }
}

async function submitPOSDirectCheckout() {
 if (posCart.length === 0) {
 showToast('Vui lòng chọn ít nhất 1 dịch vụ để thanh toán', 'warning');
 return;
 }

 const discount = parseFloat(document.getElementById('pos-direct-discount')?.value || 0);
 const method = document.getElementById('pos-direct-method')?.value || 'Tiền mặt';

 try {
 let res, data;
 if (state.selectedCheckoutAppt && state.selectedCheckoutAppt.appointment) {
 const apptId = state.selectedCheckoutAppt.appointment.MaLichHen;
 res = await authFetch('/api/billing/checkout', {
 method: 'POST',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify({
 ma_lich_hen: apptId,
 giam_gia: discount,
 phuong_thuc_thanh_toan: method
 })
 });
 data = await res.json();
 state.selectedCheckoutAppt = null;
 } else {
 const custId = document.getElementById('pos-direct-customer')?.value || 'KH001';
 const stylistId = document.getElementById('pos-direct-stylist')?.value || 'NV004';
 const serviceIds = posCart.map(s => s.ma_dich_vu);

 res = await authFetch('/api/billing/pos-walkin', {
 method: 'POST',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify({
 ma_khach_hang: custId,
 ma_nhan_vien: stylistId,
 service_ids: serviceIds,
 giam_gia: discount,
 phuong_thuc_thanh_toan: method
 })
 });
 data = await res.json();
 }

 if (data.success) {
 showToast(' Thanh toán thành công & Đã xuất hóa đơn!', 'success');
 clearPOSCart();
 if (state.currentRole === 'Admin') {
 loadDashboard();
 loadReportsPage();
 }
 loadAppointments();
 loadBillingQueue();
 openReceiptModal(data.ma_hoa_don);
 } else {
 showToast(data.message || 'Lỗi xử lý thanh toán', 'error');
 }
 } catch (err) {
 showToast('Lỗi máy chủ khi thanh toán POS', 'error');
 }
}

// ====================================================================
// FINANCIAL REPORTS & INVOICES LEDGER PAGE
// ====================================================================
async function loadReportsPage() {
 if (state.currentRole !== 'Admin') return;

 const startDate = document.getElementById('report-page-start-date') ? document.getElementById('report-page-start-date').value : '';
 const endDate = document.getElementById('report-page-end-date') ? document.getElementById('report-page-end-date').value : '';
 const method = document.getElementById('report-page-method') ? document.getElementById('report-page-method').value : '';
 const stylistId = document.getElementById('report-page-stylist') ? document.getElementById('report-page-stylist').value : '';

 let url = '/api/reports/invoices?';
 if (startDate) url += `start_date=${encodeURIComponent(startDate)}&`;
 if (endDate) url += `end_date=${encodeURIComponent(endDate)}&`;
 if (method) url += `method=${encodeURIComponent(method)}&`;
 if (stylistId) url += `stylist_id=${encodeURIComponent(stylistId)}&`;

 try {
 const res = await authFetch(url);
 const data = await res.json();
 if (!data.success) return;

 const tbody = document.getElementById('report-invoices-tbody');
 if (!tbody) return;

 if (data.invoices.length === 0) {
 tbody.innerHTML = `<tr><td colspan="9" style="text-align:center;padding:2rem;color:var(--text-muted);">Không tìm thấy hóa đơn nào phù hợp bộ lọc.</td></tr>`;
 return;
 }

 tbody.innerHTML = data.invoices.map(inv => {
 const methodBadge = inv.PhuongThucThanhToan === 'Chuyển khoản' ? '<span class="badge badge-info"> VietQR</span>' :
 (inv.PhuongThucThanhToan === 'Thẻ' ? '<span class="badge badge-primary"> Thẻ POS</span>' : '<span class="badge badge-success"> Tiền mặt</span>');
 return `
 <tr>
 <td><strong style="color:var(--gold-light);font-family:monospace;">${inv.MaHoaDon}</strong></td>
 <td><span style="font-family:monospace;font-size:0.8rem;">${inv.MaLichHen}</span></td>
 <td>${inv.NgayTao}</td>
 <td><strong>${inv.TenKhachHang}</strong><div style="font-size:0.75rem;color:var(--text-muted);">${inv.SoDienThoai || 'Vãng lai'}</div></td>
 <td>${inv.TenTho}</td>
 <td>${methodBadge}</td>
 <td style="color:var(--text-muted);">${formatCurrency(inv.TongTien)}</td>
 <td><strong style="color:var(--accent-emerald);font-size:1.05rem;">${formatCurrency(inv.ThanhTien)}</strong></td>
 <td style="text-align: center;">
 <button class="btn btn-secondary btn-sm" style="padding: 2px 8px; font-size: 0.75rem;" onclick="openReceiptModal('${inv.MaHoaDon}')" title="Xem và in lại phiếu hóa đơn">️ In Phiếu</button>
 </td>
 </tr>
 `;
 }).join('');

 const countSpan = document.getElementById('report-invoices-count');
 if (countSpan) countSpan.innerText = `${data.count} hóa đơn`;

 const filterStylist = document.getElementById('report-page-stylist');
 if (filterStylist && filterStylist.options.length <= 1) {
 filterStylist.innerHTML = '<option value="">Tất cả Stylist</option>' + state.stylists.map(s => `<option value="${s.MaNhanVien}">${s.HoTen}</option>`).join('');
 }
 } catch (err) {
 console.error("Error loading reports page:", err);
 }
}

// --- AUTO ATTACH KEYDOWN & CLICK LISTENERS FOR AI ASSISTANT ---
document.addEventListener('DOMContentLoaded', () => {
 const chatInput = document.getElementById('ai-chat-input');
 if (chatInput) {
 chatInput.addEventListener('keydown', (e) => {
 if (e.key === 'Enter' && !e.shiftKey) {
 e.preventDefault();
 handleSendAIChat(e);
 }
 });
 }

 const hubInput = document.getElementById('ai-hub-custom-input');
 if (hubInput) {
 hubInput.addEventListener('keydown', (e) => {
 if (e.key === 'Enter' && !e.shiftKey) {
 e.preventDefault();
 handleAIHubDirectSubmit(e);
 }
 });
 }
});

// ====================================================================
// QUÊN MẬT KHẨU QUA ZALO ZNS HOẶC SMS SỐ ĐIỆN THOẠI (OTP VERIFICATION)
// ====================================================================
let forgotOtpCountdownTimer = null;

function openForgotPasswordModal() {
 closeModal('modal-login');
 const step1 = document.getElementById('forgot-step-1');
 const step2 = document.getElementById('forgot-step-2');
 const err1 = document.getElementById('forgot-step1-error');
 const err2 = document.getElementById('forgot-step2-error');
 if (step1) step1.style.display = 'block';
 if (step2) step2.style.display = 'none';
 if (err1) err1.style.display = 'none';
 if (err2) err2.style.display = 'none';
 const idInput = document.getElementById('forgot-identifier');
 if (idInput) {
 idInput.value = '';
 setTimeout(() => idInput.focus(), 200);
 }
 openModal('modal-forgot-password');
}

function onOtpChannelChange() {
 const channel = document.querySelector('input[name="otp_channel"]:checked')?.value || 'zalo';
 const lblZalo = document.getElementById('lbl-channel-zalo');
 const lblSms = document.getElementById('lbl-channel-sms');
 if (channel === 'zalo') {
 if (lblZalo) {
 lblZalo.style.border = '2px solid #ea580c';
 lblZalo.style.background = '#fff7ed';
 lblZalo.style.color = '#ea580c';
 lblZalo.style.fontWeight = '700';
 }
 if (lblSms) {
 lblSms.style.border = '1.5px solid #cbd5e1';
 lblSms.style.background = '#f8fafc';
 lblSms.style.color = '#475569';
 lblSms.style.fontWeight = '600';
 }
 } else {
 if (lblSms) {
 lblSms.style.border = '2px solid #ea580c';
 lblSms.style.background = '#fff7ed';
 lblSms.style.color = '#ea580c';
 lblSms.style.fontWeight = '700';
 }
 if (lblZalo) {
 lblZalo.style.border = '1.5px solid #cbd5e1';
 lblZalo.style.background = '#f8fafc';
 lblZalo.style.color = '#475569';
 lblZalo.style.fontWeight = '600';
 }
 }
}

function backToForgotStep1() {
 if (forgotOtpCountdownTimer) clearInterval(forgotOtpCountdownTimer);
 const step1 = document.getElementById('forgot-step-1');
 const step2 = document.getElementById('forgot-step-2');
 const err1 = document.getElementById('forgot-step1-error');
 if (step1) step1.style.display = 'block';
 if (step2) step2.style.display = 'none';
 if (err1) err1.style.display = 'none';
}

async function handleSendResetOTP() {
 const identifier = document.getElementById('forgot-identifier')?.value.trim();
 const channel = document.querySelector('input[name="otp_channel"]:checked')?.value || 'zalo';
 const errBox = document.getElementById('forgot-step1-error');
 const btnSend = document.getElementById('btn-send-otp');
 
 if (!identifier) {
 if (errBox) {
 errBox.innerText = '️ Vui lòng nhập Số điện thoại nhân viên của bạn.';
 errBox.style.display = 'block';
 }
 return;
 }
 if (errBox) errBox.style.display = 'none';
 if (btnSend) {
 btnSend.disabled = true;
 btnSend.innerText = ' Đang gửi mã OTP...';
 }

 try {
 const res = await fetch('/api/auth/forgot-password/request-otp', {
 method: 'POST',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify({ identifier, channel })
 });
 const data = await res.json();

 if (!data.success) {
 if (errBox) {
 errBox.innerText = data.message || 'Không tìm thấy số điện thoại nhân viên này trong hệ thống.';
 errBox.style.display = 'block';
 }
 if (btnSend) {
 btnSend.disabled = false;
 btnSend.innerText = ' Gửi Mã OTP Xác Thực';
 }
 return;
 }

 // Gửi thành công -> chuyển sang Bước 2
 document.getElementById('forgot-step-1').style.display = 'none';
 document.getElementById('forgot-step-2').style.display = 'block';
 
 const descEl = document.getElementById('forgot-otp-sent-desc');
 if (descEl) {
 const channelText = data.channel === 'zalo' ? ' Zalo ZNS Official' : ' Tin nhắn SMS';
 let infoText = `Mã xác thực 6 số đã được gửi qua <strong>${channelText}</strong> tới số điện thoại <strong>${data.phone_masked}</strong>.`;
 if (data.otp_demo) {
 infoText += `<br><span style="display:inline-block; margin-top:6px; padding:3px 10px; background:#dbeafe; color:#1e40af; border-radius:6px; font-weight:700; font-size:0.88rem;"> Mã OTP thử nghiệm: ${data.otp_demo}</span>`;
 }
 descEl.innerHTML = infoText;
 }

 const otpInput = document.getElementById('forgot-otp-code');
 if (otpInput) {
 otpInput.value = '';
 otpInput.placeholder = 'Nhập 6 số mã OTP...';
 otpInput.focus();
 }

 // Đếm ngược 60s
 let timeLeft = 60;
 const btnResend = document.getElementById('btn-resend-otp');
 if (btnResend) {
 btnResend.disabled = true;
 btnResend.style.opacity = '0.6';
 if (forgotOtpCountdownTimer) clearInterval(forgotOtpCountdownTimer);
 forgotOtpCountdownTimer = setInterval(() => {
 timeLeft--;
 if (timeLeft <= 0) {
 clearInterval(forgotOtpCountdownTimer);
 btnResend.disabled = false;
 btnResend.style.opacity = '1';
 btnResend.innerText = 'Gửi lại mã';
 } else {
 btnResend.innerText = `Gửi lại mã (${timeLeft}s)`;
 }
 }, 1000);
 }

 showToast(data.message, 'success');
 } catch (err) {
 if (errBox) {
 errBox.innerText = 'Lỗi kết nối máy chủ khi gửi OTP: ' + err.message;
 errBox.style.display = 'block';
 }
 } finally {
 if (btnSend) {
 btnSend.disabled = false;
 btnSend.innerText = ' Gửi Mã OTP Xác Thực';
 }
 }
}

async function handleVerifyOTPAndResetPassword(e) {
 if (e) e.preventDefault();
 const identifier = document.getElementById('forgot-identifier')?.value.trim();
 const otp = document.getElementById('forgot-otp-code')?.value.trim();
 const newPassword = document.getElementById('forgot-new-password')?.value.trim();
 const confirmPassword = document.getElementById('forgot-confirm-password')?.value.trim();
 const errBox = document.getElementById('forgot-step2-error');

 if (errBox) errBox.style.display = 'none';

 if (!otp || otp.length < 6) {
 if (errBox) {
 errBox.innerText = '️ Vui lòng nhập đủ mã OTP 6 chữ số.';
 errBox.style.display = 'block';
 }
 return;
 }
 if (!newPassword || newPassword.length < 4) {
 if (errBox) {
 errBox.innerText = '️ Mật khẩu mới phải có tối thiểu 4 ký tự.';
 errBox.style.display = 'block';
 }
 return;
 }
 if (newPassword !== confirmPassword) {
 if (errBox) {
 errBox.innerText = '️ Mật khẩu xác nhận không khớp. Vui lòng nhập lại.';
 errBox.style.display = 'block';
 }
 return;
 }

 try {
 const res = await fetch('/api/auth/forgot-password/verify', {
 method: 'POST',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify({ identifier, otp, new_password: newPassword })
 });
 const data = await res.json();

 if (!data.success) {
 if (errBox) {
 errBox.innerText = data.message || 'Mã OTP không hợp lệ.';
 errBox.style.display = 'block';
 }
 return;
 }

 showToast(' ' + data.message, 'success');
 closeModal('modal-forgot-password');
 openLoginModal();
 const loginUser = document.getElementById('login-username');
 if (loginUser && data.username) loginUser.value = data.username;
 const loginPass = document.getElementById('login-password');
 if (loginPass) {
 loginPass.value = newPassword;
 loginPass.focus();
 }
 } catch (err) {
 if (errBox) {
 errBox.innerText = 'Lỗi hệ thống: ' + err.message;
 errBox.style.display = 'block';
 }
 }
}


// ====================================================================
// DYNAMIC DATE FILTERS INITIALIZATION (TODAY, YESTERDAY, TOMORROW)
// ====================================================================
function initDynamicDateFilters() {
  try {
    const now = new Date();
    const formatYMD = d => {
      const y = d.getFullYear();
      const m = String(d.getMonth() + 1).padStart(2, '0');
      const day = String(d.getDate()).padStart(2, '0');
      return `${y}-${m}-${day}`;
    };
    const formatDM = d => {
      const day = String(d.getDate()).padStart(2, '0');
      const m = String(d.getMonth() + 1).padStart(2, '0');
      return `${day}/${m}`;
    };

    const today = new Date(now);
    const tomorrow = new Date(now);
    tomorrow.setDate(tomorrow.getDate() + 1);
    const yesterday = new Date(now);
    yesterday.setDate(yesterday.getDate() - 1);

    const todayYMD = formatYMD(today);
    const tomorrowYMD = formatYMD(tomorrow);
    const yesterdayYMD = formatYMD(yesterday);

    // Update appointment date filter
    const filterDateSelect = document.getElementById('filter-date');
    if (filterDateSelect) {
      filterDateSelect.innerHTML = `
        <option value="${todayYMD}" selected>Hôm nay (${formatDM(today)})</option>
        <option value="${tomorrowYMD}">Ngày mai (${formatDM(tomorrow)})</option>
        <option value="${yesterdayYMD}">Hôm qua (${formatDM(yesterday)})</option>
        <option value="">Tất cả các ngày</option>
        <option value="custom">Chọn ngày khác...</option>
      `;
      filterDateSelect.value = todayYMD;
    }

    // Update dashboard default date inputs (First of month to today)
    const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
    const firstDayYMD = formatYMD(firstDayOfMonth);

    const repStart = document.getElementById('report-start-date');
    const repEnd = document.getElementById('report-end-date');
    if (repStart && !repStart.value) repStart.value = firstDayYMD;
    if (repEnd && !repEnd.value) repEnd.value = todayYMD;

    // Update report ledger default date inputs
    const repPageStart = document.getElementById('report-page-start-date');
    const repPageEnd = document.getElementById('report-page-end-date');
    if (repPageStart && !repPageStart.value) repPageStart.value = firstDayYMD;
    if (repPageEnd && !repPageEnd.value) repPageEnd.value = todayYMD;
  } catch (err) {
    console.error("Error initializing dynamic date filters:", err);
  }
}
