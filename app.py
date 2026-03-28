# -*- coding: utf-8 -*-
import streamlit as st
import time, base64, json, requests, random, hashlib
from openai import OpenAI
from streamlit_js_eval import streamlit_js_eval
from datetime import datetime, timedelta

# --- [1] CẤU HÌNH LÕI ---
CONFIG = {
    "NAME": "NEXUS OS GATEWAY",
    "CREATOR": "Thiên Phát",
    "MASTER_PASS": "nexus os gateway",
    "VERSION": "15.9 Pro",
    "FILE_DATA": "nexus_gateway_data.json"
}

# 🛑 KIỂM TRA SECRETS KHẮT KHE
try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS]
except Exception as e:
    st.error("🛑 HỆ THỐNG ĐÌNH CHỈ: Thiếu cấu hình Secrets trên Streamlit Cloud.")
    st.stop()

st.set_page_config(page_title=CONFIG["NAME"], layout="wide", initial_sidebar_state="expanded")

# --- [2] FINGERPRINT (ĐỊNH DANH THIẾT BỊ) ---
def get_device_fp():
    # Lấy thông tin thiết bị để khóa vĩnh viễn hoặc ghi nhớ đăng nhập
    ua = st.context.headers.get("User-Agent", "UnknownDevice")
    return hashlib.sha256(ua.encode()).hexdigest()[:16]

# --- [3] GIAO DIỆN & NÚT HOME (FIX LỖI RESET) ---
def apply_ui():
    st.markdown(f"""
    <style>
    .stApp {{
        background-image: url('https://images.unsplash.com/photo-1449824913935-59a10b8d2000?auto=format&fit=crop&w=1920&q=80');
        background-size: cover; background-attachment: fixed;
    }}
    h1, h2, h3, p, span, label, .stMarkdown {{
        color: #111 !important; font-weight: 800 !important;
        text-shadow: 1px 1px 3px #22d3ee;
    }}
    /* Giấu menu mặc định của Streamlit */
    [data-testid="stHeader"] {{ visibility: hidden; }}
    </style>
    """, unsafe_allow_html=True)
    
    # Dùng Sidebar làm nút Home tàng hình nhưng không bị reset trang
    with st.sidebar:
        st.markdown(f"### 🛡️ {CONFIG['NAME']}")
        if st.session_state.get('page') not in ["BOT_CHECK", "AUTH"]:
            if st.button("🏠 VỀ DASHBOARD", use_container_width=True):
                st.session_state.page = "DASHBOARD"
                st.rerun()
            if st.button("🔌 ĐĂNG XUẤT", use_container_width=True):
                fp = get_device_fp()
                if fp in st.session_state.db["rem"]:
                    del st.session_state.db["rem"][fp]
                    sync_io(st.session_state.db)
                st.session_state.user = None
                st.session_state.page = "AUTH"
                st.rerun()

# --- [4] KERNEL DỮ LIỆU CLOUD ---
def sync_io(data=None):
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{CONFIG['FILE_DATA']}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    if data is None: # TẢI DỮ LIỆU (GET)
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            try:
                return json.loads(base64.b64decode(res.json()['content']).decode('utf-8'))
            except: pass
        # Dữ liệu gốc nếu chưa có file
        return {
            "users": {CONFIG["CREATOR"]: CONFIG["MASTER_PASS"]},
            "blacklist": [], "pro_users": [], "rem": {}, "files": {}, "codes": {"PHAT2026": "PRO"},
            "update_cfg": {"delay": 7, "latest": "16.0", "date": str(datetime.now().date())}
        }
    else: # LƯU DỮ LIỆU (PUT)
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, ensure_ascii=False).encode('utf-8')).decode('utf-8')
        requests.put(url, headers=headers, json={"message": "Nexus Auto Sync", "content": content, "sha": sha})

# --- [5] KHỞI ĐỘNG HỆ THỐNG ---
if 'boot' not in st.session_state:
    st.session_state.db = sync_io()
    st.session_state.page = "BOT_CHECK"
    st.session_state.user = None
    st.session_state.strikes = 0 # Đếm số lần sai bot
    st.session_state.boot = True

apply_ui()
fp = get_device_fp()

