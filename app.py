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
    "VERSION": "18.0 Architect",
    "FILE_DATA": "nexus_gateway_final.json"
}

try:
    GH_TOKEN, GH_REPO = st.secrets["GH_TOKEN"], st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS]
except:
    st.error("🛑 THIẾU SECRETS TRÊN STREAMLIT CLOUD!")
    st.stop()

st.set_page_config(page_title=CONFIG["NAME"], layout="wide", initial_sidebar_state="expanded")

# --- [2] CÔNG CỤ HỖ TRỢ ---
def get_device_fp():
    ua = st.context.headers.get("User-Agent", "Unknown")
    return hashlib.sha256(ua.encode()).hexdigest()[:16]

def sync_io(data=None):
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{CONFIG['FILE_DATA']}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    res = requests.get(url, headers=headers)
    if data is None:
        if res.status_code == 200:
            return json.loads(base64.b64decode(res.json()['content']).decode('utf-8'))
        return {
            "users": {CONFIG["CREATOR"]: CONFIG["MASTER_PASS"]},
            "blacklist": [], "pro_users": [], "pro_devices": [], "rem": {}, "files": {}, 
            "codes": ["PHAT2026"], "chat_history": [],
            "update_cfg": {"delay": 7, "latest": "19.0", "date": str(datetime.now().date())}
        }
    else:
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, ensure_ascii=False).encode('utf-8')).decode('utf-8')
        requests.put(url, headers=headers, json={"message": "Nexus Architect Sync", "content": content, "sha": sha})

# --- [3] GIAO DIỆN NỀN ---
st.markdown("""<style>
.stApp { background-image: url('https://images.unsplash.com/photo-1449824913935-59a10b8d2000?auto=format&fit=crop&w=1920&q=80'); background-size: cover; background-attachment: fixed; }
h1, h2, h3, p, span, label, .stMarkdown { color: #111 !important; font-weight: 800 !important; text-shadow: 1px 1px 3px #22d3ee; }
[data-testid="stHeader"] { visibility: hidden; }
</style>""", unsafe_allow_html=True)

# --- [4] KHỞI CHẠY ---
if 'boot' not in st.session_state:
    st.session_state.db = sync_io()
    st.session_state.page = "BOT_CHECK"
    st.session_state.user = None
    st.session_state.strikes = 0
    st.session_state.boot = True

fp = get_device_fp()
if fp in st.session_state.db.get("blacklist", []):
    st.error("🛑 THIẾT BỊ ĐÃ BỊ CHẶN VĨNH VIỄN."); st.stop()

# TỰ ĐỘNG NHẬN DIỆN PRO & LOGIN
if st.session_state.user is None and fp in st.session_state.db.get("rem", {}):
    st.session_state.user = st.session_state.db["rem"][fp]
    st.session_state.page = "DASHBOARD"

is_pro = False
if st.session_state.user:
    if (st.session_state.user in st.session_state.db.get("pro_users", []) or fp in st.session_state.db.get("pro_devices", [])):
        is_pro = True

# --- [5] ĐIỀU HƯỚNG SIDEBAR ---
if st.session_state.page not in ["BOT_CHECK", "AUTH"]:
    with st.sidebar:
        st.markdown(f"### 🛡️ {CONFIG['NAME']}")
        st.info(f"User: {st.session_state.user}\n\nCấp: {'💎 PRO' if is_pro else '🆓 GUEST'}")
        if st.button("🏠 DASHBOARD", use_container_width=True): st.session_state.page = "DASHBOARD"; st.rerun()
        if st.button("🔌 ĐĂNG XUẤT", use_container_width=True):
            if fp in st.session_state.db["rem"]: del st.session_state.db["rem"][fp]
            sync_io(st.session_state.db)
            st.session_state.user = None; st.session_state.page = "AUTH"; st.rerun()

# --- [6] CÁC PHÂN HỆ TRANG ---

# BOT CHECK
if st.session_state.page == "BOT_CHECK":
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("<h2 style='text-align:center;'>SECURITY GATEWAY</h2>", unsafe_allow_html=True)
        scr_w = streamlit_js_eval(js_expressions="window.innerWidth", key="bot_monitor")
        chk = st.checkbox("Xác thực con người")
        if st.button("VÀO HỆ THỐNG", use_container_width=True):
            if chk and scr_w: st.session_state.page = "AUTH"; st.rerun()
            else:
                st.session_state.strikes += 1
                if st.session_state.strikes >= 3:
                    st.session_state.db["blacklist"].append(fp); sync_io(st.session_state.db); st.stop()
                st.error(f"Sai lỗi {st.session_state.strikes}/3")
    st.stop()

# LOGIN
elif st.session_state.page == "AUTH":
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        st.markdown(f"<h1 style='text-align:center;'>LOGIN</h1>", unsafe_allow_html=True)
        u = st.text_input("Username").strip()
        p = st.text_input("Password", type="password").strip()
        rem = st.checkbox("Ghi nhớ đăng nhập")
        if st.button("XÁC THỰC", use_container_width=True):
            if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
                st.session_state.user = u
                if rem: st.session_state.db["rem"][fp] = u; sync_io(st.session_state.db)
                st.session_state.page = "DASHBOARD"; st.rerun()
            else: st.error("Sai thông tin!")

