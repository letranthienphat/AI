# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time, base64, json, requests, random, string
from datetime import datetime, timedelta

# --- [1] CẤU HÌNH HỆ THỐNG ---
CREATOR = "Lê Trần Thiên Phát"
VERSION = "V5500 - NEXUS QUANTUM PRO"
FILE_DATA = "data.json"
SECRET_KEY = "NEXUS_ULTIMATE_KEY_2024"

try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"] # List 4 keys
    GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")
except:
    st.error("Cấu hình Secrets bị thiếu!")
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

def get_data_size(obj):
    """Tính dung lượng dữ liệu tính theo Bytes"""
    return len(json.dumps(obj).encode('utf-8'))

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
        "profiles": st.session_state.profiles, "groups": st.session_state.groups,
        "access_logs": st.session_state.access_logs, "punishments": st.session_state.punishments,
        "activation_keys": st.session_state.activation_keys, "notice": st.session_state.notice,
        "user_status": st.session_state.user_status, "chat_library": st.session_state.chat_library
    }
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, indent=4).encode()).decode()
        payload = {"message": f"Nexus Sync {datetime.now()}", "content": content, "sha": sha}
        requests.put(url, headers=headers, json=payload)
    except: pass

# --- [3] KHỞI TẠO ---
if 'initialized' not in st.session_state:
    db = tai_du_lieu()
    st.session_state.users = db.get("users", {"Thiên Phát": "2002"})
    st.session_state.user_status = db.get("user_status", {})
    st.session_state.activation_keys = db.get("activation_keys", {})
    st.session_state.notice = db.get("notice", {"content": "Hệ thống đã sẵn sàng.", "is_emergency": False, "id": 0})
    st.session_state.theme = db.get("theme", {"primary_color": "#00f2ff", "bg_list": [], "auto_rotate": True, "rotate_min": 5, "current_bg_idx": 0, "last_rotate": str(datetime.now())})
    st.session_state.profiles = db.get("profiles", {})
    st.session_state.groups = db.get("groups", {"Sảnh Chung": {"type": "FULL_AI", "msgs": []}})
    st.session_state.chat_library = db.get("chat_library", {})
    st.session_state.access_logs = db.get("access_logs", [])
    st.session_state.punishments = db.get("punishments", {})
    st.session_state.stage = "AUTH"
    st.session_state.auth_status = None
    st.session_state.last_notice_seen = -1
    st.session_state.initialized = True

# --- [4] GIAO DIỆN ---
def apply_ui():
    t = st.session_state.theme
    p_color = t['primary_color']
    bg_list = t.get('bg_list', [])
    bg = bg_list[t['current_bg_idx']] if bg_list else "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1920"
    
    st.markdown(f"""
    <style>
    .stApp {{ background: url('{bg}') no-repeat center fixed; background-size: cover; color: #ced4da; }}
    .glass-card {{ background: rgba(10, 15, 25, 0.85); backdrop-filter: blur(10px); border-radius: 12px; padding: 20px; border: 1px solid {p_color}44; }}
    .pro-tag {{ background: linear-gradient(90deg, #FFD700, #FFA500); color: black; padding: 2px 10px; border-radius: 20px; font-weight: 800; font-size: 12px; }}
    h1, h2, h3 {{ color: {p_color} !important; text-shadow: 0 0 10px {p_color}44; }}
    </style>
    """, unsafe_allow_html=True)

