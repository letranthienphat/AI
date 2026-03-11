# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time, base64, json, requests, random, string
from datetime import datetime, timedelta

# --- [1] CẤU HÌNH HỆ THỐNG ---
CREATOR = "Lê Trần Thiên Phát"
VERSION = "V5800 - ULTIMATE FIX"
FILE_DATA = "data.json"
SECRET_KEY = "NEXUS_ULTIMATE_KEY_2024"

try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS]
    GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")
except:
    st.error("⚠️ Thiếu cấu hình Secrets!")
    st.stop()

st.set_page_config(page_title=f"NEXUS OS | {CREATOR}", layout="wide", initial_sidebar_state="collapsed")

# --- [2] CÔNG CỤ NỀN TẢNG ---
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
        "theme": st.session_state.theme, "chat_library": st.session_state.chat_library,
        "groups": st.session_state.groups, "cloud_drive": st.session_state.cloud_drive,
        "tickets": st.session_state.tickets, "activation_keys": st.session_state.activation_keys,
        "notice": st.session_state.notice
    }
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None
        payload = {"message": "Nexus Sync", "content": base64.b64encode(json.dumps(data, indent=4).encode()).decode(), "sha": sha}
        requests.put(url, headers=headers, json=payload)
    except: pass

# --- [3] KHỞI TẠO ---
if 'initialized' not in st.session_state:
    db = tai_du_lieu()
    st.session_state.users = db.get("users", {"Thiên Phát": "2002"})
    st.session_state.user_status = db.get("user_status", {}) 
    st.session_state.activation_keys = db.get("activation_keys", {})
    st.session_state.notice = db.get("notice", {"content": "Hệ thống ổn định.", "is_emergency": False, "id": 0})
    st.session_state.theme = db.get("theme", {"primary_color": "#38BDF8", "bg_list": [], "current_bg_idx": 0})
    st.session_state.chat_library = db.get("chat_library", {})
    st.session_state.groups = db.get("groups", {"Cộng Đồng NEXUS": {"msgs": []}})
    st.session_state.cloud_drive = db.get("cloud_drive", {})
    st.session_state.tickets = db.get("tickets", [])
    st.session_state.stage = "AUTH"
    st.session_state.auth_status = None
    st.session_state.initialized = True

# --- [4] GIAO DIỆN DARK MODE ---
def apply_ui():
    t = st.session_state.theme
    p_color = t['primary_color']
    st.markdown(f"""
    <style>
    .stApp {{ background: #0F172A; color: #CBD5E1; }}
    .glass {{ background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(12px); border-radius: 15px; padding: 20px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px; }}
    .stButton > button {{ background: #1E293B !important; color: #94A3B8 !important; border: 1px solid #334155 !important; transition: 0.3s; }}
    .stButton > button:hover {{ border-color: {p_color} !important; color: {p_color} !important; box-shadow: 0 0 10px {p_color}33; }}
    .badge-pro {{ background: #F59E0B; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px; }}
    .badge-promax {{ background: linear-gradient(90deg, #A855F7, #EC4899); color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px; }}
    [data-testid="stHeader"] {{ visibility: hidden; }}
    </style>
    """, unsafe_allow_html=True)

# --- [5] XỬ LÝ AI (FIXED GEMINI 404) ---
def goi_ai(messages, tier):
    # Sửa lỗi 404 bằng cách dùng OpenAI SDK với đúng định dạng cho Gemini
    try:
        if tier in ["pro", "promax"]:
            client = OpenAI(api_key=GEMINI_KEY, base_url="https://generativelanguage.googleapis.com/v1beta/openai")
            model_name = "gemini-1.5-flash"
            # Nếu Promax mà Gemini lỗi, sẽ tự chuyển xuống Groq bên dưới
            res = client.chat.completions.create(model=model_name, messages=messages)
            return res.choices[0].message.content
    except Exception as e:
        if tier != "promax": return f"⚠️ Gemini Error: {str(e)}"

    # Logic cho Free hoặc Promax khi Gemini lỗi
    try:
        key = random.choice(GROQ_KEYS)
        client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages)
        return res.choices[0].message.content
    except Exception as e:
        return f"⚠️ Hệ thống AI đang bận (Error: {str(e)})"

# --- [6] CÁC MÀN HÌNH ---

