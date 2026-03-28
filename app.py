# -*- coding: utf-8 -*-
import streamlit as st
import time, base64, json, requests, random, hashlib
from openai import OpenAI
from streamlit_js_eval import streamlit_js_eval
from datetime import datetime, timedelta

# --- [1] CẤU HÌNH HỆ THỐNG ---
CONFIG = {
    "CREATOR": "Thiên Phát",
    "MASTER_PASS": "nexus os gateway",
    "VERSION": 13.0,
    "FILE_DATA": "nexus_beast_vault.json"
}

try:
    GH_TOKEN, GH_REPO = st.secrets["GH_TOKEN"], st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS]
except:
    st.error("🛑 THIẾU SECRETS!")
    st.stop()

st.set_page_config(page_title="NEXUS BEAST", layout="wide", initial_sidebar_state="collapsed")

# --- [2] UI: NÚT HOME TÀNG HÌNH & GIAO DIỆN ---
def apply_ui():
    st.markdown(f"""
    <style>
    .stApp {{
        background-image: url('https://images.unsplash.com/photo-1449824913935-59a10b8d2000?auto=format&fit=crop&w=1920&q=80');
        background-size: cover; background-attachment: fixed;
    }}
    h1, h2, h3, p, span, label, .stMarkdown {{
        color: #000 !important; font-weight: 900 !important;
        text-shadow: 1px 1px 3px #22d3ee;
    }}
    /* NÚT HOME NỔI - TRÒN MỜ */
    .floating-home {{
        position: fixed; top: 20px; left: 20px; width: 45px; height: 45px;
        background: rgba(255,255,255,0.15); border: 1px solid rgba(34, 211, 238, 0.5);
        border-radius: 50%; display: flex; align-items: center; justify-content: center;
        text-decoration: none; z-index: 10000; transition: 0.3s; opacity: 0.5; font-size: 20px;
    }}
    .floating-home:hover {{ opacity: 1; background: #22d3ee; box-shadow: 0 0 15px #22d3ee; }}
    [data-testid="stHeader"] {{ visibility: hidden; }}
    </style>
    <a href="/?p=DASHBOARD" target="_self" class="floating-home">🏠</a>
    """, unsafe_allow_html=True)

# --- [3] KERNEL DỮ LIỆU (CHỐNG MẤT DỮ LIỆU) ---
def sync_io(data=None):
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{CONFIG['FILE_DATA']}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    if data is None: # GET
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return json.loads(base64.b64decode(res.json()['content']).decode('utf-8'))
        return {"users": {CONFIG["CREATOR"]: CONFIG["MASTER_PASS"]}, "remember_map": {}, "pro_users": [], "blacklist": [], "updates": {"delay": 7, "ver": 13.5}}
    else: # PUT
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, indent=4, ensure_ascii=False).encode('utf-8')).decode('utf-8')
        requests.put(url, headers=headers, json={"message": "Beast Sync", "content": content, "sha": sha})

# --- [4] XÁC THỰC THIẾT BỊ & GHI NHỚ ---
def get_device_id():
    ua = st.context.headers.get("User-Agent", "unknown")
    return hashlib.sha256(ua.encode()).hexdigest()[:16]

def silent_verify():
    # Kiểm tra JS ngầm không thông báo
    scr_w = streamlit_js_eval(js_expressions="window.innerWidth", key="silent_check")
    return True if scr_w else False

