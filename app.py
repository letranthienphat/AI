# -*- coding: utf-8 -*-
import streamlit as st
import time, base64, json, requests, random, hashlib
from openai import OpenAI
from streamlit_js_eval import streamlit_js_eval
from datetime import datetime, timedelta

# --- [1] CẤU HÌNH HỆ THỐNG ---
CONFIG = {
    "NAME": "NEXUS OS GATEWAY",
    "CREATOR": "Thiên Phát",
    "MASTER_PASS": "nexus os gateway",
    "VERSION": "17.0 Pro",
    "FILE_DATA": "nexus_gateway_core.json"
}

# 🛑 KIỂM TRA SECRETS
try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS]
except:
    st.error("🛑 THIẾU SECRETS TRÊN STREAMLIT CLOUD!")
    st.stop()

st.set_page_config(page_title=CONFIG["NAME"], layout="wide", initial_sidebar_state="expanded")

# --- [2] ĐỊNH DANH THIẾT BỊ (FINGERPRINT) ---
def get_device_fp():
    ua = st.context.headers.get("User-Agent", "Unknown")
    return hashlib.sha256(ua.encode()).hexdigest()[:16]

# --- [3] ĐỒNG BỘ DỮ LIỆU GITHUB ---
def sync_io(data=None):
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{CONFIG['FILE_DATA']}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    res = requests.get(url, headers=headers)
    if data is None: # Tải về
        if res.status_code == 200:
            return json.loads(base64.b64decode(res.json()['content']).decode('utf-8'))
        return {
            "users": {CONFIG["CREATOR"]: CONFIG["MASTER_PASS"]},
            "blacklist": [], "pro_users": [], "pro_devices": [], "rem": {}, "files": {}, 
            "codes": {"PHAT2026": "VIP"}, "update_cfg": {"delay": 7, "latest": "18.0", "date": str(datetime.now().date())}
        }
    else: # Ghi lên
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, ensure_ascii=False).encode('utf-8')).decode('utf-8')
        requests.put(url, headers=headers, json={"message": "Nexus Ultimate Sync", "content": content, "sha": sha})

# --- [4] GIAO DIỆN & NỀN ---
def apply_ui():
    st.markdown("""<style>
    .stApp { background-image: url('https://images.unsplash.com/photo-1449824913935-59a10b8d2000?auto=format&fit=crop&w=1920&q=80'); background-size: cover; background-attachment: fixed; }
    h1, h2, h3, p, span, label, .stMarkdown { color: #111 !important; font-weight: 800 !important; text-shadow: 1px 1px 3px #22d3ee; }
    [data-testid="stHeader"] { visibility: hidden; }
    </style>""", unsafe_allow_html=True)
    
    if st.session_state.get('page') not in ["BOT_CHECK", "AUTH"]:
        with st.sidebar:
            st.markdown(f"### 🛡️ {CONFIG['NAME']}")
            is_pro = st.session_state.get('is_pro', False)
            st.info(f"Cấp độ: {'💎 PRO' if is_pro else '🆓 GUEST'}")
            if st.button("🏠 VỀ DASHBOARD", use_container_width=True):
                st.session_state.page = "DASHBOARD"; st.rerun()
            if st.button("🔌 ĐĂNG XUẤT", use_container_width=True):
                fp = get_device_fp()
                if fp in st.session_state.db["rem"]: del st.session_state.db["rem"][fp]
                sync_io(st.session_state.db)
                st.session_state.user = None; st.session_state.page = "AUTH"; st.rerun()

# --- [5] KHỞI ĐỘNG HỆ THỐNG ---
if 'boot' not in st.session_state:
    st.session_state.db = sync_io()
    st.session_state.page = "BOT_CHECK"
    st.session_state.user = None
    st.session_state.strikes = 0
    st.session_state.is_pro = False
    st.session_state.boot = True

apply_ui()
fp = get_device_fp()

# Kiểm tra Blacklist
if fp in st.session_state.db.get("blacklist", []):
    st.error("🛑 THIẾT BỊ BỊ CHẶN."); st.stop()

# --- [6] PHÁO ĐÀI BOT CHECK (3 LẦN THỬ) ---
if st.session_state.page == "BOT_CHECK":
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("<h2 style='text-align:center;'>SECURITY CHECK</h2>", unsafe_allow_html=True)
        scr_w = streamlit_js_eval(js_expressions="window.innerWidth", key="bot_monitor")
        is_human = st.checkbox("Tôi không phải là người máy")
        if st.button("TIẾP TỤC", use_container_width=True):
            if is_human and scr_w: st.session_state.page = "AUTH"; st.rerun()
            else:
                st.session_state.strikes += 1
                if st.session_state.strikes >= 3:
                    st.session_state.db["blacklist"].append(fp); sync_io(st.session_state.db)
                    st.error("🛑 ĐÃ KHÓA THIẾT BỊ."); st.stop()
                st.error(f"Xác thực thất bại lần {st.session_state.strikes}/3.")
    st.stop()

# AUTO-LOGIN & PRO RECOGNITION
if st.session_state.user is None and fp in st.session_state.db.get("rem", {}):
    st.session_state.user = st.session_state.db["rem"][fp]
    st.session_state.page = "DASHBOARD"

if st.session_state.user:
    if (st.session_state.user in st.session_state.db.get("pro_users", []) or fp in st.session_state.db.get("pro_devices", [])):
        st.session_state.is_pro = True