def screen_cloud():
    apply_ui()
    me = st.session_state.auth_status
    tier = st.session_state.user_status.get(me, "free")
    st.title("☁️ NEXUS CLOUD DRIVE")
    if st.button("⬅️ QUAY LẠI"): st.session_state.stage = "MENU"; st.rerun()

    my_files = st.session_state.cloud_drive.setdefault(me, [])
    limit = 50 if tier == "promax" else 30 if tier == "pro" else 5
    
    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    st.subheader(f"Dung lượng: {limit}GB")
    up = st.file_uploader("Chọn tệp để tải lên")
    if up and st.button("🚀 TẢI LÊN"):
        b64 = base64.b64encode(up.getvalue()).decode()
        my_files.append({"name": up.name, "data": b64, "date": datetime.now().strftime("%d/%m/%Y")})
        luu_du_lieu(); st.success("Đã lưu!"); time.sleep(1); st.rerun()
    
    st.write("---")
    for idx, f in enumerate(my_files):
        c1, c2, c3 = st.columns([0.6, 0.2, 0.2])
        c1.write(f"📄 {f['name']}")
        c2.download_button("⬇️", base64.b64decode(f['data']), file_name=f['name'], key=f"dl_{idx}")
        if c3.button("🗑️", key=f"del_{idx}"):
            my_files.pop(idx); luu_du_lieu(); st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def screen_support():
    apply_ui()
    me = st.session_state.auth_status
    st.title("🎧 HỖ TRỢ & YÊU CẦU")
    if st.button("⬅️ QUAY LẠI"): st.session_state.stage = "MENU"; st.rerun()

    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    loai = st.selectbox("Bạn cần gì?", ["Mua bản Pro (30GB)", "Mua bản Pro Max (50GB + Auto AI)", "Gia hạn thêm ngày", "Báo lỗi", "Góp ý"])
    nd = st.text_area("Nội dung chi tiết yêu cầu của bạn")
    if st.button("GỬI YÊU CẦU CHO ADMIN"):
        if nd:
            st.session_state.tickets.append({"id": str(random.randint(100,999)), "user": me, "type": loai, "content": nd, "reply": "", "status": "open"})
            luu_du_lieu(); st.success("Yêu cầu đã được gửi!"); time.sleep(1); st.rerun()
    
    st.write("### Lịch sử yêu cầu")
    for t in reversed([x for x in st.session_state.tickets if x['user'] == me]):
        with st.expander(f"{t['type']} - {'✅ Xong' if t['status']=='closed' else '⏳ Đang chờ'}"):
            st.write(f"**Nội dung:** {t['content']}")
            if t['reply']: st.info(f"👑 Admin phản hồi: {t['reply']}")
    st.markdown("</div>", unsafe_allow_html=True)

def screen_settings():
    apply_ui()
    me = st.session_state.auth_status
    st.title("⚙️ CÀI ĐẶT")
    if st.button("⬅️ QUAY LẠI"): st.session_state.stage = "MENU"; st.rerun()

    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    st.subheader("💎 Kích hoạt mã nâng cấp")
    code = st.text_input("Nhập mã kích hoạt tại đây")
    if st.button("KÍCH HOẠT NGAY"):
        keys = st.session_state.activation_keys
        if code in keys:
            k = keys[code]
            if k['global'] or len(k['used_by']) == 0:
                st.session_state.user_status[me] = k['tier']
                if me not in k['used_by']: k['used_by'].append(me)
                luu_du_lieu(); st.success(f"Nâng cấp {k['tier']} thành công!"); time.sleep(1); st.rerun()
        else: st.error("Mã không hợp lệ.")
    st.markdown("</div>", unsafe_allow_html=True)

def screen_admin():
    apply_ui()
    st.title("🛡️ SUPREME ADMIN")
    if st.button("⬅️ MENU"): st.session_state.stage = "MENU"; st.rerun()
    
    tab1, tab2, tab3 = st.tabs(["📥 YÊU CẦU MUA/HỖ TRỢ", "🔑 TẠO MÃ", "📢 THÔNG BÁO"])
    
    with tab1:
        for t in [x for x in st.session_state.tickets if x['status'] == 'open']:
            st.warning(f"User: {t['user']} | Cần: {t['type']}")
            st.write(f"Chi tiết: {t['content']}")
            rep = st.text_input("Câu trả lời / Quà tặng", key=f"r_{t['id']}")
            if st.button("GỬI PHẢN HỒI", key=f"b_{t['id']}"):
                t['reply'] = rep; t['status'] = 'closed'
                luu_du_lieu(); st.rerun()
    
    with tab2:
        c1, c2, c3 = st.columns(3)
        new_c = c1.text_input("Mã (Trống = Random)")
        tier = c2.selectbox("Cấp", ["pro", "promax"])
        is_g = c3.checkbox("Dùng nhiều lần")
        if st.button("TẠO MÃ KÍCH HOẠT"):
            final = new_c if new_c else ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            st.session_state.activation_keys[final] = {"tier": tier, "global": is_g, "used_by": []}
            luu_du_lieu(); st.success(f"Đã tạo mã: {final}")
            
    with tab3:
        n_c = st.text_area("Thông báo mới", st.session_state.notice['content'])
        is_em = st.checkbox("Khẩn cấp", st.session_state.notice['is_emergency'])
        if st.button("ĐĂNG THÔNG BÁO"):
            st.session_state.notice = {"content": n_c, "is_emergency": is_em, "id": random.randint(1,999)}
            luu_du_lieu(); st.success("Đã đăng!")

