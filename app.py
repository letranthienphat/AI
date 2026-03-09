# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time
import base64
import json
import requests

# --- 1. THÔNG TIN HỆ THỐNG ---
CREATOR_NAME = "Lê Trần Thiên Phát"
VERSION = "V4100 - SECURE WIDE-SCREEN"
FILE_DATA = "data.json"

try:
    GITHUB_TOKEN = st.secrets["GH_TOKEN"]
    REPO_NAME = st.secrets["GH_REPO"]
    GROQ_API_KEYS = st.secrets["GROQ_KEYS"]
except:
    st.error("Thiếu cấu hình Secrets!")
    st.stop()

st.set_page_config(page_title=f"NEXUS OS | {CREATOR_NAME}", layout="wide")

# --- 2. ĐỒNG BỘ GITHUB ---
def load_github():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return json.loads(base64.b64decode(res.json()['content']).decode('utf-8'))
    except: pass
    return {}

def save_github():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    data = {
        "users": st.session_state.users,
        "theme": st.session_state.theme,
        "chat_library": st.session_state.chat_library,
        "agreed_users": st.session_state.get('agreed_users', [])
    }
    try:
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, indent=4).encode()).decode()
        payload = {"message": f"Nexus Update {time.strftime('%H:%M:%S')}", "content": content, "sha": sha} if sha else {"message": "Init", "content": content}
        requests.put(url, headers=headers, json=payload)
    except: pass

# --- 3. KHỞI TẠO BIẾN ---
if 'initialized' not in st.session_state:
    db = load_github()
    st.session_state.users = db.get("users", {"admin": "123"})
    
    # Theme và Cấu hình bảo mật nằm chung để dễ đồng bộ
    default_theme = {
        "primary_color": "#00f2ff", 
        "bg_url": "", 
        "use_glass": True,
        "max_fails": 5,        # Giới hạn nhập sai mặc định
        "lockout_time": 30     # Thời gian khóa mặc định (giây)
    }
    st.session_state.theme = db.get("theme", default_theme)
    # Cập nhật các key bị thiếu nếu nạp từ data cũ
    for k, v in default_theme.items():
        if k not in st.session_state.theme:
            st.session_state.theme[k] = v
            
    st.session_state.chat_library = db.get("chat_library", {})
    st.session_state.agreed_users = db.get("agreed_users", [])
    st.session_state.stage = "AUTH"
    st.session_state.auth_status = None
    st.session_state.current_chat = None
    
    # Bộ nhớ tạm để theo dõi nhập sai (không lưu lên Github)
    st.session_state.login_track = {} 
    st.session_state.initialized = True

