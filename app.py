# -*- coding: utf-8 -*-
import streamlit as st
import time, base64, json, requests, random, hashlib
from openai import OpenAI
from datetime import datetime, timedelta
from typing import Dict, Optional

# --- [1] CẤU HÌNH ---
CONFIG = {
    "NAME": "NEXUS OS",
    "CREATOR": "Thiên Phát",
    "FILE_DATA": "nexus_gateway_v40.json",
    "GUEST_ENABLED": True,
    "MAX_RETRIES": 3,
    "RETRY_DELAY": 1
}

# Load secrets
try:
    GH_TOKEN, GH_REPO = st.secrets["GH_TOKEN"], st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS]
except Exception:
    st.error("🛑 LỖI: Thiếu cấu hình Secrets trên Streamlit Cloud!")
    st.stop()

st.set_page_config(page_title=CONFIG["NAME"], layout="wide", initial_sidebar_state="expanded")

# --- [2] CSS GIAO DIỆN HIỆN ĐẠI ---
st.markdown("""
<style>
/* Tổng thể */
.stApp {
    background: linear-gradient(135deg, #f5f7fa 0%, #e9edf2 100%);
}
/* Sidebar tùy chỉnh */
[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.95);
    backdrop-filter: blur(10px);
    border-right: 1px solid rgba(0,0,0,0.05);
    box-shadow: 2px 0 12px rgba(0,0,0,0.03);
}
/* Card cho các phần tử */
.custom-card {
    background: white;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    transition: transform 0.2s, box-shadow 0.2s;
    margin-bottom: 20px;
}
.custom-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.1);
}
/* Banner AI */
.ai-banner {
    background: linear-gradient(135deg, #0047AB, #0066CC);
    color: white !important;
    padding: 16px 20px;
    border-radius: 20px;
    margin: 12px 0;
    box-shadow: 0 4px 12px rgba(0,71,171,0.2);
    font-weight: 500;
    border-left: 4px solid #FFD966;
}
/* Nút chính */
.stButton>button {
    border-radius: 40px;
    font-weight: 600;
    padding: 0.5rem 1rem;
    transition: all 0.2s ease;
    background: #0047AB;
    color: white;
    border: none;
}
.stButton>button:hover {
    background: #003399;
    transform: scale(1.02);
    box-shadow: 0 4px 12px rgba(0,71,171,0.3);
}
/* Nút phụ */
.secondary-btn button {
    background: #f0f2f6;
    color: #1f2937;
}
.secondary-btn button:hover {
    background: #e4e7eb;
}
/* Badge */
.guest-badge {
    background: #FFD966;
    color: #1f2937;
    padding: 4px 12px;
    border-radius: 40px;
    font-size: 0.8rem;
    font-weight: bold;
    display: inline-block;
}
.pro-badge {
    background: linear-gradient(135deg, #FFD700, #FFB347);
    color: #1f2937;
}
/* Chat input */
.stChatInput textarea {
    border-radius: 24px;
    border: 1px solid #e2e8f0;
    padding: 12px 20px;
}
/* File list */
.file-item {
    background: white;
    border-radius: 12px;
    padding: 12px;
    margin: 8px 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    transition: all 0.2s;
}
.file-item:hover {
    background: #f8fafc;
}
/* Toast */
div[data-testid="stToast"] {
    border-radius: 12px;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

# --- [3] HÀM TIỆN ÍCH ---
def get_device_fp() -> str:
    ua = st.context.headers.get("User-Agent", "Unknown")
    return hashlib.sha256(ua.encode()).hexdigest()[:16]

def safe_load_json(content: str) -> Dict:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {"users": {CONFIG["CREATOR"]: "nexus os gateway"}, 
                "codes": ["PHAT2026"], 
                "pro_users": [], 
                "chats": [], 
                "files": {}}

def sync_io(data: Optional[Dict] = None, retries: int = CONFIG["MAX_RETRIES"]) -> Optional[Dict]:
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{CONFIG['FILE_DATA']}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    for attempt in range(retries):
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if data is None:
                if res.status_code == 200:
                    content = base64.b64decode(res.json()['content']).decode('utf-8')
                    return safe_load_json(content)
                elif res.status_code == 404:
                    default_data = {"users": {CONFIG["CREATOR"]: "nexus os gateway"}, 
                                    "codes": ["PHAT2026"], 
                                    "pro_users": [], 
                                    "chats": [], 
                                    "files": {}}
                    sync_io(default_data, retries=1)
                    return default_data
                else:
                    st.error(f"Lỗi đọc GitHub: {res.status_code}")
                    return None
            else:
                if res.status_code in (200, 404):
                    sha = res.json().get("sha") if res.status_code == 200 else None
                    content = base64.b64encode(json.dumps(data, ensure_ascii=False).encode('utf-8')).decode('utf-8')
                    put_res = requests.put(url, headers=headers, 
                                           json={"message": "Nexus Sync", "content": content, "sha": sha},
                                           timeout=10)
                    if put_res.status_code in (200, 201):
                        return data
                    elif put_res.status_code == 409 and attempt < retries - 1:
                        time.sleep(CONFIG["RETRY_DELAY"])
                        continue
                    else:
                        st.error(f"Lỗi ghi GitHub: {put_res.status_code}")
                        return None
                else:
                    return None
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(CONFIG["RETRY_DELAY"])
            else:
                st.error(f"Lỗi kết nối: {str(e)}")
                return None
    return None

@st.cache_data(ttl=60)
def load_db():
    return sync_io()

def init_session():
    if 'db' not in st.session_state:
        st.session_state.db = load_db()
    if 'page' not in st.session_state:
        st.session_state.page = "AUTH"
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'chat_id' not in st.session_state:
        st.session_state.chat_id = None
    if 'guest_mode' not in st.session_state:
        st.session_state.guest_mode = False
    if 'temp_chat' not in st.session_state:
        st.session_state.temp_chat = {"msgs": []}

init_session()
fp = get_device_fp()
is_pro = (st.session_state.user in st.session_state.db.get("pro_users", []))

def go_to(page):
    st.session_state.page = page
    st.rerun()

# --- [4] SIDEBAR CỐ ĐỊNH VỚI NÚT QUAY LẠI ---
with st.sidebar:
    # Logo / Tiêu đề
    st.markdown(f"### {CONFIG['NAME']}")
    if st.session_state.user:
        st.markdown(f"👤 **{st.session_state.user}**")
        if st.session_state.guest_mode:
            st.markdown('<span class="guest-badge">🔓 CHẾ ĐỘ KHÁCH</span>', unsafe_allow_html=True)
        else:
            badge = "💎 PRO" if is_pro else "🆓 FREE"
            st.markdown(f'<span class="guest-badge pro-badge">{badge}</span>', unsafe_allow_html=True)
    st.divider()
    
    # Nút quay về (chỉ hiển thị ở các trang con)
    if st.session_state.page not in ["AUTH", "DASHBOARD"]:
        if st.button("🔙 QUAY LẠI", use_container_width=True, key="back_btn"):
            go_to("DASHBOARD")
    
    # Các liên kết nhanh (tùy chọn)
    if st.session_state.user:
        st.markdown("---")
        st.caption("🚀 Tiện ích nhanh")
        if st.button("🧠 Chat AI", use_container_width=True, key="quick_chat"):
            go_to("AI")
        if st.button("☁️ Lưu trữ", use_container_width=True, key="quick_cloud"):
            go_to("CLOUD")
        if st.button("⚙️ Cài đặt", use_container_width=True, key="quick_settings"):
            go_to("SETTINGS")
        if st.session_state.user == CONFIG["CREATOR"]:
            if st.button("🛠️ Admin", use_container_width=True, key="quick_admin"):
                go_to("ADMIN")
        if st.button("🚪 Đăng xuất", use_container_width=True, key="logout"):
            st.session_state.user = None
            st.session_state.guest_mode = False
            st.session_state.temp_chat = {"msgs": []}
            go_to("AUTH")

# --- [5] TRANG ĐĂNG NHẬP ---
if st.session_state.page == "AUTH":
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.title("🔐 ĐĂNG NHẬP NEXUS")
        u = st.text_input("Tài khoản")
        p = st.text_input("Mật khẩu", type="password")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("ĐĂNG NHẬP", use_container_width=True):
                if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
                    st.session_state.user = u
                    st.session_state.guest_mode = False
                    st.toast("✅ Đăng nhập thành công!", icon="🎉")
                    go_to("DASHBOARD")
                else:
                    st.error("Sai tài khoản hoặc mật khẩu!")
        if CONFIG["GUEST_ENABLED"]:
            with col_btn2:
                if st.button("👤 DÙNG THỬ (GUEST)", use_container_width=True):
                    st.session_state.user = "guest"
                    st.session_state.guest_mode = True
                    st.toast("🔓 Bạn đang ở chế độ khách. Dữ liệu sẽ không được lưu.", icon="👋")
                    go_to("DASHBOARD")
        st.caption("💡 Guest: trải nghiệm đầy đủ tính năng nhưng không lưu trữ vĩnh viễn.")
        st.markdown('</div>', unsafe_allow_html=True)

# --- [6] DASHBOARD ---
elif st.session_state.page == "DASHBOARD":
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.title(f"🚀 Chào mừng, {st.session_state.user}!")
    if st.session_state.guest_mode:
        st.markdown('<span class="guest-badge">👤 CHẾ ĐỘ KHÁCH (Demo)</span>', unsafe_allow_html=True)
        st.info("Bạn đang dùng thử. Đăng nhập để lưu dữ liệu và kích hoạt Pro.")
    else:
        st.write(f"Cấp độ: {'💎 **PRO**' if is_pro else '🆓 **Miễn phí**'}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🧠 TRÒ CHUYỆN AI", use_container_width=True):
            go_to("AI")
    with col2:
        if st.button("☁️ LƯU TRỮ CLOUD", use_container_width=True):
            go_to("CLOUD")
    with col3:
        if st.button("⚙️ CÀI ĐẶT & VIP", use_container_width=True):
            go_to("SETTINGS")
    
    if st.session_state.user == CONFIG["CREATOR"]:
        if st.button("🛠️ QUẢN TRỊ VIÊN", use_container_width=True):
            go_to("ADMIN")

# --- [7] AI CHAT ---
elif st.session_state.page == "AI":
    st.header("🧠 NEXUS AI - Trợ lý thông minh")
    
    # Quản lý danh sách chat (sidebar đã có nút quay về, nên sidebar hiển thị thêm chat list)
    if not st.session_state.guest_mode:
        with st.sidebar:
            st.markdown("### 📝 Lịch sử chat")
            if st.button("➕ Hội thoại mới", use_container_width=True):
                st.session_state.chat_id = None
                st.rerun()
            for i, c in enumerate(st.session_state.db["chats"]):
                if c["owner"] == st.session_state.user:
                    col_t, col_d = st.columns([4, 1])
                    with col_t:
                        if st.button(f"💬 {c['name']}", key=f"chat_{i}", use_container_width=True):
                            st.session_state.chat_id = i
                            st.rerun()
                    with col_d:
                        if st.button("🗑️", key=f"del_{i}"):
                            # Xác nhận xóa
                            if st.session_state.get(f"confirm_del_{i}", False):
                                st.session_state.db["chats"].pop(i)
                                if st.session_state.chat_id == i:
                                    st.session_state.chat_id = None
                                sync_io(st.session_state.db)
                                st.toast("Đã xóa hội thoại", icon="🗑️")
                                st.rerun()
                            else:
                                st.session_state[f"confirm_del_{i}"] = True
                                st.warning("Nhấn lại để xác nhận xóa")
    else:
        with st.sidebar:
            st.info("👤 Chế độ khách: lịch sử chat không được lưu.")
    
    # Xử lý chat hiện tại
    if st.session_state.guest_mode:
        chat = st.session_state.temp_chat
        if "msgs" not in chat:
            chat["msgs"] = []
    else:
        idx = st.session_state.chat_id
        if idx is None or idx >= len(st.session_state.db["chats"]):
            new_chat = {"name": "Hội thoại mới", "msgs": [], "owner": st.session_state.user, 
                        "temp": False, "time": str(datetime.now())}
            st.session_state.db["chats"].append(new_chat)
            st.session_state.chat_id = len(st.session_state.db["chats"]) - 1
            idx = st.session_state.chat_id
        chat = st.session_state.db["chats"][idx]
        temp_mode = st.toggle("🧹 Chế độ tạm thời (xóa sau 24h)", value=chat.get("temp", False))
        chat["temp"] = temp_mode
    
    # Hiển thị tin nhắn
    for m in chat["msgs"]:
        if m["role"] == "user":
            with st.chat_message("user"):
                st.write(m["content"])
        else:
            st.markdown(f'<div class="ai-banner">{m["content"]}</div>', unsafe_allow_html=True)
    
    # Nhập câu hỏi
    if p := st.chat_input("Nhập câu hỏi của bạn..."):
        chat["msgs"].append({"role": "user", "content": p})
        with st.spinner("🤖 Đang suy nghĩ..."):
            client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
            try:
                context = chat["msgs"][-5:] if not is_pro else chat["msgs"][-10:]
                res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=context,
                    temperature=0.7,
                    max_tokens=1024
                )
                ans = res.choices[0].message.content
            except Exception as e:
                ans = f"❌ Lỗi AI: {str(e)}"
            chat["msgs"].append({"role": "assistant", "content": ans})
        
        # Đặt tên tự động nếu cần
        if not st.session_state.guest_mode and (chat["name"] == "Hội thoại mới" or len(chat["msgs"]) == (10 if is_pro else 4)):
            try:
                client_small = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
                n_res = client_small.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": f"Tóm tắt câu hỏi sau thành tối đa 5 từ: {p}"}]
                )
                new_name = n_res.choices[0].message.content.strip('".')
                if new_name:
                    chat["name"] = new_name[:30]
            except:
                pass
        
        if not st.session_state.guest_mode:
            sync_io(st.session_state.db)
        st.rerun()

# --- [8] CLOUD ---
elif st.session_state.page == "CLOUD":
    st.header("☁️ NEXUS CLOUD - Lưu trữ cá nhân")
    
    if st.session_state.guest_mode:
        st.warning("Guest không thể sử dụng lưu trữ đám mây. Đăng nhập để lưu file.")
    else:
        files = {k:v for k,v in st.session_state.db["files"].items() if v.get("owner") == st.session_state.user}
        
        # Upload file
        up = st.file_uploader("📂 Chọn tệp để tải lên", type=None)
        if up and st.button("📤 TẢI LÊN", use_container_width=True):
            with st.spinner("Đang tải lên..."):
                progress_bar = st.progress(0)
                for i in range(100):
                    time.sleep(0.01)
                    progress_bar.progress(i + 1)
                st.session_state.db["files"][up.name] = {
                    "data": base64.b64encode(up.getvalue()).decode(),
                    "owner": st.session_state.user,
                    "size": len(up.getvalue()),
                    "upload_time": str(datetime.now())
                }
                sync_io(st.session_state.db)
                st.toast(f"✅ Đã tải lên {up.name} thành công!", icon="📁")
                st.rerun()
        
        # Danh sách file
        if files:
            st.subheader("📁 Các tệp của bạn")
            for name, info in files.items():
                size_kb = info.get("size", 0) / 1024
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"📄 {name} ({size_kb:.1f} KB)")
                with col2:
                    st.markdown(f'<a href="data:application/octet-stream;base64,{info["data"]}" download="{name}" style="text-decoration:none;"><button style="background:#0047AB; color:white; border:none; border-radius:20px; padding:5px 12px;">📥 Tải về</button></a>', unsafe_allow_html=True)
                with col3:
                    if st.button("🗑️ Xóa", key=f"del_{name}"):
                        if st.session_state.get(f"confirm_del_{name}", False):
                            del st.session_state.db["files"][name]
                            sync_io(st.session_state.db)
                            st.toast(f"Đã xóa {name}", icon="🗑️")
                            st.rerun()
                        else:
                            st.session_state[f"confirm_del_{name}"] = True
                            st.warning("Nhấn lại để xác nhận xóa")
        else:
            st.info("Bạn chưa có file nào. Hãy tải lên file đầu tiên!")

# --- [9] CÀI ĐẶT & VIP ---
elif st.session_state.page == "SETTINGS":
    st.header("⚙️ CÀI ĐẶT & NÂNG CẤP VIP")
    
    if st.session_state.guest_mode:
        st.info("🔓 Guest không thể kích hoạt VIP. Đăng nhập để nâng cấp.")
    else:
        with st.container():
            st.subheader("🎁 Kích hoạt mã Pro")
            code = st.text_input("Nhập mã kích hoạt", placeholder="VD: PHAT2026", help="Liên hệ admin để có mã").upper()
            if st.button("KÍCH HOẠT NGAY", use_container_width=True):
                if code in st.session_state.db["codes"]:
                    st.session_state.db["pro_users"].append(st.session_state.user)
                    st.session_state.db["codes"].remove(code)
                    sync_io(st.session_state.db)
                    st.balloons()
                    st.toast("🎉 Chúc mừng! Bạn đã trở thành thành viên Pro!", icon="💎")
                    st.rerun()
                else:
                    st.error("❌ Mã không hợp lệ hoặc đã được sử dụng.")
        
        st.divider()
        st.subheader("ℹ️ Thông tin tài khoản")
        st.write(f"**Tên:** {st.session_state.user}")
        st.write(f"**Hạng:** {'Pro' if is_pro else 'Miễn phí'}")
        if not is_pro:
            st.caption("Nâng cấp Pro để có: Context AI dài hơn, lưu trữ không giới hạn, ưu tiên hỗ trợ.")

# --- [10] ADMIN ---
elif st.session_state.page == "ADMIN":
    if st.session_state.user != CONFIG["CREATOR"]:
        st.error("Bạn không có quyền truy cập.")
        go_to("DASHBOARD")
    else:
        st.header("🛠️ QUẢN TRỊ VIÊN")
        with st.container():
            st.subheader("➕ Tạo mã Pro mới")
            new_code = st.text_input("Nhập mã mới", placeholder="VD: VIP2025").upper()
            if st.button("TẠO MÃ", use_container_width=True):
                if new_code and new_code not in st.session_state.db["codes"]:
                    st.session_state.db["codes"].append(new_code)
                    sync_io(st.session_state.db)
                    st.toast(f"✅ Đã tạo mã {new_code} thành công!", icon="🎫")
                    st.rerun()
                else:
                    st.error("Mã đã tồn tại hoặc không hợp lệ.")
        
        st.divider()
        st.subheader("👥 Danh sách Pro Users")
        if st.session_state.db["pro_users"]:
            for u in st.session_state.db["pro_users"]:
                st.write(f"- {u}")
        else:
            st.write("Chưa có người dùng Pro.")
        
        st.divider()
        if st.button("🔄 Đồng bộ dữ liệu", use_container_width=True):
            with st.spinner("Đang đồng bộ..."):
                st.session_state.db = sync_io()
                st.toast("Đã đồng bộ dữ liệu từ GitHub!", icon="🔄")
                st.rerun()
