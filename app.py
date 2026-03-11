# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time, base64, json, requests, random, string
from datetime import datetime

# --- [1] CẤU HÌNH HỆ THỐNG ---
SYSTEM_NAME = "NEXUS"
VERSION = "V6200 - SUPER NOVA"
FILE_DATA = "data.json"
SECRET_KEY = "NEXUS_ULTIMATE_KEY_2024"

WALLPAPERS = [
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1920",
    "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=1920",
    "https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=1920"
]

# Kiểm tra Secrets
try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS]
    GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")
except Exception as e:
    st.error(f"❌ Thiếu Secrets cấu hình: {e}")
    st.stop()

st.set_page_config(page_title=SYSTEM_NAME, layout="wide", initial_sidebar_state="collapsed")

# --- [2] CÔNG CỤ DỮ LIỆU ---
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
        requests.put(url, headers=headers, json={"message": "Nexus Sync", "content": content, "sha": sha})
    except: pass

# --- [3] KHỞI TẠO TRẠNG THÁI (CHỐNG MÀN HÌNH TRẮNG) ---
def init_all():
    if 'initialized' not in st.session_state:
        db = tai_du_lieu()
        st.session_state.users = db.get("users", {"Thiên Phát": "2002"})
        st.session_state.user_status = db.get("user_status", {"Thiên Phát": "promax"})
        st.session_state.chat_library = db.get("chat_library", {})
        st.session_state.groups = db.get("groups", {"Sảnh Chung": {"msgs": []}})
        st.session_state.cloud_drive = db.get("cloud_drive", {})
        st.session_state.tickets = db.get("tickets", [])
        st.session_state.activation_keys = db.get("activation_keys", {})
        st.session_state.notice = db.get("notice", {"content": "Hệ thống Nexus Online.", "is_emergency": False, "id": 0})
        st.session_state.stage = "AUTH"
        st.session_state.auth_status = None
        st.session_state.initialized = True

init_all()

