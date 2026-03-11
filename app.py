# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time, base64, json, requests, random, string
from datetime import datetime, timedelta

# --- [1] CẤU HÌNH HỆ THỐNG ---
CREATOR = "Lê Trần Thiên Phát"
VERSION = "V5600 - QUANTUM MAX"
FILE_DATA = "data.json"
SECRET_KEY = "NEXUS_ULTIMATE_KEY_2024"

try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"] # Danh sách key Groq cho Free/Pro
    GEMINI_KEY = st.secrets.get("GEMINI_KEY", "") # Key Gemini cho Pro/Pro Max
except:
    st.error("⚠️ Cấu hình Secrets bị thiếu trên Streamlit Cloud!")
    st.stop()

st.set_page_config(page_title=f"NEXUS OS | {CREATOR}", layout="wide", initial_sidebar_state="collapsed")

# --- [2] CÔNG CỤ NỀN TẢNG (MÃ HÓA & LƯU TRỮ) ---
def ma_hoa(text, tier="free"):
    if not text: return ""
    # Pro Max có thêm 1 lớp XOR đảo ngược để bảo mật cao hơn
    key = SECRET_KEY[::-1] if tier == "promax" else SECRET_KEY
    encoded = "".join([chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(text)])
    return base64.b64encode(encoded.encode()).decode()

def giai_ma(text, tier="free"):
    if not text: return ""
    try:
        decoded = base64.b64decode(text.encode()).decode()
        key = SECRET_KEY[::-1] if tier == "promax" else SECRET_KEY
        return "".join([chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(decoded)])
    except: return text

def get_data_size(obj):
    return len(json.dumps(obj).encode('utf-8'))

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
        "theme": st.session_state.theme, "chat_library": st.session_state.chat_library,
        "groups": st.session_state.groups, "cloud_drive": st.session_state.cloud_drive,
        "access_logs": st.session_state.access_logs, "punishments": st.session_state.punishments,
        "activation_keys": st.session_state.activation_keys, "notice": st.session_state.notice
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

# --- [3] KHỞI TẠO DỮ LIỆU ---
if 'initialized' not in st.session_state:
    db = tai_du_lieu()
    st.session_state.users = db.get("users", {"Thiên Phát": "2002"})
    st.session_state.user_status = db.get("user_status", {}) # free, pro, promax
    st.session_state.activation_keys = db.get("activation_keys", {})
    st.session_state.notice = db.get("notice", {"content": "Sẵn sàng hoạt động.", "is_emergency": False, "id": 0})
    st.session_state.theme = db.get("theme", {"primary_color": "#38BDF8", "bg_list": [], "current_bg_idx": 0})
    st.session_state.chat_library = db.get("chat_library", {})
    st.session_state.groups = db.get("groups", {"Cộng Đồng NEXUS": {"msgs": []}})
    st.session_state.cloud_drive = db.get("cloud_drive", {}) # {user: [{filename, b64_data, size, date}]}
    st.session_state.access_logs = db.get("access_logs", [])
    st.session_state.punishments = db.get("punishments", {})
    st.session_state.stage = "AUTH"
    st.session_state.auth_status = None
    st.session_state.initialized = True

