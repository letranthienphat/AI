# -*- coding: utf-8 -*-
import streamlit as st
import time, base64, json, requests, random, hashlib
from openai import OpenAI
from streamlit_js_eval import streamlit_js_eval
from datetime import datetime, timedelta

# --- [1] CẤU HÌNH CỐ ĐỊNH ---
CONFIG = {
    "NAME": "NEXUS OVERLORD",
    "CREATOR": "Thiên Phát",
    "MASTER_PASS": "nexus os gateway",
    "VERSION": 14.0,
    "FILE_DATA": "nexus_overlord_vault.json"
}

try:
    GH_TOKEN, GH_REPO = st.secrets["GH_TOKEN"], st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS]
except:
    st.error("🛑 THIẾU SECRETS TRÊN STREAMLIT CLOUD!")
    st.stop()

st.set_page_config(page_title=CONFIG["NAME"], layout="wide", initial_sidebar_state="collapsed")

# --- [2] UI & LOGO KHỞI ĐỘNG SVG ---
def apply_ui():
    st.markdown(f"""
    <style>
    .stApp {{
        background-image: url('https://images.unsplash.com/photo-1449824913935-59a10b8d2000?auto=format&fit=crop&w=1920&q=80');
        background-size: cover; background-attachment: fixed;
    }}
    h1, h2, h3, p, span, label, .stMarkdown, .stCheckbox {{
        color: #000 !important; font-weight: 900 !important;
        text-shadow: 1px 1px 3px #22d3ee;
    }}
    .floating-home {{
        position: fixed; top: 20px; left: 20px; width: 45px; height: 45px;
        background: rgba(255,255,255,0.1); border: 1px solid #22d3ee;
        border-radius: 50%; display: flex; align-items: center; justify-content: center;
        text-decoration: none; z-index: 10000; transition: 0.3s; opacity: 0.6;
    }}
    .floating-home:hover {{ opacity: 1; background: #22d3ee; box-shadow: 0 0 20px #22d3ee; color: white !important; }}
    [data-testid="stHeader"] {{ visibility: hidden; }}
    </style>
    <a href="/?p=DASHBOARD" target="_self" class="floating-home">🏠</a>
    """, unsafe_allow_html=True)

def show_splash():
    if 'splashed' not in st.session_state:
        placeholder = st.empty()
        with placeholder.container():
            st.markdown("""
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; background: white;">
                <svg width="200" height="200" viewBox="0 0 100 100">
                    <path d="M10 50 Q 25 25, 40 50 T 70 50 T 90 50" fill="none" stroke="#22d3ee" stroke-width="3">
                        <animate attributeName="stroke-dasharray" from="0,200" to="200,0" dur="2s" repeatCount="indefinite" />
                    </path>
                </svg>
                <h1 style="color: #000; letter-spacing: 10px; animation: pulse 2s infinite;">NEXUS ACTIVATING</h1>
            </div>
            """, unsafe_allow_html=True)
            time.sleep(3)
        placeholder.empty()
        st.session_state.splashed = True

# --- [3] HỆ THỐNG DỮ LIỆU & FILE ---
def sync_io(data=None):
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{CONFIG['FILE_DATA']}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    res = requests.get(url, headers=headers)
    if data is None: # GET
        if res.status_code == 200:
            return json.loads(base64.b64decode(res.json()['content']).decode('utf-8'))
        return {"users": {CONFIG["CREATOR"]: CONFIG["MASTER_PASS"]}, "remember": {}, "files": {}, "codes": {}, "delay": 7}
    else: # PUT
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, indent=4, ensure_ascii=False).encode('utf-8')).decode('utf-8')
        requests.put(url, headers=headers, json={"message": "Overlord Sync", "content": content, "sha": sha})

# --- [4] XỬ LÝ TRANG ---
show_splash()
apply_ui()

if 'db' not in st.session_state:
    st.session_state.db = sync_io()
    st.session_state.page = "AUTH"
    st.session_state.user = None

# Ghi nhớ thiết bị
dev_id = hashlib.sha256(st.context.headers.get("User-Agent", "unknown").encode()).hexdigest()[:12]
if st.session_state.user is None and dev_id in st.session_state.db.get("remember", {}):
    st.session_state.user = st.session_state.db["remember"][dev_id]
    st.session_state.page = "DASHBOARD"

