# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time, base64, json, requests
from datetime import datetime, timedelta

# --- [1] CẤU HÌNH ---
CREATOR = "Lê Trần Thiên Phát"
VERSION = "V5300 - NEXUS MULTIVERSE"
FILE_DATA = "data.json"
SECRET_KEY = "NEXUS_ULTIMATE_KEY_2024"

# Thư viện hình nền mặc định (Chủ đề Sci-fi, Cyberpunk)
NEXUS_LIBRARY = [
    "https://images.unsplash.com/photo-1614728894747-a83421e2b9c9?q=80&w=1920",
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1920",
    "https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=1920",
    "https://images.unsplash.com/photo-1531297484001-80022131f5a1?q=80&w=1920",
    "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=1920"
]

try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
except:
    st.error("❌ Cấu hình Secrets bị thiếu!")
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
        payload = {"message": f"Nexus Update", "content": content, "sha": sha} if sha else {"message": "Init", "content": content}
        requests.put(url, headers=headers, json=payload)
    except: pass

# --- [3] KHỞI TẠO ---
if 'initialized' not in st.session_state:
    db = tai_du_lieu()
    st.session_state.users = db.get("users", {"Thiên Phát": "2002"})
    st.session_state.profiles = db.get("profiles", {})
    
    t_db = db.get("theme", {})
    st.session_state.theme = {
        "primary_color": t_db.get("primary_color", "#00f2ff"),
        "bg_list": t_db.get("bg_list", NEXUS_LIBRARY), # Sử dụng thư viện sẵn có
        "auto_rotate": t_db.get("auto_rotate", True),
        "rotate_min": t_db.get("rotate_min", 5),
        "current_bg_idx": t_db.get("current_bg_idx", 0),
        "last_rotate": t_db.get("last_rotate", str(datetime.now()))
    }
    
    st.session_state.chat_library = db.get("chat_library", {})
    st.session_state.groups = db.get("groups", {"Sảnh Chung": {"type": "FULL_AI", "msgs": []}})
    st.session_state.access_logs = db.get("access_logs", [])
    st.session_state.punishments = db.get("punishments", {})
    st.session_state.stage = "AUTH"
    st.session_state.auth_status = None
    st.session_state.initialized = True

# --- [4] UI ---
def apply_ui():
    t = st.session_state.theme
    p_color = t['primary_color']
    
    # Auto rotate logic
    if t['auto_rotate'] and t['bg_list']:
        last = datetime.strptime(t['last_rotate'], "%Y-%m-%d %H:%M:%S.%f")
        if datetime.now() > last + timedelta(minutes=t['rotate_min']):
            t['current_bg_idx'] = (t['current_bg_idx'] + 1) % len(t['bg_list'])
            t['last_rotate'] = str(datetime.now())
    
    bg = t['bg_list'][t['current_bg_idx']] if t['bg_list'] else ""
    st.markdown(f"""
    <style>
    .stApp {{ background: url('{bg}') no-repeat center fixed; background-size: cover; color: #E0E0E0; }}
    .glass {{ background: rgba(10, 15, 25, 0.85); backdrop-filter: blur(12px); border-radius: 15px; padding: 20px; border: 1px solid {p_color}44; }}
    .stButton > button {{ background: rgba(0,0,0,0.4); color: {p_color}; border: 1px solid {p_color}; border-radius: 8px; }}
    .stButton > button:hover {{ background: {p_color}; color: #000; box-shadow: 0 0 20px {p_color}; }}
    [data-testid="stHeader"] {{ visibility: hidden; }}
    </style>
    """, unsafe_allow_html=True)

def draw_logo():
    color = st.session_state.theme['primary_color']
    st.markdown(f"""
    <div style="display: flex; flex-direction: column; align-items: center; margin-bottom: 20px;">
        <div style="width: 60px; height: 60px; border: 3px solid {color}; border-radius: 50%; border-top-color: transparent; animation: spin 1s linear infinite;"></div>
        <div style="color: {color}; font-size: 20px; font-weight: bold; margin-top: 10px; letter-spacing: 5px;">NEXUS</div>
    </div>
    <style> @keyframes spin {{ 100% {{ transform: rotate(360deg); }} }} </style>
    """, unsafe_allow_html=True)

# --- [5] MÀN HÌNH CHỨC NĂNG ---

def screen_settings():
    apply_ui()
    st.title("⚙️ CÀI ĐẶT & BẢO MẬT")
    me = st.session_state.auth_status
    
    with st.expander("🔐 ĐỔI MẬT KHẨU"):
        old_p = st.text_input("Mật khẩu cũ", type="password")
        new_p = st.text_input("Mật khẩu mới", type="password")
        if st.button("XÁC NHẬN ĐỔI"):
            if st.session_state.users[me] == old_p:
                st.session_state.users[me] = new_p
                luu_du_lieu(); st.success("Đã đổi mật khẩu thành công!")
            else: st.error("Mật khẩu cũ không đúng!")

    with st.expander("🖼️ THƯ VIỆN HÌNH NỀN"):
        st.write("Đang sử dụng thư viện NEXUS CLOUD (Auto-Update)")
        t = st.session_state.theme
        t['auto_rotate'] = st.checkbox("Tự động đổi nền", t['auto_rotate'])
        t['rotate_min'] = st.slider("Thời gian đổi (phút)", 1, 60, t['rotate_min'])
        if st.button("LƯU CẤU HÌNH"): luu_du_lieu(); st.rerun()

    if st.button("⬅️ QUAY LẠI"): st.session_state.stage = "MENU"; st.rerun()