# --- [4] UI & RESPONSIVE DESIGN ---
def apply_ui():
    t = st.session_state.theme
    p_color = t['primary_color']
    bg = t['bg_list'][t['current_bg_idx']] if t['bg_list'] else "#0F172A"
    bg_css = f"url('{bg}') no-repeat center fixed" if "http" in bg else bg
    
    st.markdown(f"""
    <style>
    /* Tổng thể & Nền */
    .stApp {{ background: {bg_css}; background-size: cover; color: #CBD5E1; font-family: 'Segoe UI', sans-serif; }}
    
    /* Box thủy tinh mờ, làm tối lại để dịu mắt */
    .glass-box {{ 
        background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(16px); 
        border-radius: 16px; padding: 24px; border: 1px solid rgba(255,255,255,0.05); 
        box-shadow: 0 10px 30px rgba(0,0,0,0.5); margin-bottom: 20px;
    }}
    
    /* Chữ cái */
    h1, h2, h3 {{ color: #F8FAFC !important; text-shadow: 0 2px 4px rgba(0,0,0,0.8); }}
    
    /* Nút bấm tinh tế, bớt chói */
    .stButton > button {{ 
        background-color: #1E293B !important; color: #94A3B8 !important; 
        border: 1px solid #334155 !important; border-radius: 8px; 
        transition: all 0.3s ease; width: 100%; font-weight: 600;
    }}
    .stButton > button:hover {{ 
        background-color: #0F172A !important; color: {p_color} !important; 
        border-color: {p_color} !important; box-shadow: 0 0 10px {p_color}44;
    }}
    
    /* Nhãn phân cấp */
    .badge-pro {{ background: #F59E0B; color: #fff; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: bold; }}
    .badge-promax {{ background: linear-gradient(90deg, #8B5CF6, #EC4899); color: #fff; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: bold; box-shadow: 0 0 8px #EC4899; }}
    
    [data-testid="stHeader"] {{ visibility: hidden; }}
    </style>
    """, unsafe_allow_html=True)

# --- [5] AI AUTO-SWITCH ENGINE (PRO MAX) ---
def goi_ai(messages, user_tier):
    if user_tier == "promax":
        # Ưu tiên Gemini, nếu lỗi -> tự động nhảy sang Groq 1 -> Groq 2...
        try:
            client = OpenAI(api_key=GEMINI_KEY, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
            return client.chat.completions.create(model="gemini-1.5-flash", messages=messages).choices[0].message.content
        except:
            for key in GROQ_KEYS:
                try:
                    client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
                    return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages).choices[0].message.content
                except: continue
        return "⚠️ Tất cả lõi AI đang quá tải. Hãy thử lại sau 1 phút."
    
    elif user_tier == "pro":
        try:
            client = OpenAI(api_key=GEMINI_KEY, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
            return client.chat.completions.create(model="gemini-1.5-flash", messages=messages).choices[0].message.content
        except: return "⚠️ Token Gemini đã hết hạn mức."
    
    else: # Free (Dùng chung pool Groq)
        try:
            client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
            return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages).choices[0].message.content
        except: return "⚠️ Bể Token Free đã cạn. Vui lòng chờ người khác nhường chỗ."

# --- [6] MODULES CHỨC NĂNG ---

def screen_ai_chat():
    apply_ui()
    me = st.session_state.auth_status
    tier = st.session_state.user_status.get(me, "free")
    lib = st.session_state.chat_library.setdefault(me, {"history": []})
    
    col1, col2 = st.columns([0.8, 0.2])
    col1.title("🧠 AI ASSISTANT")
    if col2.button("⬅️ HOME"): st.session_state.stage = "MENU"; st.rerun()
    
    if st.button("🗑️ XÓA HỘI THOẠI NÀY"):
        st.session_state.chat_library[me]["history"] = []
        luu_du_lieu(); st.rerun()

    st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
    for m in lib['history']:
        with st.chat_message(m['role']): st.write(giai_ma(m['content'], tier))

    if p := st.chat_input("Nhập lệnh cho AI..."):
        lib['history'].append({"role": "user", "content": ma_hoa(p, tier)})
        with st.chat_message("user"): st.write(p)
        with st.chat_message("assistant"):
            with st.spinner("Đang phân tích..."):
                res = goi_ai([{"role": "user", "content": p}], tier)
                st.write(res)
                lib['history'].append({"role": "assistant", "content": ma_hoa(res, tier)})
                luu_du_lieu()
    st.markdown("</div>", unsafe_allow_html=True)

