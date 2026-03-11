# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time, base64, json, requests, random, string
from datetime import datetime

# --- [1] CẤU HÌNH HỆ THỐNG ---
SYSTEM_NAME = "NEXUS"
VERSION = "V6000 - ETERNITY"
FILE_DATA = "data.json"
SECRET_KEY = "NEXUS_ULTIMATE_KEY_2024"

# Kho hình nền nghệ thuật tự động
WALLPAPERS = [
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1920",
    "https://images.unsplash.com/photo-1534972195531-d756b9bfa9f2?q=80&w=1920",
    "https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=1920"
]

try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS]
    GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")
except:
    st.error("⚠️ Cấu hình Secrets bị thiếu trên Streamlit Cloud!")
    st.stop()

st.set_page_config(page_title=SYSTEM_NAME, layout="wide", initial_sidebar_state="collapsed")

# --- [2] CÔNG CỤ XỬ LÝ DỮ LIỆU ---
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
        payload = {"message": "Nexus Sync", "content": content, "sha": sha}
        requests.put(url, headers=headers, json=payload)
    except: pass

# --- [3] HÀM TỰ SỬA LỖI KEYERROR ---
def kiem_tra_du_lieu():
    """Đảm bảo mọi biến cần thiết đều tồn tại, tránh KeyError khi nâng cấp."""
    if "groups" not in st.session_state or not st.session_state.groups:
        st.session_state.groups = {"Sảnh Chung": {"msgs": []}, "Góc Chia Sẻ": {"msgs": []}}
    
    if "chat_library" not in st.session_state: st.session_state.chat_library = {}
    
    me = st.session_state.get("auth_status")
    if me and me != "Guest":
        # Sửa lỗi Session AI
        if me not in st.session_state.chat_library or not isinstance(st.session_state.chat_library[me], dict):
            st.session_state.chat_library[me] = {"sessions": {"Cuộc trò chuyện 1": []}, "active": "Cuộc trò chuyện 1"}
        elif "active" not in st.session_state.chat_library[me]:
            st.session_state.chat_library[me]["active"] = "Cuộc trò chuyện 1"
            st.session_state.chat_library[me]["sessions"] = {"Cuộc trò chuyện 1": []}

# --- [4] KHỞI TẠO ---
if 'initialized' not in st.session_state:
    db = tai_du_lieu()
    st.session_state.users = db.get("users", {"Thiên Phát": "2002"})
    st.session_state.user_status = db.get("user_status", {"Thiên Phát": "promax"})
    st.session_state.chat_library = db.get("chat_library", {})
    st.session_state.groups = db.get("groups", {})
    st.session_state.cloud_drive = db.get("cloud_drive", {})
    st.session_state.tickets = db.get("tickets", [])
    st.session_state.activation_keys = db.get("activation_keys", {})
    st.session_state.notice = db.get("notice", {"content": "Chào mừng tới Nexus.", "is_emergency": False, "id": 0})
    st.session_state.stage = "AUTH"
    st.session_state.auth_status = None
    st.session_state.initialized = True
    kiem_tra_du_lieu()

# --- [5] GIAO DIỆN (UI/UX) ---
def apply_ui():
    bg = random.choice(WALLPAPERS)
    st.markdown(f"""
    <style>
    .stApp {{ background: url('{bg}') no-repeat center fixed; background-size: cover; color: #E2E8F0; }}
    .glass-card {{ background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(15px); border-radius: 20px; padding: 25px; border: 1px solid rgba(255,255,255,0.08); margin-bottom: 20px; }}
    .stButton > button {{ background: #1E293B !important; color: #94A3B8 !important; border-radius: 12px; border: 1px solid #334155 !important; transition: 0.3s; width: 100%; }}
    .stButton > button:hover {{ border-color: #38BDF8 !important; color: #38BDF8 !important; background: #0F172A !important; }}
    input {{ background: rgba(30, 41, 59, 0.5) !important; color: white !important; border: 1px solid #334155 !important; }}
    .badge-promax {{ background: linear-gradient(90deg, #A855F7, #EC4899); color: white; padding: 2px 10px; border-radius: 20px; font-size: 11px; font-weight: bold; }}
    [data-testid="stHeader"] {{ visibility: hidden; }}
    </style>
    """, unsafe_allow_html=True)

