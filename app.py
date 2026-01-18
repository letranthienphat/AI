import streamlit as st
from openai import OpenAI
from gtts import gTTS
from io import BytesIO
from streamlit_mic_recorder import mic_recorder
import qrcode
import base64
from langdetect import detect
import re
import json

# --- 1. CẤU HÌNH UI & CSS SPOTLIGHT CAO CẤP ---
st.set_page_config(page_title="Nexus v17 Interactive", layout="wide", page_icon="💡")

st.markdown("""
    <style>
    /* Spotlight & Hiệu ứng làm mờ */
    .spotlight-active {
        border: 4px solid #007bff !important;
        box-shadow: 0 0 30px rgba(0,123,255,0.5) !important;
        background: #f0f7ff !important;
        z-index: 9999;
        position: relative;
    }
    .dimmed { opacity: 0.2; filter: blur(3px); pointer-events: none; transition: 0.5s; }
    
    /* Ghim bảng hướng dẫn ở giữa màn hình điện thoại/máy tính */
    .floating-guide {
        position: fixed;
        top: 20%;
        left: 50%;
        transform: translate(-50%, -20%);
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        z-index: 10001;
        width: 90%;
        max-width: 500px;
        border-top: 5px solid #007bff;
    }
    
    .stApp { background-color: #ffffff; }
    .stChatInputContainer { z-index: 1000; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HÀM TRỢ NĂNG ---
def speak_js(text, speed, lang):
    clean = text.replace('"', "'").replace('\n', ' ')
    return f"<script>window.speechSynthesis.cancel(); var m=new SpeechSynthesisUtterance('{clean}'); m.lang='{lang}'; m.rate={speed}; window.speechSynthesis.speak(m);</script>"

def get_lang_code(text):
    try:
        l = detect(text)
        mapping = {"vi":"vi-VN", "en":"en-US"}
        return mapping.get(l, "vi-VN")
    except: return "vi-VN"

# --- 3. KHỞI TẠO STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "guide_step" not in st.session_state: st.session_state.guide_step = 0 # 0: Ko có, 1-4: Các bước
if "suggestions" not in st.session_state: st.session_state.suggestions = ["Chào bạn", "Tin tức", "Kể chuyện"]

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 4. HÀM XỬ LÝ AI ---
def process_ai(user_input):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("assistant"):
        p = st.empty(); full = ""
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            stream=True
        )
        for chunk in res:
            if chunk.choices[0].delta.content:
                full += chunk.choices[0].delta.content
                p.markdown(full + "▌")
        p.markdown(full)
        st.session_state.messages.append({"role": "assistant", "content": full})

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("💎 Nexus Terminal")
    if st.button("📖 Chạy hướng dẫn mẫu", use_container_width=True):
        st.session_state.guide_step = 1
        st.rerun()
    
    st.divider()
    st.subheader("💾 Dữ liệu")
    if st.button("📤 Lưu chat (.json)", use_container_width=True):
        data = json.dumps(st.session_state.messages, ensure_ascii=False)
        st.download_button("Tải file về", data=data, file_name="backup.json")
    
    if st.button("🗑️ Xóa sạch", use_container_width=True):
        st.session_state.messages = []; st.rerun()

# --- 6. GIAO DIỆN CHÍNH ---
st.title("AI Nexus v17: Interactive 💡")

# MÀN HÌNH CHÀO HỎI BAN ĐẦU
if st.session_state.guide_step == 0 and not st.session_state.messages:
    st.info("Chào mừng! Bạn muốn bắt đầu chat ngay hay trải nghiệm thử hướng dẫn mẫu?")
    if st.button("Bắt đầu Hướng dẫn mẫu ✨", use_container_width=True):
        st.session_state.guide_step = 1
        # Tạo dữ liệu mẫu để trải nghiệm luôn
        st.session_state.messages = [
            {"role": "user", "content": "Đây là hướng dẫn mẫu phải không?"},
            {"role": "assistant", "content": "Chính xác! Tôi là AI Nexus. Đây là tin nhắn mẫu để bạn dùng thử các tính năng Nghe, Tải và quét mã QR."}
        ]
        st.rerun()

# HỆ THỐNG FLOATING GUIDE (Bảng hướng dẫn nổi)
if 1 <= st.session_state.guide_step <= 4:
    guides = {
        1: "🎤 **BƯỚC 1: NHẬP LIỆU** - Bạn có thể dùng Mic hoặc Chat Input bên dưới để nói chuyện với tôi.",
        2: "🔊 **BƯỚC 2: TRẢI NGHIỆM MẪU** - Thử nhấn vào nút Nghe hoặc Tải Mp3 ở tin nhắn mẫu bên dưới!",
        3: "💡 **BƯỚC 3: GỢI Ý NHANH** - Nhấn vào các nút gợi ý để hỏi tiếp mà không cần gõ.",
        4: "⚙️ **BƯỚC 4: LƯU TRỮ** - Mọi cài đặt và sao lưu nằm ở thanh bên trái (Sidebar)."
    }
    st.markdown(f"""
        <div class="floating-guide">
            <h4>🎯 Hướng dẫn ({st.session_state.guide_step}/4)</h4>
            <p>{guides[st.session_state.guide_step]}</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button(f"Tiếp theo ({st.session_state.guide_step}/4) ➡️", use_container_width=True):
        st.session_state.guide_step += 1
        if st.session_state.guide_step > 4: st.session_state.guide_step = 0
        st.rerun()

# HIỂN THỊ CHAT (Có hiệu ứng mờ/sáng theo bước)
for i, m in enumerate(st.session_state.messages):
    is_demo = (st.session_state.guide_step == 2 and m["role"] == "assistant")
    chat_style = "spotlight-active" if is_demo else ("dimmed" if st.session_state.guide_step != 0 and st.session_state.guide_step != 2 else "")
    
    st.markdown(f'<div class="{chat_style}">', unsafe_allow_html=True)
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("🔊 Nghe", key=f"s_{i}"):
                    st.components.v1.html(speak_js(m["content"], 1.1, get_lang_code(m["content"])), height=0)
            with c2:
                # Tải Mp3 mẫu
                tts = gTTS(text=m["content"][:100], lang="vi")
                b = BytesIO(); tts.write_to_fp(b); b64 = base64.b64encode(b.getvalue()).decode()
                st.markdown(f'<a href="data:audio/mp3;base64,{b64}" download="demo.mp3"><button style="width:100%; border-radius:10px; border:1px solid #ddd; padding:5px;">📥 Tải</button></a>', unsafe_allow_html=True)
            with c3:
                if st.button("📱 QR", key=f"q_{i}"):
                    qr = qrcode.make(m["content"][:200]); buf = BytesIO(); qr.save(buf, format="PNG"); st.image(buf, width=100)
    st.markdown('</div>', unsafe_allow_html=True)

# NÚT GỢI Ý (Mờ trừ khi ở bước 3)
st.write("---")
sug_style = "spotlight-active" if st.session_state.guide_step == 3 else ("dimmed" if st.session_state.guide_step != 0 and st.session_state.guide_step != 3 else "")
st.markdown(f'<div class="{sug_style}">', unsafe_allow_html=True)
cols = st.columns(len(st.session_state.suggestions))
for idx, sug in enumerate(st.session_state.suggestions):
    cols[idx].button(sug, key=f"s_{idx}", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# INPUT AREA (Mờ trừ khi ở bước 1)
st.write("<br><br><br><br>", unsafe_allow_html=True)
in_style = "spotlight-active" if st.session_state.guide_step == 1 else ("dimmed" if st.session_state.guide_step != 0 and st.session_state.guide_step != 1 else "")
st.markdown(f'<div class="{in_style}" style="position:fixed; bottom:0; width:100%; background:white; padding:10px;">', unsafe_allow_html=True)
st.chat_input("Nhập tin nhắn...")
st.markdown('</div>', unsafe_allow_html=True)