# DASHBOARD
elif st.session_state.page == "DASHBOARD":
    st.title(f"🚀 TRUNG TÂM ĐIỀU KHIỂN")
    c = st.columns(4)
    if c[0].button("🧠 AI"): st.session_state.page = "AI"; st.rerun()
    if c[1].button("☁️ CLOUD"): st.session_state.page = "CLOUD"; st.rerun()
    if c[2].button("⚙️ SETTINGS"): st.session_state.page = "SETTINGS"; st.rerun()
    if c[3].button("🛠️ ADMIN") and st.session_state.user == CONFIG["CREATOR"]: st.session_state.page = "ADMIN"; st.rerun()

# AI NEXUS
elif st.session_state.page == "AI":
    st.header("🧠 AI NEXUS INTELLIGENCE")
    for m in st.session_state.db.get("chat_history", [])[-10:]:
        with st.chat_message(m["role"]): st.write(m["content"])
    if p := st.chat_input("Nhập lệnh..."):
        st.session_state.db["chat_history"].append({"role": "user", "content": p})
        with st.chat_message("user"): st.write(p)
        client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "system", "content": "Bạn là AI của NEXUS OS."}] + st.session_state.db["chat_history"][-5:])
        ans = res.choices[0].message.content
        st.session_state.db["chat_history"].append({"role": "assistant", "content": ans})
        sync_io(st.session_state.db); st.rerun()

# CLOUD (CÓ GIỚI HẠN FREE)
elif st.session_state.page == "CLOUD":
    st.header("☁️ NEXUS CLOUD STORAGE")
    user_files = {k: v for k, v in st.session_state.db["files"].items() if v.get("owner") == st.session_state.user}
    limit = 999 if is_pro else 2
    
    st.write(f"Sức chứa: {len(user_files)}/{'∞' if is_pro else 2} tệp.")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        if len(user_files) < limit:
            up = st.file_uploader("Tải lên (<1MB)")
            if up and st.button("LƯU TRỮ"):
                f_64 = base64.b64encode(up.getvalue()).decode()
                st.session_state.db["files"][up.name] = {"data": f_64, "size": up.size, "owner": st.session_state.user}
                sync_io(st.session_state.db); st.success("Đã lưu!"); st.rerun()
        else: st.warning("💎 Nâng cấp PRO để lưu trữ không giới hạn.")

    with col2:
        for n, i in user_files.items():
            c_a, c_b, c_c = st.columns([3, 1, 1])
            c_a.write(f"📄 {n}")
            c_b.markdown(f'<a href="data:octet-stream;base64,{i["data"]}" download="{n}">📥</a>', unsafe_allow_html=True)
            if c_c.button("🗑️", key=n):
                del st.session_state.db["files"][n]; sync_io(st.session_state.db); st.rerun()

# SETTINGS
elif st.session_state.page == "SETTINGS":
    st.header("⚙️ CÀI ĐẶT")
    t1, t2 = st.tabs(["💎 PRO CODE", "🆙 UPDATE"])
    with t1:
        if is_pro: st.success("💎 BẠN LÀ NGƯỜI DÙNG PRO")
        else:
            c = st.text_input("Mã Pro (8 ký tự)").upper()
            if st.button("KÍCH HOẠT"):
                if c in st.session_state.db["codes"]:
                    st.session_state.db["pro_users"].append(st.session_state.user)
                    st.session_state.db["pro_devices"].append(fp)
                    sync_io(st.session_state.db); st.balloons(); st.rerun()
                else: st.error("Mã sai!")

# ADMIN (FULL QUYỀN)
elif st.session_state.page == "ADMIN":
    st.header("🛠️ ADMIN GATEWAY")
    tab_a, tab_b, tab_c = st.tabs(["💬 CHAT MGMT", "🔑 CODE MGMT", "🚫 SECURITY"])
    with tab_a:
        st.subheader("Quản lý lịch sử hội thoại")
        st.write(f"Tổng số tin nhắn: {len(st.session_state.db['chat_history'])}")
        if st.button("XÓA TOÀN BỘ LỊCH SỬ CHAT"):
            st.session_state.db["chat_history"] = []
            sync_io(st.session_state.db); st.success("Đã dọn dẹp!"); st.rerun()
    with tab_b:
        st.subheader("Tạo mã PRO mới")
        new_code = st.text_input("Nhập mã muốn tạo (8 ký tự)").upper()
        if st.button("THÊM MÃ"):
            if len(new_code) == 8:
                st.session_state.db["codes"].append(new_code)
                sync_io(st.session_state.db); st.success(f"Đã thêm mã: {new_code}")
            else: st.error("Mã phải đúng 8 ký tự.")
        st.write("Mã hiện có:", st.session_state.db["codes"])
    with tab_c:
        if st.button("RESET BLACKLIST"):
            st.session_state.db["blacklist"] = []; sync_io(st.session_state.db); st.rerun()