# --- [6] AI ENGINE (AUTO-SWITCH) ---
def goi_ai(messages, tier):
    # Dùng Gemini chuẩn (Sửa lỗi 404)
    if tier in ["pro", "promax"]:
        try:
            client = OpenAI(api_key=GEMINI_KEY, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
            res = client.chat.completions.create(model="gemini-1.5-flash", messages=messages)
            return res.choices[0].message.content
        except Exception as e:
            if tier != "promax": return f"⚠️ Gemini Error: {str(e)}"
    
    # Dùng Groq làm dự phòng hoặc cho Free
    try:
        client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages)
        return res.choices[0].message.content
    except Exception as e:
        return f"⚠️ Lỗi kết nối lõi AI: {str(e)}"

# --- [7] MÀN HÌNH CHỨC NĂNG ---

def screen_ai_chat():
    apply_ui()
    kiem_tra_du_lieu() # Bảo vệ chống lỗi
    me = st.session_state.auth_status
    tier = st.session_state.user_status.get(me, "free")
    
    col1, col2 = st.columns([0.8, 0.2])
    col1.title("🧠 NEXUS AI")
    if col2.button("⬅️ HOME"): st.session_state.stage = "MENU"; st.rerun()

    lib = st.session_state.chat_library[me]
    
    with st.sidebar:
        st.subheader("Hội thoại")
        if st.button("➕ Hội thoại mới"):
            name = f"Cuộc hội thoại {len(lib['sessions'])+1}"
            lib['sessions'][name] = []; lib['active'] = name
            luu_du_lieu(); st.rerun()
        for s in lib['sessions'].keys():
            if st.button(f"💬 {s}"): lib['active'] = s; st.rerun()

    active_session = lib['active']
    history = lib['sessions'][active_session]
    
    st.markdown(f"<div class='glass-card'><b>Đang chat tại: {active_session}</b>", unsafe_allow_html=True)
    for m in history:
        with st.chat_message(m['role']): st.write(giai_ma(m['content'], tier))
    
    if p := st.chat_input("Nhập câu hỏi cho AI..."):
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
    kiem_tra_du_lieu() # Bảo vệ KeyError
    me = st.session_state.auth_status
    
    c1, c2, c3 = st.columns([0.6, 0.2, 0.2])
    c1.title("🌐 CỘNG ĐỒNG")
    if c2.button("📞 GỌI ADMIN"): st.session_state.stage = "SUPPORT"; st.rerun()
    if c3.button("⬅️ HOME"): st.session_state.stage = "MENU"; st.rerun()

    group = st.session_state.groups["Sảnh Chung"]
    
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    for m in group['msgs'][-30:]:
        with st.chat_message("user"):
            st.markdown(f"**{m['user']}**: {giai_ma(m['text'])}")
            
    if me != "Guest":
        if p := st.chat_input("Nhắn gì đó vào sảnh..."):
            group['msgs'].append({"user": me, "text": ma_hoa(p)})
            luu_du_lieu(); st.rerun()
    else: st.warning("Khách chỉ có thể xem. Hãy Đăng ký để chat!")
    st.markdown("</div>", unsafe_allow_html=True)

