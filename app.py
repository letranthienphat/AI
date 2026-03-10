# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time, base64, json, requests
from datetime import datetime, timedelta

# --- [1] CẤU HÌNH ---
CREATOR = "Lê Trần Thiên Phát"
VERSION = "V5100 - NEXUS GATEWAY ULTIMATE"
FILE_DATA = "data.json"
SECRET_KEY = "NEXUS_ULTIMATE_KEY_2024"

try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
except:
    st.error("❌ Thiếu cấu hình Secrets!")
    st.stop()

st.set_page_config(page_title=f"NEXUS OS | {CREATOR}", layout="wide")

# --- [2] HÀM NỀN TẢNG ---
def ma_hoa(text):
    if not text: return ""
    encoded = "".join([chr(ord(c) ^ ord(SECRET_KEY[i % len(SECRET_KEY)])) for i, c in enumerate(text)])
    return base64.b64encode(encoded.encode()).decode()

def giai_ma(text):
    if not text: return ""
    try:
        decoded = base64.b64decode(text.encode()).decode()
        return "".join([chr(ord(c) ^ ord(SECRET_KEY[i % len(SECRET_KEY)])) for i, c in enumerate(decoded)])
    except: return text

def tai_du_lieu():
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GH_TOKEN}"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return json.loads(base64.b64decode(res.json()['content']).decode('utf-8'))
    except: pass
    return {}

def luu_du_lieu():
    data = {
        "users": st.session_state.users, "theme": st.session_state.theme,
        "chat_library": st.session_state.chat_library, "profiles": st.session_state.profiles,
        "groups": st.session_state.groups, "access_logs": st.session_state.access_logs,
        "punishments": st.session_state.punishments
    }
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, indent=4).encode()).decode()
        payload = {"message": f"Sync {datetime.now()}", "content": content, "sha": sha} if sha else {"message": "Init", "content": content}
        requests.put(url, headers=headers, json=payload)
    except: pass

# --- [3] KHỞI TẠO ---
if 'initialized' not in st.session_state:
    db = tai_du_lieu()
    st.session_state.users = db.get("users", {"Thiên Phát": "2002", "admin": "123"})
    st.session_state.profiles = db.get("profiles", {})
    st.session_state.theme = db.get("theme", {"primary_color": "#00f2ff", "bg_list": [], "auto_rotate": False, "rotate_min": 5, "current_bg_idx": 0, "last_rotate": str(datetime.now())})
    st.session_state.chat_library = db.get("chat_library", {})
    st.session_state.groups = db.get("groups", {"Sảnh Chung": {"type": "FULL_AI", "msgs": []}})
    st.session_state.access_logs = db.get("access_logs", [])
    st.session_state.punishments = db.get("punishments", {})
    st.session_state.stage = "AUTH"
    st.session_state.auth_status = None
    st.session_state.initialized = True

# --- [4] UI & LOGO ---
def apply_ui():
    t = st.session_state.theme
    p_color = t['primary_color']
    bg_url = t["bg_list"][t["current_bg_idx"]] if t["bg_list"] else ""
    bg_css = f"url('{bg_url}')" if bg_url else "#0a0a0c"
    st.markdown(f"""
    <style>
    .stApp {{ background: {bg_css} no-repeat center fixed; background-size: cover; color: #E2E8F0; }}
    .glass {{ background: rgba(10, 10, 15, 0.8) !important; backdrop-filter: blur(15px); border-radius: 12px; padding: 20px; border: 1px solid {p_color}44; }}
    h1, h2, h3 {{ color: {p_color} !important; text-shadow: 0 0 10px {p_color}55; }}
    .stButton > button {{ background: transparent; color: {p_color}; border: 1px solid {p_color}; border-radius: 5px; }}
    .stButton > button:hover {{ background: {p_color}; color: #000; box-shadow: 0 0 15px {p_color}; }}
    [data-testid="stHeader"] {{ visibility: hidden; }}
    </style>
    """, unsafe_allow_html=True)

