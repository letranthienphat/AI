# -*- coding: utf-8 -*-
import streamlit as st
import time, base64, json, requests, random, hashlib
from openai import OpenAI
from datetime import datetime

# --- [1] CẤU HÌNH ---
CONFIG = {
    "NAME": "NEXUS PLATINUM OS",
    "CREATOR": "Thiên Phát",
    "FILE_DATA": "nexus_v31_core.json" # Đổi tên file để tránh dữ liệu lỗi cũ
}

try:
    GH_TOKEN, GH_REPO = st.secrets["GH_TOKEN"], st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS]
except:
    st.error("🛑 THIẾU SECRETS!"); st.stop()

st.set_page_config(page_title=CONFIG["NAME"], layout="wide", initial_sidebar_state="collapsed")

# --- [2] KERNEL BẢO VỆ JSON (FIX LỖI JSONDECODEERROR) ---
def sync_io(data=None):
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{CONFIG['FILE_DATA']}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    res = requests.get(url, headers=headers)
    
    # Mẫu dữ liệu mặc định để cứu hệ thống
    default_db = {
        "users": {CONFIG["CREATOR"]: "nexus2026"}, 
        "codes": ["PHAT888"], "pro_users": [], "chats": [], "files": {}, "rem": {}
    }

    if data is None: # Chế độ ĐỌC
        if res.status_code == 200:
            try:
                content = base64.b64decode(res.json()['content']).decode('utf-8')
                return json.loads(content) if content.strip() else default_db
            except: return default_db
        return default_db
    else: # Chế độ GHI
        sha = res.json().get("sha") if res.status_code == 200 else None
        js_str = json.dumps(data, ensure_ascii=False, indent=2)
        content = base64.b64encode(js_str.encode('utf-8')).decode('utf-8')
        requests.put(url, headers=headers, json={"message": "Nexus Sync", "content": content, "sha": sha})

