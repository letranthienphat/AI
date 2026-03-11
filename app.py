# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time, base64, json, requests, random, string
from datetime import datetime

# --- [1] CẤU HÌNH NEXUS ---
SYSTEM_NAME = "NEXUS"
VERSION = "V6300 - INFINITY"
FILE_DATA = "data.json"
SECRET_KEY = "NEXUS_ULTIMATE_KEY_2024"

WALLPAPERS = [
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1920",
    "https://images.unsplash.com/photo-1534972195531-d756b9bfa9f2?q=80&w=1920",
    "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=1920"
]

try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS]
    GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")
except Exception as e:
    st.error(f"❌ Cấu hình lỗi: {e}")
    st.stop()

st.set_page_config(page_title=SYSTEM_NAME, layout="wide", initial_sidebar_state="collapsed")

# --- [2] CORE DATA ENGINE ---
def ma_hoa(text, tier="free"):
    if not text: return ""
    k = SECRET_KEY[::-1] if tier == "promax" else SECRET_KEY
    enc = "".join([chr(ord(c) ^ ord(k[i % len(k)])) for i, c in enumerate(text)])
    return base64.b64encode(enc.encode()).decode()

def giai_ma(text, tier="free"):
    if not text: return ""
    try:
        dec = base64.decodebytes(text.encode()).decode()
        k = SECRET_KEY[::-1] if tier == "promax" else SECRET_KEY
        return "".join([chr(ord(c) ^ ord(k[i % len(k)])) for i, c in enumerate(dec)])
    except: return text

def tai_du_lieu():
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GH_TOKEN}"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200: return json.loads(base64.b64decode(res.json()['content']).decode('utf-8'))
    except: pass
    return {}

def luu_du_lieu():
    data = {
        "users": st.session_state.users, "user_status": st.session_state.user_status,
        "chat_library": st.session_state.chat_library, "groups": st.session_state.groups,
        "cloud_drive": st.session_state.cloud_drive, "tickets": st.session_state.tickets,
        "activation_keys": st.session_state.activation_keys, "notice": st.session_state.notice,
        "profiles": st.session_state.profiles, "shared_files": st.session_state.shared_files
    }
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, indent=4).encode()).decode()
        requests.put(url, headers=headers, json={"message": "Nexus Infinity Sync", "content": content, "sha": sha})
    except: pass

# --- [3] KHỞI TẠO AN TOÀN ---
if 'initialized' not in st.session_state:
    db = tai_du_lieu()
    st.session_state.users = db.get("users", {"Thiên Phát": "2002"})
    st.session_state.user_status = db.get("user_status", {"Thiên Phát": "promax"})
    st.session_state.profiles = db.get("profiles", {})
    st.session_state.shared_files = db.get("shared_files", [])
    st.session_state.chat_library = db.get("chat_library", {})
    st.session_state.groups = db.get("groups", {"Sảnh Chung": {"msgs": []}})
    st.session_state.cloud_drive = db.get("cloud_drive", {})
    st.session_state.tickets = db.get("tickets", [])
    st.session_state.activation_keys = db.get("activation_keys", {})
    st.session_state.notice = db.get("notice", {"content": "Nexus Infinity đã sẵn sàng.", "is_emergency": False, "id": 0})
    st.session_state.stage = "AUTH"
    st.session_state.auth_status = None
    st.session_state.initialized = True

# --- [4] GIAO DIỆN GLASSMORPHISM ---
def apply_ui():
    bg = random.choice(WALLPAPERS)
    st.markdown(f"""
    <style>
    .stApp {{ background: url('{bg}') no-repeat center fixed; background-size: cover; color: #F8FAFC; }}
    .glass-card, .stChatMessage {{
        background: rgba(15, 23, 42, 0.75) !important;
        backdrop-filter: blur(15px); border-radius: 20px !important;
        padding: 20px; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 15px;
    }}
    .tile-button {{
        background: rgba(30, 41, 59, 0.6); border: 1px solid #38BDF8;
        padding: 30px; border-radius: 20px; text-align: center;
        transition: 0.3s; cursor: pointer; height: 100%;
    }}
    .tile-button:hover {{ background: #38BDF8; color: #0F172A; transform: scale(1.02); }}
    .stButton > button {{ border-radius: 12px; width: 100%; }}
    [data-testid="stHeader"] {{ visibility: hidden; }}
    </style>
    """, unsafe_allow_html=True)

# --- [5] AI ENGINE ---
def goi_ai(messages, tier):
    try:
        client = OpenAI(api_key=GEMINI_KEY, base_url="https://generativelanguage.googleapis.com/v1beta/openai")
        res = client.chat.completions.create(model="gemini-1.5-flash", messages=messages)
        return res.choices[0].message.content
    except:
        client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages)
        return res.choices[0].message.content

