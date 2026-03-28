# -*- coding: utf-8 -*-
import streamlit as st
import time, base64, json, requests, random, hashlib
from openai import OpenAI
from datetime import datetime

# --- [1] CẤU HÌNH HỆ THỐNG ---
CONFIG = {
    "NAME": "NEXUS PLATINUM OS",
    "CREATOR": "Thiên Phát",
    "FILE_DATA": "nexus_platinum_v30.json"
}

try:
    GH_TOKEN, GH_REPO = st.secrets["GH_TOKEN"], st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS]
except:
    st.error("🛑 THIẾU SECRETS TRÊN CLOUD!"); st.stop()

st.set_page_config(page_title=CONFIG["NAME"], layout="wide", initial_sidebar_state="collapsed")

# --- [2] KERNEL DỮ LIỆU ---
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
            "users": {CONFIG["CREATOR"]: "nexus2026"}, 
            "codes": ["VIP999"], "pro_users": [], "chats": [], "files": {}, "rem": {}
        }
    else:
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, ensure_ascii=False).encode('utf-8')).decode('utf-8')
        requests.put(url, headers=headers, json={"message": "Nexus Sync", "content": content, "sha": sha})

# --- [3] GIAO DIỆN XỊN (CSS CUSTOM) ---
st.markdown(f"""
<style>
    .stApp {{ background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: white; }}
    [data-testid="stHeader"] {{ visibility: hidden; }}
    .main-card {{
        background: rgba(255, 255, 255, 0.05); padding: 25px; border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 20px;
    }}
    .ai-bubble {{
        background: #0047AB; color: white; padding: 15px; border-radius: 15px 15px 15px 2px;
        margin: 10px 0; border: 1px solid #1d4ed8; box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }}
    .stButton>button {{
        background: linear-gradient(90deg, #1d4ed8 0%, #3b82f6 100%);
        color: white; border: none; border-radius: 10px; font-weight: bold; transition: 0.3s;
    }}
    .stButton>button:hover {{ transform: translateY(-2px); box-shadow: 0 5px 15px rgba(59, 130, 246, 0.4); }}
    .back-btn {{ color: #94a3b8 !important; text-decoration: none; font-weight: bold; }}
</style>
""", unsafe_allow_html=True)

# --- [4] KHỞI CHẠY ---
if 'db' not in st.session_state:
    st.session_state.db = sync_io()
    st.session_state.user = None
    st.session_state.page = "AUTH"

fp = get_device_fp()
# Tự động đăng nhập
if st.session_state.user is None and fp in st.session_state.db.get("rem", {}):
    st.session_state.user = st.session_state.db["rem"][fp]
    st.session_state.page = "DASHBOARD"

is_pro = (st.session_state.user in st.session_state.db.get("pro_users", []))

def nav(page):
    st.session_state.page = page
    st.rerun()

# --- [5] MÀN HÌNH ĐĂNG NHẬP ---
if st.session_state.page == "AUTH":
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<h1 style='text-align:center; color:#3b82f6;'>NEXUS PLATINUM</h1>", unsafe_allow_html=True)
        with st.container():
            u = st.text_input("Tài khoản").strip()
            p = st.text_input("Mật khẩu", type="password").strip()
            rem = st.checkbox("Ghi nhớ thiết bị này")
            if st.button("🚀 ĐĂNG NHẬP HỆ THỐNG", use_container_width=True):
                if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
                    st.session_state.user = u
                    if rem: st.session_state.db["rem"][fp] = u; sync_io(st.session_state.db)
                    nav("DASHBOARD")
                else: st.error("Sai tài khoản hoặc mật khẩu!")

# --- [6] DASHBOARD (GIAO DIỆN CARD) ---
elif st.session_state.page == "DASHBOARD":
    st.markdown(f"### 🛡️ Hệ điều hành Nexus | Chào, {st.session_state.user}")
    st.write(f"Cấp độ: {'💎 PLATINUM PRO' if is_pro else '🆓 STANDARD'}")
    st.divider()
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("<div class='main-card'><h3>🧠 AI Core</h3><p>Trí tuệ nhân tạo thế hệ mới</p></div>", unsafe_allow_html=True)
        if st.button("TRUY CẬP AI", key="nav_ai"): nav("AI")
    with c2:
        st.markdown("<div class='main-card'><h3>☁️ Cloud Storage</h3><p>Lưu trữ dữ liệu đám mây</p></div>", unsafe_allow_html=True)
        if st.button("MỞ KHO LƯU TRỮ", key="nav_cloud"): nav("CLOUD")
    with c3:
        st.markdown("<div class='main-card'><h3>⚙️ Settings</h3><p>Cấu hình và nâng cấp VIP</p></div>", unsafe_allow_html=True)
        if st.button("CÀI ĐẶT HỆ THỐNG", key="nav_set"): nav("SETTINGS")
    
    st.write("---")
    col_a, col_b = st.columns([5, 1])
    if st.session_state.user == CONFIG["CREATOR"]:
        if col_a.button("🛠️ BẢNG ĐIỀU KHIỂN QUẢN TRỊ (ADMIN)"): nav("ADMIN")
    if col_b.button("🔌 ĐĂNG XUẤT"):
        if fp in st.session_state.db["rem"]: del st.session_state.db["rem"][fp]
        sync_io(st.session_state.db); st.session_state.user = None; nav("AUTH")