# --- [3] GIAO DIỆN XỊN ---
st.markdown("""
<style>
    .stApp { background: #0f172a; color: #f1f5f9; }
    .ai-bubble { 
        background: #0047AB; color: white !important; padding: 18px; 
        border-radius: 15px 15px 15px 5px; margin: 10px 0;
        box-shadow: 0 4px 15px rgba(0,71,171,0.3); border-left: 5px solid #3b82f6;
    }
    .stButton>button { 
        border-radius: 12px; height: 50px; font-weight: bold; 
        background: linear-gradient(90deg, #1e40af, #3b82f6); color: white; border: none;
    }
    .main-card {
        background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1);
        padding: 20px; border-radius: 20px; text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# --- [4] LOGIC HỆ THỐNG ---
if 'db' not in st.session_state:
    st.session_state.db = sync_io()
    st.session_state.user = None
    st.session_state.page = "AUTH"

def get_fp(): return hashlib.sha256(st.context.headers.get("User-Agent","").encode()).hexdigest()[:16]

# Tự động vào (Ghi nhớ)
if st.session_state.user is None and get_fp() in st.session_state.db.get("rem", {}):
    st.session_state.user = st.session_state.db["rem"][get_fp()]
    st.session_state.page = "DASHBOARD"

is_pro = (st.session_state.user in st.session_state.db.get("pro_users", []))

# --- [5] TRANG ĐĂNG NHẬP ---
if st.session_state.page == "AUTH":
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.title("💠 NEXUS LOGIN")
        u = st.text_input("Tên đăng nhập")
        p = st.text_input("Mật khẩu", type="password")
        r = st.checkbox("Ghi nhớ thiết bị này")
        if st.button("🚀 TRUY CẬP", use_container_width=True):
            if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
                st.session_state.user = u
                if r: st.session_state.db["rem"][get_fp()] = u; sync_io(st.session_state.db)
                st.session_state.page = "DASHBOARD"; st.rerun()
            else: st.error("Sai thông tin!")

# --- [6] DASHBOARD ---
elif st.session_state.page == "DASHBOARD":
    st.title(f"🚀 Chào Phát, Nexus đã sẵn sàng")
    st.caption(f"Trạng thái: {'💎 PRO' if is_pro else '🆓 Miễn phí'}")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="main-card"><h3>🧠 AI CORE</h3></div>', unsafe_allow_html=True)
        if st.button("MỞ CHAT"): st.session_state.page = "AI"; st.rerun()
    with c2:
        st.markdown('<div class="main-card"><h3>☁️ CLOUD</h3></div>', unsafe_allow_html=True)
        if st.button("MỞ KHO FILE"): st.session_state.page = "CLOUD"; st.rerun()
    with c3:
        st.markdown('<div class="main-card"><h3>⚙️ VIP</h3></div>', unsafe_allow_html=True)
        if st.button("NÂNG CẤP"): st.session_state.page = "SETTINGS"; st.rerun()
    
    st.write("---")
    if st.session_state.user == CONFIG["CREATOR"]:
        if st.button("🛠️ QUẢN TRỊ VIÊN (ADMIN)"): st.session_state.page = "ADMIN"; st.rerun()
    if st.button("🚪 ĐĂNG XUẤT"):
        if get_fp() in st.session_state.db["rem"]: del st.session_state.db["rem"][get_fp()]
        sync_io(st.session_state.db); st.session_state.user = None; st.session_state.page = "AUTH"; st.rerun()

# --- [7] AI CHAT ---
elif st.session_state.page == "AI":
    if st.button("🔙 QUAY LẠI"): st.session_state.page = "DASHBOARD"; st.rerun()
    
    with st.sidebar:
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
        st.session_state.db["chats"].append({"name": "Mới", "msgs": [], "owner": st.session_state.user})
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

# --- [8] CLOUD (TỰ LƯU & XÓA) ---
elif st.session_state.page == "CLOUD":
    if st.button("🔙 QUAY LẠI DASHBOARD"): st.session_state.page = "DASHBOARD"; st.rerun()
    st.header("☁️ KHO LƯU TRỮ")
    
    up = st.file_uploader("Kéo thả để tự động lưu", label_visibility="collapsed")
    if up:
        if up.name not in st.session_state.db["files"]:
            st.session_state.db["files"][up.name] = {
                "data": base64.b64encode(up.getvalue()).decode(),
                "owner": st.session_state.user
            }
            sync_io(st.session_state.db); st.success("Đã tự động lưu!"); time.sleep(1); st.rerun()

    st.write("---")
    my_files = {k:v for k,v in st.session_state.db["files"].items() if v.get("owner") == st.session_state.user}
    for name, info in my_files.items():
        c1, c2, c3 = st.columns([3, 1, 1])
        c1.write(f"📄 {name}")
        c2.download_button("📥 TẢI VỀ", base64.b64decode(info["data"]), file_name=name, key=f"dl_{name}")
        if c3.button("🗑️ XÓA", key=f"del_{name}"):
            del st.session_state.db["files"][name]; sync_io(st.session_state.db); st.rerun()

# --- [9] ADMIN PANEL ---
elif st.session_state.page == "ADMIN":
    if st.button("🔙 QUAY LẠI"): st.session_state.page = "DASHBOARD"; st.rerun()
    st.title("🛠️ QUẢN TRỊ VIÊN")
    
    t1, t2, t3 = st.tabs(["👥 NGƯỜI DÙNG", "🔑 MÃ VIP", "📂 TOÀN BỘ FILE"])
    with t1:
        new_u = st.text_input("Tên User mới")
        new_p = st.text_input("Mật khẩu mới")
        if st.button("THÊM NGƯỜI DÙNG"):
            st.session_state.db["users"][new_u] = new_p; sync_io(st.session_state.db); st.success("Đã thêm!")
        st.write(st.session_state.db["users"])
    with t2:
        v_code = st.text_input("Tạo mã Pro").upper()
        if st.button("TẠO MÃ"):
            st.session_state.db["codes"].append(v_code); sync_io(st.session_state.db); st.success("Đã tạo!")
        st.write("Mã chưa dùng:", st.session_state.db["codes"])
    with t3:
        for f in list(st.session_state.db["files"].keys()):
            col_f, col_x = st.columns([4, 1])
            col_f.write(f"📄 {f} (By: {st.session_state.db['files'][f]['owner']})")
            if col_x.button("XÓA", key=f"adm_{f}"):
                del st.session_state.db["files"][f]; sync_io(st.session_state.db); st.rerun()

# --- [10] SETTINGS ---
elif st.session_state.page == "SETTINGS":
    if st.button("🔙 QUAY LẠI"): st.session_state.page = "DASHBOARD"; st.rerun()
    st.header("⚙️ NÂNG CẤP VIP")
    if is_pro: st.success("💎 BẠN ĐANG LÀ PLATINUM PRO")
    else:
        c = st.text_input("Nhập mã kích hoạt").upper()
        if st.button("KÍCH HOẠT"):
            if c in st.session_state.db["codes"]:
                st.session_state.db["pro_users"].append(st.session_state.user)
                st.session_state.db["codes"].remove(c)
                sync_io(st.session_state.db); st.balloons(); st.rerun()
