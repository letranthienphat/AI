# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time, base64, json, requests, random, string
from datetime import datetime

# --- [1] CẤU HÌNH NEXUS ---
SYSTEM_NAME = "NEXUS"
VERSION = "V6100 - NEBULA"
FILE_DATA = "data.json"
SECRET_KEY = "NEXUS_ULTIMATE_KEY_2024"

WALLPAPERS = [
    "https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?q=80&w=1920",
    "https://images.unsplash.com/photo-1506318137071-a8e063b4b519?q=80&w=1920",
    "https://images.unsplash.com/photo-1439337153520-7082a56a81f4?q=80&w=1920"
]

try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS]
    GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")
except:
    st.error("⚠️ Lỗi: Chưa cấu hình Secrets trên Cloud!")
    st.stop()

st.set_page_config(page_title=SYSTEM_NAME, layout="wide", initial_sidebar_state="collapsed")

# --- [2] CORE FUNCTIONS ---
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
        requests.put(url, headers=headers, json={"message": "Nexus Nebula Update", "content": content, "sha": sha})
    except: pass

# --- [3] KIỂM TRA DỮ LIỆU (CHỐNG KEYERROR) ---
def kiem_tra_du_lieu():
    if not isinstance(st.session_state.groups, dict): st.session_state.groups = {}
    if "Sảnh Chung" not in st.session_state.groups:
        st.session_state.groups["Sảnh Chung"] = {"msgs": []}
    
    me = st.session_state.get("auth_status")
    if me and me != "Guest":
        if me not in st.session_state.chat_library:
            st.session_state.chat_library[me] = {"sessions": {"Cuộc trò chuyện mới": []}, "active": "Cuộc trò chuyện mới"}

# --- [4] UI GLASSMORPHISM ---
def apply_ui():
    bg = random.choice(WALLPAPERS)
    st.markdown(f"""
    <style>
    .stApp {{ background: url('{bg}') no-repeat center fixed; background-size: cover; color: #F8FAFC; }}
    /* Lớp sương mờ cho tất cả khung phản hồi */
    .stChatMessage, .glass-card, [data-testid="stExpander"] {{
        background: rgba(15, 23, 42, 0.65) !important;
        backdrop-filter: blur(12px) saturate(180%);
        -webkit-backdrop-filter: blur(12px) saturate(180%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px !important;
        padding: 15px;
        margin-bottom: 15px;
    }}
    .stButton > button {{ 
        background: rgba(30, 41, 59, 0.7) !important; 
        backdrop-filter: blur(5px);
        color: #38BDF8 !important; border: 1px solid #38BDF8 !important; border-radius: 10px; font-weight: 600; 
    }}
    .stButton > button:hover {{ background: #38BDF8 !important; color: #0F172A !important; }}
    [data-testid="stHeader"] {{ visibility: hidden; }}
    h1, h2, h3 {{ text-shadow: 0 4px 12px rgba(0,0,0,0.5); }}
    </style>
    """, unsafe_allow_html=True)

# --- [5] AI ENGINE ---
def goi_ai(messages, tier):
    try:
        # Cấu hình Gemini chuẩn
        client = OpenAI(api_key=GEMINI_KEY, base_url="https://generativelanguage.googleapis.com/v1beta/openai")
        res = client.chat.completions.create(model="gemini-1.5-flash", messages=messages)
        return res.choices[0].message.content
    except:
        try:
            # Fallback sang Groq
            client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
            res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages)
            return res.choices[0].message.content
        except Exception as e: return f"⚠️ Lỗi AI: {str(e)}"

def ai_dat_ten(text):
    prompt = f"Đặt 1 cái tên ngắn gọn (dưới 5 từ) cho cuộc trò chuyện này dựa trên nội dung: {text}"
    try:
        res = goi_ai([{"role": "user", "content": prompt}], "free")
        return res.strip().replace('"', '')
    except: return text[:15] + "..."

# --- [6] MÀN HÌNH ---

