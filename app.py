# -*- coding: utf-8 -*-
import streamlit as st
import time, base64, json, requests, random, hashlib, os
from openai import OpenAI
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import threading

# --- [1] CẤU HÌNH CỐ ĐỊNH ---
CONFIG = {
    "NAME": "NEXUS OS",
    "CREATOR": "Thiên Phát",
    "FILE_DATA": "nexus_gateway_v40.json",  # tên file mới để tránh xung đột
    "GUEST_ENABLED": True,                  # Bật guest mode
    "MAX_RETRIES": 3,                       # Số lần thử lại khi sync GitHub
    "RETRY_DELAY": 1                        # Giây giữa các lần thử
}

# Load secrets
try:
    GH_TOKEN, GH_REPO = st.secrets["GH_TOKEN"], st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS]
except Exception:
    st.error("🛑 LỖI: Thiếu cấu hình Secrets trên Streamlit Cloud! Vui lòng kiểm tra lại.")
    st.stop()

st.set_page_config(page_title=CONFIG["NAME"], layout="wide", initial_sidebar_state="collapsed")

# --- [2] HỆ THỐNG DỮ LIỆU NÂNG CẤP ---
def get_device_fp() -> str:
    """Lấy dấu vân tay thiết bị dựa trên User-Agent."""
    ua = st.context.headers.get("User-Agent", "Unknown")
    return hashlib.sha256(ua.encode()).hexdigest()[:16]

def safe_load_json(content: str) -> Dict:
    """An toàn load JSON, trả về dict mặc định nếu lỗi."""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Nếu file bị hỏng, trả về cấu trúc mặc định
        return {"users": {CONFIG["CREATOR"]: "nexus os gateway"}, 
                "codes": ["PHAT2026"], 
                "pro_users": [], 
                "chats": [], 
                "files": {}}

def sync_io(data: Optional[Dict] = None, retries: int = CONFIG["MAX_RETRIES"]) -> Optional[Dict]:
    """
    Đồng bộ dữ liệu với GitHub, có cơ chế retry và conflict handling.
    Nếu data = None: đọc dữ liệu.
    Nếu data != None: ghi dữ liệu (cập nhật).
    """
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{CONFIG['FILE_DATA']}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    for attempt in range(retries):
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if data is None:
                # Đọc dữ liệu
                if res.status_code == 200:
                    content = base64.b64decode(res.json()['content']).decode('utf-8')
                    return safe_load_json(content)
                elif res.status_code == 404:
                    # File chưa tồn tại, tạo mới
                    default_data = {"users": {CONFIG["CREATOR"]: "nexus os gateway"}, 
                                    "codes": ["PHAT2026"], 
                                    "pro_users": [], 
                                    "chats": [], 
                                    "files": {}}
                    # Ghi ngay lập tức
                    sync_io(default_data, retries=1)
                    return default_data
                else:
                    st.error(f"Lỗi đọc GitHub: {res.status_code}")
                    return None
            else:
                # Ghi dữ liệu
                if res.status_code in (200, 404):
                    sha = res.json().get("sha") if res.status_code == 200 else None
                    content = base64.b64encode(json.dumps(data, ensure_ascii=False).encode('utf-8')).decode('utf-8')
                    put_res = requests.put(url, headers=headers, 
                                           json={"message": "Nexus Sync", "content": content, "sha": sha},
                                           timeout=10)
                    if put_res.status_code in (200, 201):
                        return data
                    else:
                        # Conflict hoặc lỗi khác
                        if put_res.status_code == 409 and attempt < retries - 1:
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
                st.error(f"Lỗi kết nối GitHub: {str(e)}")
                return None
    return None

# --- [3] STYLE GIAO DIỆN (BẢO TRÌ BLUE BANNER) ---
st.markdown("""
<style>
.stApp { background-color: #f0f2f6; }
.ai-banner { 
    background-color: #0047AB; color: white !important; padding: 15px; 
    border-radius: 8px; font-weight: 600; margin: 10px 0;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1); 
}
.stButton>button { width: 100%; border-radius: 5px; font-weight: bold; transition: 0.2s; }
.stButton>button:hover { transform: scale(1.02); }
[data-testid="stHeader"] { visibility: hidden; }
.guest-badge {
    background-color: #ffcc00; color: #000; padding: 2px 8px; border-radius: 20px;
    font-size: 0.8rem; font-weight: bold; display: inline-block;
}
</style>
""", unsafe_allow_html=True)

# --- [4] KHỞI TẠO SESSION STATE VỚI CACHE ---
@st.cache_data(ttl=60)  # Cache 1 phút để giảm tải GitHub
def load_db():
    """Load dữ liệu từ GitHub, có cache."""
    return sync_io()

