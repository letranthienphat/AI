# -*- coding: utf-8 -*-
import streamlit as st
import time, base64, json, requests, random, hashlib
from openai import OpenAI
from datetime import datetime

# --- [1] CẤU HÌNH ---
CONFIG = {
    "NAME": "NEXUS TITAN OS",
    "CREATOR": "Thiên Phát",
    "FILE_DATA": "nexus_v32_final.json" # Đổi tên file để reset dữ liệu lỗi cũ
}

try:
    GH_TOKEN, GH_REPO = st.secrets["GH_TOKEN"], st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS]
except:
    st.error("🛑 THIẾU SECRETS!"); st.stop()

st.set_page_config(page_title=CONFIG["NAME"], layout="wide", initial_sidebar_state="collapsed")

# --- [2] KERNEL BẢO VỆ DỮ LIỆU (CHỐNG JSON DECODE ERROR) ---
def sync_io(data=None):
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{CONFIG['FILE_DATA']}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    # Mẫu dữ liệu chuẩn để cứu hệ thống khi có lỗi
    default_db = {
        "users": {CONFIG["CREATOR"]: "nexus2026"}, 
        "codes": ["ADMIN99"], "pro_users": [], "chats": [], "files": {}, "rem": {}
    }

    res = requests.get(url, headers=headers)
    
    if data is None: # Chế độ ĐỌC
        if res.status_code == 200:
            try:
                raw_content = base64.b64decode(res.json()['content']).decode('utf-8')
                if not raw_content.strip(): return default_db
                return json.loads(raw_content)
            except Exception: return default_db # Nếu lỗi JSON, trả về mặc định để app không sập
        return default_db
    else: # Chế độ GHI
        sha = res.json().get("sha") if res.status_code == 200 else None
        js_str = json.dumps(data, ensure_ascii=False, indent=2)
        content = base64.b64encode(js_str.encode('utf-8')).decode('utf-8')
        requests.put(url, headers=headers, json={"message": "Nexus Update", "content": content, "sha": sha})

