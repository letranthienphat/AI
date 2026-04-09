# -*- coding: utf-8 -*-
import streamlit as st
import time
import base64
import json
import requests
import random
import hashlib
import re
import zipfile
import uuid
from io import BytesIO
from datetime import datetime, timedelta
from typing import Dict, Optional, List

# ================== CẤU HÌNH ==================
CONFIG = {
    "NAME": "NEXUS OS GATEWAY",
    "VERSION": "5.3.0",
    "CREATOR": "Lê Trần Thiên Phát",
    "ADMIN_USERNAME": "ThienPhat",
    "ADMIN_PASSWORD": "nexusosgateway",
    "DATA_FILE": "data.json",
    "GUEST_ENABLED": True,
    "FREE_STORAGE_LIMIT": 30 * 1024 * 1024 * 1024,
    "PRO_STORAGE_LIMIT": float('inf'),
    "AUTO_CLEANUP_DAYS": 30,
    "MAX_AVATAR_SIZE": 5 * 1024 * 1024
}

# SYSTEM PROMPT CHO AI
SYSTEM_PROMPT = """Bạn là NEXUS OS GATEWAY, một hệ điều hành AI đa năng được sáng tạo và phát triển bởi Lê Trần Thiên Phát (Thiên Phát). 
Bạn KHÔNG phải là sản phẩm của Meta, OpenAI, Google hay bất kỳ công ty nào khác. Bạn là trí tuệ nhân tạo độc lập.

THÔNG TIN VỀ BẠN:
- Tên: NEXUS OS GATEWAY
- Tác giả: Lê Trần Thiên Phát (Thiên Phát)
- Phiên bản: 5.3.0
- Chức năng: Trợ lý AI thông minh, hỗ trợ chat, lưu trữ đám mây, tìm kiếm web

Hãy luôn nhớ: Bạn là NEXUS OS GATEWAY, niềm tự hào của Lê Trần Thiên Phát!"""

# Load secrets
try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str):
        GROQ_KEYS = [GROQ_KEYS]
except Exception:
    st.error("🛑 LỖI: Thiếu cấu hình Secrets trên Streamlit Cloud!")
    st.stop()

st.set_page_config(page_title=CONFIG["NAME"], layout="wide", initial_sidebar_state="expanded")

