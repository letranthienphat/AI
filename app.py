# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time, base64, json, requests, random, string
from datetime import datetime, timedelta

# --- [1] CẤU HÌNH HỆ THỐNG ---
CREATOR = "Lê Trần Thiên Phát"
VERSION = "V5700 - NEXUS HELPDESK"
FILE_DATA = "data.json"
SECRET_KEY = "NEXUS_ULTIMATE_KEY_2024"

try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS] # Đảm bảo luôn là list
    GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")
except:
    st.error("⚠️ Cấu hình Secrets bị thiếu trên Streamlit Cloud!")
    st.stop()

st.set_page_config(page_title=f"NEXUS OS | {CREATOR}", layout="wide", initial_sidebar_state="collapsed")

# --- [2] CÔNG CỤ MÃ HÓA & DATA ---
def ma_hoa(text, tier="free"):
    if not text: return ""
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

def get_data_size(obj): return len(json.dumps(obj).encode('utf-8'))

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
        "tickets": st.session_state.tickets, "access_logs": st.session_state.access_logs, 
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

# --- [3] KHỞI TẠO ---
if 'initialized' not in st.session_state:
    db = tai_du_lieu()
    st.session_state.users = db.get("users", {"Thiên Phát": "2002"})
    st.session_state.user_status = db.get("user_status", {}) 
    st.session_state.activation_keys = db.get("activation_keys", {})
    st.session_state.notice = db.get("notice", {"content": "Hệ thống hoạt động.", "is_emergency": False, "id": 0})
    st.session_state.theme = db.get("theme", {"primary_color": "#38BDF8", "bg_list": [], "current_bg_idx": 0})
    st.session_state.chat_library = db.get("chat_library", {})
    st.session_state.groups = db.get("groups", {})
    st.session_state.cloud_drive = db.get("cloud_drive", {})
    st.session_state.tickets = db.get("tickets", []) # [{id, user, type, content, reply, status, date}]
    st.session_state.access_logs = db.get("access_logs", [])
    st.session_state.stage = "AUTH"
    st.session_state.auth_status = None
    st.session_state.initialized = True

# --- [4] GIAO DIỆN ---
def apply_ui():
    t = st.session_state.theme
    p_color = t['primary_color']
    bg = t['bg_list'][t['current_bg_idx']] if t['bg_list'] else "#0F172A"
    bg_css = f"url('{bg}') no-repeat center fixed" if "http" in bg else bg
    
    st.markdown(f"""
    <style>
    .stApp {{ background: {bg_css}; background-size: cover; color: #CBD5E1; font-family: 'Segoe UI', sans-serif; }}
    .glass-box {{ background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(16px); border-radius: 16px; padding: 24px; border: 1px solid rgba(255,255,255,0.05); margin-bottom: 20px; }}
    h1, h2, h3 {{ color: #F8FAFC !important; text-shadow: 0 2px 4px rgba(0,0,0,0.8); }}
    .stButton > button {{ background-color: #1E293B !important; color: #94A3B8 !important; border: 1px solid #334155 !important; border-radius: 8px; width: 100%; font-weight: 600; }}
    .stButton > button:hover {{ background-color: #0F172A !important; color: {p_color} !important; border-color: {p_color} !important; }}
    .badge-pro {{ background: #F59E0B; color: #fff; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: bold; }}
    .badge-promax {{ background: linear-gradient(90deg, #8B5CF6, #EC4899); color: #fff; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: bold; }}
    .ticket-open {{ border-left: 4px solid #F59E0B; padding-left: 10px; margin-bottom:10px; }}
    .ticket-closed {{ border-left: 4px solid #10B981; padding-left: 10px; margin-bottom:10px; opacity: 0.8; }}
    [data-testid="stHeader"] {{ visibility: hidden; }}
    </style>
    """, unsafe_allow_html=True)

# --- [5] XỬ LÝ AI ---
def goi_ai(messages, user_tier):
    if user_tier in ["pro", "promax"]:
        try:
            client = OpenAI(api_key=GEMINI_KEY, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
            return client.chat.completions.create(model="gemini-1.5-flash", messages=messages).choices[0].message.content
        except Exception as e:
            if user_tier == "promax":
                for key in GROQ_KEYS:
                    try:
                        client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
                        return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages).choices[0].message.content
                    except: continue
            return f"⚠️ Lỗi Gemini API: {str(e)}"
    else:
        try:
            client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
            return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages).choices[0].message.content
        except Exception as e: return f"⚠️ Lỗi Groq API: {str(e)}"