# --- [5] MÀN HÌNH ĐĂNG NHẬP (FIX LỖI B-01) ---
if st.session_state.page == "AUTH":
    st.markdown("<h1 style='text-align:center;'>🛡️ NEXUS OVERLORD</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.2, 1])
    
    # Check bot ngầm - Lấy chiều rộng màn hình làm tín hiệu sẵn sàng
    sys_ready = streamlit_js_eval(js_expressions="window.innerWidth", key="sys_warmup")
    
    with col:
        u = st.text_input("Định danh User").strip()
        p = st.text_input("Mật mã", type="password").strip()
        rem = st.checkbox("Ghi nhớ thiết bị này")
        
        if st.button("XÁC THỰC TRUY CẬP", use_container_width=True):
            if not sys_ready:
                st.warning("Hệ thống đang khởi động lớp bảo mật, vui lòng nhấn lại sau 1 giây.")
            elif u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
                st.session_state.user = u
                if rem:
                    st.session_state.db["remember"][dev_id] = u
                    sync_io(st.session_state.db)
                st.session_state.page = "DASHBOARD"
                st.rerun()
            else: st.error("❌ Thông tin sai hoặc bạn bị từ chối truy cập.")

# --- [6] DASHBOARD ---
elif st.session_state.page == "DASHBOARD":
    st.title(f"🚀 XIN CHÀO: {st.session_state.user}")
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("🧠 AI NEXUS"): st.session_state.page = "AI"; st.rerun()
    if c2.button("☁️ NEXUS CLOUD"): st.session_state.page = "CLOUD"; st.rerun()
    if c3.button("⚙️ CÀI ĐẶT"): st.session_state.page = "SETTINGS"; st.rerun()
    if c4.button("🔌 ĐĂNG XUẤT"):
        if dev_id in st.session_state.db["remember"]: del st.session_state.db["remember"][dev_id]
        sync_io(st.session_state.db)
        st.session_state.user = None; st.session_state.page = "AUTH"; st.rerun()

# --- [7] NEXUS CLOUD (FULL TÍNH NĂNG) ---
elif st.session_state.page == "CLOUD":
    st.header("☁️ NEXUS STORAGE SYSTEM")
    if st.button("🔙 VỀ"): st.session_state.page = "DASHBOARD"; st.rerun()
    
    col_up, col_list = st.columns([1, 2])
    with col_up:
        st.subheader("📤 Tải lên")
        up_file = st.file_uploader("Chọn tệp (Max 5MB)")
        if up_file and st.button("LƯU VÀO CLOUD"):
            f_bytes = up_file.getvalue()
            f_base64 = base64.b64encode(f_bytes).decode()
            st.session_state.db["files"][up_file.name] = {
                "content": f_base64, "size": up_file.size, "date": str(datetime.now().date())
            }
            sync_io(st.session_state.db)
            st.success(f"Đã lưu: {up_file.name}")
            
    with col_list:
        st.subheader("📁 Tệp của bạn")
        for f_name, f_info in st.session_state.db.get("files", {}).items():
            c_a, c_b, c_c = st.columns([3, 1, 1])
            c_a.write(f"📄 {f_name} ({f_info['size']//1024} KB)")
            # Download link
            href = f'<a href="data:file/txt;base64,{f_info["content"]}" download="{f_name}">📥 Tải</a>'
            c_b.markdown(href, unsafe_allow_html=True)
            if c_c.button("🗑️", key=f_name):
                del st.session_state.db["files"][f_name]
                sync_io(st.session_state.db); st.rerun()

# --- [8] AI NEXUS V2 (PHÂN TÍCH & CHAT) ---
elif st.session_state.page == "AI":
    st.header("🧠 AI NEXUS INTELLIGENCE")
    if 'chat' not in st.session_state: st.session_state.chat = []
    
    for m in st.session_state.chat:
        with st.chat_message(m["role"]): st.write(m["content"])
        
    if p := st.chat_input("Nhập lệnh cho Nexus..."):
        st.session_state.chat.append({"role": "user", "content": p})
        with st.chat_message("user"): st.write(p)
        
        client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": f"Bạn là lõi não của NEXUS OS. Trả lời Phát (Creator) một cách trung thành, hài hước và phân tích cực kỳ sắc bén."}] + st.session_state.chat[-5:]
        )
        ans = res.choices[0].message.content
        st.session_state.chat.append({"role": "assistant", "content": ans})
        with st.chat_message("assistant"): st.write(ans)

# --- [9] CÀI ĐẶT (SETTINGS) ---
elif st.session_state.page == "SETTINGS":
    st.header("⚙️ CÀI ĐẶT HỆ THỐNG")
    t1, t2 = st.tabs(["💎 PRO CODE", "🆙 CẬP NHẬT"])
    with t1:
        code = st.text_input("Nhập mã 8 ký tự").upper()
        if st.button("KÍCH HOẠT"):
            st.success("💎 Quyền PRO đã được kích hoạt!")
    with t2:
        st.write(f"Phiên bản: {CONFIG['VERSION']}")
        if st.button("KIỂM TRA UPDATE"):
            st.info(f"Bạn đang dùng bản {CONFIG['VERSION']}. Không có bản mới hơn cho Guest.")