def screen_cloud():
    apply_ui()
    me = st.session_state.auth_status
    tier = st.session_state.user_status.get(me, "free")
    st.title("☁️ NEXUS CLOUD")
    if st.button("⬅️ HOME"): st.session_state.stage = "MENU"; st.rerun()
    
    my_files = st.session_state.cloud_drive.setdefault(me, [])
    limit = 50 if tier == "promax" else 30 if tier == "pro" else 5
    
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.write(f"📊 Giới hạn lưu trữ: **{limit}GB**")
    up = st.file_uploader("Chọn file tải lên Cloud")
    if up and st.button("XÁC NHẬN TẢI LÊN"):
        b64 = base64.b64encode(up.getvalue()).decode()
        my_files.append({"name": up.name, "data": b64, "date": datetime.now().strftime("%d/%m/%Y")})
        luu_du_lieu(); st.success("Đã tải lên!"); time.sleep(1); st.rerun()
    
    st.write("---")
    for idx, f in enumerate(my_files):
        c1, c2, c3 = st.columns([0.6, 0.2, 0.2])
        c1.write(f"📄 {f['name']} ({f['date']})")
        c2.download_button("Tải về", base64.b64decode(f['data']), file_name=f['name'], key=f"dl_{idx}")
        if c3.button("Xóa", key=f"del_{idx}"):
            my_files.pop(idx); luu_du_lieu(); st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def screen_support():
    apply_ui()
    me = st.session_state.auth_status
    st.title("🎧 HỖ TRỢ & MUA BẢN QUYỀN")
    if st.button("⬅️ HOME"): st.session_state.stage = "MENU"; st.rerun()

    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    loai = st.selectbox("Mục tiêu", ["Mua gói PRO MAX (50GB)", "Mua gói PRO (30GB)", "Gia hạn thêm ngày", "Báo lỗi hệ thống", "Góp ý"])
    nd = st.text_area("Nội dung yêu cầu (Hãy để lại STK hoặc thông tin liên hệ nếu cần)")
    if st.button("🚀 GỬI YÊU CẦU CHO ADMIN"):
        if nd:
            st.session_state.tickets.append({
                "id": str(random.randint(100,999)), "user": me, "type": loai, 
                "content": nd, "reply": "", "status": "open", "date": datetime.now().strftime("%H:%M %d/%m")
            })
            luu_du_lieu(); st.success("Đã gửi! Admin sẽ phản hồi sớm."); time.sleep(1.5); st.rerun()
    
    st.write("### Phản hồi từ Admin")
    for t in reversed([x for x in st.session_state.tickets if x['user'] == me]):
        with st.expander(f"[{t['status'].upper()}] {t['type']} - {t['date']}"):
            st.write(f"💬 Nội dung: {t['content']}")
            if t['reply']: st.info(f"👑 Admin: {t['reply']}")
            else: st.write("⏳ Đang chờ xử lý...")
    st.markdown("</div>", unsafe_allow_html=True)

def screen_admin():
    apply_ui()
    st.title("🛡️ ADMIN PANEL")
    if st.button("⬅️ MENU"): st.session_state.stage = "MENU"; st.rerun()
    
    t1, t2, t3 = st.tabs(["📥 TICKETS", "🔑 TẠO MÃ", "📢 THÔNG BÁO"])
    
    with t1:
        for t in [x for x in st.session_state.tickets if x['status'] == 'open']:
            st.warning(f"User: {t['user']} | Yêu cầu: {t['type']}")
            st.write(f"ND: {t['content']}")
            rep = st.text_input("Phản hồi / Gửi mã nâng cấp", key=f"rep_{t['id']}")
            if st.button("PHÊ DUYỆT & GỬI", key=f"btn_{t['id']}"):
                t['reply'] = rep; t['status'] = 'closed'
                luu_du_lieu(); st.success("Đã xong!"); time.sleep(0.5); st.rerun()
    
    with t2:
        c1, c2, c3 = st.columns(3)
        code = c1.text_input("Mã (Trống = Random)")
        tr = c2.selectbox("Gói", ["pro", "promax"])
        is_g = c3.checkbox("Dùng nhiều lần")
        if st.button("TẠO MÃ KÍCH HOẠT"):
            final = code if code else ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            st.session_state.activation_keys[final] = {"tier": tr, "global": is_g, "used_by": []}
            luu_du_lieu(); st.success(f"Mã mới: {final}")
            
    with t3:
        note = st.text_area("Thông báo hệ thống", st.session_state.notice['content'])
        is_em = st.checkbox("Khẩn cấp", st.session_state.notice['is_emergency'])
        if st.button("ĐĂNG TIN"):
            st.session_state.notice = {"content": note, "is_emergency": is_em, "id": random.randint(1,999)}
            luu_du_lieu(); st.success("Đã đăng!"); st.rerun()