def screen_group_chat():
    apply_ui()
    gn = st.session_state.current_group
    gi = st.session_state.groups[gn]
    me = st.session_state.auth_status
    
    st.title(f"🏘️ NHÓM: {gn}")
    if st.button("⬅️ RỜI NHÓM"): st.session_state.stage = "SOCIAL"; st.rerun()

    # Hiển thị tin nhắn
    for m in gi['msgs']:
        with st.chat_message("user" if m['user'] == me else "assistant"):
            st.write(f"**{m['user']}**:")
            if "file" in m:
                st.info(f"📁 Tệp đính kèm: {m['filename']}")
                st.download_button("Tải xuống tệp", base64.b64decode(m['file']), file_name=m['filename'])
            st.write(giai_ma(m['text']))

    # Gửi tin & File
    with st.container():
        msg = st.chat_input("Nhập tin nhắn...")
        up_file = st.file_uploader("Đính kèm tệp (Tùy chọn)", label_visibility="collapsed")
        
        if msg:
            new_msg = {"user": me, "text": ma_hoa(msg)}
            if up_file:
                new_msg["file"] = base64.b64encode(up_file.getvalue()).decode()
                new_msg["filename"] = up_file.name
            
            gi['msgs'].append(new_msg)
            
            # AI phản hồi nếu là FULL_AI
            if gi['type'] == "FULL_AI":
                try:
                    client = OpenAI(api_key=GROQ_KEYS[0], base_url="https://api.groq.com/openai/v1")
                    res = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role":"user", "content": f"Trong nhóm chat, {me} vừa gửi: {msg}. Hãy phản hồi ngắn gọn."}]
                    )
                    gi['msgs'].append({"user": "NEXUS_AI", "text": ma_hoa(res.choices[0].message.content)})
                except: pass
            
            luu_du_lieu(); st.rerun()

def screen_admin():
    apply_ui()
    st.title("🛡️ KIỂM SOÁT HỆ THỐNG")
    for log in reversed(st.session_state.access_logs):
        agent = log.get('info', '')
        os = "Windows" if "Windows" in agent else "Android" if "Android" in agent else "iPhone" if "iPhone" in agent else "MacOS" if "Mac" in agent else "Linux"
        browser = "Chrome" if "Chrome" in agent else "Edge" if "Edg" in agent else "Safari" if "Safari" in agent else "Firefox"
        with st.expander(f"👤 {log['user']} | {log['time']}"):
            st.write(f"🖥️ **Hệ điều hành:** {os} | 🌐 **Trình duyệt:** {browser}")

    if st.button("⬅️ MENU"): st.session_state.stage = "MENU"; st.rerun()

# --- [6] ROUTER ---
if st.session_state.stage == "AUTH":
    apply_ui(); draw_logo()
    _, cc, _ = st.columns([1, 1.2, 1])
    with cc:
        st.markdown("<div class='glass'>", unsafe_allow_html=True)
        u = st.text_input("Định danh")
        p = st.text_input("Mật mã", type="password")
        if st.button("KẾT NỐI", use_container_width=True):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.auth_status = u; st.session_state.stage = "MENU"
                st.session_state.access_logs.append({"user": u, "time": datetime.now().strftime("%H:%M:%S"), "info": st.context.headers.get("User-Agent", "")})
                luu_du_lieu(); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.stage == "MENU":
    apply_ui()
    st.title(f"🚀 XIN CHÀO, {st.session_state.auth_status.upper()}")
    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    if c1.button("🧠 AI CHAT", use_container_width=True): st.session_state.stage = "CHAT"; st.rerun()
    if c2.button("🌐 CỘNG ĐỒNG", use_container_width=True): st.session_state.stage = "SOCIAL"; st.rerun()
    if c3.button("⚙️ CÀI ĐẶT", use_container_width=True): st.session_state.stage = "SETTINGS"; st.rerun()
    if st.session_state.auth_status.lower() == "thiên phát":
        if st.button("🛡️ ADMIN PANEL", use_container_width=True): st.session_state.stage = "ADMIN"; st.rerun()
    if st.button("🚪 ĐĂNG XUẤT", use_container_width=True): st.session_state.stage = "AUTH"; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.stage == "SETTINGS": screen_settings()
elif st.session_state.stage == "GROUP_CHAT": screen_group_chat()
elif st.session_state.stage == "ADMIN": screen_admin()
elif st.session_state.stage == "SOCIAL": 
    apply_ui(); st.title("🌐 CỘNG ĐỒNG")
    for g in st.session_state.groups:
        if st.button(f"🚪 Vào nhóm {g}", use_container_width=True):
            st.session_state.current_group = g; st.session_state.stage = "GROUP_CHAT"; st.rerun()
    if st.button("⬅️ MENU"): st.session_state.stage = "MENU"; st.rerun()
else:
    st.session_state.stage = "MENU"; st.rerun()