def init_session():
    """Khởi tạo các biến session state."""
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
        st.session_state.temp_chat = {"msgs": []}  # Lưu tạm cho guest

init_session()
fp = get_device_fp()
is_pro = (st.session_state.user in st.session_state.db.get("pro_users", []))

# --- [5] ĐIỀU HƯỚNG ---
def go_to(page):
    st.session_state.page = page
    st.rerun()

# --- [6] MÀN HÌNH ĐĂNG NHẬP (CÓ GUEST) ---
if st.session_state.page == "AUTH":
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.title("🔐 NEXUS LOGIN")
        u = st.text_input("Tài khoản")
        p = st.text_input("Mật khẩu", type="password")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("ĐĂNG NHẬP", use_container_width=True):
                if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
                    st.session_state.user = u
                    st.session_state.guest_mode = False
                    go_to("DASHBOARD")
                else:
                    st.error("Sai thông tin!")
        if CONFIG["GUEST_ENABLED"]:
            with col2:
                if st.button("👤 DÙNG THỬ (GUEST)", use_container_width=True):
                    st.session_state.user = "guest"
                    st.session_state.guest_mode = True
                    go_to("DASHBOARD")
        st.caption("💡 Guest: xem demo, không lưu dữ liệu vĩnh viễn.")

# --- [7] TRUNG TÂM ĐIỀU KHIỂN ---
elif st.session_state.page == "DASHBOARD":
    st.title(f"🚀 Xin chào, {st.session_state.user}")
    if st.session_state.guest_mode:
        st.markdown('<span class="guest-badge">👤 CHẾ ĐỘ KHÁCH (Demo)</span>', unsafe_allow_html=True)
        st.info("Bạn đang dùng thử. Dữ liệu sẽ không được lưu khi thoát.")
    else:
        st.write(f"Cấp độ: {'💎 PRO' if is_pro else '🆓 Miễn phí'}")
    st.divider()
    
    c1, c2, c3 = st.columns(3)
    if c1.button("🧠 TRÒ CHUYỆN AI"): go_to("AI")
    if c2.button("☁️ LƯU TRỮ CLOUD"): go_to("CLOUD")
    if c3.button("⚙️ CÀI ĐẶT & VIP"): go_to("SETTINGS")
    
    if st.session_state.user == CONFIG["CREATOR"]:
        if st.button("🛠️ QUẢN TRỊ VIÊN"): go_to("ADMIN")
    
    if st.button("🚪 Đăng xuất"):
        st.session_state.user = None
        st.session_state.guest_mode = False
        st.session_state.temp_chat = {"msgs": []}
        go_to("AUTH")

# --- [8] TRÒ CHUYỆN AI (CẢI TIẾN) ---
elif st.session_state.page == "AI":
    if st.button("🔙 QUAY LẠI"): go_to("DASHBOARD")
    st.header("🧠 NEXUS AI")
    
    # Quản lý danh sách chat (cho user thường)
    if not st.session_state.guest_mode:
        with st.sidebar:
            if st.button("➕ Hội thoại mới"): 
                st.session_state.chat_id = None
                st.rerun()
            st.write("---")
            for i, c in enumerate(st.session_state.db["chats"]):
                if c["owner"] == st.session_state.user:
                    col_t, col_d = st.columns([4, 1])
                    if col_t.button(f"💬 {c['name']}", key=f"t_{i}"):
                        st.session_state.chat_id = i
                        st.rerun()
                    if col_d.button("🗑️", key=f"d_{i}"):
                        st.session_state.db["chats"].pop(i)
                        if st.session_state.chat_id == i:
                            st.session_state.chat_id = None
                        sync_io(st.session_state.db)
                        st.rerun()
    else:
        st.sidebar.info("👤 Guest: không lưu lịch sử. Các hội thoại sẽ mất khi thoát.")
    
    # Xử lý nội dung chat
    if st.session_state.guest_mode:
        # Guest mode: dùng session_state.temp_chat
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
        
        # Toggle chế độ tạm thời (xóa sau 24h) - giữ nguyên
        temp_mode = st.toggle("Chế độ tạm thời (Xóa sau 24h)", value=chat.get("temp", False))
        chat["temp"] = temp_mode
    
    # Hiển thị lịch sử tin nhắn
    for m in chat["msgs"]:
        if m["role"] == "user":
            with st.chat_message("user"):
                st.write(m["content"])
        else:
            st.markdown(f'<div class="ai-banner">{m["content"]}</div>', unsafe_allow_html=True)
    
    # Input và gọi AI
    if p := st.chat_input("Nhập câu hỏi..."):
        # Thêm tin nhắn user
        chat["msgs"].append({"role": "user", "content": p})
        # Gọi AI với context 5 tin nhắn gần nhất (có thể tùy chỉnh)
        client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
        try:
            # Lấy context tối đa 5 tin nhắn (hoặc toàn bộ nếu là pro?)
            context = chat["msgs"][-5:] if not is_pro else chat["msgs"][-10:]  # Pro được context dài hơn
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
        
        # Đặt tên tự động (chỉ cho user thường, khi chưa có tên hoặc tên mặc định)
        if not st.session_state.guest_mode and (chat["name"] == "Hội thoại mới" or len(chat["msgs"]) == (10 if is_pro else 4)):
            try:
                # Dùng model nhỏ để tóm tắt
                client_small = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
                n_res = client_small.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": f"Tóm tắt nội dung chính của câu hỏi sau thành tối đa 5 từ: {p}"}]
                )
                new_name = n_res.choices[0].message.content.strip('".')
                if new_name:
                    chat["name"] = new_name[:30]  # giới hạn độ dài
            except:
                pass  # giữ nguyên tên cũ
        
        # Lưu lại (nếu không phải guest)
        if not st.session_state.guest_mode:
            sync_io(st.session_state.db)
        st.rerun()