# --- [4] GIAO DIỆN SƯƠNG MỜ ---
def apply_ui():
    bg = random.choice(WALLPAPERS)
    st.markdown(f"""
    <style>
    .stApp {{ background: url('{bg}') no-repeat center fixed; background-size: cover; color: #F8FAFC; }}
    /* Hiệu ứng sương mờ Deep Blur */
    .glass-card, .stChatMessage, [data-testid="stExpander"], .stSidebar {{
        background: rgba(15, 23, 42, 0.7) !important;
        backdrop-filter: blur(15px) saturate(160%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px !important;
        padding: 15px;
        margin-bottom: 15px;
    }}
    .stButton > button {{ 
        background: rgba(30, 41, 59, 0.8) !important; 
        color: #38BDF8 !important; border: 1px solid #38BDF8 !important; 
        border-radius: 10px; transition: 0.3s; width: 100%;
    }}
    .stButton > button:hover {{ background: #38BDF8 !important; color: #0F172A !important; transform: translateY(-2px); }}
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
        try:
            client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
            res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages)
            return res.choices[0].message.content
        except Exception as e: return f"⚠️ Hệ thống AI quá tải: {str(e)}"

def ai_dat_ten(text):
    prompt = [{"role": "user", "content": f"Đặt 1 cái tên tiêu đề ngắn (3-5 từ) cho cuộc trò chuyện về: {text}"}]
    try:
        res = goi_ai(prompt, "free")
        return res.strip().replace('"', '')
    except: return "Hội thoại mới"

# --- [6] CÁC MÀN HÌNH CHỨC NĂNG ---

def screen_ai_chat():
    apply_ui()
    me = st.session_state.auth_status
    tier = st.session_state.user_status.get(me, "free")
    lib = st.session_state.chat_library.setdefault(me, {"sessions": {"Cuộc trò chuyện mới": []}, "active": "Cuộc trò chuyện mới"})
    
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        new_name = st.text_input("📍 Tiêu đề hội thoại", value=lib["active"])
        if new_name != lib["active"]:
            lib["sessions"][new_name] = lib["sessions"].pop(lib["active"])
            lib["active"] = new_name
            luu_du_lieu(); st.rerun()
    if col2.button("⬅️ HOME"): st.session_state.stage = "MENU"; st.rerun()

    with st.sidebar:
        st.subheader("Cấu hình AI")
        limit = st.slider("Trí nhớ (số tin nhắn)", 1, 40, 10)
        if st.button("➕ Hội thoại mới"):
            n = f"Chat {len(lib['sessions'])+1}"
            lib["sessions"][n] = []; lib["active"] = n; st.rerun()
        for s in list(lib["sessions"].keys()):
            if st.button(f"💬 {s}"): lib["active"] = s; st.rerun()

    history = lib["sessions"][lib["active"]]
    for m in history:
        with st.chat_message(m['role']): st.write(giai_ma(m['content'], tier))

    if p := st.chat_input("Hỏi Nexus..."):
        if not history:
            lib["active"] = ai_dat_ten(p)
            lib["sessions"][lib["active"]] = lib["sessions"].pop("Cuộc trò chuyện mới")
            history = lib["sessions"][lib["active"]]

        history.append({"role": "user", "content": ma_hoa(p, tier)})
        with st.chat_message("user"): st.write(p)
        with st.chat_message("assistant"):
            ctx = [{"role": m['role'], "content": giai_ma(m['content'], tier)} for m in history[-limit:]]
            res = goi_ai(ctx, tier)
            st.write(res)
            history.append({"role": "assistant", "content": ma_hoa(res, tier)})
            luu_du_lieu()

def screen_social():
    apply_ui()
    st.title("🌐 CỘNG ĐỒNG NEXUS")
    if st.button("⬅️ QUAY LẠI"): st.session_state.stage = "MENU"; st.rerun()
    
    group = st.session_state.groups.setdefault("Sảnh Chung", {"msgs": []})
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    for m in group['msgs'][-30:]:
        with st.chat_message("user"): st.write(f"**{m['user']}**: {giai_ma(m['text'])}")
    
    if st.session_state.auth_status != "Guest":
        if p := st.chat_input("Nhắn tin vào sảnh..."):
            group['msgs'].append({"user": st.session_state.auth_status, "text": ma_hoa(p)})
            luu_du_lieu(); st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def screen_cloud():
    apply_ui()
    me = st.session_state.auth_status
    st.title("☁️ NEXUS CLOUD STORAGE")
    if st.button("⬅️ HOME"): st.session_state.stage = "MENU"; st.rerun()
    
    my_files = st.session_state.cloud_drive.setdefault(me, [])
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    up = st.file_uploader("Chọn tệp")
    if up and st.button("🚀 TẢI LÊN"):
        my_files.append({"name": up.name, "data": base64.b64encode(up.getvalue()).decode(), "date": datetime.now().strftime("%d/%m/%Y")})
        luu_du_lieu(); st.success("Đã xong!"); st.rerun()
    
    for idx, f in enumerate(my_files):
        c1, c2, c3 = st.columns([0.7, 0.15, 0.15])
        c1.write(f"📄 {f['name']}")
        c2.download_button("💾", base64.b64decode(f['data']), file_name=f['name'], key=f"d_{idx}")
        if c3.button("🗑️", key=f"del_{idx}"):
            my_files.pop(idx); luu_du_lieu(); st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def screen_admin():
    apply_ui()
    st.title("🛡️ SUPREME ADMIN")
    if st.button("⬅️ MENU"): st.session_state.stage = "MENU"; st.rerun()
    t1, t2 = st.tabs(["📥 YÊU CẦU", "📢 THÔNG BÁO"])
    with t1:
        for t in [x for x in st.session_state.tickets if x['status'] == 'open']:
            st.warning(f"Từ: {t['user']} | Loại: {t['type']}")
            st.write(t['content'])
            rep = st.text_input("Phản hồi/Mã quà", key=f"r_{t['id']}")
            if st.button("GỬI PHẢN HỒI", key=f"b_{t['id']}"):
                t['reply'] = rep; t['status'] = 'closed'; luu_du_lieu(); st.rerun()

# --- [7] ROUTER ---
if st.session_state.stage == "AUTH":
    apply_ui()
    _, cc, _ = st.columns([1, 1.2, 1])
    with cc:
        st.markdown("<div class='glass-card' style='text-align:center;'>", unsafe_allow_html=True)
        st.title("NEXUS LOGIN")
        m = st.tabs(["Vào", "Tạo", "Khách"])
        with m[0]:
            u = st.text_input("Tên")
            p = st.text_input("Mật mã", type="password")
            if st.button("TIẾN VÀO"):
                if u in st.session_state.users and st.session_state.users[u] == p:
                    st.session_state.auth_status = u; st.session_state.stage = "MENU"; st.rerun()
        with m[1]:
            nu = st.text_input("Tên mới"); np = st.text_input("Mật mã mới", type="password")
            if st.button("ĐĂNG KÝ"):
                st.session_state.users[nu] = np; luu_du_lieu(); st.success("Xong!")
        with m[2]:
            if st.button("VÀO VỚI QUYỀN GUEST"):
                st.session_state.auth_status = "Guest"; st.session_state.stage = "MENU"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.stage == "MENU":
    apply_ui()
    st.title(f"🚀 NEXUS | {st.session_state.auth_status.upper()}")
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    c1, c2 = st.columns(2); c3, c4 = st.columns(2)
    if c1.button("🧠 AI CHAT"): st.session_state.stage = "AI_CHAT"; st.rerun()
    if c2.button("🌐 COMMUNITY"): st.session_state.stage = "SOCIAL"; st.rerun()
    if c3.button("☁️ STORAGE"): st.session_state.stage = "CLOUD"; st.rerun()
    if c4.button("🎧 SUPPORT"): st.session_state.stage = "SUPPORT"; st.rerun()
    
    st.write("---")
    if st.button("⚙️ SETTINGS"): st.session_state.stage = "SETTINGS"; st.rerun()
    if st.session_state.auth_status == "Thiên Phát" and st.button("🛡️ ADMIN PANEL"): 
        st.session_state.stage = "ADMIN"; st.rerun()
    if st.button("🚪 ĐĂNG XUẤT"): st.session_state.stage = "AUTH"; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.stage == "AI_CHAT": screen_ai_chat()
elif st.session_state.stage == "SOCIAL": screen_social()
elif st.session_state.stage == "CLOUD": screen_cloud()
elif st.session_state.stage == "ADMIN": screen_admin()
elif st.session_state.stage == "SUPPORT":
    apply_ui()
    st.title("🎧 HỖ TRỢ")
    if st.button("⬅️ HOME"): st.session_state.stage = "MENU"; st.rerun()
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    tp = st.selectbox("Vấn đề", ["Mua bản Pro", "Lỗi phần mềm", "Khác"])
    ct = st.text_area("Chi tiết")
    if st.button("GỬI"):
        st.session_state.tickets.append({"id": str(random.randint(1,999)), "user": st.session_state.auth_status, "type": tp, "content": ct, "status": "open", "reply": ""})
        luu_du_lieu(); st.success("Đã gửi!"); st.rerun()
    for t in reversed(st.session_state.tickets):
        if t['user'] == st.session_state.auth_status:
            with st.expander(f"[{t['status'].upper()}] {t['type']}"):
                st.write(t['content'])
                if t['reply']: st.info(f"Admin: {t['reply']}")
    st.markdown("</div>", unsafe_allow_html=True)
elif st.session_state.stage == "SETTINGS":
    apply_ui()
    st.title("⚙️ CÀI ĐẶT")
    if st.button("⬅️ HOME"): st.session_state.stage = "MENU"; st.rerun()
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    code = st.text_input("Nhập mã kích hoạt")
    if st.button("KÍCH HOẠT"):
        if code in st.session_state.activation_keys:
            st.session_state.user_status[st.session_state.auth_status] = st.session_state.activation_keys[code]['tier']
            luu_du_lieu(); st.success("Nâng cấp thành công!"); st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