def screen_ai_chat():
    apply_ui()
    kiem_tra_du_lieu()
    me = st.session_state.auth_status
    tier = st.session_state.user_status.get(me, "free")
    lib = st.session_state.chat_library[me]
    active_s = lib["active"]

    # --- Header & Đổi tên ---
    c1, c2 = st.columns([0.8, 0.2])
    with c1:
        new_title = st.text_input("📍 Tên cuộc trò chuyện (Nhấn để đổi)", value=active_s)
        if new_title != active_s:
            lib["sessions"][new_title] = lib["sessions"].pop(active_s)
            lib["active"] = new_title
            luu_du_lieu(); st.rerun()
    if c2.button("⬅️ HOME"): st.session_state.stage = "MENU"; st.rerun()

    # --- Sidebar Cấu hình ---
    with st.sidebar:
        st.title("⚙️ AI CONFIG")
        context_limit = st.slider("Số lượng tin nhắn xử lý", 1, 30, 10)
        st.write("---")
        if st.button("➕ Hội thoại mới"):
            name = f"Chat {len(lib['sessions'])+1}"
            lib["sessions"][name] = []; lib["active"] = name
            luu_du_lieu(); st.rerun()
        for s in lib["sessions"].keys():
            if st.button(f"💬 {s}", use_container_width=True):
                lib["active"] = s; st.rerun()

    # --- Khu vực Chat ---
    history = lib["sessions"][active_s]
    for m in history:
        with st.chat_message(m['role']):
            st.markdown(f"<div style='color: #E2E8F0;'>{giai_ma(m['content'], tier)}</div>", unsafe_allow_html=True)

    if p := st.chat_input("Hỏi Nexus Nebula..."):
        # AI tự đặt tên nếu là tin nhắn đầu tiên
        if not history:
            auto_name = ai_dat_ten(p)
            lib["sessions"][auto_name] = lib["sessions"].pop(active_s)
            lib["active"] = auto_name
            active_s = auto_name
            history = lib["sessions"][active_s]

        history.append({"role": "user", "content": ma_hoa(p, tier)})
        with st.chat_message("user"): st.write(p)
        
        with st.chat_message("assistant"):
            # Chỉ gửi số lượng tin nhắn giới hạn theo slider
            context = [{"role": giai_ma(m['role']), "content": giai_ma(m['content'], tier)} for m in history[-context_limit:]]
            res = goi_ai(context, tier)
            st.write(res)
            history.append({"role": "assistant", "content": ma_hoa(res, tier)})
            luu_du_lieu()

def screen_social():
    apply_ui()
    kiem_tra_du_lieu() # Bảo vệ KeyError
    me = st.session_state.auth_status
    
    st.title("🌐 NEXUS COMMUNITY")
    if st.button("⬅️ HOME"): st.session_state.stage = "MENU"; st.rerun()

    # Đảm bảo group tồn tại
    group = st.session_state.groups.get("Sảnh Chung", {"msgs": []})
    
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    for m in group['msgs'][-50:]:
        with st.chat_message("user"):
            st.write(f"**{m['user']}**: {giai_ma(m['text'])}")
    
    if me != "Guest":
        if p := st.chat_input("Nhắn gì đó..."):
            group['msgs'].append({"user": me, "text": ma_hoa(p)})
            luu_du_lieu(); st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# --- [7] ROUTER ---
if 'initialized' not in st.session_state:
    db = tai_du_lieu()
    st.session_state.users = db.get("users", {"Thiên Phát": "2002"})
    st.session_state.user_status = db.get("user_status", {})
    st.session_state.chat_library = db.get("chat_library", {})
    st.session_state.groups = db.get("groups", {"Sảnh Chung": {"msgs": []}})
    st.session_state.cloud_drive = db.get("cloud_drive", {})
    st.session_state.tickets = db.get("tickets", [])
    st.session_state.activation_keys = db.get("activation_keys", {})
    st.session_state.notice = db.get("notice", {"content": "Nexus Nebula v6.1", "is_emergency": False, "id": 0})
    st.session_state.stage = "AUTH"
    st.session_state.initialized = True

if st.session_state.stage == "AUTH":
    apply_ui()
    _, cc, _ = st.columns([1, 1.2, 1])
    with cc:
        st.markdown("<div class='glass-card' style='text-align:center;'>", unsafe_allow_html=True)
        st.title("NEXUS NEBULA")
        t1, t2, t3 = st.tabs(["Đăng nhập", "Đăng ký", "Khách"])
        with t1:
            u = st.text_input("Định danh")
            p = st.text_input("Mật mã", type="password")
            if st.button("TRUY CẬP"):
                if u in st.session_state.users and st.session_state.users[u] == p:
                    st.session_state.auth_status = u; st.session_state.stage = "MENU"; st.rerun()
        with t2:
            nu = st.text_input("Tên mới")
            np = st.text_input("Mật mã mới", type="password")
            if st.button("TẠO"):
                st.session_state.users[nu] = np; luu_du_lieu(); st.success("Xong!")
        with t3:
            if st.button("VÀO VỚI QUYỀN KHÁCH"):
                st.session_state.auth_status = "Guest"; st.session_state.stage = "MENU"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.stage == "MENU":
    apply_ui()
    st.title(f"🚀 NEXUS | {st.session_state.auth_status.upper()}")
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    c1, c2 = st.columns(2); c3, c4 = st.columns(2)
    if c1.button("🧠 AI CHAT"): st.session_state.stage = "AI_CHAT"; st.rerun()
    if c2.button("🌐 COMMUNITY"): st.session_state.stage = "SOCIAL"; st.rerun()
    if c3.button("🛡️ ADMIN PANEL"): 
        if st.session_state.auth_status == "Thiên Phát": st.session_state.stage = "ADMIN"; st.rerun()
    if c4.button("🚪 LOGOUT"): st.session_state.stage = "AUTH"; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.stage == "AI_CHAT": screen_ai_chat()
elif st.session_state.stage == "SOCIAL": screen_social()
