# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time, base64, json, requests, random, string, sys
from datetime import datetime, timedelta

# --- [1] CẤU HÌNH & SECRETS ---
CREATOR = "Lê Trần Thiên Phát"
VERSION = "V5400 - NEXUS PRO SYSTEM"
FILE_DATA = "data.json"
SECRET_KEY = "NEXUS_ULTIMATE_KEY_2024"

# Thư viện ảnh Sci-fi
NEXUS_LIBRARY = [
    "https://images.unsplash.com/photo-1614728894747-a83421e2b9c9?q=80&w=1920",
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1920",
    "https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=1920"
]

try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"] # List 4 key cho Free
    GEMINI_KEY = st.secrets.get("GEMINI_KEY", "") # Key riêng cho Pro
except:
    st.error("Cấu hình Secrets bị thiếu!")
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

def get_size(obj):
    """Tính dung lượng dữ liệu (bytes)"""
    return len(json.dumps(obj))

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
        "activation_keys": st.session_state.activation_keys,
        "notice": st.session_state.notice, "user_status": st.session_state.user_status,
        "chat_library": st.session_state.chat_library
    }
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, indent=4).encode()).decode()
        payload = {"message": "Nexus Update", "content": content, "sha": sha}
        requests.put(url, headers=headers, json=payload)
    except: pass

# --- [3] KHỞI TẠO ---
if 'initialized' not in st.session_state:
    db = tai_du_lieu()
    st.session_state.users = db.get("users", {"Thiên Phát": "2002"})
    st.session_state.user_status = db.get("user_status", {}) # {user: "pro" / "free"}
    st.session_state.activation_keys = db.get("activation_keys", {}) # {code: {expiry, is_global, used_by:[]}}
    st.session_state.notice = db.get("notice", {"content": "Chào mừng đến Nexus!", "is_emergency": False, "id": 0})
    st.session_state.theme = db.get("theme", {"primary_color": "#00f2ff", "bg_list": NEXUS_LIBRARY, "auto_rotate": True, "rotate_min": 5, "current_bg_idx": 0, "last_rotate": str(datetime.now())})
    st.session_state.profiles = db.get("profiles", {})
    st.session_state.groups = db.get("groups", {"Sảnh Chung": {"type": "FULL_AI", "msgs": []}})
    st.session_state.chat_library = db.get("chat_library", {})
    st.session_state.access_logs = db.get("access_logs", [])
    st.session_state.punishments = db.get("punishments", {})
    st.session_state.stage = "AUTH"
    st.session_state.auth_status = None
    st.session_state.last_notice_seen = -1
    st.session_state.initialized = True

# --- [4] UI & LOGIC BỘ NHỚ ---
def apply_ui():
    t = st.session_state.theme
    p_color = t['primary_color']
    bg = t['bg_list'][t['current_bg_idx']] if t['bg_list'] else ""
    st.markdown(f"""
    <style>
    .stApp {{ background: url('{bg}') no-repeat center fixed; background-size: cover; color: #E0E0E0; }}
    .glass {{ background: rgba(10, 15, 25, 0.85); backdrop-filter: blur(10px); border-radius: 15px; padding: 20px; border: 1px solid {p_color}33; }}
    .pro-badge {{ background: linear-gradient(45deg, #ffd700, #ff8c00); color: black; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }}
    </style>
    """, unsafe_allow_html=True)

def get_user_storage(user):
    """Tính tổng dung lượng data của user này"""
    total = 0
    total += get_size(st.session_state.profiles.get(user, {}))
    total += get_size(st.session_state.chat_library.get(user, {}))
    # Tính thêm các file trong nhóm chat nếu user đó gửi
    for g in st.session_state.groups.values():
        for m in g['msgs']:
            if m.get('user') == user: total += get_size(m)
    return total