def draw_logo():
    color = st.session_state.theme.get('primary_color', '#00f2ff')
    st.markdown(f"""
    <div style="display: flex; flex-direction: column; align-items: center; margin-bottom: 20px;">
        <div style="width: 80px; height: 80px; border: 3px solid {color}; border-radius: 50%; border-top-color: transparent; animation: spin 2s linear infinite; display: flex; align-items: center; justify-content: center;">
            <div style="width: 30px; height: 30px; background: {color}; border-radius: 50%; box-shadow: 0 0 20px {color};"></div>
        </div>
        <div style="color: {color}; font-size: 22px; font-weight: bold; margin-top: 10px;">NEXUS GATEWAY</div>
    </div>
    <style> @keyframes spin {{ 100% {{ transform: rotate(360deg); }} }} </style>
    """, unsafe_allow_html=True)

# --- [5] XỬ LÝ AI ---
def goi_ai(messages):
    try:
        client = OpenAI(api_key=GROQ_KEYS[0], base_url="https://api.groq.com/openai/v1")
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"system","content":f"Bạn là NEXUS AI, trợ lý của {CREATOR}. Nói chuyện ngầu, thông minh, bình dân."}] + messages,
            temperature=st.session_state.theme.get("ai_temp", 0.7)
        )
        return res.choices[0].message.content
    except: return "Hệ thống AI đang quá tải, chờ xíu nhé!"

# --- [6] MÀN HÌNH CHỨC NĂNG ---

def screen_ai_chat():
    apply_ui()
    me = st.session_state.auth_status
    lib = st.session_state.chat_library.setdefault(me, {"History": []})
    
    st.title("🧠 NEXUS AI CHAT")
    if st.button("⬅️ VỀ MENU"): st.session_state.stage = "MENU"; st.rerun()

    for m in lib["History"]:
        with st.chat_message(m["role"]): st.write(giai_ma(m["content"]))

    if p := st.chat_input("Hỏi AI..."):
        lib["History"].append({"role": "user", "content": ma_hoa(p)})
        with st.chat_message("user"): st.write(p)
        
        with st.chat_message("assistant"):
            context = [{"role": m["role"], "content": giai_ma(m["content"])} for m in lib["History"][-6:]]
            ai_res = goi_ai(context)
            st.write(ai_res)
            lib["History"].append({"role": "assistant", "content": ma_hoa(ai_res)})
            luu_du_lieu()

def screen_social():
    apply_ui()
    st.title("🌐 CỘNG ĐỒNG NEXUS")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.write("### Nhóm hiện có")
        for g_name in st.session_state.groups.keys():
            if st.button(f"🚪 Vào {g_name}", use_container_width=True):
                st.session_state.current_group = g_name
                st.session_state.stage = "GROUP_CHAT"; st.rerun()
    
    with col2:
        st.write("### Tạo nhóm mới")
        n_g = st.text_input("Tên nhóm")
        t_g = st.selectbox("Chế độ AI", ["FULL_AI", "HALF_AI", "NONE"])
        if st.button("TẠO NHÓM"):
            st.session_state.groups[n_g] = {"type": t_g, "msgs": []}
            luu_du_lieu(); st.success("Đã tạo!"); st.rerun()
    
    if st.button("🏠 VỀ MENU"): st.session_state.stage = "MENU"; st.rerun()