# --- 4. ENGINE GIAO DIỆN (WIDESCREEN OPTIMIZED) ---
def apply_ui():
    t = st.session_state.theme
    bg_style = f"background: url('{t['bg_url']}') no-repeat center center fixed; background-size: cover;" if t['bg_url'] else "background-color: #0e1117;"
    
    glass_bg = "rgba(255, 255, 255, 0.45)" if t.get('use_glass', True) else "transparent"
    glass_blur = "blur(12px)" if t.get('use_glass', True) else "none"
    glass_border = "1px solid rgba(255, 255, 255, 0.4)" if t.get('use_glass', True) else "none"

    st.markdown(f"""
    <style>
    .stApp {{ {bg_style} }}
    
    .main-title {{
        color: {t['primary_color']} !important;
        text-align: center; font-size: 3rem; font-weight: 900;
        text-shadow: 0px 0px 15px {t['primary_color']}; margin-bottom: 25px;
        text-transform: uppercase;
    }}

    /* Ép chữ đen trên nền sương mờ */
    .stApp p, .stApp span, .stApp label, .stMarkdown p, .stMarkdown li, h1, h2, h3 {{
        color: #000000 !important; font-weight: 600 !important;
    }}

    .glass-card, div[data-testid="stChatMessage"], [data-testid="stSidebar"], .stTabs {{
        background: {glass_bg} !important;
        backdrop-filter: {glass_blur} !important;
        border: {glass_border} !important;
        border-radius: 15px; padding: 25px;
    }}

    div.stButton > button {{
        width: 100%; border-radius: 12px; font-weight: 800; padding: 10px;
        border: 2px solid {t['primary_color']} !important;
        background: rgba(255, 255, 255, 0.8) !important; color: #000000 !important;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1); transition: 0.3s;
    }}
    div.stButton > button:hover {{ background: {t['primary_color']} !important; color: #000000 !important; }}

    [data-testid="stSidebarContent"] * {{ color: #000000 !important; }}
    
    /* Tận dụng chiều ngang cho input */
    input, textarea {{
        background: rgba(255, 255, 255, 0.9) !important;
        color: #000000 !important; border: 2px solid #000000 !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. LÕI AI ---
def call_ai(messages):
    client = OpenAI(api_key=GROQ_API_KEYS[0], base_url="https://api.groq.com/openai/v1")
    return client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": f"Trợ lý AI Nexus OS của {CREATOR_NAME}"}] + messages,
        stream=True
    )

# --- 6. CÁC MÀN HÌNH CHỨC NĂNG ---

def screen_auth():
    apply_ui()
    st.markdown('<h1 class="main-title">🛡️ NEXUS OS GATEWAY</h1>', unsafe_allow_html=True)
    
    # Chia 3 cột để ôm form vào giữa màn hình rộng
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        t1, t2, t3 = st.tabs(["🔑 LOGIN", "📝 REGISTER", "👤 GUEST"])
        
        with t1:
            u = st.text_input("Tên đăng nhập", key="l_u")
            p = st.text_input("Mật khẩu", type="password", key="l_p")
            
            if st.button("TRUY CẬP HỆ THỐNG", use_container_width=True):
                if u == "":
                    st.warning("Vui lòng nhập tên tài khoản.")
                else:
                    # Logic khóa tài khoản (Rate Limit)
                    track = st.session_state.login_track.setdefault(u, {"fails": 0, "locked_until": 0})
                    current_time = time.time()
                    max_fails = st.session_state.theme['max_fails']
                    lock_time = st.session_state.theme['lockout_time']

                    if current_time < track["locked_until"]:
                        remaining = int(track["locked_until"] - current_time)
                        st.error(f"🔒 Tài khoản đang bị khóa! Vui lòng thử lại sau **{remaining} giây**.")
                    else:
                        if u in st.session_state.users:
                            if st.session_state.users[u] == p:
                                track["fails"] = 0 # Reset nếu đúng
                                st.session_state.auth_status = u
                                st.session_state.stage = "MENU" if u in st.session_state.agreed_users else "TERMS"
                                st.rerun()
                            else:
                                track["fails"] += 1
                                if track["fails"] >= max_fails:
                                    track["locked_until"] = current_time + lock_time
                                    st.error(f"⛔ Bạn đã nhập sai {max_fails} lần. Tài khoản tạm khóa trong {lock_time} giây!")
                                else:
                                    st.error(f"❌ Sai mật khẩu! Bạn còn {max_fails - track['fails']} lần thử.")
                        else:
                            st.error("❌ Tài khoản không tồn tại!")
                            
        with t2:
            nu = st.text_input("Tên tài khoản mới", key="r_u")
            p1 = st.text_input("Mật khẩu", type="password", key="r_p1")
            p2 = st.text_input("Xác nhận lại", type="password", key="r_p2")
            if st.button("TẠO TÀI KHOẢN", use_container_width=True):
                if p1 == p2 and nu != "":
                    st.session_state.users[nu] = p1
                    save_github(); st.success("Đăng ký thành công! Hãy sang tab Login.")
                else: st.error("Lỗi: Mật khẩu không khớp hoặc để trống!")

        with t3:
            st.info("Chế độ khách: Cho phép trải nghiệm nhanh AI. Dữ liệu chat sẽ không được lưu.")
            if st.button("TIẾP TỤC VỚI QUYỀN KHÁCH", use_container_width=True):
                st.session_state.auth_status = "Guest"; st.session_state.stage = "TERMS"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

def screen_terms():
    apply_ui()
    st.markdown('<h1 class="main-title">📜 ĐIỀU KHOẢN & THÔNG TIN</h1>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div class="glass-card">
            <h3>Xin chào, {st.session_state.auth_status.upper()}</h3>
            <p><b>Phiên bản hệ thống:</b> {VERSION}</p>
            <p><b>Tác giả:</b> {CREATOR_NAME}</p>
            <hr>
            <h4>Điều khoản sử dụng:</h4>
            <ul>
                <li>Mọi cuộc hội thoại AI đều được lưu trữ bảo mật qua GitHub (trừ Quyền Khách).</li>
                <li>Không sử dụng công cụ để Spam hoặc gửi yêu cầu vi phạm pháp luật.</li>
                <li>Tài khoản sẽ bị khóa tạm thời nếu đăng nhập sai nhiều lần.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.checkbox("Tôi xác nhận đã hiểu rõ thông tin và điều khoản") and st.button("BẮT ĐẦU SỬ DỤNG"):
            if st.session_state.auth_status != "Guest":
                if st.session_state.auth_status not in st.session_state.agreed_users:
                    st.session_state.agreed_users.append(st.session_state.auth_status)
                    save_github()
            st.session_state.stage = "MENU"; st.rerun()

def screen_menu():
    apply_ui()
    st.markdown(f'<h1 class="main-title">🚀 NEXUS CONTROL PANEL</h1>', unsafe_allow_html=True)
    
    st.markdown(f'<h3 style="text-align:center;">Người dùng hiện tại: {st.session_state.auth_status.upper()}</h3>', unsafe_allow_html=True)
    st.write("<br>", unsafe_allow_html=True)

    # Chia cột tận dụng chiều ngang
    c1, c2, c3 = st.columns(3)
    with c1: 
        if st.button("🧠 MỞ TRỢ LÝ AI", use_container_width=True): st.session_state.stage = "CHAT"; st.rerun()
    with c2: 
        if st.button("🎨 CÀI ĐẶT HỆ THỐNG", use_container_width=True): st.session_state.stage = "SETTINGS"; st.rerun()
    with c3: 
        if st.button("🚪 ĐĂNG XUẤT", use_container_width=True): st.session_state.auth_status = None; st.session_state.stage = "AUTH"; st.rerun()

def screen_chat():
    apply_ui()
    with st.sidebar:
        st.header("📂 Thư Viện Hội Thoại")
        if st.button("➕ TẠO CHAT MỚI", use_container_width=True): 
            st.session_state.current_chat = None; st.rerun()
        st.write("---")
        
        for title in list(st.session_state.chat_library.keys()):
            col_btn, col_del = st.columns([4, 1])
            with col_btn:
                if st.button(f"📄 {title[:15]}", key=f"c_{title}", use_container_width=True):
                    st.session_state.current_chat = title; st.rerun()
            with col_del:
                if st.button("🗑️", key=f"d_{title}"):
                    del st.session_state.chat_library[title]
                    save_github(); st.rerun()
        
        st.write("---")
        if st.button("🏠 VỀ TRANG CHỦ", use_container_width=True): st.session_state.stage = "MENU"; st.rerun()

    history = st.session_state.chat_library.get(st.session_state.current_chat, []) if st.session_state.current_chat else []
    for m in history:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if p := st.chat_input("Nhập lệnh cho Nexus..."):
        if not st.session_state.current_chat:
            st.session_state.current_chat = p[:20]
            st.session_state.chat_library[st.session_state.current_chat] = []
        
        st.session_state.chat_library[st.session_state.current_chat].append({"role": "user", "content": p})
        with st.chat_message("user"): st.markdown(p)
        
        with st.chat_message("assistant"):
            res = st.empty(); full = ""
            for chunk in call_ai(st.session_state.chat_library[st.session_state.current_chat]):
                if chunk.choices[0].delta.content:
                    full += chunk.choices[0].delta.content
                    res.markdown(full + "▌")
            res.markdown(full)
        
        st.session_state.chat_library[st.session_state.current_chat].append({"role": "assistant", "content": full})
        if st.session_state.auth_status != "Guest": save_github()

def screen_settings():
    apply_ui()
    st.markdown('<h1 class="main-title">⚙️ CÀI ĐẶT HỆ THỐNG</h1>', unsafe_allow_html=True)
    
    # Chia 2 cột để Cài đặt UI bên trái, Cài đặt Bảo mật bên phải
    col_ui, col_sec = st.columns(2)
    
    with col_ui:
        st.markdown("""<div class="glass-card"><h3>🎨 Tùy chỉnh Giao diện</h3>""", unsafe_allow_html=True)
        st.session_state.theme['bg_url'] = st.text_input("Link ảnh nền (URL):", st.session_state.theme['bg_url'])
        st.session_state.theme['primary_color'] = st.color_picker("Màu chủ đạo:", st.session_state.theme['primary_color'])
        st.session_state.theme['use_glass'] = st.toggle("Bật lớp Sương Mờ bảo vệ chữ", st.session_state.theme['use_glass'])
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_sec:
        st.markdown("""<div class="glass-card"><h3>🛡️ Thiết lập Bảo mật</h3>""", unsafe_allow_html=True)
        st.session_state.theme['max_fails'] = st.number_input("Số lần nhập sai mật khẩu tối đa:", min_value=1, max_value=20, value=st.session_state.theme.get('max_fails', 5))
        st.session_state.theme['lockout_time'] = st.number_input("Thời gian khóa tạm thời (Giây):", min_value=10, max_value=300, value=st.session_state.theme.get('lockout_time', 30))
        st.markdown("</div>", unsafe_allow_html=True)
        
    st.write("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("💾 LƯU THAY ĐỔI & ĐỒNG BỘ", use_container_width=True):
            save_github(); st.success("Cập nhật thành công!"); time.sleep(1); st.session_state.stage = "MENU"; st.rerun()
        if st.button("🔙 QUAY LẠI MENU", use_container_width=True): st.session_state.stage = "MENU"; st.rerun()

# --- 7. LUỒNG ĐIỀU HƯỚNG TỔNG (FIX LỖI MÀN HÌNH TRẮNG) ---
if st.session_state.stage == "AUTH": screen_auth()
elif st.session_state.stage == "TERMS": screen_terms()
elif st.session_state.stage == "MENU": screen_menu()
elif st.session_state.stage == "CHAT": screen_chat()
elif st.session_state.stage == "SETTINGS": screen_settings()