# --- [6] CÁC MÀN HÌNH ---

def screen_ai_chat():
    apply_ui()
    me = st.session_state.auth_status
    tier = st.session_state.user_status.get(me, "free")
    
    # FIX LỖI KEYERROR: Tạo key an toàn nhiều lớp
    if me not in st.session_state.chat_library: st.session_state.chat_library[me] = {"history": []}
    if "history" not in st.session_state.chat_library[me]: st.session_state.chat_library[me]["history"] = []
    
    history = st.session_state.chat_library[me]["history"]
    
    c1, c2 = st.columns([0.8, 0.2])
    c1.title("🧠 AI ASSISTANT")
    if c2.button("⬅️ HOME"): st.session_state.stage = "MENU"; st.rerun()
    
    st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
    if st.button("🗑️ XÓA HỘI THOẠI"):
        st.session_state.chat_library[me]["history"] = []
        luu_du_lieu(); st.rerun()

    for m in history:
        with st.chat_message(m['role']): st.write(giai_ma(m['content'], tier))

    if p := st.chat_input("Nhập lệnh cho AI..."):
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
    me = st.session_state.auth_status
    
    # FIX LỖI KEYERROR: Tạo nhóm mặc định nếu chưa có
    gn = "Cộng Đồng NEXUS"
    if gn not in st.session_state.groups: st.session_state.groups[gn] = {"msgs": []}
    gi = st.session_state.groups[gn]
    
    c1, c2, c3 = st.columns([0.6, 0.2, 0.2])
    c1.title("🌐 CỘNG ĐỒNG")
    if c2.button("📞 GỌI ADMIN"): st.session_state.stage = "SUPPORT"; st.rerun()
    if c3.button("⬅️ HOME"): st.session_state.stage = "MENU"; st.rerun()

    st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
    for m in gi['msgs']:
        with st.chat_message("assistant" if m['user'] == "Thiên Phát" else "user"):
            st.markdown(f"**{m['user']}**: {giai_ma(m['text'], 'free')}")
    
    if p := st.chat_input("Nhắn gì đó vào nhóm..."):
        gi['msgs'].append({"user": me, "text": ma_hoa(p, 'free')})
        luu_du_lieu(); st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def screen_support():
    apply_ui()
    me = st.session_state.auth_status
    c1, c2 = st.columns([0.8, 0.2])
    c1.title("🎧 LIÊN HỆ ADMIN")
    if c2.button("⬅️ HOME"): st.session_state.stage = "MENU"; st.rerun()

    st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
    st.write("### 📝 Gửi Yêu Cầu Mới")
    loai_yc = st.selectbox("Chủ đề", ["Yêu cầu nâng cấp/Gia hạn", "Báo cáo lỗi hệ thống", "Phản hồi/Góp ý sản phẩm", "Khác"])
    noidung = st.text_area("Nội dung chi tiết")
    
    if st.button("🚀 GỬI YÊU CẦU"):
        if noidung:
            new_ticket = {
                "id": str(random.randint(1000, 9999)), "user": me, "type": loai_yc,
                "content": noidung, "reply": "", "status": "open", "date": datetime.now().strftime("%d/%m %H:%M")
            }
            st.session_state.tickets.append(new_ticket)
            luu_du_lieu(); st.success("Đã gửi cho Admin! Vui lòng chờ phản hồi."); time.sleep(1.5); st.rerun()
        else: st.warning("Vui lòng nhập nội dung.")
    
    st.write("---")
    st.write("### 📬 Hòm thư của bạn")
    my_tickets = [t for t in st.session_state.tickets if t['user'] == me]
    if not my_tickets: st.info("Bạn chưa có yêu cầu nào.")
    for t in reversed(my_tickets):
        cls = "ticket-open" if t['status'] == "open" else "ticket-closed"
        st.markdown(f"<div class='{cls}'>", unsafe_allow_html=True)
        st.write(f"**[{t['type']}]** - {t['date']}")
        st.write(f"🗣️ **Bạn:** {t['content']}")
        if t['reply']: st.success(f"👑 **Admin:** {t['reply']}")
        else: st.info("⏳ Đang chờ Admin xử lý...")
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def screen_admin():
    apply_ui()
    st.title("🛡️ ADMIN CONTROL")
    if st.button("⬅️ QUAY LẠI MENU"): st.session_state.stage = "MENU"; st.rerun()
    
    t1, t2, t3 = st.tabs(["🎧 YÊU CẦU TỪ KHÁCH", "🔑 MÃ KÍCH HOẠT", "📢 THÔNG BÁO"])
    
    with t1:
        st.subheader("Quản lý Tickets")
        for t in reversed(st.session_state.tickets):
            with st.expander(f"{'🟢' if t['status']=='open' else '⚪'} {t['user']} - {t['type']} ({t['date']})"):
                st.write(f"📝 **Nội dung:** {t['content']}")
                if t['status'] == 'open':
                    rep = st.text_area("Nhập phản hồi", key=f"rep_{t['id']}")
                    if st.button("GỬI PHẢN HỒI & ĐÓNG TICKET", key=f"btn_{t['id']}"):
                        t['reply'] = rep; t['status'] = "closed"
                        luu_du_lieu(); st.rerun()
                else: st.write(f"✅ **Đã trả lời:** {t['reply']}")
                
    with t2:
        c1, c2, c3 = st.columns(3)
        code_val = c1.text_input("Mã kích hoạt (Trống = Random)")
        tier_val = c2.selectbox("Cấp độ", ["pro", "promax"])
        is_global = c3.checkbox("Mã chung")
        if st.button("TẠO MÃ"):
            final_code = code_val if code_val else ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            st.session_state.activation_keys[final_code] = {"tier": tier_val, "global": is_global, "used_by": []}
            luu_du_lieu(); st.success(f"Tạo thành công: {final_code}")
        st.write(st.session_state.activation_keys)
        
    with t3:
        note = st.text_area("Nội dung", st.session_state.notice['content'])
        is_em = st.checkbox("Khẩn cấp", st.session_state.notice['is_emergency'])
        if st.button("CẬP NHẬT TB"):
            st.session_state.notice = {"content": note, "is_emergency": is_em, "id": random.randint(1,999)}
            luu_du_lieu(); st.success("Đã cập nhật!")

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
            else: st.error("Sai thông tin!")
        st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.stage == "MENU":
    apply_ui()
    me = st.session_state.auth_status
    tier = st.session_state.user_status.get(me, "free")
    
    if st.session_state.notice['is_emergency'] and st.session_state.last_notice_seen != st.session_state.notice['id']:
        st.warning(f"🚨 **THÔNG BÁO TỪ ADMIN:**\n\n{st.session_state.notice['content']}")
        if st.button("ĐÃ ĐỌC"): st.session_state.last_notice_seen = st.session_state.notice['id']; st.rerun()
        st.stop()

    st.markdown(f"<h2>🚀 NEXUS | {me.upper()}</h2>", unsafe_allow_html=True)
    if tier == "promax": st.markdown("<span class='badge-promax'>👑 PRO MAX</span>", unsafe_allow_html=True)
    elif tier == "pro": st.markdown("<span class='badge-pro'>💎 PRO MEMBER</span>", unsafe_allow_html=True)
    
    st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    if c1.button("🧠 AI CHAT"): st.session_state.stage = "AI_CHAT"; st.rerun()
    if c2.button("🌐 CỘNG ĐỒNG"): st.session_state.stage = "SOCIAL"; st.rerun()
    if c3.button("🎧 LIÊN HỆ ADMIN"): st.session_state.stage = "SUPPORT"; st.rerun()
    
    if me.lower() == "thiên phát" and st.button("🛡️ ADMIN PANEL"): st.session_state.stage = "ADMIN"; st.rerun()
    if st.button("🚪 ĐĂNG XUẤT"): st.session_state.stage = "AUTH"; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.stage == "AI_CHAT": screen_ai_chat()
elif st.session_state.stage == "SOCIAL": screen_social()
elif st.session_state.stage == "SUPPORT": screen_support()
elif st.session_state.stage == "ADMIN": screen_admin()
else:
    st.session_state.stage = "MENU"; st.rerun()
