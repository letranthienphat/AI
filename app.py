# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time, base64, json, requests
from datetime import datetime

# --- [1] CẤU HÌNH ---
CREATOR = "Lê Trần Thiên Phát"
VERSION = "V4800 - NEXUS GATEWAY"
FILE_DATA = "data.json"
SECRET_KEY = "NEXUS_ULTIMATE_KEY_2024"

try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
except:
    st.error("👉 Vui lòng dán Keys vào Secrets trên Streamlit Cloud!")
    st.stop()

st.set_page_config(page_title=f"NEXUS OS | {CREATOR}", layout="wide")

# --- [2] CÔNG CỤ NỀN TẢNG ---
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
        "chat_library": st.session_state.chat_library, "friends": st.session_state.friends,
        "friend_requests": st.session_state.friend_requests, "groups": st.session_state.groups,
        "access_logs": st.session_state.get("access_logs", [])
    }
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, indent=4).encode()).decode()
        payload = {"message": f"Nexus Update {datetime.now()}", "content": content}
        if sha: payload["sha"] = sha
        requests.put(url, headers=headers, json=payload)
    except: pass

# --- [3] KHỞI TẠO ---
if 'initialized' not in st.session_state:
    db = tai_du_lieu()
    st.session_state.users = db.get("users", {"admin": "123", "Thiên Phát": "2002"})
    st.session_state.theme = db.get("theme", {"primary_color": "#00f2ff", "bg_url": ""})
    st.session_state.friends = db.get("friends", {})
    st.session_state.friend_requests = db.get("friend_requests", {})
    st.session_state.groups = db.get("groups", {}) # {name: {"type": "FULL_AI", "msgs": []}}
    st.session_state.access_logs = db.get("access_logs", [])
    st.session_state.chat_library = db.get("chat_library", {})
    st.session_state.stage = "AUTH"
    st.session_state.auth_status = None
    st.session_state.initialized = True

# --- [4] UI & LOGO ---
def apply_ui():
    t = st.session_state.theme
    p_color = t['primary_color']
    bg = f"url('{t['bg_url']}')" if t['bg_url'] else "#0f172a"
    st.markdown(f"""
    <style>
    .stApp {{ background: {bg} no-repeat center fixed; background-size: cover; color: #F8F9FA; }}
    .glass-box {{
        background: rgba(15, 23, 42, 0.8) !important;
        backdrop-filter: blur(12px); border-radius: 15px; padding: 20px; border: 1px solid {p_color}33;
    }}
    h1, h2, h3, p, label {{ color: #F8F9FA !important; text-shadow: 0px 2px 4px rgba(0,0,0,0.3); }}
    .stButton > button {{ background: rgba(30, 41, 59, 0.7); color: #F8F9FA; border: 1px solid {p_color}; border-radius: 8px; }}
    .stButton > button:hover {{ background: {p_color}; color: #000; }}
    </style>
    """, unsafe_allow_html=True)

def draw_logo():
    color = st.session_state.theme.get('primary_color', '#00f2ff')
    st.markdown(f"""
    <div style="display: flex; flex-direction: column; align-items: center; margin-bottom: 20px;">
        <div style="width: 80px; height: 80px; border-radius: 50%; border: 4px solid {color}; 
                    border-top-color: transparent; animation: spin 2s linear infinite; 
                    display: flex; align-items: center; justify-content: center; box-shadow: 0 0 20px {color}66;">
            <div style="width: 30px; height: 30px; background: {color}; border-radius: 50%; animation: pulse 1.5s infinite;"></div>
        </div>
        <div style="color: #F8F9FA; font-weight: 800; letter-spacing: 2px; margin-top: 10px;">NEXUS GATEWAY</div>
    </div>
    <style>
    @keyframes spin {{ 100% {{ transform: rotate(360deg); }} }}
    @keyframes pulse {{ 0%, 100% {{ transform: scale(0.8); opacity: 0.5; }} 50% {{ transform: scale(1.1); opacity: 1; }} }}
    </style>
    """, unsafe_allow_html=True)

# --- [5] XỬ LÝ AI ---
def goi_ai(messages, temp=0.7):
    try:
        client = OpenAI(api_key=GROQ_KEYS[0], base_url="https://api.groq.com/openai/v1")
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"system","content":"Bạn là thành viên trong nhóm chat Nexus. Nói chuyện tự nhiên, bình dân."}] + messages,
            temperature=temp
        )
        return res.choices[0].message.content
    except: return "Hệ thống AI đang bận xử lý..."