# --- [9] LƯU TRỮ CLOUD (CÓ TẢI XUỐNG, CÓ PROGRESS) ---
elif st.session_state.page == "CLOUD":
    if st.button("🔙 QUAY LẠI"): go_to("DASHBOARD")
    st.header("☁️ NEXUS CLOUD")
    
    if st.session_state.guest_mode:
        st.warning("Guest không thể sử dụng lưu trữ đám mây. Đăng nhập để lưu file.")
    else:
        files = {k:v for k,v in st.session_state.db["files"].items() if v.get("owner") == st.session_state.user}
        
        up = st.file_uploader("Chọn tệp")
        if up and st.button("TẢI LÊN"):
            with st.spinner("Đang tải lên..."):
                # Mô phỏng progress bar (vì base64 nhanh)
                progress_bar = st.progress(0)
                for i in range(100):
                    time.sleep(0.01)
                    progress_bar.progress(i + 1)
                st.session_state.db["files"][up.name] = {
                    "data": base64.b64encode(up.getvalue()).decode(),
                    "owner": st.session_state.user,
                    "size": len(up.getvalue())
                }
                sync_io(st.session_state.db)
                st.success("Đã tải lên!")
                st.rerun()
        
        st.write("---")
        for name, info in files.items():
            c1, c2, c3 = st.columns([3, 1, 1])
            size_kb = info.get("size", 0) / 1024
            c1.write(f"📄 {name} ({size_kb:.1f} KB)")
            # NÚT TẢI XUỐNG
            c2.markdown(f'<a href="data:application/octet-stream;base64,{info["data"]}" download="{name}" style="text-decoration:none;">📥 Tải về</a>', unsafe_allow_html=True)
            if c3.button("🗑️ Xóa", key=name):
                del st.session_state.db["files"][name]
                sync_io(st.session_state.db)
                st.rerun()

# --- [10] CÀI ĐẶT & ADMIN (GIỮ NGUYÊN) ---
elif st.session_state.page == "SETTINGS":
    if st.button("🔙 QUAY LẠI"): go_to("DASHBOARD")
    st.header("⚙️ CÀI ĐẶT")
    if st.session_state.guest_mode:
        st.info("Guest không thể kích hoạt VIP. Đăng nhập để nâng cấp.")
    else:
        code = st.text_input("Nhập mã kích hoạt Pro").upper()
        if st.button("KÍCH HOẠT"):
            if code in st.session_state.db["codes"]:
                st.session_state.db["pro_users"].append(st.session_state.user)
                st.session_state.db["codes"].remove(code)
                sync_io(st.session_state.db)
                st.balloons()
                st.success("Chúc mừng! Bạn đã là thành viên Pro.")
                st.rerun()
            else:
                st.error("Mã không hợp lệ hoặc đã được sử dụng.")

elif st.session_state.page == "ADMIN":
    if st.session_state.user != CONFIG["CREATOR"]:
        st.error("Bạn không có quyền truy cập.")
        go_to("DASHBOARD")
    else:
        if st.button("🔙 QUAY LẠI"): go_to("DASHBOARD")
        st.header("🛠️ ADMIN")
        new_code = st.text_input("Tạo mã Pro mới").upper()
        if st.button("TẠO MÃ"):
            if new_code:
                st.session_state.db["codes"].append(new_code)
                sync_io(st.session_state.db)
                st.success(f"Đã tạo mã {new_code}!")
                st.rerun()
        st.subheader("Danh sách Pro Users")
        for u in st.session_state.db["pro_users"]:
            st.write(f"- {u}")
