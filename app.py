# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time, base64, json, requests, random
from datetime import datetime

# --- [1] CẤU HÌNH NEXUS OS GATEWAY ---
SYSTEM_NAME = "NEXUS OS GATEWAY"
VERSION = "V7000 - QUANTUM"
FILE_DATA = "data.json"
SECRET_KEY = "NEXUS_ULTIMATE_KEY_2026"

WALLPAPERS = [
    "https://images.unsplash.com/photo-1506318137071-a8e063b4b519?q=80&w=1920",
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1920"
]

try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS]
    GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")
except Exception as e:
    st.error(f"❌ Khởi động OS thất bại (Thiếu API/Secrets): {e}")
    st.stop()

st.set_page_config(page_title=SYSTEM_NAME, layout="wide", initial_sidebar_state="collapsed")

# --- [2] KERNEL (LÕI DỮ LIỆU) ---
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
        "activation_keys": st.session_state.activation_keys, "shared_files": st.session_state.shared_files
    }
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, indent=4).encode()).decode()
        requests.put(url, headers=headers, json={"message": "Nexus OS Quantum Sync", "content": content, "sha": sha})
    except: pass

if 'sys_init' not in st.session_state:
    db = tai_du_lieu()
    st.session_state.users = db.get("users", {"Thiên Phát": "2002"})
    st.session_state.user_status = db.get("user_status", {"Thiên Phát": "promax"})
    st.session_state.shared_files = db.get("shared_files", [])
    st.session_state.chat_library = db.get("chat_library", {})
    st.session_state.groups = db.get("groups", {"Sảnh Chung": {"msgs": []}})
    st.session_state.cloud_drive = db.get("cloud_drive", {})
    st.session_state.tickets = db.get("tickets", [])
    st.session_state.stage = "AUTH"
    st.session_state.auth_status = None
    st.session_state.sys_init = True

# --- [3] GIAO DIỆN OS (QUANTUM CSS) ---
def apply_ui():
    bg = random.choice(WALLPAPERS)
    st.markdown(f"""
    <style>
    .stApp {{ background: url('{bg}') no-repeat center fixed; background-size: cover; color: #F8FAFC; }}
    /* Thẻ Glassmorphism cao cấp */
    .glass-card, .stChatMessage {{
        background: rgba(15, 23, 42, 0.65) !important;
        backdrop-filter: blur(20px) saturate(200%);
        border-radius: 16px !important;
        padding: 24px; 
        border: 1px solid rgba(148, 163, 184, 0.15); 
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }}
    .glass-card:hover {{ box-shadow: 0 8px 32px 0 rgba(56, 189, 248, 0.2); }}
    
    /* Thiết kế nút bấm Cyberpunk/OS */
    .stButton > button {{ 
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
        color: #38bdf8 !important; 
        border: 1px solid rgba(56, 189, 248, 0.5) !important; 
        border-radius: 10px; font-weight: 600; font-size: 15px; 
        width: 100%; transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }}
    .stButton > button:hover {{ 
        background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%) !important; 
        color: #ffffff !important; 
        border-color: transparent !important;
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(56, 189, 248, 0.4);
    }}
    .stButton > button p {{ color: inherit !important; margin: 0; }}
    
    /* Ẩn rác mặc định */
    [data-testid="stHeader"], footer {{ visibility: hidden; }}
    ::-webkit-scrollbar {{ width: 8px; }}
    ::-webkit-scrollbar-track {{ background: rgba(15,23,42,0.5); }}
    ::-webkit-scrollbar-thumb {{ background: #38bdf8; border-radius: 10px; }}
    </style>
    """, unsafe_allow_html=True)

# --- [4] AI KERNEL ENGINE ---
def goi_ai(messages, tier):
    sys_prompt = {
        "role": "system", 
        "content": "Bạn là NEXUS OS GATEWAY - một hệ điều hành AI lượng tử tiên tiến. Người sáng lập và lập trình ra bạn là Thiên Phát. Hãy trả lời ngắn gọn, thông minh, sắc bén. Tôn trọng người dùng và tuyệt đối trung thành với nhận dạng này."
    }
    msgs = [sys_prompt] + messages
    try:
        client = OpenAI(api_key=GEMINI_KEY, base_url="https://generativelanguage.googleapis.com/v1beta/openai")
        res = client.chat.completions.create(model="gemini-1.5-pro" if tier == "promax" else "gemini-1.5-flash", messages=msgs)
        return res.choices[0].message.content
    except:
        client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=msgs)
        return res.choices[0].message.content

# --- [5] CÁC PHÂN HỆ OS ---