# --- [8] ROUTER CHÍNH ---
if st.session_state.stage == "AUTH":
    apply_ui()
    _, cc, _ = st.columns([1, 1.2, 1])
    with cc:
        st.markdown("<div class='glass-card' style='text-align:center;'>", unsafe_allow_html=True)
        st.title(SYSTEM_NAME)
        mode = st.tabs(["Đăng nhập", "Đăng ký", "Khách"])
        with mode[0]:
            u = st.text_input("Tên định danh", key="u_login")
            p = st.text_input("Mật mã", type="password", key="p_login")
            if st.button("TRUY CẬP"):
                if u in st.session_state.users and st.session_state.users[u] == p:
                    st.session_state.auth_status = u; st.session_state.stage = "MENU"
                    kiem_tra_du_lieu(); st.rerun()
                else: st.error("Sai thông tin!")
        with mode[1]:
            nu = st.text_input("Tên mới", key="u_reg")
            np = st.text_input("Mật mã mới", type="password", key="p_reg")
            if st.button("TẠO TÀI KHOẢN"):
                if nu and nu not in st.session_state.users:
                    st.session_state.users[nu] = np
                    st.session_state.user_status[nu] = "free"
                    luu_du_lieu(); st.success("Thành công! Hãy quay lại Đăng nhập."); time.sleep(1)
                else: st.error("Tên đã tồn tại!")
        with mode[2]:
            if st.button("VÀO VỚI QUYỀN KHÁCH"):
                st.session_state.auth_status = "Guest"; st.session_state.stage = "MENU"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.stage == "MENU":
    apply_ui()
    me = st.session_state.auth_status
    tier = st.session_state.user_status.get(me, "free")
    
    if st.session_state.notice['is_emergency'] and st.session_state.get('last_n') != st.session_state.notice['id']:
        st.warning(f"🚨 CHỈ THỊ ADMIN: {st.session_state.notice['content']}")
        if st.button("ĐÃ XÁC NHẬN"): st.session_state.last_n = st.session_state.notice['id']; st.rerun()
        st.stop()

    st.title(f"🚀 {SYSTEM_NAME} | {me.upper()}")
    if tier == "promax": st.markdown("<span class='badge-promax'>👑 PRO MAX (Ưu tiên AI)</span>", unsafe_allow_html=True)
    
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    c1, c2 = st.columns(2); c3, c4 = st.columns(2)
    if c1.button("🧠 NEXUS AI"): st.session_state.stage = "AI_CHAT"; st.rerun()
    if c2.button("🌐 CỘNG ĐỒNG"): st.session_state.stage = "SOCIAL"; st.rerun()
    if c3.button("☁️ CLOUD STORAGE"):
        if me == "Guest": st.error("Khách không được dùng Cloud!")
        else: st.session_state.stage = "CLOUD"; st.rerun()
    if c4.button("🎧 HỖ TRỢ / MUA"): st.session_state.stage = "SUPPORT"; st.rerun()
    
    st.write("---")
    if st.button("⚙️ CÀI ĐẶT"): st.session_state.stage = "SETTINGS"; st.rerun()
    if me.lower() == "thiên phát" and st.button("🛡️ ADMIN PANEL"): st.session_state.stage = "ADMIN"; st.rerun()
    if st.button("🚪 ĐĂNG XUẤT"): st.session_state.stage = "AUTH"; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.stage == "AI_CHAT": screen_ai_chat()
elif st.session_state.stage == "SOCIAL": screen_social()
elif st.session_state.stage == "CLOUD": screen_cloud()
elif st.session_state.stage == "SUPPORT": screen_support()
elif st.session_state.stage == "ADMIN": screen_admin()
elif st.session_state.stage == "SETTINGS":
    apply_ui()
    st.title("⚙️ CÀI ĐẶT")
    if st.button("⬅️ HOME"): st.session_state.stage = "MENU"; st.rerun()
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    code = st.text_input("Nhập mã kích hoạt gói")
    if st.button("KÍCH HOẠT MÃ"):
        if code in st.session_state.activation_keys:
            k = st.session_state.activation_keys[code]
            st.session_state.user_status[st.session_state.auth_status] = k['tier']
            luu_du_lieu(); st.success(f"Nâng cấp {k['tier']} thành công!"); time.sleep(1); st.rerun()
        else: st.error("Mã sai!")
    st.markdown("</div>", unsafe_allow_html=True)