# --- [5] XỬ LÝ AI THEO PHÂN CẤP ---
def goi_ai(messages, model_choice="Llama-3"):
    user = st.session_state.auth_status
    is_pro = st.session_state.user_status.get(user) == "pro"
    
    try:
        if is_pro and "Gemini" in model_choice:
            # Dùng Gemini cho Pro
            client = OpenAI(api_key=GEMINI_KEY, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
            model_name = "gemini-1.5-flash"
        else:
            # Dùng Pool Groq cho Free/Pro
            key = random.choice(GROQ_KEYS)
            client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
            model_name = "llama-3.3-70b-versatile" if "Llama" in model_choice else "mixtral-8x7b-32768"

        res = client.chat.completions.create(model=model_name, messages=messages)
        return res.choices[0].message.content
    except Exception as e:
        return f"⚠️ Token đã hết hoặc lỗi: {str(e)[:50]}... Vui lòng đợi!"

# --- [6] MÀN HÌNH CHỨC NĂNG ---

def screen_admin():
    apply_ui()
    st.title("🛡️ SUPREME ADMIN PANEL")
    tab1, tab2, tab3 = st.tabs(["🔑 Activation Keys", "📢 Notice Board", "📊 Users & Logs"])
    
    with tab1:
        st.subheader("Tạo mã kích hoạt Pro")
        c1, c2, c3 = st.columns(3)
        with c1: 
            new_code = st.text_input("Mã (Để trống để tạo ngẫu nhiên)")
            if st.button("🎲 Random Code"): new_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        with c2: 
            expiry = st.date_input("Ngày hết hạn", datetime.now() + timedelta(days=30))
            is_inf = st.checkbox("Vô hạn thời gian")
        with c3:
            is_glob = st.checkbox("Mã toàn cầu (Tất cả có thể nhập)")
        
        if st.button("🔥 PHÁT HÀNH MÃ"):
            code = new_code if new_code else ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            st.session_state.activation_keys[code] = {
                "expiry": "infinite" if is_inf else str(expiry),
                "is_global": is_glob, "used_by": []
            }
            luu_du_lieu(); st.success(f"Đã tạo mã: {code}")

        st.write("---")
        for c, v in st.session_state.activation_keys.items():
            st.code(f"Mã: {c} | Hạn: {v['expiry']} | Global: {v['is_global']}")

    with tab2:
        st.subheader("Quản lý bảng thông báo")
        content = st.text_area("Nội dung thông báo", st.session_state.notice['content'])
        is_em = st.checkbox("⚠️ THÔNG BÁO KHẨN (Hiện ngay khi đăng nhập)", st.session_state.notice['is_emergency'])
        if st.button("CẬP NHẬT THÔNG BÁO"):
            st.session_state.notice = {"content": content, "is_emergency": is_em, "id": random.randint(1, 9999)}
            luu_du_lieu(); st.success("Đã cập nhật!")

    if st.button("⬅️ MENU"): st.session_state.stage = "MENU"; st.rerun()

def screen_settings():
    apply_ui()
    me = st.session_state.auth_status
    st.title("⚙️ CÀI ĐẶT TÀI KHOẢN")
    
    # Nhập mã Pro
    st.subheader("💎 Kích hoạt Premium")
    code_input = st.text_input("Nhập mã kích hoạt của bạn")
    if st.button("XÁC THỰC MÃ"):
        keys = st.session_state.activation_keys
        if code_input in keys:
            k = keys[code_input]
            # Check expiry
            valid = True
            if k['expiry'] != "infinite":
                if datetime.now() > datetime.strptime(k['expiry'], "%Y-%m-%d"): valid = False
            
            if valid:
                if not k['is_global'] and len(k['used_by']) > 0:
                    st.error("Mã này đã được sử dụng!")
                elif me in k['used_by']:
                    st.warning("Bạn đã dùng mã này rồi!")
                else:
                    st.session_state.user_status[me] = "pro"
                    k['used_by'].append(me)
                    luu_du_lieu(); st.success("CHÚC MỪNG! BẠN ĐÃ LÀ THÀNH VIÊN PRO!"); time.sleep(1); st.rerun()
            else: st.error("Mã đã hết hạn!")
        else: st.error("Mã không hợp lệ!")

    # Hiển thị dung lượng
    st.write("---")
    usage = get_user_storage(me)
    limit = 30 * 1024 * 1024 * 1024 if st.session_state.user_status.get(me) == "pro" else 5 * 1024 * 1024 * 1024
    st.write(f"📁 **Dung lượng Cloud:** {usage / 1024:.2f} KB / {limit / (1024**3):.1f} GB")
    st.progress(min(usage / limit, 1.0))
    
    if st.button("⬅️ QUAY LẠI"): st.session_state.stage = "MENU"; st.rerun()

# --- [7] CHAT & COMMUNITY ---

def screen_ai_chat():
    apply_ui()
    me = st.session_state.auth_status
    is_pro = st.session_state.user_status.get(me) == "pro"
    st.title("🧠 AI ASSISTANT")
    
    model = st.selectbox("Chọn bộ não AI", ["Llama-3 (Standard)", "Mixtral (Creative)", "Gemini 1.5 (Pro Only)"] if is_pro else ["Llama-3 (Standard)"])
    
    lib = st.session_state.chat_library.setdefault(me, {"history": []})
    for m in lib['history']:
        with st.chat_message(m['role']): st.write(giai_ma(m['content']))

    if p := st.chat_input("Hỏi Nexus AI..."):
        lib['history'].append({"role": "user", "content": ma_hoa(p)})
        with st.chat_message("user"): st.write(p)
        
        with st.chat_message("assistant"):
            with st.spinner("AI đang suy nghĩ..."):
                res = goi_ai([{"role": "user", "content": p}], model)
                st.write(res)
                lib['history'].append({"role": "assistant", "content": ma_hoa(res)})
                luu_du_lieu()

# --- [8] ROUTER CHÍNH ---
if st.session_state.stage == "AUTH":
    apply_ui()
    _, cc, _ = st.columns([1, 1.2, 1])
    with cc:
        st.markdown("<div class='glass'>", unsafe_allow_html=True)
        st.subheader("NEXUS GATEWAY")
        u = st.text_input("Định danh")
        p = st.text_input("Mật mã", type="password")
        if st.button("ĐĂNG NHẬP", use_container_width=True):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.auth_status = u; st.session_state.stage = "MENU"
                st.session_state.access_logs.append({"user": u, "time": datetime.now().strftime("%H:%M:%S"), "info": st.context.headers.get("User-Agent", "")})
                luu_du_lieu(); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.stage == "MENU":
    apply_ui()
    me = st.session_state.auth_status
    is_pro = st.session_state.user_status.get(me) == "pro"
    
    # KIỂM TRA THÔNG BÁO KHẨN
    if st.session_state.notice['is_emergency'] and st.session_state.last_notice_seen != st.session_state.notice['id']:
        st.warning(f"🚨 **THÔNG BÁO KHẨN TỪ ADMIN:**\n\n{st.session_state.notice['content']}")
        if st.button("Đã rõ"): st.session_state.last_notice_seen = st.session_state.notice['id']; st.rerun()
        st.stop()

    # GIAO DIỆN MENU
    st.title(f"🚀 NEXUS OS | {me}")
    if is_pro: st.markdown("<span class='pro-badge'>💎 PRO MEMBER</span>", unsafe_allow_html=True)
    
    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    if c1.button("🧠 AI CHAT", use_container_width=True): st.session_state.stage = "AI_CHAT"; st.rerun()
    if c2.button("🌐 CỘNG ĐỒNG", use_container_width=True): st.session_state.stage = "SOCIAL"; st.rerun()
    if c3.button("⚙️ SETTINGS", use_container_width=True): st.session_state.stage = "SETTINGS"; st.rerun()
    
    if st.button("📢 BẢNG THÔNG BÁO", use_container_width=True):
        st.info(f"📌 **CẬP NHẬT MỚI NHẤT:**\n\n{st.session_state.notice['content']}")
        
    if me.lower() == "thiên phát":
        if st.button("🛡️ ADMIN PANEL", use_container_width=True): st.session_state.stage = "ADMIN"; st.rerun()
    if st.button("🚪 ĐĂNG XUẤT", use_container_width=True): st.session_state.stage = "AUTH"; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.stage == "AI_CHAT": screen_ai_chat()
elif st.session_state.stage == "ADMIN": screen_admin()
elif st.session_state.stage == "SETTINGS": screen_settings()
elif st.session_state.stage == "SOCIAL":
    apply_ui(); st.title("🌐 CỘNG ĐỒNG")
    for g in st.session_state.groups:
        if st.button(f"🚪 Vào nhóm {g}", use_container_width=True):
            st.session_state.current_group = g; st.session_state.stage = "GROUP_CHAT"; st.rerun()
    if st.button("⬅️ MENU"): st.session_state.stage = "MENU"; st.rerun()
else:
    st.session_state.stage = "MENU"; st.rerun()