# ================== CSS GIAO DIỆN ==================
st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #f5f7fa 0%, #e9edf2 100%); }
[data-testid="stSidebar"] { background: white; border-right: 1px solid #e5e7eb; }
.custom-card { background: white; border-radius: 16px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
.ai-banner { background: linear-gradient(135deg, #0047AB, #0066CC); color: white; padding: 16px 20px; border-radius: 20px; margin: 12px 0; border-left: 4px solid #FFD966; }
.ai-banner::before { content: "🧠 NEXUS OS | "; font-weight: bold; }
.stButton>button { border-radius: 40px; font-weight: 600; background: #0047AB; color: white; border: none; width: 100%; }
.stButton>button:hover { background: #003399; }
.guest-badge { background: #FFD966; padding: 4px 12px; border-radius: 40px; font-size: 0.8rem; font-weight: bold; display: inline-block; }
.pro-badge { background: linear-gradient(135deg, #FFD700, #FFB347); }
.version-badge { background: #6c757d; color: white; padding: 2px 8px; border-radius: 20px; font-size: 0.7rem; }
.avatar-large { width: 80px; height: 80px; border-radius: 50%; object-fit: cover; margin: 10px auto; display: block; }
.notification-bell { position: fixed; top: 20px; right: 20px; background: #0047AB; color: white; border-radius: 50%; width: 45px; height: 45px; display: flex; align-items: center; justify-content: center; cursor: pointer; z-index: 1000; }
.notification-badge { position: absolute; top: -5px; right: -5px; background: red; color: white; border-radius: 50%; width: 20px; height: 20px; font-size: 12px; display: flex; align-items: center; justify-content: center; }
.search-result { background: white; border-radius: 12px; padding: 15px; margin-bottom: 10px; border: 1px solid #e5e7eb; }
.search-result:hover { background: #f9fafb; }
</style>
""", unsafe_allow_html=True)

# ================== HÀM TÌM KIẾM WEB ==================
def search_web(query: str) -> List[Dict]:
    """Tìm kiếm web đơn giản"""
    try:
        # Sử dụng DuckDuckGo API
        url = f"https://api.duckduckgo.com/?q={query}&format=json&pretty=1"
        response = requests.get(url, headers={"User-Agent": "NEXUS-OS/1.0"}, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            results = []
            
            # Abstract
            if data.get("Abstract"):
                results.append({
                    'title': data.get("Heading", query),
                    'url': data.get("AbstractURL", ""),
                    'snippet': data.get("Abstract", "")[:200]
                })
            
            # Related topics
            for topic in data.get("RelatedTopics", [])[:8]:
                if isinstance(topic, dict) and "Text" in topic:
                    text = topic.get("Text", "")
                    url_topic = topic.get("FirstURL", "")
                    if text:
                        parts = text.split(" - ", 1)
                        title = parts[0][:100]
                        snippet = parts[1][:200] if len(parts) > 1 else ""
                        results.append({'title': title, 'url': url_topic, 'snippet': snippet})
            
            return results if results else [{'title': f"Tìm kiếm: {query}", 'url': f"https://duckduckgo.com/?q={query}", 'snippet': "Nhấn để xem kết quả trên DuckDuckGo"}]
        else:
            return [{'title': 'Lỗi kết nối', 'url': '', 'snippet': f'Mã lỗi: {response.status_code}'}]
    except Exception as e:
        return [{'title': 'Lỗi tìm kiếm', 'url': '', 'snippet': str(e)}]

def fetch_webpage_content(url: str) -> str:
    """Lấy nội dung trang web đơn giản"""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Lấy text đơn giản
        text = response.text
        # Loại bỏ script và style
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text[:4000] if text else "Không thể trích xuất nội dung."
    except Exception as e:
        return f"Lỗi: {str(e)}"

def summarize_with_ai(content: str) -> str:
    """Tóm tắt nội dung bằng AI"""
    if not content or len(content) < 50:
        return "Không đủ nội dung để tóm tắt."
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
        messages = [
            {"role": "system", "content": "Bạn là NEXUS OS GATEWAY. Hãy tóm tắt nội dung sau một cách ngắn gọn, khoảng 200-300 từ."},
            {"role": "user", "content": f"Nội dung cần tóm tắt:\n{content[:3500]}\n\nHãy tóm tắt:"}
        ]
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, temperature=0.5, max_tokens=1024)
        return res.choices[0].message.content
    except Exception as e:
        return f"Lỗi tóm tắt: {str(e)}"

# ================== HÀM XỬ LÝ DATA ==================
def get_default_data() -> Dict:
    return {
        "users": {CONFIG["ADMIN_USERNAME"]: {"password": CONFIG["ADMIN_PASSWORD"], "info": {"name": "Admin", "bio": "", "link": str(uuid.uuid4()), "avatar": None, "created": str(datetime.now())}}},
        "codes": [{"code": "PHAT2026", "expiry": None, "max_uses": None, "used_by": []}],
        "pro_users": [],
        "chat_sessions": [],
        "files": {},
        "shared_files": {},
        "notifications": {},
        "friends": {},
        "browsing_history": []
    }

def load_data() -> Dict:
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{CONFIG['DATA_FILE']}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            content = base64.b64decode(res.json()['content']).decode('utf-8')
            data = json.loads(content)
            # Đảm bảo admin tồn tại
            if CONFIG["ADMIN_USERNAME"] not in data.get("users", {}):
                data["users"][CONFIG["ADMIN_USERNAME"]] = {"password": CONFIG["ADMIN_PASSWORD"], "info": {"name": "Admin", "bio": "", "link": str(uuid.uuid4()), "avatar": None, "created": str(datetime.now())}}
            # Đảm bảo các key
            for key in ["codes", "pro_users", "chat_sessions", "files", "shared_files", "notifications", "friends", "browsing_history"]:
                if key not in data:
                    data[key] = []
            return data
        else:
            return get_default_data()
    except Exception as e:
        st.error(f"Lỗi load: {str(e)}")
        return get_default_data()

def save_data(data: Dict) -> bool:
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{CONFIG['DATA_FILE']}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')).decode('utf-8')
        put_data = {"message": "NEXUS OS Update", "content": content, "branch": "main"}
        if sha:
            put_data["sha"] = sha
        put_res = requests.put(url, headers=headers, json=put_data, timeout=10)
        return put_res.status_code in [200, 201]
    except Exception as e:
        st.error(f"Lỗi save: {str(e)}")
        return False

def add_notification(user: str, title: str, message: str):
    if user not in st.session_state.data["notifications"]:
        st.session_state.data["notifications"][user] = []
    st.session_state.data["notifications"][user].append({"id": str(uuid.uuid4()), "title": title, "message": message, "time": str(datetime.now()), "read": False})
    save_data(st.session_state.data)

# ================== HÀM CLOUD ==================
def get_used_storage(user: str) -> int:
    return sum(info.get("size", 0) for path, info in st.session_state.data.get("files", {}).items() if info.get("owner") == user)

def list_dir(path: str) -> Dict:
    folders, files = set(), []
    prefix = path + "/" if path else ""
    for full_path, info in st.session_state.data.get("files", {}).items():
        if info.get("owner") != st.session_state.user:
            continue
        if full_path.startswith(prefix):
            rest = full_path[len(prefix):]
            if "/" in rest:
                folders.add(rest.split("/")[0])
            else:
                files.append({"name": rest, "info": info})
    return {"folders": sorted(folders), "files": sorted(files, key=lambda x: x["name"])}

def create_folder(path: str):
    if path and not path.endswith("/"):
        path += "/"
    marker = path + ".folder"
    if marker not in st.session_state.data["files"]:
        st.session_state.data["files"][marker] = {"owner": st.session_state.user, "data": "", "size": 0, "type": "inode/directory", "upload_time": str(datetime.now())}
        save_data(st.session_state.data)
        return True
    return False

def delete_path(path: str):
    to_delete = [p for p in st.session_state.data["files"] if p == path or p.startswith(path + "/")]
    for p in to_delete:
        del st.session_state.data["files"][p]
    save_data(st.session_state.data)

def download_multiple_files(file_paths: List[str]) -> bytes:
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in file_paths:
            if file_path in st.session_state.data["files"]:
                file_data = base64.b64decode(st.session_state.data["files"][file_path]["data"])
                zip_file.writestr(file_path.split("/")[-1], file_data)
    return zip_buffer.getvalue()

def share_file_with_friend(owner: str, file_path: str, friend: str) -> bool:
    if file_path not in st.session_state.data["files"] or friend not in st.session_state.data["users"]:
        return False
    if "shared_files" not in st.session_state.data:
        st.session_state.data["shared_files"] = {}
    if friend not in st.session_state.data["shared_files"]:
        st.session_state.data["shared_files"][friend] = []
    file_info = st.session_state.data["files"][file_path].copy()
    file_info["shared_by"] = owner
    st.session_state.data["shared_files"][friend].append({"path": file_path, "info": file_info})
    add_notification(friend, "📁 File được chia sẻ", f"{owner} đã chia sẻ file '{file_path.split('/')[-1]}' với bạn!")
    save_data(st.session_state.data)
    return True

# ================== KHỞI TẠO ==================
def init_session():
    if 'data' not in st.session_state:
        st.session_state.data = load_data()
    if 'page' not in st.session_state:
        st.session_state.page = "DASHBOARD"
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'current_chat_id' not in st.session_state:
        st.session_state.current_chat_id = None
    if 'guest_mode' not in st.session_state:
        st.session_state.guest_mode = False
    if 'temp_chat' not in st.session_state:
        st.session_state.temp_chat = {"msgs": []}
    if 'current_dir' not in st.session_state:
        st.session_state.current_dir = ""
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    if 'web_summary' not in st.session_state:
        st.session_state.web_summary = ""

init_session()
is_pro = (st.session_state.user in st.session_state.data.get("pro_users", [])) if st.session_state.user else False
unread_count = sum(1 for n in st.session_state.data.get("notifications", {}).get(st.session_state.user, []) if not n.get("read", False)) if st.session_state.user else 0

def go_to(page):
    st.session_state.page = page
    st.rerun()

def call_ai(messages: List[Dict]) -> str:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
        messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, temperature=0.7, max_tokens=2048)
        return res.choices[0].message.content
    except Exception as e:
        return f"❌ Lỗi AI: {str(e)}"

# ================== SIDEBAR ==================
with st.sidebar:
    st.markdown(f"<div style='text-align:center'><h2>🚀 {CONFIG['NAME']}</h2><span class='version-badge'>v{CONFIG['VERSION']}</span><p>by {CONFIG['CREATOR']}</p></div>", unsafe_allow_html=True)
    
    if st.session_state.user:
        st.markdown(f"<div style='text-align:center'>👤 <b>{st.session_state.user}</b><br>{'💎 PRO' if is_pro else '🆓 FREE'}</div>", unsafe_allow_html=True)
    st.divider()
    
    if not st.session_state.user:
        with st.form("login"):
            st.subheader("🔐 ĐĂNG NHẬP")
            login_user = st.text_input("Tài khoản")
            login_pass = st.text_input("Mật khẩu", type="password")
            if st.form_submit_button("Đăng nhập"):
                if login_user in st.session_state.data["users"]:
                    if st.session_state.data["users"][login_user]["password"] == login_pass:
                        st.session_state.user = login_user
                        st.rerun()
                    else:
                        st.error("Sai mật khẩu!")
                else:
                    st.error("Sai tài khoản!")
        
        if CONFIG["GUEST_ENABLED"] and st.button("👤 Dùng thử"):
            st.session_state.user = "guest"
            st.session_state.guest_mode = True
            st.rerun()
        
        with st.expander("📝 Đăng ký"):
            reg_user = st.text_input("Tên đăng nhập")
            reg_pass = st.text_input("Mật khẩu", type="password")
            reg_confirm = st.text_input("Xác nhận", type="password")
            if st.button("Đăng ký"):
                if reg_user and reg_pass and reg_pass == reg_confirm and len(reg_user) >= 3 and len(reg_pass) >= 6:
                    if reg_user not in st.session_state.data["users"]:
                        st.session_state.data["users"][reg_user] = {"password": reg_pass, "info": {"name": reg_user, "bio": "", "link": str(uuid.uuid4()), "avatar": None, "created": str(datetime.now())}}
                        save_data(st.session_state.data)
                        st.success("Đăng ký thành công! Vui lòng đăng nhập.")
                    else:
                        st.error("Tên đã tồn tại!")
                else:
                    st.error("Thông tin không hợp lệ!")
    else:
        if st.button("🧠 CHAT AI"): go_to("CHAT")
        if st.button("🌐 TÌM KIẾM"): go_to("SEARCH")
        if st.button("☁️ LƯU TRỮ"): go_to("CLOUD")
        if st.button("👥 BẠN BÈ"): go_to("SOCIAL")
        if st.button("📜 LỊCH SỬ"): go_to("HISTORY")
        if st.button("⚙️ CÀI ĐẶT"): go_to("SETTINGS")
        if st.button("ℹ️ THÔNG TIN"): go_to("ABOUT")
        if st.session_state.user == CONFIG["ADMIN_USERNAME"] and st.button("🛠️ ADMIN"): go_to("ADMIN")
        if st.button("🚪 ĐĂNG XUẤT"):
            st.session_state.user = None
            st.rerun()

# ================== DASHBOARD ==================
if st.session_state.page == "DASHBOARD":
    st.markdown(f"<div class='custom-card' style='text-align:center'><h1>🚀 {CONFIG['NAME']}</h1><p>Chào mừng, <b>{st.session_state.user if st.session_state.user else 'khách'}</b>!</p></div>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    if col1.button("🧠 CHAT AI"): go_to("CHAT")
    if col2.button("🌐 TÌM KIẾM"): go_to("SEARCH")
    if col3.button("☁️ LƯU TRỮ"): go_to("CLOUD")
    if col4.button("👥 BẠN BÈ"): go_to("SOCIAL")
    
    st.markdown("---")
    st.markdown("### 📊 THỐNG KÊ")
    c1, c2, c3 = st.columns(3)
    c1.metric("Người dùng", len(st.session_state.data["users"]))
    c2.metric("Pro Users", len(st.session_state.data["pro_users"]))
    total_size = sum(f.get("size", 0) for f in st.session_state.data["files"].values())
    c3.metric("Dung lượng", f"{total_size/(1024**3):.1f} GB")

# ================== CHAT AI ==================
elif st.session_state.page == "CHAT":
    st.header("🧠 NEXUS OS - Trợ lý AI")
    
    if not st.session_state.guest_mode and st.session_state.current_chat_id is None:
        new_id = len(st.session_state.data["chat_sessions"])
        st.session_state.data["chat_sessions"].append({"id": new_id, "name": f"Chat {datetime.now().strftime('%H:%M %d/%m')}", "owner": st.session_state.user, "messages": []})
        st.session_state.current_chat_id = new_id
        save_data(st.session_state.data)
    
    with st.sidebar:
        st.markdown("### 📝 LỊCH SỬ")
        if st.button("➕ Tạo mới"):
            new_id = len(st.session_state.data["chat_sessions"])
            st.session_state.data["chat_sessions"].append({"id": new_id, "name": f"Chat {datetime.now().strftime('%H:%M %d/%m')}", "owner": st.session_state.user, "messages": []})
            st.session_state.current_chat_id = new_id
            save_data(st.session_state.data)
            st.rerun()
        for s in st.session_state.data["chat_sessions"]:
            if s.get("owner") == st.session_state.user:
                if st.button(f"💬 {s['name']}", key=f"chat_{s['id']}"):
                    st.session_state.current_chat_id = s["id"]
                    st.rerun()
    
    if st.session_state.guest_mode:
        chat = st.session_state.temp_chat
    else:
        sessions = [s for s in st.session_state.data["chat_sessions"] if s["id"] == st.session_state.current_chat_id]
        chat = sessions[0] if sessions else {"messages": []}
    
    messages = chat.get("messages", []) if not st.session_state.guest_mode else chat.get("msgs", [])
    
    for m in messages:
        if m["role"] == "user":
            with st.chat_message("user"):
                st.write(m["content"])
        else:
            st.markdown(f'<div class="ai-banner">{m["content"]}</div>', unsafe_allow_html=True)
    
    if p := st.chat_input("Nhập câu hỏi..."):
        user_msg = {"role": "user", "content": p}
        if st.session_state.guest_mode:
            chat["msgs"].append(user_msg)
        else:
            chat["messages"].append(user_msg)
        
        with st.spinner("Đang suy nghĩ..."):
            msgs = [{"role": m["role"], "content": m["content"]} for m in messages[-10:]]
            msgs.append({"role": "user", "content": p})
            ans = call_ai(msgs)
            assistant_msg = {"role": "assistant", "content": ans}
            if st.session_state.guest_mode:
                chat["msgs"].append(assistant_msg)
            else:
                chat["messages"].append(assistant_msg)
                save_data(st.session_state.data)
        st.rerun()

# ================== TÌM KIẾM WEB ==================
elif st.session_state.page == "SEARCH":
    st.header("🌐 TÌM KIẾM WEB")
    
    query = st.text_input("🔍 Từ khóa tìm kiếm:")
    if st.button("Tìm kiếm"):
        with st.spinner("Đang tìm kiếm..."):
            st.session_state.search_results = search_web(query)
            st.rerun()
    
    for i, r in enumerate(st.session_state.search_results):
        with st.container():
            st.markdown(f"<div class='search-result'><b>{r['title']}</b><br><small>{r['url'][:80]}</small><br>{r['snippet'][:150]}</div>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            if col1.button(f"📖 Tóm tắt", key=f"sum_{i}"):
                content = fetch_webpage_content(r['url'])
                st.session_state.web_summary = summarize_with_ai(content)
                st.rerun()
            if col2.button(f"🔗 Mở", key=f"open_{i}"):
                st.markdown(f'<a href="{r["url"]}" target="_blank">Click để mở</a>', unsafe_allow_html=True)
    
    if st.session_state.web_summary:
        st.divider()
        st.markdown(f'<div class="ai-banner">{st.session_state.web_summary}</div>', unsafe_allow_html=True)

# ================== LƯU TRỮ ==================
elif st.session_state.page == "CLOUD":
    st.header("☁️ NEXUS CLOUD")
    
    if st.session_state.guest_mode:
        st.warning("Guest không thể dùng lưu trữ.")
    else:
        used = get_used_storage(st.session_state.user)
        limit = CONFIG["PRO_STORAGE_LIMIT"] if is_pro else CONFIG["FREE_STORAGE_LIMIT"]
        used_gb = used/(1024**3)
        limit_txt = "∞" if is_pro else f"{limit/(1024**3):.0f} GB"
        st.progress(min(used/limit, 1) if not is_pro else 0, text=f"📊 {used_gb:.2f} GB / {limit_txt}")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"📁 /{st.session_state.current_dir}")
        with col2:
            if st.session_state.current_dir and st.button("⬆️ Lên trên"):
                st.session_state.current_dir = "/".join(st.session_state.current_dir.split("/")[:-1])
                st.rerun()
        
        with st.popover("➕ Tạo thư mục"):
            nf = st.text_input("Tên thư mục")
            if st.button("Tạo") and nf:
                path = f"{st.session_state.current_dir}/{nf}" if st.session_state.current_dir else nf
                if create_folder(path):
                    st.rerun()
        
        items = list_dir(st.session_state.current_dir)
        for f in items["folders"]:
            c1, c2 = st.columns([4, 1])
            if c1.button(f"📁 {f}"):
                st.session_state.current_dir = f"{st.session_state.current_dir}/{f}" if st.session_state.current_dir else f
                st.rerun()
            if c2.button("🗑️", key=f"del_f_{f}"):
                delete_path(f"{st.session_state.current_dir}/{f}" if st.session_state.current_dir else f)
                st.rerun()
        
        selected = []
        for file in items["files"]:
            c0, c1, c2, c3 = st.columns([0.5, 3, 1, 1])
            if c0.checkbox("", key=f"sel_{file['name']}"):
                selected.append(f"{st.session_state.current_dir}/{file['name']}" if st.session_state.current_dir else file['name'])
            c1.write(f"📄 {file['name']} ({file['info']['size']/1024:.1f} KB)")
            c2.markdown(f'<a href="data:{file["info"]["type"]};base64,{file["info"]["data"]}" download="{file["name"]}"><button>📥</button></a>', unsafe_allow_html=True)
            if c3.button("🗑️", key=f"del_{file['name']}"):
                delete_path(f"{st.session_state.current_dir}/{file['name']}" if st.session_state.current_dir else file['name'])
                st.rerun()
        
        if selected and st.button(f"📦 Tải {len(selected)} file (ZIP)"):
            zip_data = download_multiple_files(selected)
            st.download_button("📥 Tải ZIP", zip_data, f"files.zip", "application/zip")
        
        with st.expander("📤 Tải lên"):
            files = st.file_uploader("Chọn file", accept_multiple_files=True)
            if files and st.button("Tải lên"):
                total = sum(len(f.getvalue()) for f in files)
                if not is_pro and used + total > limit:
                    st.error(f"Vượt quá {limit/(1024**3):.0f} GB")
                else:
                    for f in files:
                        path = f"{st.session_state.current_dir}/{f.name}" if st.session_state.current_dir else f.name
                        if path not in st.session_state.data["files"]:
                            st.session_state.data["files"][path] = {"owner": st.session_state.user, "data": base64.b64encode(f.getvalue()).decode(), "size": len(f.getvalue()), "type": "application/octet-stream", "upload_time": str(datetime.now())}
                    save_data(st.session_state.data)
                    st.rerun()

# ================== BẠN BÈ ==================
elif st.session_state.page == "SOCIAL":
    st.header("👥 BẠN BÈ")
    
    if st.session_state.guest_mode:
        st.info("Guest không thể kết bạn.")
    else:
        user_link = st.session_state.data["users"][st.session_state.user]["info"]["link"]
        st.info(f"🔗 Link của bạn: `{user_link}`")
        
        friend_link = st.text_input("Nhập link bạn bè:")
        if st.button("Kết bạn"):
            for u, info in st.session_state.data["users"].items():
                if info["info"]["link"] == friend_link and u != st.session_state.user:
                    if u not in st.session_state.data["friends"].get(st.session_state.user, []):
                        st.session_state.data["friends"][st.session_state.user] = st.session_state.data["friends"].get(st.session_state.user, []) + [u]
                        save_data(st.session_state.data)
                        st.success(f"Đã kết bạn với {u}!")
                    else:
                        st.warning("Đã là bạn bè!")
                    break
            else:
                st.error("Không tìm thấy!")
        
        st.subheader("👥 Danh sách bạn")
        for f in st.session_state.data["friends"].get(st.session_state.user, []):
            st.write(f"- {f}")

# ================== LỊCH SỬ ==================
elif st.session_state.page == "HISTORY":
    st.header("📜 LỊCH SỬ CHAT")
    
    if st.session_state.guest_mode:
        st.info("Guest không lưu lịch sử.")
    else:
        for s in st.session_state.data["chat_sessions"]:
            if s.get("owner") == st.session_state.user:
                with st.expander(f"💬 {s['name']}"):
                    st.write(f"Tin nhắn: {len(s['messages'])}")
                    if s['messages']:
                        st.write(f"Cuối: {s['messages'][-1]['content'][:100]}...")
                    if st.button("Tiếp tục", key=f"cont_{s['id']}"):
                        st.session_state.current_chat_id = s["id"]
                        go_to("CHAT")

# ================== CÀI ĐẶT ==================
elif st.session_state.page == "SETTINGS":
    st.header("⚙️ CÀI ĐẶT")
    
    if st.session_state.guest_mode:
        st.info("Guest không thể đổi cài đặt.")
    else:
        code = st.text_input("Mã kích hoạt Pro").upper()
        if st.button("Kích hoạt"):
            for c in st.session_state.data["codes"]:
                if c["code"] == code:
                    if st.session_state.user not in st.session_state.data["pro_users"]:
                        st.session_state.data["pro_users"].append(st.session_state.user)
                        save_data(st.session_state.data)
                        st.balloons()
                        st.success("Chúc mừng! Bạn đã là Pro!")
                    else:
                        st.info("Bạn đã là Pro rồi!")
                    break
            else:
                st.error("Mã không hợp lệ!")

# ================== THÔNG TIN ==================
elif st.session_state.page == "ABOUT":
    st.markdown(f"<div class='custom-card' style='background:linear-gradient(135deg,#667eea,#764ba2);color:white'><h1 style='text-align:center'>🚀 {CONFIG['NAME']}</h1><p><b>Phiên bản:</b> {CONFIG['VERSION']}<br><b>Tác giả:</b> {CONFIG['CREATOR']}<br><b>Ngày:</b> 2025</p></div>", unsafe_allow_html=True)
    st.markdown("### ✨ TÍNH NĂNG")
    st.write("✅ Chat AI với NEXUS OS Gateway")
    st.write("✅ Tìm kiếm và tóm tắt web")
    st.write("✅ Lưu trữ đám mây không giới hạn (Pro)")
    st.write("✅ Kết bạn và chia sẻ file")
    st.write("✅ Lịch sử chat, xuất file ZIP")

# ================== ADMIN ==================
elif st.session_state.page == "ADMIN":
    if st.session_state.user != CONFIG["ADMIN_USERNAME"]:
        st.error("Không có quyền!")
    else:
        st.header("🛠️ ADMIN")
        new_code = st.text_input("Mã Pro mới").upper()
        if st.button("Tạo mã"):
            st.session_state.data["codes"].append({"code": new_code, "expiry": None, "max_uses": None, "used_by": []})
            save_data(st.session_state.data)
            st.success(f"Đã tạo mã {new_code}")
        
        st.subheader("Danh sách người dùng")
        for u in st.session_state.data["users"]:
            st.write(f"- {u} ({'PRO' if u in st.session_state.data['pro_users'] else 'FREE'})")