def screen_social():
    apply_ui()
    me = st.session_state.auth_status
    tier = st.session_state.user_status.get(me, "free")
    
    c1, c2 = st.columns([0.8, 0.2])
    c1.title("🌐 NEXUS COMMUNITY")
    if c2.button("⬅️ HOME"): st.session_state.stage = "MENU"; st.rerun()

    gn = "Cộng Đồng NEXUS"
    gi = st.session_state.groups[gn]
    
    st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
    for m in gi['msgs']:
        with st.chat_message("user"):
            st.markdown(f"**{m['user']}**: {giai_ma(m['text'], 'free')}") # Cộng đồng dùng chuẩn chung
    
    if p := st.chat_input("Nhắn gì đó vào nhóm..."):
        gi['msgs'].append({"user": me, "text": ma_hoa(p, 'free')})
        luu_du_lieu(); st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def screen_cloud():
    apply_ui()
    me = st.session_state.auth_status
    tier = st.session_state.user_status.get(me, "free")
    my_files = st.session_state.cloud_drive.setdefault(me, [])
    
    c1, c2 = st.columns([0.8, 0.2])
    c1.title("☁️ NEXUS CLOUD DRIVE")
    if c2.button("⬅️ HOME"): st.session_state.stage = "MENU"; st.rerun()

    # Tính dung lượng
    usage = get_data_size(st.session_state.chat_library.get(me, {})) + get_data_size(my_files)
    limit = 50 * 1024**3 if tier == "promax" else 30 * 1024**3 if tier == "pro" else 5 * 1024**3
    
    st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
    st.progress(min(usage/limit, 1.0))
    st.write(f"📊 Đã dùng: **{usage/1024/1024:.2f} MB** / **{limit/(1024**3):.0f} GB**")
    
    up_file = st.file_uploader("Tải tệp lên Cloud (Giới hạn thực tế của API là dưới 10MB/lần)")
    if up_file:
        if st.button("LƯU TRỮ TỆP NÀY"):
            b64_data = base64.b64encode(up_file.getvalue()).decode()
            my_files.append({
                "name": up_file.name, "data": b64_data,
                "date": datetime.now().strftime("%d/%m/%Y"), "size": len(b64_data)
            })
            luu_du_lieu(); st.success("Đã lưu lên Cloud!"); time.sleep(1); st.rerun()
            
    st.write("---")
    st.write("### Tệp của bạn")
    for idx, f in enumerate(my_files):
        fc1, fc2, fc3 = st.columns([0.6, 0.2, 0.2])
        fc1.write(f"📄 {f['name']} ({f['date']})")
        fc2.download_button("⬇️ Tải về", base64.b64decode(f['data']), file_name=f['name'], key=f"dl_{idx}")
        if fc3.button("🗑️ Xóa", key=f"del_{idx}"):
            my_files.pop(idx); luu_du_lieu(); st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def screen_admin():
    apply_ui()
    st.title("🛡️ ADMIN CONTROL")
    if st.button("⬅️ QUAY LẠI MENU"): st.session_state.stage = "MENU"; st.rerun()
    
    t1, t2 = st.tabs(["🔑 MÃ KÍCH HOẠT", "📢 THÔNG BÁO"])
    with t1:
        c1, c2, c3 = st.columns(3)
        code_val = c1.text_input("Mã kích hoạt (Trống = Random)")
        tier_val = c2.selectbox("Cấp độ", ["pro", "promax"])
        is_global = c3.checkbox("Mã chung (Dùng nhiều lần)")
        
        if st.button("TẠO MÃ"):
            final_code = code_val if code_val else ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            st.session_state.activation_keys[final_code] = {"tier": tier_val, "global": is_global, "used_by": []}
            luu_du_lieu(); st.success(f"Tạo thành công: {final_code}")
            
        st.write(st.session_state.activation_keys)
        
    with t2:
        note = st.text_area("Nội dung", st.session_state.notice['content'])
        is_em = st.checkbox("Khẩn cấp", st.session_state.notice['is_emergency'])
        if st.button("CẬP NHẬT TB"):
            st.session_state.notice = {"content": note, "is_emergency": is_em, "id": random.randint(1,999)}
            luu_du_lieu(); st.success("Đã cập nhật!")