# --- [5] XỬ LÝ AI ---
def goi_ai(messages, model_choice):
    me = st.session_state.auth_status
    is_pro = st.session_state.user_status.get(me) == "pro"
    try:
        if is_pro and "Gemini" in model_choice:
            client = OpenAI(api_key=GEMINI_KEY, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
            model = "gemini-1.5-flash"
        else:
            client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
            model = "llama-3.3-70b-versatile"
        
        res = client.chat.completions.create(model=model, messages=messages)
        return res.choices[0].message.content
    except Exception as e: return f"Lỗi AI: {str(e)[:50]}"

# --- [6] CÁC MÀN HÌNH ---

def screen_admin():
    apply_ui()
    st.title("🛡️ NEXUS SUPREME ADMIN")
    t1, t2, t3 = st.tabs(["🔑 MÃ KÍCH HOẠT", "📢 THÔNG BÁO", "📊 LOGS"])
    
    with t1:
        c1, c2, c3 = st.columns(3)
        with c1: 
            code_val = st.text_input("Mã kích hoạt", placeholder="Để trống để Random")
            if st.button("🎲 TẠO NGẪU NHIÊN"): code_val = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
        with c2:
            h_dung = st.date_input("Hạn dùng", datetime.now() + timedelta(days=30))
            is_inf = st.checkbox("Vô hạn")
        with c3:
            is_global = st.checkbox("Mã chung (Mọi người đều dùng được)")
            
        if st.button("🚀 PHÁT HÀNH MÃ"):
            final_code = code_val if code_val else ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
            st.session_state.activation_keys[final_code] = {
                "expiry": "vô hạn" if is_inf else str(h_dung),
                "global": is_global, "used_by": []
            }
            luu_du_lieu(); st.success(f"Đã tạo mã: {final_code}")

    with t2:
        new_note = st.text_area("Nội dung thông báo", st.session_state.notice['content'])
        is_em = st.checkbox("⚠️ THÔNG BÁO KHẨN CẤP", st.session_state.notice['is_emergency'])
        if st.button("CẬP NHẬT"):
            st.session_state.notice = {"content": new_note, "is_emergency": is_em, "id": random.randint(1, 9999)}
            luu_du_lieu(); st.rerun()

    if st.button("⬅️ QUAY LẠI MENU"): st.session_state.stage = "MENU"; st.rerun()

def screen_ai_chat():
    apply_ui()
    me = st.session_state.auth_status
    is_pro = st.session_state.user_status.get(me) == "pro"
    
    st.title("🧠 NEXUS AI ASSISTANT")
    if st.button("⬅️ QUAY LẠI MENU"): st.session_state.stage = "MENU"; st.rerun()
    
    # SỬA LỖI KEYERROR TẠI ĐÂY: Sử dụng .setdefault và .get an toàn
    user_lib = st.session_state.chat_library.setdefault(me, {"history": []})
    history = user_lib.get("history", [])
    
    model = st.selectbox("Chọn bộ não AI", ["Llama-3 (Free/Pro)", "Gemini 1.5 (Chỉ Pro)"] if is_pro else ["Llama-3 (Free)"])

    for m in history:
        with st.chat_message(m['role']): st.write(giai_ma(m['content']))

    if p := st.chat_input("Hỏi AI..."):
        history.append({"role": "user", "content": ma_hoa(p)})
        with st.chat_message("user"): st.write(p)
        
        with st.chat_message("assistant"):
            res = goi_ai([{"role": "user", "content": p}], model)
            st.write(res)
            history.append({"role": "assistant", "content": ma_hoa(res)})
            st.session_state.chat_library[me]["history"] = history
            luu_du_lieu()

def screen_settings():
    apply_ui()
    me = st.session_state.auth_status
    st.title("⚙️ CÀI ĐẶT")
    
    # Kích hoạt Pro
    st.subheader("💎 NÂNG CẤP PRO")
    c_in = st.text_input("Nhập mã kích hoạt của bạn")
    if st.button("XÁC NHẬN MÃ"):
        keys = st.session_state.activation_keys
        if c_in in keys:
            k = keys[c_in]
            if k['global'] or (not k['global'] and len(k['used_by']) == 0):
                if me not in k['used_by']:
                    st.session_state.user_status[me] = "pro"
                    k['used_by'].append(me)
                    luu_du_lieu(); st.success("💎 CHÚC MỪNG! BẠN ĐÃ LÊN PRO!"); time.sleep(1); st.rerun()
                else: st.warning("Bạn đã dùng mã này rồi.")
            else: st.error("Mã này đã có người sử dụng.")
        else: st.error("Mã không đúng.")

    # Thống kê bộ nhớ
    st.write("---")
    usage = get_data_size(st.session_state.chat_library.get(me, {})) + get_data_size(st.session_state.profiles.get(me, {}))
    limit = 30 * 1024**3 if st.session_state.user_status.get(me) == "pro" else 5 * 1024**3
    st.write(f"📁 **Lưu trữ Cloud:** {usage/1024:.2f} KB / {limit/(1024**3):.1f} GB")
    st.progress(min(usage/limit, 1.0))

    if st.button("⬅️ QUAY LẠI MENU"): st.session_state.stage = "MENU"; st.rerun()

# --- [7] ROUTER CHÍNH ---
if st.session_state.stage == "AUTH":
    apply_ui()
    _, cc, _ = st.columns([1, 1.2, 1])
    with cc:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("NEXUS GATEWAY")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("TIẾN VÀO", use_container_width=True):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.auth_status = u; st.session_state.stage = "MENU"
                st.session_state.access_logs.append({"user": u, "time": datetime.now().strftime("%d/%m %H:%M"), "info": st.context.headers.get("User-Agent", "")})
                luu_du_lieu(); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.stage == "MENU":
    apply_ui()
    me = st.session_state.auth_status
    
    # THÔNG BÁO KHẨN
    if st.session_state.notice['is_emergency'] and st.session_state.last_notice_seen != st.session_state.notice['id']:
        st.warning(f"🚨 **THÔNG BÁO KHẨN:**\n\n{st.session_state.notice['content']}")
        if st.button("ĐÃ ĐỌC"): st.session_state.last_notice_seen = st.session_state.notice['id']; st.rerun()
        st.stop()

    st.title(f"🚀 NEXUS | {me.upper()}")
    if st.session_state.user_status.get(me) == "pro": st.markdown("<span class='pro-tag'>💎 PRO MEMBER</span>", unsafe_allow_html=True)
    
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    if c1.button("🧠 AI CHAT", use_container_width=True): st.session_state.stage = "AI_CHAT"; st.rerun()
    if c2.button("🌐 CỘNG ĐỒNG", use_container_width=True): st.session_state.stage = "SOCIAL"; st.rerun()
    if c3.button("⚙️ CÀI ĐẶT", use_container_width=True): st.session_state.stage = "SETTINGS"; st.rerun()
    
    if st.button("📢 BẢNG THÔNG BÁO", use_container_width=True):
        st.info(f"📌 **CẬP NHẬT:**\n\n{st.session_state.notice['content']}")

    if me.lower() == "thiên phát" and st.button("🛡️ ADMIN PANEL", use_container_width=True): st.session_state.stage = "ADMIN"; st.rerun()
    if st.button("🚪 ĐĂNG XUẤT", use_container_width=True): st.session_state.stage = "AUTH"; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.stage == "AI_CHAT": screen_ai_chat()
elif st.session_state.stage == "ADMIN": screen_admin()
elif st.session_state.stage == "SETTINGS": screen_settings()
elif st.session_state.stage == "SOCIAL":
    apply_ui(); st.title("🌐 CỘNG ĐỒNG")
    if st.button("⬅️ QUAY LẠI MENU"): st.session_state.stage = "MENU"; st.rerun()
    # Hiển thị các nhóm chat...
else:
    st.session_state.stage = "MENU"; st.rerun()
