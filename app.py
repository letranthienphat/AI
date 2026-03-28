# -*- coding: utf-8 -*-
import streamlit as st
import time, base64, json, requests, random
from openai import OpenAI
from datetime import datetime, timedelta

# --- [1] CẤU HÌNH HỆ THỐNG ---
SYSTEM_NAME = "NEXUS OS GATEWAY"
CREATOR = "Thiên Phát"
MASTER_PASS = "nexus os gateway"
FILE_DATA = "nexus_vault_v2.json"

try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS]
except:
    st.error("🛑 THIẾU SECRETS!")
    st.stop()

st.set_page_config(page_title=SYSTEM_NAME, layout="wide", initial_sidebar_state="collapsed")

# --- [2] CSS FIX LỖI HIỂN THỊ & THEME THÀNH PHỐ ---
def apply_ui():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@700&display=swap');
    .stApp {{
        background-image: url('https://images.unsplash.com/photo-1449824913935-59a10b8d2000?auto=format&fit=crop&w=1920&q=80');
        background-size: cover; background-attachment: fixed;
    }}
    
    /* Chữ đen viền xanh dương - Chống lỗi đọc trên nền sáng */
    h1, h2, h3, p, span, label, .stMarkdown, .stCheckbox {{
        color: black !important;
        font-family: 'Segoe UI', sans-serif !important;
        text-shadow: -1px -1px 0 #22d3ee, 1px -1px 0 #22d3ee, -1px 1px 0 #22d3ee, 1px 1px 0 #22d3ee;
    }}

    /* FIX LỖI HIỂN THỊ CHAT BUBBLE (KHÔNG ĐÈ CHỮ) */
    .stChatMessage {{
        background: rgba(255, 255, 255, 0.85) !important;
        border: 2px solid #22d3ee !important;
        border-radius: 15px !important;
        padding: 20px !important;
        margin-bottom: 15px !important;
    }}
    /* Tách biệt nhãn người dùng và nội dung */
    [data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"] {{
        background-color: #22d3ee !important;
        border: 2px solid black !important;
    }}

    div.stButton > button {{
        background-color: rgba(255, 255, 255, 0.9) !important;
        color: black !important; border: 2px solid #22d3ee !important;
        font-weight: bold !important; border-radius: 10px !important;
    }}
    div.stButton > button:hover {{ background-color: #22d3ee !important; color: white !important; }}
    
    [data-testid="stHeader"] {{ visibility: hidden; }}
    </style>
    """, unsafe_allow_html=True)

# --- [3] KERNEL DỮ LIỆU ---
def sync_get():
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GH_TOKEN}"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return json.loads(base64.b64decode(res.json()['content']).decode('utf-8'))
    except: pass
    return {"users": {CREATOR: MASTER_PASS}, "status": {}, "codes": {}, "vault": {}}

def sync_save():
    data = {"users": st.session_state.users, "status": st.session_state.status, 
            "codes": st.session_state.codes, "vault": st.session_state.vault}
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, indent=4, ensure_ascii=False).encode('utf-8')).decode('utf-8')
        requests.put(url, headers=headers, json={"message": "Admin Update", "content": content, "sha": sha})
    except: st.error("⚠️ Lỗi đồng bộ dữ liệu!")

# --- [4] KHỞI CHẠY ---
if 'boot' not in st.session_state:
    db = sync_get()
    st.session_state.update({
        "users": db.get("users", {CREATOR: MASTER_PASS}),
        "status": db.get("status", {}),
        "codes": db.get("codes", {}),
        "vault": db.get("vault", {}),
        "page": "AUTH", "user": None, "boot": True
    })

apply_ui()

# --- [5] TRANG ĐĂNG NHẬP ---
if st.session_state.page == "AUTH":
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<div style='height: 15vh;'></div>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align:center;'>🏙️ {SYSTEM_NAME}</h1>", unsafe_allow_html=True)
        u = st.text_input("Tên định danh").strip()
        p = st.text_input("Mật mã truy cập", type="password").strip()
        if st.button("KÍCH HOẠT HỆ THỐNG"):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.user = u
                st.session_state.page = "DASHBOARD"
                st.rerun()
            else: st.error("❌ Thông tin sai lệch!")
        if st.button("ĐĂNG KÝ MỚI"):
            if u and p and u not in st.session_state.users:
                st.session_state.users[u] = p
                sync_save(); st.success("✅ Đã tạo tài khoản!")
            else: st.warning("⚠️ Tên đã tồn tại hoặc trống.")

# --- [6] DASHBOARD ---
elif st.session_state.page == "DASHBOARD":
    st.title(f"🚀 NEXUS TERMINAL | {st.session_state.user}")
    
    # Hiển thị hạn dùng
    user_stat = st.session_state.status.get(st.session_state.user, "FREE")
    st.write(f"Cấp độ hiện tại: **{user_stat}**")

    c1, c2, c3, c4 = st.columns(4)
    with c1: 
        if st.button("🧠 AI CHAT"): st.session_state.page = "AI"; st.rerun()
    with c2:
        if st.button("☁️ CLOUD"): st.session_state.page = "CLOUD"; st.rerun()
    with c3:
        if st.button("💎 NÂNG CẤP"): st.session_state.page = "UPGRADE"; st.rerun()
    with c4:
        if st.session_state.user == CREATOR:
            if st.button("🛠️ ADMIN PANEL"): st.session_state.page = "ADMIN"; st.rerun()

    if st.button("🔌 ĐĂNG XUẤT"): 
        st.session_state.page = "AUTH"; st.session_state.user = None; st.rerun()

# --- [7] ADMIN PANEL (MỚI) ---
elif st.session_state.page == "ADMIN":
    st.header("🛠️ BẢNG ĐIỀU KHIỂN TỐI CAO")
    if st.button("🔙 VỀ"): st.session_state.page = "DASHBOARD"; st.rerun()
    
    with st.expander("✨ TẠO MÃ KÍCH HOẠT MỚI", expanded=True):
        new_code = st.text_input("Nhập mã (8 ký tự)", max_chars=8).strip()
        is_multi = st.checkbox("Cho phép nhiều người dùng chung mã này")
        is_perm = st.checkbox("Đặt thời hạn vĩnh viễn")
        days = st.number_input("Số ngày hiệu lực (nếu không vĩnh viễn)", min_value=1, value=30)
        
        if st.button("PHÁT HÀNH MÃ"):
            if len(new_code) == 8:
                st.session_state.codes[new_code] = {
                    "multi": is_multi,
                    "perm": is_perm,
                    "days": days,
                    "used_by": []
                }
                sync_save(); st.success(f"✅ Đã tạo mã: {new_code}")
            else: st.error("❌ Mã phải đúng 8 ký tự!")

    st.subheader("📋 Danh sách mã hiện có")
    st.write(st.session_state.codes)

# --- [8] TRANG NÂNG CẤP (DÀNH CHO USER) ---
elif st.session_state.page == "UPGRADE":
    st.subheader("💎 KÍCH HOẠT QUYỀN LỢI")
    if st.button("🔙 VỀ"): st.session_state.page = "DASHBOARD"; st.rerun()
    
    code_input = st.text_input("Nhập mã 8 ký tự").strip()
    if st.button("XÁC NHẬN"):
        if code_input in st.session_state.codes:
            c_info = st.session_state.codes[code_input]
            
            # Kiểm tra xem mã đã dùng chưa (nếu không phải mã multi)
            if not c_info['multi'] and len(c_info['used_by']) >= 1:
                st.error("❌ Mã này đã được sử dụng!")
            elif st.session_state.user in c_info['used_by']:
                st.warning("⚠️ Bạn đã dùng mã này rồi.")
            else:
                # Tính ngày hết hạn
                if c_info['perm']:
                    expiry = "VĨNH VIỄN"
                else:
                    exp_date = datetime.now() + timedelta(days=c_info['days'])
                    expiry = exp_date.strftime("%d/%m/%Y")
                
                st.session_state.status[st.session_state.user] = f"PRO-MAX (Hạn: {expiry})"
                c_info['used_by'].append(st.session_state.user)
                sync_save()
                st.balloons(); st.success(f"💎 Nâng cấp thành công! Hạn dùng: {expiry}")
        else:
            st.error("❌ Mã không tồn tại!")

# --- [9] AI CHAT (FIX LỖI ĐÈ CHỮ) ---
elif st.session_state.page == "AI":
    st.subheader("🧠 NEXUS INTELLIGENCE")
    if st.button("🔙 VỀ"): st.session_state.page = "DASHBOARD"; st.rerun()
    
    if st.session_state.user not in st.session_state.vault:
        st.session_state.vault[st.session_state.user] = []
        
    for m in st.session_state.vault[st.session_state.user]:
        # Streamlit tự động xử lý bubble, CSS ở trên sẽ đảm bảo không đè chữ
        with st.chat_message(m['role']):
            st.markdown(m['content'])
            
    if p := st.chat_input("Nhập lệnh..."):
        st.session_state.vault[st.session_state.user].append({"role": "user", "content": p})
        st.rerun()