# --- [7] TRÒ CHUYỆN AI ---
elif st.session_state.page == "AI":
    if st.button("🔙 QUAY LẠI"): nav("DASHBOARD")
    
    with st.sidebar:
        st.header("Lịch sử")
        if st.button("➕ Hội thoại mới"): st.session_state.chat_id = None; st.rerun()
        for i, c in enumerate(st.session_state.db["chats"]):
            if c["owner"] == st.session_state.user:
                col_t, col_d = st.columns([4, 1])
                if col_t.button(f"💬 {c['name']}", key=f"t_{i}"): st.session_state.chat_id = i; st.rerun()
                if col_d.button("🗑️", key=f"d_{i}"):
                    st.session_state.db["chats"].pop(i)
                    st.session_state.chat_id = None; sync_io(st.session_state.db); st.rerun()

    cid = st.session_state.get("chat_id")
    if cid is None or cid >= len(st.session_state.db["chats"]):
        st.session_state.db["chats"].append({"name": "Hội thoại mới", "msgs": [], "owner": st.session_state.user, "time": str(datetime.now())})
        st.session_state.chat_id = len(st.session_state.db["chats"]) - 1
        cid = st.session_state.chat_id

    chat = st.session_state.db["chats"][cid]
    for m in chat["msgs"]:
        if m["role"] == "user": st.chat_message("user").write(m["content"])
        else: st.markdown(f'<div class="ai-bubble">{m["content"]}</div>', unsafe_allow_html=True)

    if p := st.chat_input("Hỏi Nexus AI..."):
        chat["msgs"].append({"role": "user", "content": p})
        client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=chat["msgs"][-5:])
        ans = res.choices[0].message.content
        chat["msgs"].append({"role": "assistant", "content": ans})
        sync_io(st.session_state.db); st.rerun()

# --- [8] CLOUD (AUTO SAVE & DELETE) ---
elif st.session_state.page == "CLOUD":
    if st.button("🔙 QUAY LẠI"): nav("DASHBOARD")
    st.header("☁️ CLOUD STORAGE")
    
    # Auto-upload
    up = st.file_uploader("Kéo file vào để tự động tải lên", label_visibility="collapsed")
    if up:
        if up.name not in st.session_state.db["files"]:
            f_data = up.getvalue()
            st.session_state.db["files"][up.name] = {"data": base64.b64encode(f_data).decode(), "owner": st.session_state.user}
            sync_io(st.session_state.db); st.success(f"Đã lưu: {up.name}"); time.sleep(1); st.rerun()

    st.write("---")
    my_files = {k:v for k,v in st.session_state.db["files"].items() if v.get("owner") == st.session_state.user}
    
    for name, info in my_files.items():
        with st.container():
            c1, c2, c3 = st.columns([4, 1, 1])
            c1.markdown(f"📄 **{name}**")
            # Tải xuống
            bin_f = base64.b64decode(info["data"])
            c2.download_button("📥 TẢI VỀ", data=bin_f, file_name=name, key=f"dl_{name}")
            # XÓA FILE
            if c3.button("🗑️ XÓA", key=f"del_{name}"):
                del st.session_state.db["files"][name]; sync_io(st.session_state.db); st.rerun()

# --- [9] ADMIN PANEL (SIÊU QUYỀN LỰC) ---
elif st.session_state.page == "ADMIN":
    if st.button("🔙 QUAY LẠI"): nav("DASHBOARD")
    st.title("🛠️ HỆ THỐNG QUẢN TRỊ")
    
    tab1, tab2, tab3 = st.tabs(["👥 NGƯỜI DÙNG", "📂 TẤT CẢ FILE", "🔑 MÃ VIP"])
    
    with tab1:
        st.write("### Danh sách người dùng")
        for user, pwd in st.session_state.db["users"].items():
            col_u, col_p, col_x = st.columns([2, 2, 1])
            col_u.write(f"👤 {user}")
            col_p.write(f"🔑 {pwd}")
            if user != CONFIG["CREATOR"]:
                if col_x.button("XÓA USER", key=f"u_{user}"):
                    del st.session_state.db["users"][user]; sync_io(st.session_state.db); st.rerun()
    
    with tab2:
        st.write("### Quản lý tệp tin toàn hệ thống")
        for fname, finfo in st.session_state.db["files"].items():
            col_f, col_o, col_dx = st.columns([3, 1, 1])
            col_f.write(f"📄 {fname}")
            col_o.write(f"By: {finfo['owner']}")
            if col_dx.button("XÓA FILE", key=f"admin_f_{fname}"):
                del st.session_state.db["files"][fname]; sync_io(st.session_state.db); st.rerun()
                
    with tab3:
        new_vip = st.text_input("Tạo mã VIP mới").upper()
        if st.button("XÁC NHẬN TẠO"):
            st.session_state.db["codes"].append(new_vip); sync_io(st.session_state.db); st.success("Đã tạo mã!")
        st.write("Mã chưa dùng:", st.session_state.db["codes"])

# --- [10] SETTINGS ---
elif st.session_state.page == "SETTINGS":
    if st.button("🔙 QUAY LẠI"): nav("DASHBOARD")
    st.header("⚙️ CÀI ĐẶT")
    if not is_pro:
        code = st.text_input("Nhập mã kích hoạt PRO").upper()
        if st.button("KÍCH HOẠT"):
            if code in st.session_state.db["codes"]:
                st.session_state.db["pro_users"].append(st.session_state.user)
                st.session_state.db["codes"].remove(code)
                sync_io(st.session_state.db); st.balloons(); st.rerun()
    else: st.success("💎 BẠN ĐANG SỬ DỤNG PHIÊN BẢN PLATINUM PRO")
