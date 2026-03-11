# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time, base64, json, requests, random, string
from datetime import datetime

# --- [1] CẤU HÌNH NEXUS ---
CREATOR = "Lê Trần Thiên Phát"
SYSTEM_NAME = "NEXUS QUANTUM"
FILE_DATA = "data.json"
SECRET_KEY = "NEXUS_ULTIMATE_KEY_2024"

# Kho hình nền tự động (Auto-Wallpaper)
WALLPAPERS = [
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1920",
    "https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=1920",
    "https://images.unsplash.com/photo-1534723328310-e82dad3ee43f?q=80&w=1920",
    "https://images.unsplash.com/photo-1478760329108-5c3ed9d495a0?q=80&w=1920"
]

try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS]
    GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")
except:
    st.error("⚠️ Secrets chưa được cấu hình!")
    st.stop()

st.set_page_config(page_title=SYSTEM_NAME, layout="wide", initial_sidebar_state="collapsed")

# --- [2] CORE ENGINE ---
def ma_hoa(text, tier="free"):
    if not text: return ""
    k = SECRET_KEY[::-1] if tier == "promax" else SECRET_KEY
    enc = "".join([chr(ord(c) ^ ord(k[i % len(k)])) for i, c in enumerate(text)])
    return base64.b64encode(enc.encode()).decode()

def giai_ma(text, tier="free"):
    if not text: return ""
    try:
        dec = base64.b64decode(text.encode()).decode()
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
        "activation_keys": st.session_state.activation_keys, "notice": st.session_state.notice
    }
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, indent=4).encode()).decode()
        payload = {"message": "Nexus Quantum Sync", "content": content, "sha": sha}
        requests.put(url, headers=headers, json=payload)
    except: pass

# --- [3] KHỞI TẠO ---
if 'initialized' not in st.session_state:
    db = tai_du_lieu()
    st.session_state.users = db.get("users", {"Thiên Phát": "2002"})
    st.session_state.user_status = db.get("user_status", {"Thiên Phát": "promax"}) 
    st.session_state.chat_library = db.get("chat_library", {})
    st.session_state.groups = db.get("groups", {"Sảnh Chung": {"msgs": []}, "Góc Chia Sẻ": {"msgs": []}})
    st.session_state.cloud_drive = db.get("cloud_drive", {})
    st.session_state.tickets = db.get("tickets", [])
    st.session_state.activation_keys = db.get("activation_keys", {})
    st.session_state.notice = db.get("notice", {"content": "Hệ thống Nexus Online.", "is_emergency": False, "id": 0})
    st.session_state.stage = "AUTH"
    st.session_state.auth_status = None # Lưu username
    st.session_state.initialized = True

# --- [4] UI & AUTO WALLPAPER ---
def apply_ui():
    bg = random.choice(WALLPAPERS)
    st.markdown(f"""
    <style>
    .stApp {{ background: url('{bg}') no-repeat center fixed; background-size: cover; color: #E2E8F0; }}
    .glass-card {{ background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(12px); border-radius: 20px; padding: 25px; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 8px 32px rgba(0,0,0,0.5); }}
    .stButton > button {{ background: #1E293B !important; color: #94A3B8 !important; border-radius: 10px; border: 1px solid #334155 !important; font-weight: 600; width: 100%; }}
    .stButton > button:hover {{ border-color: #38BDF8 !important; color: #38BDF8 !important; }}
    h1, h2, h3 {{ color: #F8FAFC !important; text-shadow: 0 2px 10px rgba(0,0,0,0.5); }}
    .badge-promax {{ background: linear-gradient(135deg, #A855F7, #EC4899); color: white; padding: 2px 10px; border-radius: 20px; font-size: 12px; }}
    [data-testid="stHeader"] {{ visibility: hidden; }}
    </style>
    """, unsafe_allow_html=True)

# --- [5] AI ENGINE ---
def goi_ai(messages, tier):
    # Cấu hình chuẩn cho Gemini 1.5 Flash
    if tier in ["pro", "promax"]:
        try:
            client = OpenAI(api_key=GEMINI_KEY, base_url="https://generativelanguage.googleapis.com/v1beta/openai")
            res = client.chat.completions.create(model="gemini-1.5-flash", messages=messages)
            return res.choices[0].message.content
        except Exception as e:
            if tier != "promax": return f"⚠️ Gemini Lỗi: {str(e)}"
    
    # Fallback cho Free hoặc Promax khi Gemini lỗi
    try:
        client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages)
        return res.choices[0].message.content
    except Exception as e:
        return f"⚠️ Cạn kiệt Token AI: {str(e)}"

# --- [6] MÀN HÌNH CHỨC NĂNG ---