# --- [6] MÀN HÌNH CỘNG ĐỒNG ---
def screen_social():
    apply_ui()
    me = st.session_state.auth_status
    st.title("🌐 NEXUS COMMUNITY")
    
    tab1, tab2, tab3 = st.tabs(["👥 Bạn bè", "🏘️ Nhóm Chat", "➕ Tạo Nhóm"])
    
    with tab1:
        # Kết bạn & Lời mời (Giữ logic cũ đã sửa lỗi)
        st.subheader("Lời mời kết bạn")
        reqs = st.session_state.friend_requests.get(me, [])
        for r in reqs:
            c1, c2 = st.columns([0.7, 0.3])
            c1.write(f"🔔 **{r}** muốn kết bạn")
            if c2.button("Đồng ý", key=f"acc_{r}"):
                st.session_state.friends.setdefault(me, []).append(r)
                st.session_state.friends.setdefault(r, []).append(me)
                st.session_state.friend_requests[me].remove(r)
                luu_du_lieu(); st.rerun()

    with tab2:
        st.subheader("Danh sách nhóm")
        for g_name, g_info in st.session_state.groups.items():
            type_label = "🤖 AI Toàn phần" if g_info['type'] == "FULL_AI" else "🌗 AI Bán phần" if g_info['type'] == "HALF_AI" else "👤 Người"
            if st.button(f"{g_name} ({type_label})", use_container_width=True):
                st.session_state.current_group = g_name
                st.session_state.stage = "GROUP_CHAT"
                st.rerun()

    with tab3:
        st.subheader("Tạo nhóm mới")
        new_g_name = st.text_input("Tên nhóm")
        g_type = st.selectbox("Chế độ AI", ["FULL_AI", "HALF_AI", "NONE"], format_func=lambda x: "🤖 AI Toàn phần (Tự thảo luận)" if x=="FULL_AI" else "🌗 AI Bán phần (Thanh bên)" if x=="HALF_AI" else "👤 Không có AI")
        if st.button("Khởi tạo nhóm"):
            if new_g_name and new_g_name not in st.session_state.groups:
                st.session_state.groups[new_g_name] = {"type": g_type, "msgs": []}
                luu_du_lieu(); st.success("Đã tạo nhóm!"); st.rerun()

    if st.button("🏠 VỀ MENU"): st.session_state.stage = "MENU"; st.rerun()

def screen_group_chat():
    apply_ui()
    g_name = st.session_state.current_group
    g_info = st.session_state.groups[g_name]
    me = st.session_state.auth_status

    st.title(f"🏘️ Nhóm: {g_name}")
    
    if g_info['type'] == "HALF_AI":
        with st.sidebar:
            st.write("### 🌗 Trợ lý nhóm")
            ask = st.text_input("Hỏi riêng AI trong nhóm...")
            if st.button("Hỏi"):
                res = goi_ai([{"role":"user","content": ask}])
                st.info(res)

    # Hiển thị tin nhắn
    for m in g_info['msgs']:
        with st.chat_message("user" if m['user'] == me else "assistant"):
            st.write(f"**{m['user']}**: {giai_ma(m['text'])}")

    if p := st.chat_input("Gửi tin nhắn..."):
        # Người gửi
        g_info['msgs'].append({"user": me, "text": ma_hoa(p)})
        
        # Nếu là FULL_AI, AI sẽ tự trả lời ngay trong dòng chat
        if g_info['type'] == "FULL_AI":
            context = [{"role": "user" if m['user'] != "NEXUS_AI" else "assistant", "content": giai_ma(m['text'])} for m in g_info['msgs'][-5:]]
            ai_res = goi_ai(context)
            g_info['msgs'].append({"user": "NEXUS_AI", "text": ma_hoa(ai_res)})
        
        luu_du_lieu(); st.rerun()

    if st.button("⬅️ RỜI NHÓM"): st.session_state.stage = "SOCIAL"; st.rerun()

# --- [7] ROUTER ---
if st.session_state.stage == "AUTH":
    apply_ui(); draw_logo()
    _, cc, _ = st.columns([1, 1.5, 1])
    with cc:
        st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
        u = st.text_input("Tên đăng nhập")
        p = st.text_input("Mật khẩu", type="password")
        if st.button("VÀO HỆ THỐNG", use_container_width=True):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.auth_status = u; st.session_state.stage = "MENU"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.stage == "MENU":
    apply_ui()
    st.title(f"CHÀO {st.session_state.auth_status.upper()}")
    st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    if c1.button("🧠 AI CHAT"): st.session_state.stage = "CHAT"; st.rerun()
    if c2.button("🌐 CỘNG ĐỒNG"): st.session_state.stage = "SOCIAL"; st.rerun()
    if c3.button("⚙️ CÀI ĐẶT"): st.session_state.stage = "SETTINGS"; st.rerun()
    if st.button("🛡️ ADMIN", use_container_width=True) and st.session_state.auth_status.lower() == "thiên phát":
        st.session_state.stage = "ADMIN"; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.stage == "SOCIAL": screen_social()
elif st.session_state.stage == "GROUP_CHAT": screen_group_chat()
elif st.session_state.stage == "CHAT": 
    # Thêm lại screen_chat() từ bản trước của bạn vào đây
    st.write("Màn hình AI Chat riêng tư")
    if st.button("Về Menu"): st.session_state.stage = "MENU"; st.rerun()