def screen_settings():
    apply_ui()
    me = st.session_state.auth_status
    
    col1, col2 = st.columns([0.8, 0.2])
    col1.title("⚙️ CÀI ĐẶT & NÂNG CẤP")
    if col2.button("⬅️ HOME"): st.session_state.stage = "MENU"; st.rerun()
    
    st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
    st.write("### Nhập mã Nâng cấp")
    code_in = st.text_input("Nhập mã Admin cấp cho bạn")
    if st.button("KÍCH HOẠT"):
        keys = st.session_state.activation_keys
        if code_in in keys:
            k = keys[code_in]
            if k['global'] or (not k['global'] and len(k['used_by']) == 0):
                if me not in k['used_by']:
                    st.session_state.user_status[me] = k['tier']
                    k['used_by'].append(me)
                    luu_du_lieu(); st.success(f"Bạn đã thăng cấp {k['tier'].upper()}!"); time.sleep(1); st.rerun()
                else: st.warning("Bạn đã dùng mã này rồi.")
            else: st.error("Mã đã được sử dụng.")
        else: st.error("Mã không hợp lệ.")
    st.markdown("</div>", unsafe_allow_html=True)

# --- [7] ROUTER CHÍNH ---
if st.session_state.stage == "AUTH":
    apply_ui()
    _, cc, _ = st.columns([1, 1.2, 1])
    with cc:
        st.markdown("<div class='glass-box' style='text-align:center;'>", unsafe_allow_html=True)
        st.write("<h2>NEXUS GATEWAY</h2>", unsafe_allow_html=True)
        u = st.text_input("Định danh")
        p = st.text_input("Mật mã", type="password")
        if st.button("ĐĂNG NHẬP"):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.auth_status = u; st.session_state.stage = "MENU"
                st.session_state.access_logs.append({"user": u, "time": datetime.now().strftime("%d/%m %H:%M"), "info": st.context.headers.get("User-Agent", "")})
                luu_du_lieu(); st.rerun()
            else: st.error("Thông tin sai!")
        st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.stage == "MENU":
    apply_ui()
    me = st.session_state.auth_status
    tier = st.session_state.user_status.get(me, "free")
    
    # Check Thông báo khẩn
    if st.session_state.notice['is_emergency'] and st.session_state.last_notice_seen != st.session_state.notice['id']:
        st.warning(f"🚨 **THÔNG BÁO KHẨN TỪ ADMIN:**\n\n{st.session_state.notice['content']}")
        if st.button("ĐÃ ĐỌC"): st.session_state.last_notice_seen = st.session_state.notice['id']; st.rerun()
        st.stop()

    # Header Menu
    st.markdown(f"<h2>🚀 NEXUS | {me.upper()}</h2>", unsafe_allow_html=True)
    if tier == "promax": st.markdown("<span class='badge-promax'>👑 PRO MAX</span>", unsafe_allow_html=True)
    elif tier == "pro": st.markdown("<span class='badge-pro'>💎 PRO MEMBER</span>", unsafe_allow_html=True)
    
    # Khối chức năng
    st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)
    
    if c1.button("🧠 AI CHAT"): st.session_state.stage = "AI_CHAT"; st.rerun()
    if c2.button("🌐 CỘNG ĐỒNG"): st.session_state.stage = "SOCIAL"; st.rerun()
    if c3.button("☁️ CLOUD DRIVE"): st.session_state.stage = "CLOUD"; st.rerun()
    if c4.button("⚙️ CÀI ĐẶT"): st.session_state.stage = "SETTINGS"; st.rerun()
    
    st.write("---")
    if me.lower() == "thiên phát" and st.button("🛡️ ADMIN PANEL"): st.session_state.stage = "ADMIN"; st.rerun()
    if st.button("🚪 ĐĂNG XUẤT"): st.session_state.stage = "AUTH"; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.stage == "AI_CHAT": screen_ai_chat()
elif st.session_state.stage == "SOCIAL": screen_social()
elif st.session_state.stage == "CLOUD": screen_cloud()
elif st.session_state.stage == "SETTINGS": screen_settings()
elif st.session_state.stage == "ADMIN": screen_admin()
else:
    st.session_state.stage = "MENU"; st.rerun()