# --- [5] TRANG CHÍNH ---
def main():
    apply_ui()
    if 'db' not in st.session_state:
        st.session_state.db = sync_io()
        st.session_state.page = "AUTH"
        st.session_state.user = None

    dev_id = get_device_id()
    
    # Tự động đăng nhập (Remember Me)
    if st.session_state.user is None and dev_id in st.session_state.db["remember_map"]:
        st.session_state.user = st.session_state.db["remember_map"][dev_id]
        st.session_state.page = "DASHBOARD"

    # --- MÀN HÌNH ĐĂNG NHẬP ---
    if st.session_state.page == "AUTH":
        st.markdown("<h1 style='text-align:center;'>🏙️ NEXUS GATEWAY</h1>", unsafe_allow_html=True)
        _, col, _ = st.columns([1, 1.5, 1])
        with col:
            u = st.text_input("Định danh").strip()
            p = st.text_input("Mật mã", type="password").strip()
            rem = st.checkbox("Ghi nhớ đăng nhập")
            
            if st.button("TRUY CẬP", use_container_width=True):
                if silent_verify(): # Kiểm tra bot ngầm
                    if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
                        st.session_state.user = u
                        if rem:
                            st.session_state.db["remember_map"][dev_id] = u
                            sync_io(st.session_state.db)
                        st.session_state.page = "DASHBOARD"
                        st.rerun()
                    else: st.error("Sai thông tin truy cập!")
                else: st.error("Lỗi hệ thống (B-01). Thử lại sau.")

    # --- DASHBOARD ---
    elif st.session_state.page == "DASHBOARD":
        st.title(f"🚀 {st.session_state.user}")
        c = st.columns(4)
        if c[0].button("🧠 AI"): st.session_state.page = "AI"; st.rerun()
        if c[1].button("☁️ CLOUD"): st.session_state.page = "CLOUD"; st.rerun()
        if c[2].button("⚙️ CÀI ĐẶT"): st.session_state.page = "SETTINGS"; st.rerun()
        if c[3].button("🛠️ ADMIN") and st.session_state.user == CONFIG["CREATOR"]:
            st.session_state.page = "ADMIN"; st.rerun()

    # --- CÀI ĐẶT (NHẬP MÃ & CẬP NHẬT) ---
    elif st.session_state.page == "SETTINGS":
        st.header("⚙️ CÀI ĐẶT")
        if st.button("🔙 QUAY LẠI"): st.session_state.page = "DASHBOARD"; st.rerun()
        
        tab1, tab2, tab3 = st.tabs(["💎 PRO CODE", "🆙 UPDATE", "ℹ️ ABOUT"])
        with tab1:
            code = st.text_input("Nhập mã 8 ký tự").upper()
            if st.button("KÍCH HOẠT"):
                # Logic check mã từ db...
                st.session_state.db["pro_users"].append(st.session_state.user)
                sync_io(st.session_state.db); st.success("💎 Đã lên PRO!")
        
        with tab2:
            is_pro = st.session_state.user in st.session_state.db["pro_users"]
            st.write(f"Version: {CONFIG['VERSION']}")
            if st.button("KIỂM TRA CẬP NHẬT"):
                if is_pro: st.success("Bản V13.5 đã sẵn sàng cho PRO!")
                else: st.warning(f"Bản cập nhật mới đang được delay {st.session_state.db['updates']['delay']} ngày cho Guest.")

    # --- AI NEXUS (THÔNG MINH HƠN) ---
    elif st.session_state.page == "AI":
        st.subheader("🧠 NEXUS INTELLIGENCE")
        if 'chat_log' not in st.session_state: st.session_state.chat_log = []
        
        for m in st.session_state.chat_log:
            with st.chat_message(m["role"]): st.write(m["content"])
            
        if prompt := st.chat_input("Lệnh..."):
            st.session_state.chat_log.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.write(prompt)
            
            try:
                client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
                res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": "Bạn là NEXUS OS, trợ lý tối cao của Thiên Phát. Hãy trả lời cực kỳ thông minh, ngắn gọn và có tầm nhìn."}] + st.session_state.chat_log[-10:]
                )
                ans = res.choices[0].message.content
                st.session_state.chat_log.append({"role": "assistant", "content": ans})
                with st.chat_message("assistant"): st.write(ans)
            except: st.error("AI đang bận xử lý dữ liệu khác.")

    # --- ADMIN ---
    elif st.session_state.page == "ADMIN":
        st.header("🛠️ CONTROL CENTER")
        if st.button("🔙 VỀ"): st.session_state.page = "DASHBOARD"; st.rerun()
        new_delay = st.slider("Delay cho Guest (ngày)", 0, 30, st.session_state.db["updates"]["delay"])
        if st.button("LƯU CẤU HÌNH"):
            st.session_state.db["updates"]["delay"] = new_delay
            sync_io(st.session_state.db); st.success("Đã áp dụng!")

if __name__ == "__main__":
    main()