def screen_ai_chat():
    apply_ui()
    me = st.session_state.auth_status
    tier = st.session_state.user_status.get(me, "free")
    
    c1, c2 = st.columns([0.8, 0.2])
    c1.title("🧠 NEXUS AI INTELLIGENCE")
    if c2.button("⬅️ HOME"): st.session_state.stage = "MENU"; st.rerun()

    # Quản lý Lịch sử (Chat Library)
    user_lib = st.session_state.chat_library.setdefault(me, {"sessions": {"Phiên 1": []}, "active": "Phiên 1"})
    active_s = user_lib["active"]
    
    with st.sidebar:
        st.subheader("Trò chuyện đã lưu")
        if st.button("➕ Cuộc trò chuyện mới"):
            new_name = f"Phiên {len(user_lib['sessions']) + 1}"
            user_lib["sessions"][new_name] = []
            user_lib["active"] = new_name
            luu_du_lieu(); st.rerun()
        for s_name in user_lib["sessions"].keys():
            if st.button(f"💬 {s_name}", key=f"btn_{s_name}"):
                user_lib["active"] = s_name; st.rerun()

    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.info(f"Đang trong: {active_s}")
    history = user_lib["sessions"][active_s]
    
    for m in history:
        with st.chat_message(m['role']): st.write(giai_ma(m['content'], tier))

    if p := st.chat_input("Hỏi Nexus..."):
        history.append({"role": "user", "content": ma_hoa(p, tier)})
        with st.chat_message("user"): st.write(p)
        with st.chat_message("assistant"):
            res = goi_ai([{"role": "user", "content": p}], tier)
            st.write(res)
            history.append({"role": "assistant", "content": ma_hoa(res, tier)})
            luu_du_lieu()
    st.markdown("</div>", unsafe_allow_html=True)

def screen_social():
    apply_ui()
    me = st.session_state.auth_status
    st.title("🌐 NEXUS COMMUNITY")
    if st.button("⬅️ QUAY LẠI MENU"): st.session_state.stage = "MENU"; st.rerun()

    t1, t2 = st.tabs(["💬 SẢNH CHUNG", "📂 GÓC CHIA SẺ FILE"])
    
    with t1:
        group = st.session_state.groups["Sảnh Chung"]
        for m in group['msgs'][-20:]: # Hiện 20 tin mới nhất
            with st.chat_message("user"):
                st.write(f"**{m['user']}**: {giai_ma(m['text'])}")
        
        if me != "Guest":
            p = st.chat_input("Nhắn vào sảnh...", key="input_hall")
            if p:
                group['msgs'].append({"user": me, "text": ma_hoa(p)})
                luu_du_lieu(); st.rerun()
        else: st.warning("Khách chỉ có thể xem, vui lòng Đăng ký để chat.")

    with t2:
        st.info("Khu vực chia sẻ kiến thức và tài liệu Nexus.")
        # Logic tương tự cho Góc Chia Sẻ...

# --- [7] AUTH & ROUTER ---
def screen_auth():
    apply_ui()
    _, cc, _ = st.columns([1, 1.2, 1])
    with cc:
        st.markdown("<div class='glass-card' style='text-align:center;'>", unsafe_allow_html=True)
        st.title("NEXUS GATEWAY")
        mode = st.tabs(["Đăng nhập", "Đăng ký", "Khách"])
        
        with mode[0]:
            u = st.text_input("Username", key="login_u")
            p = st.text_input("Password", type="password", key="login_p")
            if st.button("VÀO HỆ THỐNG", use_container_width=True):
                if u in st.session_state.users and st.session_state.users[u] == p:
                    st.session_state.auth_status = u; st.session_state.stage = "MENU"; st.rerun()
                else: st.error("Sai thông tin!")
        
        with mode[1]:
            new_u = st.text_input("Tạo Username", key="reg_u")
            new_p = st.text_input("Tạo Password", type="password", key="reg_p")
            if st.button("TẠO TÀI KHOẢN", use_container_width=True):
                if new_u and new_u not in st.session_state.users:
                    st.session_state.users[new_u] = new_p
                    st.session_state.user_status[new_u] = "free"
                    luu_du_lieu(); st.success("Đăng ký thành công! Hãy Đăng nhập."); time.sleep(1)
                else: st.error("Tên đã tồn tại hoặc để trống!")

        with mode[2]:
            st.write("Dùng thử Nexus với quyền hạn hạn chế.")
            if st.button("TRUY CẬP GUEST", use_container_width=True):
                st.session_state.auth_status = "Guest"; st.session_state.stage = "MENU"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.stage == "AUTH": screen_auth()
elif st.session_state.stage == "MENU":
    apply_ui()
    me = st.session_state.auth_status
    tier = st.session_state.user_status.get(me, "free")
    
    st.title(f"🚀 {SYSTEM_NAME} | {me.upper()}")
    if tier == "promax": st.markdown("<span class='badge-promax'>👑 PRO MAX</span>", unsafe_allow_html=True)
    
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    c1, c2 = st.columns(2); c3, c4 = st.columns(2)
    if c1.button("🧠 AI INTELLIGENCE"): st.session_state.stage = "AI_CHAT"; st.rerun()
    if c2.button("🌐 COMMUNITY"): st.session_state.stage = "SOCIAL"; st.rerun()
    if c3.button("☁️ NEXUS CLOUD"):
        if me == "Guest": st.error("Guest không có Cloud!")
        else: st.session_state.stage = "CLOUD"; st.rerun()
    if c4.button("🎧 SUPPORT"): st.session_state.stage = "SUPPORT"; st.rerun()
    
    st.write("---")
    if st.button("⚙️ SETTINGS"): st.session_state.stage = "SETTINGS"; st.rerun()
    if me == "Thiên Phát" and st.button("🛡️ ADMIN PANEL"): st.session_state.stage = "ADMIN"; st.rerun()
    if st.button("🚪 LOGOUT"): st.session_state.stage = "AUTH"; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.stage == "AI_CHAT": screen_ai_chat()
elif st.session_state.stage == "SOCIAL": screen_social()
# ... Các màn hình khác tương tự bản trước ...
