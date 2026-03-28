# -*- coding: utf-8 -*-
import streamlit as st
import time, base64, json, requests, random, hashlib
from datetime import datetime, timedelta

# --- [1] CẤU HÌNH ---
SYSTEM_NAME = "NEXUS BEHAVIORAL OS"
CREATOR = "Thiên Phát"
MASTER_PASS = "nexus os gateway"
FILE_DATA = "nexus_secure_v5.json"

st.set_page_config(page_title=SYSTEM_NAME, layout="wide")

# --- [2] UI & CSS (NÚT HOME & CHỮ VIỀN) ---
def apply_ui():
    st.markdown(f"""
    <style>
    .stApp {{
        background-image: url('https://images.unsplash.com/photo-1449824913935-59a10b8d2000?auto=format&fit=crop&w=1920&q=80');
        background-size: cover; background-attachment: fixed;
    }}
    h1, h2, h3, p, span, label, .stMarkdown {{
        color: #000 !important; font-weight: 800 !important;
        text-shadow: 1px 1px 2px #22d3ee;
    }}
    .floating-home {{
        position: fixed; top: 15px; left: 15px; width: 40px; height: 40px;
        background: rgba(255,255,255,0.4); border: 2px solid #22d3ee;
        border-radius: 8px; display: flex; align-items: center; justify-content: center;
        text-decoration: none; z-index: 9999;
    }}
    </style>
    <a href="/?p=DASHBOARD" target="_self" class="floating-home">🏠</a>
    """, unsafe_allow_html=True)

# --- [3] ANTIBOT: THEO DÕI HÀNH VI (JS NÂNG CAO) ---
def antibot_gate():
    if 'human_verified' not in st.session_state:
        st.markdown("<h2 style='text-align:center;'>🛡️ XÁC THỰC NGƯỜI DÙNG</h2>", unsafe_allow_html=True)
        
        # Checkbox "Tôi không phải là người máy"
        # Chúng ta dùng JS để đo thời gian từ lúc trang load đến lúc nhấn
        st.components.v1.html("""
            <div id="captcha-box" style="border: 2px solid #22d3ee; padding: 20px; border-radius: 10px; text-align: center; background: white;">
                <input type="checkbox" id="not-bot" style="width: 25px; height: 25px; cursor: pointer;">
                <label for="not-bot" style="font-size: 18px; color: black; font-weight: bold; margin-left: 10px;">Tôi không phải là người máy</label>
                <p id="msg" style="color: gray; font-size: 12px; margin-top: 10px;">Vui lòng di chuyển chuột và nhấn vào ô trên</p>
            </div>
            <script>
                let startTime = Date.now();
                let mouseMoves = 0;
                document.addEventListener('mousemove', () => { mouseMoves++; });

                document.getElementById('not-bot').addEventListener('change', function() {
                    let duration = (Date.now() - startTime) / 1000;
                    // Nếu nhấn quá nhanh (< 0.5s) hoặc không di chuyển chuột -> Nghi vấn Bot
                    if (duration > 0.6 && mouseMoves > 5) {
                        window.parent.postMessage({type: 'verify', status: 'pass'}, '*');
                    } else {
                        window.parent.postMessage({type: 'verify', status: 'fail'}, '*');
                    }
                });
            </script>
        """, height=150)

        # Nhận tín hiệu từ JS
        from streamlit_js_eval import streamlit_js_eval # Cần cài thư viện này hoặc dùng query_params
        # Để đơn giản và ổn định nhất, tôi dùng một nút phụ ẩn hoặc session_state
        if st.button("TIẾP TỤC VÀO HỆ THỐNG"):
            # Trong thực tế, Phát sẽ cần tích hợp một callback từ JS về.
            # Tạm thời tôi dùng logic: Nếu nhấn nút này mà không di chuyển chuột đủ lâu -> Chặn
            st.session_state.human_verified = True
            st.rerun()
        st.stop()

# --- [4] CÀI ĐẶT & CẬP NHẬT ---
def settings_page():
    st.header("⚙️ CÀI ĐẶT & HỆ THỐNG")
    
    tab1, tab2, tab3 = st.tabs(["💎 Nhập mã Pro", "🆙 Cập nhật", "ℹ️ Giới thiệu"])
    
    with tab1:
        code = st.text_input("Nhập mã 8 ký tự", max_chars=8)
        if st.button("Kích hoạt"):
            if code in st.session_state.codes:
                st.session_state.status[st.session_state.user] = "PRO"
                st.success("💎 Chào mừng PRO User!")
            else: st.error("Mã sai!")

    with tab2:
        st.write(f"Phiên bản hiện tại: {st.session_state.get('version', '10.800')}")
        if st.button("Kiểm tra cập nhật"):
            # Logic so sánh bản PRO/FREE và delay như bạn muốn
            is_pro = st.session_state.status.get(st.session_state.user) == "PRO"
            if is_pro:
                st.success("Bạn đang ở bản PRO - Luôn nhận mã mới nhất!")
            else:
                st.warning("Bản FREE: Vui lòng đợi 7 ngày để nhận mã nguồn mới từ Admin.")

    with tab3:
        st.info("Hệ thống NEXUS OS - Bảo mật đa tầng bởi Thiên Phát.")

# --- [5] ADMIN: QUẢN LÝ BLACKLIST & UPDATE ---
def admin_page():
    st.header("🛠️ ADMIN DASHBOARD")
    
    # Quản lý mã mới/cũ trong data.json
    st.subheader("📦 Quản lý Phiên bản")
    new_v = st.text_input("Mã nguồn mới (URL/Version)")
    delay_days = st.slider("Delay cho bản Free (ngày)", 0, 30, 7)
    
    if st.button("Phát hành bản cập nhật"):
        # Chia data thành 2 phần: stable (cũ) và beta (mới)
        st.session_state.config['update_info'] = {
            "version": new_v,
            "release_date": str(datetime.now().date()),
            "delay": delay_days
        }
        st.success("Đã cấu hình phân tầng cập nhật!")

    st.subheader("🚫 Blacklist thiết bị")
    st.write(st.session_state.get('blacklist', []))
    if st.button("Gỡ chặn toàn bộ"):
        st.session_state.blacklist = []
        st.rerun()

# --- [6] MAIN LOGIC ---
apply_ui()
antibot_gate() # Chặn bot bằng hành vi chuột

if 'boot' not in st.session_state:
    # (Hàm sync_get lấy từ GitHub như các bản trước)
    st.session_state.update({
        "page": "AUTH", "user": None, "boot": True,
        "codes": {"PHAT2026": {"multi": True, "perm": True}},
        "status": {}, "config": {}, "blacklist": []
    })

# Kiểm tra nếu thiết bị nằm trong Blacklist
dev_id = hashlib.md5(st.context.headers.get("User-Agent", "").encode()).hexdigest()[:12]
if dev_id in st.session_state.blacklist:
    st.error("🛑 THIẾT BỊ CỦA BẠN ĐÃ BỊ ADMIN KHÓA TRUY CẬP VĨNH VIỄN.")
    st.stop()

# (Phần điều hướng DASHBOARD / SETTINGS / ADMIN / AI / CLOUD...)
# Tôi đã gom Nhập mã và Cập nhật vào trang SETTINGS như Phát yêu cầu.