def screen_group_chat():
    apply_ui()
    g_name = st.session_state.current_group
    g_info = st.session_state.groups[g_name]
    st.title(f"🏘️ {g_name} ({g_info['type']})")
    
    if st.button("⬅️ RỜI NHÓM"): st.session_state.stage = "SOCIAL"; st.rerun()

    if g_info['type'] == "HALF_AI":
        with st.sidebar:
            draw_logo()
            ask = st.text_input("Hỏi AI trong nhóm...")
            if st.button("Gửi"): st.info(goi_ai([{"role":"user","content":ask}]))

    for m in g_info['msgs']:
        with st.chat_message("user" if m['user'] != "NEXUS_AI" else "assistant"):
            st.write(f"**{m['user']}**: {giai_ma(m['text'])}")

    if p := st.chat_input("Chat với mọi người..."):
        g_info['msgs'].append({"user": st.session_state.auth_status, "text": ma_hoa(p)})
        if g_info['type'] == "FULL_AI":
            ai_res = goi_ai([{"role":"user", "content": p}])
            g_info['msgs'].append({"user": "NEXUS_AI", "text": ma_hoa(ai_res)})
        luu_du_lieu(); st.rerun()

def screen_admin():
    apply_ui()
    st.title("🛡️ ADMIN CONTROL")
    
    tab1, tab2 = st.tabs(["📊 Lịch sử", "🔨 Hình phạt"])
    with tab1:
        for log in reversed(st.session_state.access_logs):
            agent = log.get("info", "")
            # TỰ ĐỘNG PHÂN TÍCH OS VÀ TRÌNH DUYỆT ĐỂ BỎ DÒNG USER-AGENT RÁC
            os = "Windows" if "Windows" in agent else "Android" if "Android" in agent else "iPhone" if "iPhone" in agent else "MacOS" if "Mac" in agent else "Linux"
            browser = "Chrome" if "Chrome" in agent else "Edge" if "Edg" in agent else "Safari" if "Safari" in agent else "Firefox"
            
            with st.expander(f"👤 {log['user']} | {log['time']}"):
                st.write(f"🖥️ **Hệ điều hành:** {os}")
                st.write(f"🌐 **Trình duyệt:** {browser}")
                # ĐÃ BỎ DÒNG st.code(agent) TẠI ĐÂY THEO YÊU CẦU

    with tab2:
        target = st.selectbox("Chọn user", list(st.session_state.users.keys()))
        reason = st.text_input("Lý do phạm tội")
        if st.button("BAN NGƯỜI NÀY"):
            st.session_state.punishments[target] = {"reason": reason, "until": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")}
            luu_du_lieu(); st.rerun()
            
    if st.button("🏠 MENU"): st.session_state.stage = "MENU"; st.rerun()

# --- [7] ROUTER ---
if st.session_state.stage == "AUTH":
    apply_ui(); draw_logo()
    _, cc, _ = st.columns([1, 1.2, 1])
    with cc:
        st.markdown("<div class='glass'>", unsafe_allow_html=True)
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("LOGIN", use_container_width=True):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.auth_status = u; st.session_state.stage = "MENU"
                st.session_state.access_logs.append({"user": u, "time": datetime.now().strftime("%H:%M:%S"), "info": st.context.headers.get("User-Agent", "")})
                luu_du_lieu(); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.stage == "MENU":
    apply_ui()
    st.title(f"🚀 NEXUS - CHÀO {st.session_state.auth_status.upper()}")
    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    if c1.button("🧠 AI CHAT", use_container_width=True): st.session_state.stage = "AI_CHAT"; st.rerun()
    if c2.button("🌐 COMMUNITY", use_container_width=True): st.session_state.stage = "SOCIAL"; st.rerun()
    if c3.button("⚙️ SETTINGS", use_container_width=True): st.session_state.stage = "SETTINGS"; st.rerun()
    
    if st.session_state.auth_status.lower() == "thiên phát":
        if st.button("🛡️ ADMIN PANEL", use_container_width=True): st.session_state.stage = "ADMIN"; st.rerun()
    if st.button("🚪 LOGOUT", use_container_width=True): st.session_state.stage = "AUTH"; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.stage == "AI_CHAT": screen_ai_chat()
elif st.session_state.stage == "SOCIAL": screen_social()
elif st.session_state.stage == "GROUP_CHAT": screen_group_chat()
elif st.session_state.stage == "ADMIN": screen_admin()
else:
    st.session_state.stage = "MENU"; st.rerun()