# --- [7] TRANG ĐĂNG NHẬP ---
if st.session_state.page == "AUTH":
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        st.markdown(f"<h1 style='text-align:center;'>{CONFIG['NAME']}</h1>", unsafe_allow_html=True)
        u = st.text_input("Username").strip()
        p = st.text_input("Password", type="password").strip()
        rem = st.checkbox("Ghi nhớ thiết bị")
        if st.button("TRUY CẬP", use_container_width=True):
            if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
                st.session_state.user = u
                if rem: st.session_state.db["rem"][fp] = u; sync_io(st.session_state.db)
                st.session_state.page = "DASHBOARD"; st.rerun()
            else: st.error("❌ Sai thông tin.")

# --- [8] DASHBOARD ---
elif st.session_state.page == "DASHBOARD":
    st.title(f"🚀 XIN CHÀO: {st.session_state.user}")
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("🧠 AI NEXUS"): st.session_state.page = "AI"; st.rerun()
    if c2.button("☁️ CLOUD DRIVE"): st.session_state.page = "CLOUD"; st.rerun()
    if c3.button("⚙️ CÀI ĐẶT"): st.session_state.page = "SETTINGS"; st.rerun()
    if c4.button("🛠️ ADMIN") and st.session_state.user == CONFIG["CREATOR"]:
        st.session_state.page = "ADMIN"; st.rerun()

# --- [9] AI NEXUS (THÔNG MINH) ---
elif st.session_state.page == "AI":
    st.header("🧠 TỔNG LÃNH AI NEXUS")
    if 'chat_log' not in st.session_state: st.session_state.chat_log = []
    for m in st.session_state.chat_log:
        with st.chat_message(m["role"]): st.write(m["content"])
    if prompt := st.chat_input("Nhập lệnh..."):
        st.session_state.chat_log.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.write(prompt)
        client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "system", "content": "Bạn là AI của NEXUS OS, phục vụ Thiên Phát."}] + st.session_state.chat_log[-5:])
        ans = res.choices[0].message.content
        st.session_state.chat_log.append({"role": "assistant", "content": ans})
        with st.chat_message("assistant"): st.write(ans)

# --- [10] CLOUD DRIVE ---
elif st.session_state.page == "CLOUD":
    st.header("☁️ NEXUS CLOUD STORAGE")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("📤 Tải lên")
        up = st.file_uploader("Chọn file (<1MB)")
        if up and st.button("LƯU TRỮ"):
            f_b64 = base64.b64encode(up.getvalue()).decode()
            st.session_state.db["files"][up.name] = {"data": f_b64, "size": up.size}
            sync_io(st.session_state.db); st.success("Xong!"); st.rerun()
    with col2:
        st.subheader("📁 Tệp tin")
        for n, i in st.session_state.db.get("files", {}).items():
            c_a, c_b, c_c = st.columns([3, 1, 1])
            c_a.write(f"📄 {n}")
            c_b.markdown(f'<a href="data:octet-stream;base64,{i["data"]}" download="{n}">📥</a>', unsafe_allow_html=True)
            if c_c.button("🗑️", key=n):
                del st.session_state.db["files"][n]; sync_io(st.session_state.db); st.rerun()

# --- [11] SETTINGS (NHẬP MÃ PRO & UPDATE) ---
elif st.session_state.page == "SETTINGS":
    st.header("⚙️ CÀI ĐẶT")
    t1, t2 = st.tabs(["💎 PRO CODE", "🆙 UPDATE"])
    with t1:
        if st.session_state.is_pro: st.success("💎 TRẠNG THÁI: PRO VĨNH VIỄN")
        else:
            code = st.text_input("Nhập mã 8 ký tự").upper()
            if st.button("KÍCH HOẠT PRO"):
                if code in st.session_state.db["codes"]:
                    st.session_state.db["pro_users"].append(st.session_state.user)
                    st.session_state.db["pro_devices"].append(fp)
                    sync_io(st.session_state.db); st.balloons(); st.rerun()
                else: st.error("Mã sai!")
    with t2:
        cfg = st.session_state.db["update_cfg"]
        st.write(f"Bản hiện tại: {CONFIG['VERSION']}")
        if st.button("KIỂM TRA"):
            wait = datetime.strptime(cfg["date"], "%Y-%m-%d") + timedelta(days=cfg["delay"])
            if st.session_state.is_pro or datetime.now() >= wait: st.success(f"Bản {cfg['latest']} đã sẵn sàng!")
            else: st.warning(f"Bản mới khóa đến {wait.date()} (Guest Delay).")

# --- [12] ADMIN ---
elif st.session_state.page == "ADMIN":
    st.header("🛠️ ADMIN CONTROL")
    st.subheader("🚫 Blacklist")
    st.write(st.session_state.db["blacklist"])
    if st.button("RESET BLACKLIST"):
        st.session_state.db["blacklist"] = []; sync_io(st.session_state.db); st.rerun()
    st.subheader("⚙️ Update Delay")
    d = st.slider("Số ngày delay", 0, 30, st.session_state.db["update_cfg"]["delay"])
    if st.button("LƯU DELAY"):
        st.session_state.db["update_cfg"]["delay"] = d; sync_io(st.session_state.db); st.success("Đã lưu!")