def screen_ai_chat():
    apply_ui()
    me = st.session_state.auth_status
    tier = st.session_state.user_status.get(me, "free")
    lib = st.session_state.chat_library.setdefault(me, {"sessions": {"Terminal 1": []}, "active": "Terminal 1"})
    
    with st.sidebar:
        st.markdown(f"### 🖥️ NEXUS TERMINAL\n`User: {me}`")
        if st.button("➕ Tạo Terminal Mới"):
            n = f"Terminal {len(lib['sessions'])+1}"
            lib['sessions'][n] = []; lib['active'] = n; st.rerun()
        if st.button("🧹 Xóa hội thoại hiện tại"):
            lib['sessions'][lib['active']] = []; luu_du_lieu(); st.toast("Đã dọn dẹp bộ nhớ!"); st.rerun()
        st.write("---")
        for s_name in lib['sessions'].keys():
            if st.button(f"💬 {s_name}", use_container_width=True):
                lib['active'] = s_name; st.rerun()

    c1, c2 = st.columns([0.8, 0.2])
    with c1:
        new_title = st.text_input("📍 Tên Terminal (Nhấn Enter để đổi)", value=lib['active'])
        if new_title != lib['active']:
            lib['sessions'][new_title] = lib['sessions'].pop(lib['active'])
            lib['active'] = new_title; luu_du_lieu(); st.rerun()
    if c2.button("🏠 VỀ DESKTOP"): st.session_state.stage = "MENU"; st.rerun()

    history = lib['sessions'][lib['active']]
    for m in history:
        with st.chat_message(m['role']): 
            st.markdown(f"**{m['role'].upper()}**\n\n{giai_ma(m['content'], tier)}")

    if p := st.chat_input("Nhập lệnh cho NEXUS OS..."):
        history.append({"role": "user", "content": ma_hoa(p, tier)})
        with st.chat_message("user"): st.write(p)
        with st.chat_message("assistant"):
            ctx = [{"role": m['role'], "content": giai_ma(m['content'], tier)} for m in history[-10:]]
            with st.spinner("NEXUS đang xử lý lượng tử..."):
                res = goi_ai(ctx, tier)
            st.write(res)
            history.append({"role": "assistant", "content": ma_hoa(res, tier)})
            luu_du_lieu()