# --- [3] GIAO DIỆN XỊN (CSS DARK MODE & AI BLUE) ---
st.markdown("""
<style>
    .stApp { background: #0f172a; color: #f1f5f9; }
    .ai-bubble { 
        background: #0047AB; color: white !important; padding: 20px; 
        border-radius: 15px 15px 15px 5px; margin: 12px 0;
        box-shadow: 0 4px 15px rgba(0,71,171,0.4); border-left: 6px solid #3b82f6;
    }
    .stButton>button { 
        border-radius: 12px; height: 52px; font-weight: bold; font-size: 16px;
        background: linear-gradient(90deg, #1e40af, #3b82f6); color: white; border: none;
    }
    .card {
        background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
        padding: 25px; border-radius: 20px; text-align: center; margin-bottom: 20px;
    }
    [data-testid="stHeader"] { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- [4] KHỞI TẠO ---
if 'db' not in st.session_state:
    st.session_state.db = sync_io()
    st.session_state.user = None
    st.session_state.page = "AUTH"

def get_fp(): return hashlib.sha256(st.context.headers.get("User-Agent","").encode()).hexdigest()[:16]

# Ghi nhớ đăng nhập
if st.session_state.user is None and get_fp() in st.session_state.db.get("rem", {}):
    st.session_state.user = st.session_state.db["rem"][get_fp()]
    st.session_state.page = "DASHBOARD"

is_pro = (st.session_state.user in st.session_state.db.get("pro_users", []))

# --- [5] TRANG ĐĂNG NHẬP ---
if st.session_state.page == "AUTH":
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<h1 style='text-align:center; color:#3b82f6;'>NEXUS TITAN</h1>", unsafe_allow_html=True)
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        rem = st.checkbox("Ghi nhớ thiết bị này")
        if st.button("🔓 TRUY CẬP HỆ THỐNG", use_container_width=True):
            if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
                st.session_state.user = u
                if rem: st.session_state.db["rem"][get_fp()] = u; sync_io(st.session_state.db)
                st.session_state.page = "DASHBOARD"; st.rerun()
            else: st.error("⚠️ Tài khoản hoặc mật khẩu không chính xác!")

# --- [6] DASHBOARD ---
elif st.session_state.page == "DASHBOARD":
    st.title(f"🚀 Dashboard | {st.session_state.user}")
    st.write(f"Level: {'💎 PLATINUM PRO' if is_pro else '🆓 STANDARD USER'}")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="card"><h3>🧠 AI CORE</h3><p>Trí tuệ nhân tạo</p></div>', unsafe_allow_html=True)
        if st.button("MỞ CHAT"): st.session_state.page = "AI"; st.rerun()
    with c2:
        st.markdown('<div class="card"><h3>☁️ CLOUD</h3><p>Kho lưu trữ mây</p></div>', unsafe_allow_html=True)
        if st.button("MỞ KHO FILE"): st.session_state.page = "CLOUD"; st.rerun()
    with c3:
        st.markdown('<div class="card"><h3>⚙️ VIP</h3><p>Nâng cấp tài khoản</p></div>', unsafe_allow_html=True)
        if st.button("NÂNG CẤP"): st.session_state.page = "SETTINGS"; st.rerun()
    
    st.divider()
    if st.session_state.user == CONFIG["CREATOR"]:
        if st.button("🛠️ QUẢN TRỊ VIÊN (ADMIN PANEL)", use_container_width=True): st.session_state.page = "ADMIN"; st.rerun()
    
    if st.button("🚪 ĐĂNG XUẤT & QUÊN THIẾT BỊ"):
        if get_fp() in st.session_state.db["rem"]: del st.session_state.db["rem"][get_fp()]
        sync_io(st.session_state.db); st.session_state.user = None; st.session_state.page = "AUTH"; st.rerun()

# --- [7] AI CHAT (BANNER XANH) ---
elif st.session_state.page == "AI":
    if st.button("🔙 QUAY LẠI"): st.session_state.page = "DASHBOARD"; st.rerun()
    
    with st.sidebar:
        st.header("Lịch sử")
        if st.button("➕ Hội thoại mới"): st.session_state.chat_id = None; st.rerun()
        for i, c in enumerate(st.session_state.db["chats"]):
            if c["owner"] == st.session_state.user:
                col_c, col_d = st.columns([4, 1])
                if col_c.button(f"💬 {c['name']}", key=f"c_{i}"): st.session_state.chat_id = i; st.rerun()
                if col_d.button("🗑️", key=f"d_{i}"):
                    st.session_state.db["chats"].pop(i)
                    st.session_state.chat_id = None; sync_io(st.session_state.db); st.rerun()

    cid = st.session_state.get("chat_id")
    if cid is None or cid >= len(st.session_state.db["chats"]):
        st.session_state.db["chats"].append({"name": "Hội thoại mới", "msgs": [], "owner": st.session_state.user})
        st.session_state.chat_id = len(st.session_state.db["chats"]) - 1
        cid = st.session_state.chat_id

    chat = st.session_state.db["chats"][cid]
    for m in chat["msgs"]:
        if m["role"] == "user": st.chat_message("user").write(m["content"])
        else: st.markdown(f'<div class="ai-bubble">{m["content"]}</div>', unsafe_allow_html=True)

    if p := st.chat_input("Hỏi Nexus..."):
        chat["msgs"].append({"role": "user", "content": p})
        client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=chat["msgs"][-5:])
        ans = res.choices[0].message.content
        chat["msgs"].append({"role": "assistant", "content": ans})
        sync_io(st.session_state.db); st.rerun()

# --- [8] CLOUD (AUTO SAVE & XÓA) ---
elif st.session_state.page == "CLOUD":
    if st.button("🔙 QUAY LẠI"): st.session_state.page = "DASHBOARD"; st.rerun()
    st.header("☁️ KHO LƯU TRỮ")
    
    up = st.file_uploader("Chọn file để tự động tải lên", label_visibility="collapsed")
    if up:
        if up.name not in st.session_state.db["files"]:
            with st.status("Đang đồng bộ mây..."):
                f_data = up.getvalue()
                st.session_state.db["files"][up.name] = {
                    "data": base64.b64encode(f_data).decode(),
                    "owner": st.session_state.user
                }
                sync_io(st.session_state.db)
            st.success(f"✅ Đã lưu: {up.name}"); time.sleep(1); st.rerun()

    st.divider()
    my_files = {k:v for k,v in st.session_state.db["files"].items() if v.get("owner") == st.session_state.user}
    for name, info in my_files.items():
        c1, c2, c3 = st.columns([3, 1, 1])
        c1.write(f"📄 **{name}**")
        # NÚT TẢI XUỐNG XỊN
        c2.download_button("📥 TẢI VỀ", base64.b64decode(info["data"]), file_name=name, key=f"dl_{name}")
        # NÚT XÓA XỊN
        if c3.button("🗑️ XÓA", key=f"del_{name}"):
            del st.session_state.db["files"][name]; sync_io(st.session_state.db); st.rerun()

# --- [9] ADMIN PANEL ---
elif st.session_state.page == "ADMIN":
    if st.button("🔙 QUAY LẠI"): st.session_state.page = "DASHBOARD"; st.rerun()
    st.title("🛠️ QUẢN TRỊ HỆ THỐNG")
    
    t1, t2, t3 = st.tabs(["👥 USERS", "🔑 MÃ VIP", "📂 FILES"])
    with t1:
        st.write(st.session_state.db["users"])
        new_u = st.text_input("Tên User mới")
        new_p = st.text_input("Pass mới")
        if st.button("THÊM USER"):
            st.session_state.db["users"][new_u] = new_p; sync_io(st.session_state.db); st.success("Xong!")
    with t2:
        v_code = st.text_input("Tạo mã VIP").upper()
        if st.button("XÁC NHẬN"):
            st.session_state.db["codes"].append(v_code); sync_io(st.session_state.db); st.success("Đã tạo!")
        st.write("Mã chưa dùng:", st.session_state.db["codes"])
    with t3:
        for f in list(st.session_state.db["files"].keys()):
            col_f, col_x = st.columns([4, 1])
            col_f.write(f"📄 {f} (By: {st.session_state.db['files'][f]['owner']})")
            if col_x.button("XÓA FILE", key=f"adm_{f}"):
                del st.session_state.db["files"][f]; sync_io(st.session_state.db); st.rerun()

# --- [10] SETTINGS ---
elif st.session_state.page == "SETTINGS":
    if st.button("🔙 QUAY LẠI"): st.session_state.page = "DASHBOARD"; st.rerun()
    st.header("⚙️ NÂNG CẤP")
    if is_pro: st.success("💎 PLATINUM PRO ACTIVATED")
    else:
        c = st.text_input("Nhập mã Pro").upper()
        if st.button("KÍCH HOẠT"):
            if c in st.session_state.db["codes"]:
                st.session_state.db["pro_users"].append(st.session_state.user)
                st.session_state.db["codes"].remove(c)
                sync_io(st.session_state.db); st.balloons(); st.rerun()