# 🛑 KIỂM TRA FINGERPRINT BLACKLIST
if fp in st.session_state.db.get("blacklist", []):
    st.error("🛑 LỆNH CẤM TRUY CẬP: Thiết bị này đã bị khóa vĩnh viễn do vi phạm an ninh.")
    st.stop()

# --- [6] PHÁO ĐÀI ANTIBOT (3 LẦN THỬ) ---
if st.session_state.page == "BOT_CHECK":
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("<h2 style='text-align:center;'>🛡️ SECURITY GATEWAY</h2>", unsafe_allow_html=True)
        st.write("Hệ thống đang giám sát hành vi môi trường...")
        
        # JS lấy chiều rộng màn hình ngầm
        scr_w = streamlit_js_eval(js_expressions="window.innerWidth", key="bot_monitor")
        
        is_human = st.checkbox("Tôi không phải là người máy")
        if st.button("TIẾP TỤC", use_container_width=True):
            if is_human and scr_w: # Tick và là trình duyệt thật
                st.session_state.page = "AUTH"
                st.rerun()
            elif not scr_w:
                st.warning("⏳ Đang khởi tạo bộ đệm bảo mật, vui lòng đợi 1 giây rồi nhấn lại.")
            else:
                st.session_state.strikes += 1
                if st.session_state.strikes >= 3:
                    st.session_state.db["blacklist"].append(fp)
                    sync_io(st.session_state.db)
                    st.error("🛑 PHÁT HIỆN BOT! ĐÃ KHÓA THIẾT BỊ VĨNH VIỄN.")
                    st.stop()
                st.error(f"Xác thực thất bại! Cảnh báo lần {st.session_state.strikes}/3.")
    st.stop()

# TỰ ĐỘNG ĐĂNG NHẬP (AUTO-LOGIN)
if st.session_state.user is None and fp in st.session_state.db.get("rem", {}):
    st.session_state.user = st.session_state.db["rem"][fp]
    st.session_state.page = "DASHBOARD"

# --- [7] TRANG ĐĂNG NHẬP ---
if st.session_state.page == "AUTH":
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        st.markdown(f"<h1 style='text-align:center;'>{CONFIG['NAME']}</h1>", unsafe_allow_html=True)
        u = st.text_input("Định danh User").strip()
        p = st.text_input("Mật mã", type="password").strip()
        rem = st.checkbox("Ghi nhớ thiết bị này")
        
        if st.button("TRUY CẬP", use_container_width=True):
            if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
                st.session_state.user = u
                if rem: 
                    st.session_state.db["rem"][fp] = u
                    sync_io(st.session_state.db)
                st.session_state.page = "DASHBOARD"
                st.rerun()
            else: st.error("❌ Truy cập bị từ chối.")

# --- [8] DASHBOARD CHÍNH ---
elif st.session_state.page == "DASHBOARD":
    st.title(f"🚀 XIN CHÀO: {st.session_state.user}")
    st.write("Vui lòng chọn phân hệ thao tác:")
    
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("🧠 AI NEXUS", use_container_width=True): st.session_state.page = "AI"; st.rerun()
    if c2.button("☁️ CLOUD DRIVE", use_container_width=True): st.session_state.page = "CLOUD"; st.rerun()
    if c3.button("⚙️ CÀI ĐẶT", use_container_width=True): st.session_state.page = "SETTINGS"; st.rerun()
    if c4.button("🛠️ ADMIN", use_container_width=True):
        if st.session_state.user == CONFIG["CREATOR"]:
            st.session_state.page = "ADMIN"; st.rerun()
        else: st.error("Bạn không có quyền Admin.")

# --- [9] AI NEXUS (MƯỢT & NHỚ HỘI THOẠI) ---
elif st.session_state.page == "AI":
    st.header("🧠 TỔNG LÃNH AI NEXUS")
    if 'chat_log' not in st.session_state: st.session_state.chat_log = []
    
    for msg in st.session_state.chat_log:
        with st.chat_message(msg["role"]): st.write(msg["content"])
        
    if prompt := st.chat_input("Nhập lệnh..."):
        st.session_state.chat_log.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.write(prompt)
        
        try:
            client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": f"Bạn là AI của {CONFIG['NAME']}, phục vụ {CONFIG['CREATOR']}."}] + st.session_state.chat_log[-5:]
            )
            ans = res.choices[0].message.content
            st.session_state.chat_log.append({"role": "assistant", "content": ans})
            with st.chat_message("assistant"): st.write(ans)
        except Exception as e:
            st.error("Lỗi kết nối AI. Vui lòng thử lại.")