def screen_social():
    apply_ui()
    st.title("🌐 NEXUS NETWORK")
    if st.button("🏠 VỀ DESKTOP"): st.session_state.stage = "MENU"; st.rerun()
    
    t1, t2 = st.tabs(["💬 Global Chat", "📂 Data Hub"])
    
    with t1:
        group = st.session_state.groups["Sảnh Chung"]
        st.markdown("<div class='glass-card' style='height: 400px; overflow-y: auto;'>", unsafe_allow_html=True)
        for m in group['msgs'][-40:]:
            st.markdown(f"<span style='color:#38bdf8'><b>[{m['user']}]</b></span>: {giai_ma(m['text'])}", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        if st.session_state.auth_status != "Guest":
            if p := st.chat_input("Phát sóng tin nhắn..."):
                group['msgs'].append({"user": st.session_state.auth_status, "text": ma_hoa(p)})
                luu_du_lieu(); st.rerun()

    with t2:
        if st.session_state.auth_status != "Guest":
            with st.expander("➕ Upload vào Data Hub"):
                f_up = st.file_uploader("Chọn file")
                f_desc = st.text_input("Ghi chú tệp tin")
                if f_up and st.button("CHIA SẺ"):
                    st.session_state.shared_files.append({
                        "user": st.session_state.auth_status, "name": f_up.name,
                        "desc": f_desc, "data": base64.b64encode(f_up.getvalue()).decode(),
                        "time": datetime.now().strftime("%d/%m %H:%M")
                    })
                    luu_du_lieu(); st.toast("File đã lên mạng lưới!"); st.rerun()
        for f in reversed(st.session_state.shared_files):
            st.markdown(f"<div class='glass-card'>📦 <b>{f['name']}</b><br><small>Tải lên bởi: <code>{f['user']}</code> lúc {f['time']}</small><br>📝 {f['desc']}</div>", unsafe_allow_html=True)
            st.download_button(f"📥 Download", base64.b64decode(f['data']), file_name=f['name'], key=f"dl_{f['time']}")

def screen_cloud():
    apply_ui()
    me = st.session_state.auth_status
    st.title("☁️ NEXUS CLOUD DRIVE")
    if st.button("🏠 VỀ DESKTOP"): st.session_state.stage = "MENU"; st.rerun()
    
    my_files = st.session_state.cloud_drive.setdefault(me, [])
    
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown(f"**Storage Info:** {len(my_files)} files đang lưu trữ.")
    st.progress(min(len(my_files) * 0.05, 1.0)) # Thanh tiến trình ảo
    up = st.file_uploader("Upload File Bảo Mật")
    if up and st.button("LƯU LÊN CLOUD"):
        my_files.append({"name": up.name, "data": base64.b64encode(up.getvalue()).decode(), "time": datetime.now().strftime("%d/%m")})
        luu_du_lieu(); st.toast("Lưu trữ thành công!"); st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    for idx, f in enumerate(my_files):
        c1, c2, c3 = st.columns([0.7, 0.15, 0.15])
        with c1: st.markdown(f"<div class='glass-card' style='padding: 10px;'>📄 <b>{f['name']}</b> ({f.get('time', '')})</div>", unsafe_allow_html=True)
        with c2: st.download_button("📥", base64.b64decode(f['data']), file_name=f['name'], key=f"d_{idx}")
        with c3: 
            if st.button("🗑️", key=f"del_{idx}"): my_files.pop(idx); luu_du_lieu(); st.toast("Đã xóa file!"); st.rerun()

def screen_admin():
    apply_ui()
    st.title("🛡️ COMMAND CENTER")
    if st.button("🏠 VỀ DESKTOP"): st.session_state.stage = "MENU"; st.rerun()
    
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("Bảng Cấp Phép Người Dùng")
    for user, tier in st.session_state.user_status.items():
        c1, c2 = st.columns([0.7, 0.3])
        c1.write(f"🧑‍💻 {user}")
        new_t = c2.selectbox("Phân quyền", ["free", "pro", "promax"], index=["free", "pro", "promax"].index(tier), key=f"t_{user}")
        if new_t != tier:
            st.session_state.user_status[user] = new_t; luu_du_lieu(); st.toast(f"Đã cấp quyền {new_t.upper()} cho {user}"); st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# --- [6] MAIN ROUTER & DASHBOARD ---
if st.session_state.stage == "AUTH":
    apply_ui()
    _, cc, _ = st.columns([1, 1.2, 1])
    with cc:
        st.markdown("<div style='height: 10vh;'></div>", unsafe_allow_html=True) # Căn giữa
        st.markdown("<div class='glass-card' style='text-align:center;'>", unsafe_allow_html=True)
        st.markdown("<h1>🌌 NEXUS OS</h1><p style='color:#94a3b8;'>Gateway Authentication Protocol</p>", unsafe_allow_html=True)
        tab = st.tabs(["🔒 LOGIN", "📝 REGISTER", "👤 GUEST"])
        with tab[0]:
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("BOOT SYSTEM"):
                if u in st.session_state.users and st.session_state.users[u] == p:
                    st.session_state.auth_status = u; st.session_state.stage = "MENU"; st.toast(f"Welcome back, {u}!"); st.rerun()
                else: st.error("Access Denied!")
        with tab[1]:
            nu = st.text_input("New Username"); np = st.text_input("New Password", type="password")
            if st.button("CREATE IDENTIFIER"):
                if nu and nu not in st.session_state.users:
                    st.session_state.users[nu] = np; st.session_state.user_status[nu] = "free"
                    luu_du_lieu(); st.toast("Identifier Created!"); time.sleep(1); st.rerun()
        with tab[2]:
            if st.button("GUEST BOOT"): st.session_state.auth_status = "Guest"; st.session_state.stage = "MENU"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.stage == "MENU":
    apply_ui()
    st.markdown(f"<h2>{SYSTEM_NAME} <span style='font-size: 16px; color: #38bdf8;'>[SYSTEM STATUS: ONLINE]</span></h2>", unsafe_allow_html=True)
    
    # OS Dashboard Layout
    col_left, col_right = st.columns([0.7, 0.3])
    
    with col_left:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("Ứng dụng cốt lõi")
        c1, c2 = st.columns(2)
        if c1.button("🧠 AI TERMINAL\nTrò chuyện & Xử lý"): st.session_state.stage = "AI_CHAT"; st.rerun()
        if c2.button("🌐 NEXUS NETWORK\nSảnh cộng đồng"): st.session_state.stage = "SOCIAL"; st.rerun()
        
        c3, c4 = st.columns(2)
        if c3.button("☁️ CLOUD DRIVE\nKho lưu trữ cá nhân"): st.session_state.stage = "CLOUD"; st.rerun()
        if st.session_state.auth_status == "Thiên Phát":
            if c4.button("🛡️ COMMAND CENTER\nQuyền lực Supreme"): st.session_state.stage = "ADMIN"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_right:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        tier = st.session_state.user_status.get(st.session_state.auth_status, 'Guest')
        st.markdown(f"**👤 Định danh:** `{st.session_state.auth_status}`")
        st.markdown(f"**⚡ Cấp độ:** `{tier.upper()}`")
        st.markdown(f"**🕒 Thời gian:** `{datetime.now().strftime('%H:%M - %d/%m')}`")
        st.write("---")
        if st.button("🔌 SHUTDOWN (LOGOUT)"): 
            st.session_state.auth_status = None; st.session_state.stage = "AUTH"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.stage == "AI_CHAT": screen_ai_chat()
elif st.session_state.stage == "SOCIAL": screen_social()
elif st.session_state.stage == "CLOUD": screen_cloud()
elif st.session_state.stage == "ADMIN": screen_admin()