# --- [7] ROUTER CHÍNH ---
if st.session_state.stage == "AUTH":
    apply_ui()
    _, cc, _ = st.columns([1, 1.2, 1])
    with cc:
        st.markdown("<div class='glass' style='text-align:center;'>", unsafe_allow_html=True)
        st.subheader("NEXUS LOGIN")
        u = st.text_input("Tên đăng nhập")
        p = st.text_input("Mật khẩu", type="password")
        if st.button("TIẾN VÀO"):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.auth_status = u; st.session_state.stage = "MENU"; st.rerun()
            else: st.error("Sai tài khoản!")
        st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.stage == "MENU":
    apply_ui()
    me = st.session_state.auth_status
    tier = st.session_state.user_status.get(me, "free")
    
    # Emergency Notice
    if st.session_state.notice['is_emergency'] and st.session_state.get('last_n') != st.session_state.notice['id']:
        st.warning(f"🚨 ADMIN: {st.session_state.notice['content']}")
        if st.button("ĐÃ HIỂU"): st.session_state.last_n = st.session_state.notice['id']; st.rerun()
        st.stop()

    st.title(f"🚀 NEXUS OS | {me.upper()}")
    if tier == "promax": st.markdown("<span class='badge-promax'>👑 PRO MAX (50GB)</span>", unsafe_allow_html=True)
    elif tier == "pro": st.markdown("<span class='badge-pro'>💎 PRO MEMBER (30GB)</span>", unsafe_allow_html=True)
    
    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    c1, c2 = st.columns(2); c3, c4 = st.columns(2)
    if c1.button("🧠 AI CHAT", use_container_width=True): 
        # Khởi tạo history nếu chưa có để tránh KeyError
        if me not in st.session_state.chat_library: st.session_state.chat_library[me] = {"history": []}
        st.session_state.stage = "AI_CHAT"; st.rerun()
    if c2.button("🌐 CỘNG ĐỒNG", use_container_width=True): st.session_state.stage = "SOCIAL"; st.rerun()
    if c3.button("☁️ CLOUD DRIVE", use_container_width=True): st.session_state.stage = "CLOUD"; st.rerun()
    if c4.button("🎧 HỖ TRỢ / MUA", use_container_width=True): st.session_state.stage = "SUPPORT"; st.rerun()
    
    st.write("---")
    if st.button("⚙️ CÀI ĐẶT", use_container_width=True): st.session_state.stage = "SETTINGS"; st.rerun()
    if me.lower() == "thiên phát" and st.button("🛡️ ADMIN PANEL", use_container_width=True): st.session_state.stage = "ADMIN"; st.rerun()
    if st.button("🚪 ĐĂNG XUẤT", use_container_width=True): st.session_state.stage = "AUTH"; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.stage == "AI_CHAT":
    apply_ui()
    me = st.session_state.auth_status
    tier = st.session_state.user_status.get(me, "free")
    st.title("🧠 NEXUS AI")
    if st.button("⬅️ HOME"): st.session_state.stage = "MENU"; st.rerun()
    
    history = st.session_state.chat_library[me]["history"]
    for m in history:
        with st.chat_message(m['role']): st.write(giai_ma(m['content'], tier))
        
    if p := st.chat_input("Hỏi bất cứ điều gì..."):
        history.append({"role": "user", "content": ma_hoa(p, tier)})
        with st.chat_message("user"): st.write(p)
        with st.chat_message("assistant"):
            res = goi_ai([{"role": "user", "content": p}], tier)
            st.write(res)
            history.append({"role": "assistant", "content": ma_hoa(res, tier)})
            luu_du_lieu()

elif st.session_state.stage == "SOCIAL":
    apply_ui()
    st.title("🌐 CỘNG ĐỒNG")
    if st.button("⬅️ HOME"): st.session_state.stage = "MENU"; st.rerun()
    st.info("Tính năng chat cộng đồng đang đồng bộ...")
    # Tương tự như bản trước, tích hợp nhóm chat tại đây

elif st.session_state.stage == "CLOUD": screen_cloud()
elif st.session_state.stage == "SUPPORT": screen_support()
elif st.session_state.stage == "SETTINGS": screen_settings()
elif st.session_state.stage == "ADMIN": screen_admin()