# --- [10] CLOUD DRIVE (TẢI LÊN / XÓA / TẢI XUỐNG) ---
elif st.session_state.page == "CLOUD":
    st.header("☁️ NEXUS CLOUD STORAGE")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📤 Tải tệp lên")
        up_file = st.file_uploader("Chọn tệp (Tối đa 1MB)")
        if up_file and st.button("LƯU TRỮ", use_container_width=True):
            if up_file.size > 1024 * 1024:
                st.error("Tệp quá lớn (>1MB). Github API từ chối.")
            else:
                f_64 = base64.b64encode(up_file.getvalue()).decode()
                st.session_state.db["files"][up_file.name] = {
                    "data": f_64, "size": up_file.size, "date": str(datetime.now().date())
                }
                sync_io(st.session_state.db)
                st.success("Tải lên thành công!")
                st.rerun()
                
    with col2:
        st.subheader("📁 Tệp của bạn")
        for fname, finfo in st.session_state.db.get("files", {}).items():
            c_a, c_b, c_c = st.columns([3, 1, 1])
            c_a.write(f"📄 {fname} ({finfo['size']//1024} KB)")
            # Tạo link tải
            href = f'<a href="data:application/octet-stream;base64,{finfo["data"]}" download="{fname}" style="color:#22d3ee;">📥 Tải</a>'
            c_b.markdown(href, unsafe_allow_html=True)
            if c_c.button("🗑️", key=f"del_{fname}"):
                del st.session_state.db["files"][fname]
                sync_io(st.session_state.db); st.rerun()

# --- [11] CÀI ĐẶT (PRO & CẬP NHẬT PHÂN TẦNG) ---
elif st.session_state.page == "SETTINGS":
    st.header("⚙️ CÀI ĐẶT HỆ THỐNG")
    t1, t2 = st.tabs(["💎 KÍCH HOẠT PRO", "🆙 CẬP NHẬT"])
    
    with t1:
        code = st.text_input("Nhập mã 8 ký tự").upper()
        if st.button("KÍCH HOẠT"):
            if code in st.session_state.db["codes"]:
                if st.session_state.user not in st.session_state.db["pro_users"]:
                    st.session_state.db["pro_users"].append(st.session_state.user)
                    sync_io(st.session_state.db)
                st.balloons(); st.success("💎 BẠN ĐÃ ĐƯỢC NÂNG CẤP LÊN BẢN PRO!")
            else: st.error("Mã không hợp lệ.")
            
    with t2:
        is_pro = st.session_state.user in st.session_state.db["pro_users"]
        cfg = st.session_state.db["update_cfg"]
        st.write(f"Phiên bản hiện tại: **{CONFIG['VERSION']}**")
        
        if st.button("KIỂM TRA CẬP NHẬT MỚI NHẤT"):
            release_date = datetime.strptime(cfg["date"], "%Y-%m-%d")
            free_date = release_date + timedelta(days=cfg["delay"])
            
            if is_pro or datetime.now() >= free_date:
                st.success(f"Bản V{cfg['latest']} đã sẵn sàng. Hệ thống sẽ tự cập nhật cấu hình.")
            else:
                st.warning(f"Bản V{cfg['latest']} đang ưu tiên cho PRO. Người dùng Free vui lòng đợi đến {free_date.date()}.")

# --- [12] ADMIN ĐIỀU KHIỂN ---
elif st.session_state.page == "ADMIN":
    st.header("🛠️ ADMIN GATEWAY")
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("🚫 Quản lý Blacklist")
        st.write(st.session_state.db["blacklist"])
        if st.button("XÓA TOÀN BỘ BLACKLIST"):
            st.session_state.db["blacklist"] = []
            sync_io(st.session_state.db); st.rerun()
            
    with c2:
        st.subheader("📦 Cấu hình Delay Update (Guest)")
        delay = st.number_input("Số ngày khóa bản mới với Guest", 0, 30, st.session_state.db["update_cfg"]["delay"])
        if st.button("LƯU THAY ĐỔI"):
            st.session_state.db["update_cfg"]["delay"] = delay
            sync_io(st.session_state.db); st.success("Đã áp dụng!")