# --- [6] MÀN HÌNH CHÍNH ---

def screen_ai_chat():
    apply_ui()
    me = st.session_state.auth_status
    tier = st.session_state.user_status.get(me, "free")
    lib = st.session_state.chat_library.setdefault(me, {"sessions": {"Chat mới": []}, "active": "Chat mới"})
    
    with st.sidebar:
        st.title("🧠 AI CHAT")
        search = st.text_input("🔍 Tìm hội thoại")
        if st.button("➕ Hội thoại mới"):
            n = f"Hội thoại {len(lib['sessions'])+1}"
            lib['sessions'][n] = []; lib['active'] = n; st.rerun()
        st.write("---")
        for s_name in lib['sessions'].keys():
            if search.lower() in s_name.lower():
                if st.button(f"💬 {s_name}", use_container_width=True):
                    lib['active'] = s_name; st.rerun()

    c1, c2 = st.columns([0.8, 0.2])
    with c1:
        new_title = st.text_input("📍 Tên phiên chat", value=lib['active'])
        if new_title != lib['active']:
            lib['sessions'][new_title] = lib['sessions'].pop(lib['active'])
            lib['active'] = new_title; luu_du_lieu(); st.rerun()
    if c2.button("⬅️ HOME"): st.session_state.stage = "MENU"; st.rerun()

    history = lib['sessions'][lib['active']]
    for m in history:
        with st.chat_message(m['role']): st.write(giai_ma(m['content'], tier))

    if p := st.chat_input("Hỏi Nexus Infinity..."):
        history.append({"role": "user", "content": ma_hoa(p, tier)})
        with st.chat_message("user"): st.write(p)
        with st.chat_message("assistant"):
            res = goi_ai([{"role": "user", "content": p}], tier)
            st.write(res)
            history.append({"role": "assistant", "content": ma_hoa(res, tier)})
            luu_du_lieu()

def screen_social():
    apply_ui()
    st.title("🌐 CỘNG ĐỒNG")
    if st.button("⬅️ QUAY LẠI"): st.session_state.stage = "MENU"; st.rerun()
    
    t1, t2 = st.tabs(["💬 SẢNH CHUNG", "📂 CHIA SẺ FILE"])
    
    with t1:
        group = st.session_state.groups["Sảnh Chung"]
        for m in group['msgs'][-30:]:
            st.markdown(f"**{m['user']}**: {giai_ma(m['text'])}")
        if st.session_state.auth_status != "Guest":
            if p := st.chat_input("Nhắn tin..."):
                group['msgs'].append({"user": st.session_state.auth_status, "text": ma_hoa(p)})
                luu_du_lieu(); st.rerun()

    with t2:
        if st.session_state.auth_status != "Guest":
            with st.expander("➕ ĐĂNG FILE LÊN CỘNG ĐỒNG"):
                f_up = st.file_uploader("Chọn file")
                f_desc = st.text_input("Mô tả file")
                if f_up and st.button("CHIA SẺ"):
                    st.session_state.shared_files.append({
                        "user": st.session_state.auth_status, "name": f_up.name,
                        "desc": f_desc, "data": base64.b64encode(f_up.getvalue()).decode(),
                        "time": datetime.now().strftime("%d/%m %H:%M")
                    })
                    luu_du_lieu(); st.success("Đã chia sẻ!"); st.rerun()
        
        for f in reversed(st.session_state.shared_files):
            with st.container():
                st.markdown(f"<div class='glass-card'>📦 <b>{f['name']}</b><br><small>Bởi: {f['user']} | {f['time']}</small><br>📝 {f['desc']}</div>", unsafe_allow_html=True)
                st.download_button(f"Tải xuống {f['name']}", base64.b64decode(f['data']), file_name=f['name'], key=f"shared_{f['time']}")

def screen_profile():
    apply_ui()
    me = st.session_state.auth_status
    st.title("👤 TRANG CÁ NHÂN")
    if st.button("⬅️ HOME"): st.session_state.stage = "MENU"; st.rerun()
    
    prof = st.session_state.profiles.setdefault(me, {"bio": "Chào mừng tới Profile của tôi", "avatar": "https://cdn-icons-png.flaticon.com/512/149/149071.png"})
    
    c1, c2 = st.columns([0.3, 0.7])
    with c1:
        st.image(prof['avatar'], width=150)
        new_ava = st.text_input("URL Ảnh đại diện", value=prof['avatar'])
    with c2:
        st.subheader(f"User: {me}")
        st.write(f"Cấp độ: **{st.session_state.user_status.get(me, 'free').upper()}**")
        new_bio = st.text_area("Tiểu sử", value=prof['bio'])
        if st.button("LƯU THAY ĐỔI"):
            prof['avatar'] = new_ava; prof['bio'] = new_bio
            luu_du_lieu(); st.success("Đã cập nhật!"); st.rerun()

