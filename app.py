# -*- coding: utf-8 -*-
import streamlit as st
import time, base64, json, requests, random, hashlib
from openai import OpenAI
from datetime import datetime

# --- [1] CẤU HÌNH ---
CONFIG = {
    "NAME": "NEXUS OS",
    "CREATOR": "Thiên Phát",
    "FILE_DATA": "nexus_final_v27.json"
}

try:
    GH_TOKEN, GH_REPO = st.secrets["GH_TOKEN"], st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS]
except:
    st.error("🛑 THIẾU SECRETS!"); st.stop()

st.set_page_config(page_title=CONFIG["NAME"], layout="wide")

# --- [2] KERNEL DỮ LIỆU ---
def get_device_fp():
    ua = st.context.headers.get("User-Agent", "Unknown")
    return hashlib.sha256(ua.encode()).hexdigest()[:16]

def sync_io(data=None):
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{CONFIG['FILE_DATA']}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    res = requests.get(url, headers=headers)
    if data is None:
        if res.status_code == 200:
            return json.loads(base64.b64decode(res.json()['content']).decode('utf-8'))
        return {"users": {CONFIG["CREATOR"]: "nexus os gateway"}, "codes": ["PHAT2026"], "pro_users": [], "chats": [], "files": {}, "rem": {}}
    else:
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, ensure_ascii=False).encode('utf-8')).decode('utf-8')
        requests.put(url, headers=headers, json={"message": "Nexus Sync", "content": content, "sha": sha})

# --- [3] STYLE ---
st.markdown("""
<style>
.ai-banner { 
    background-color: #0047AB; color: white !important; padding: 16px; 
    border-radius: 10px; font-weight: 600; margin: 12px 0;
}
.stButton>button { width: 100%; border-radius: 8px; }
[data-testid="stHeader"] { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- [4] KHỞI TẠO ---
if 'boot' not in st.session_state:
    st.session_state.db = sync_io()
    st.session_state.user = None
    st.session_state.page = "AUTH"
    st.session_state.boot = True

fp = get_device_fp()

# Ghi nhớ đăng nhập
if st.session_state.user is None and fp in st.session_state.db.get("rem", {}):
    st.session_state.user = st.session_state.db["rem"][fp]
    st.session_state.page = "DASHBOARD"

is_pro = (st.session_state.user in st.session_state.db.get("pro_users", []))

# --- [5] LOGIN ---
if st.session_state.page == "AUTH":
    st.title("🔐 NEXUS OS LOGIN")
    u = st.text_input("User")
    p = st.text_input("Pass", type="password")
    rem = st.checkbox("Ghi nhớ thiết bị")
    if st.button("TRUY CẬP"):
        if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
            st.session_state.user = u
            if rem: st.session_state.db["rem"][fp] = u; sync_io(st.session_state.db)
            st.session_state.page = "DASHBOARD"; st.rerun()

# --- [6] DASHBOARD ---
elif st.session_state.page == "DASHBOARD":
    st.title(f"🚀 Dashboard: {st.session_state.user}")
    c = st.columns(3)
    if c[0].button("🧠 AI CHAT"): st.session_state.page = "AI"; st.rerun()
    if c[1].button("☁️ CLOUD"): st.session_state.page = "CLOUD"; st.rerun()
    if c[2].button("⚙️ VIP"): st.session_state.page = "SETTINGS"; st.rerun()
    if st.button("🚪 Đăng xuất & Quên máy"):
        if fp in st.session_state.db["rem"]: del st.session_state.db["rem"][fp]
        sync_io(st.session_state.db); st.session_state.user = None; st.session_state.page = "AUTH"; st.rerun()

# --- [7] AI CHAT (BANNER XANH) ---
elif st.session_state.page == "AI":
    if st.button("🔙 QUAY LẠI"): st.session_state.page = "DASHBOARD"; st.rerun()
    
    # Sidebar quản lý chat
    with st.sidebar:
        if st.button("➕ Hội thoại mới"): st.session_state.chat_id = None; st.rerun()
        for i, c in enumerate(st.session_state.db["chats"]):
            if c["owner"] == st.session_state.user:
                if st.button(f"💬 {c['name']}", key=f"c_{i}"): st.session_state.chat_id = i; st.rerun()

    cid = st.session_state.get("chat_id")
    if cid is None or cid >= len(st.session_state.db["chats"]):
        st.session_state.db["chats"].append({"name": "Mới", "msgs": [], "owner": st.session_state.user, "time": str(datetime.now())})
        st.session_state.chat_id = len(st.session_state.db["chats"]) - 1
        cid = st.session_state.chat_id

    chat = st.session_state.db["chats"][cid]
    for m in chat["msgs"]:
        if m["role"] == "user": st.chat_message("user").write(m["content"])
        else: st.markdown(f'<div class="ai-banner">{m["content"]}</div>', unsafe_allow_html=True)

    if p := st.chat_input("Hỏi AI..."):
        chat["msgs"].append({"role": "user", "content": p})
        client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=chat["msgs"][-5:])
        ans = res.choices[0].message.content
        chat["msgs"].append({"role": "assistant", "content": ans})
        sync_io(st.session_state.db); st.rerun()

# --- [8] CLOUD (TỰ LƯU & TẢI MƯỢT) ---
elif st.session_state.page == "CLOUD":
    if st.button("🔙 QUAY LẠI"): st.session_state.page = "DASHBOARD"; st.rerun()
    st.header("☁️ KHO LƯU TRỮ")
    
    # TỰ ĐỘNG LƯU: Bỏ nút "Lưu", chỉ cần chọn file là up luôn
    up = st.file_uploader("Kéo file vào đây để tự động tải lên")
    if up:
        if up.name not in st.session_state.db["files"]:
            with st.spinner("Đang tự động đồng bộ..."):
                f_data = up.getvalue()
                st.session_state.db["files"][up.name] = {
                    "data": base64.b64encode(f_data).decode(),
                    "owner": st.session_state.user
                }
                sync_io(st.session_state.db)
                st.success(f"Đã tự động lưu: {up.name}!")
                time.sleep(1); st.rerun()

    st.divider()
    my_files = {k:v for k,v in st.session_state.db["files"].items() if v.get("owner") == st.session_state.user}
    
    for name, info in my_files.items():
        c1, c2, c3 = st.columns([3, 1, 1])
        c1.write(f"📄 {name}")
        
        # FIX TẢI XUỐNG: Dùng nút chuẩn của Streamlit
        try:
            bin_file = base64.b64decode(info["data"])
            c2.download_button(label="📥 TẢI VỀ", data=bin_file, file_name=name, key=f"dl_{name}")
        except: st.error("Lỗi file")
        
        if c3.button("🗑️ XÓA", key=f"del_{name}"):
            del st.session_state.db["files"][name]; sync_io(st.session_state.db); st.rerun()

# --- [9] VIP & SETTINGS ---
elif st.session_state.page == "SETTINGS":
    if st.button("🔙 QUAY LẠI"): st.session_state.page = "DASHBOARD"; st.rerun()
    st.header("⚙️ SETTINGS")
    code = st.text_input("Nhập mã Pro").upper()
    if st.button("KÍCH HOẠT"):
        if code in st.session_state.db["codes"]:
            st.session_state.db["pro_users"].append(st.session_state.user)
            st.session_state.db.get("codes", []).remove(code)
            sync_io(st.session_state.db); st.balloons(); st.rerun()