# --- [7] ADMIN PANEL ---
def screen_admin():
    apply_ui()
    st.title("🛡️ SUPREME CONTROL PANEL")
    if st.button("⬅️ MENU"): st.session_state.stage = "MENU"; st.rerun()
    
    tab1, tab2, tab3 = st.tabs(["👥 NGƯỜI DÙNG", "📥 TICKETS", "📢 THÔNG BÁO"])
    
    with tab1:
        for user, tier in st.session_state.user_status.items():
            col1, col2 = st.columns([0.7, 0.3])
            col1.write(f"👤 {user} | Cấp: {tier}")
            new_tier = col2.selectbox("Đổi cấp", ["free", "pro", "promax"], index=["free", "pro", "promax"].index(tier), key=f"t_{user}")
            if new_tier != tier:
                st.session_state.user_status[user] = new_tier; luu_du_lieu(); st.rerun()

# --- [8] MÀN HÌNH AUTH ---
def screen_auth():
    apply_ui()
    _, cc, _ = st.columns([1, 1.2, 1])
    with cc:
        st.markdown("<div class='glass-card' style='text-align:center;'>", unsafe_allow_html=True)
        st.title("NEXUS INFINITY")
        tab = st.tabs(["Đăng nhập", "Đăng ký", "Khách"])
        with tab[0]:
            u = st.text_input("Tên đăng nhập")
            p = st.text_input("Mật mã", type="password")
            if st.button("VÀO HỆ THỐNG", use_container_width=True):
                if u in st.session_state.users and st.session_state.users[u] == p:
                    st.session_state.auth_status = u; st.session_state.stage = "MENU"; st.rerun()
                else: st.error("Sai thông tin!")
        with tab[1]:
            nu = st.text_input("Tên mới")
            np = st.text_input("Mật mã mới", type="password")
            if st.button("TẠO TÀI KHOẢN", use_container_width=True):
                if nu and nu not in st.session_state.users:
                    st.session_state.users[nu] = np
                    st.session_state.user_status[nu] = "free"
                    luu_du_lieu(); st.success("Đã đăng ký!"); time.sleep(1)
        with tab[2]:
            if st.button("TRUY CẬP GUEST", use_container_width=True):
                st.session_state.auth_status = "Guest"; st.session_state.stage = "MENU"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# --- [9] ROUTER ---
if st.session_state.stage == "AUTH": screen_auth()
elif st.session_state.stage == "MENU":
    apply_ui()
    st.title(f"🚀 NEXUS | {st.session_state.auth_status.upper()}")
    
    # Dashboard Tiles
    c1, c2, c3 = st.columns(3)
    with c1: 
        if st.button("🧠 AI CHAT\nHội thoại thông minh"): st.session_state.stage = "AI_CHAT"; st.rerun()
    with c2:
        if st.button("🌐 COMMUNITY\nSảnh & Chia sẻ file"): st.session_state.stage = "SOCIAL"; st.rerun()
    with c3:
        if st.button("👤 PROFILE\nTrang cá nhân"): st.session_state.stage = "PROFILE"; st.rerun()
        
    c4, c5, c6 = st.columns(3)
    with c4:
        if st.button("☁️ STORAGE\nKho lưu trữ mây"): st.session_state.stage = "CLOUD"; st.rerun()
    with c5:
        if st.button("🎧 SUPPORT\nGửi yêu cầu"): st.session_state.stage = "SUPPORT"; st.rerun()
    with c6:
        if st.button("⚙️ SETTINGS\nKích hoạt gói"): st.session_state.stage = "SETTINGS"; st.rerun()

    if st.session_state.auth_status == "Thiên Phát":
        if st.button("🛡️ SUPREME ADMIN PANEL", use_container_width=True): st.session_state.stage = "ADMIN"; st.rerun()
    if st.button("🚪 ĐĂNG XUẤT", use_container_width=True): st.session_state.stage = "AUTH"; st.rerun()

elif st.session_state.stage == "AI_CHAT": screen_ai_chat()
elif st.session_state.stage == "SOCIAL": screen_social()
elif st.session_state.stage == "PROFILE": screen_profile()
elif st.session_state.stage == "ADMIN": screen_admin()
# ... Các màn hình khác: CLOUD, SUPPORT, SETTINGS (Giữ nguyên logic bản trước) ...
