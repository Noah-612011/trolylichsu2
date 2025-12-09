import streamlit as st
from gtts import gTTS
from io import BytesIO
import base64
import openai
import streamlit.components.v1 as components

# ======================
# 🔑 CẤU HÌNH API
# ======================
openai.api_key = st.secrets["openai_api_key"]

# ======================
# 🔍 TỪ KHÓA LỊCH SỬ
# ======================
history_keywords = [
    "lịch sử", "chiến tranh", "khởi nghĩa", "cách mạng", 
    "triều đại", "vua", "thế chiến", "cổ đại", "trung đại",
    "hiện đại", "di tích", "danh lam", "quân", "trận", "đế quốc"
]

def is_history_question(question):
    q = question.lower()
    return any(kw in q for kw in history_keywords)

# ======================
# 📜 DỮ LIỆU CỨNG
# ======================
lich_su_data = {
    "trưng trắc": "Hai Bà Trưng khởi nghĩa chống quân Hán năm 40 sau Công Nguyên.",
    "ngô quyền": "Ngô Quyền đánh bại quân Nam Hán trên sông Bạch Đằng năm 938.",
    "lý thái tổ": "Năm 1010, Lý Thái Tổ dời đô về Thăng Long.",
    "trần hưng đạo": "Trần Hưng Đạo ba lần đánh bại quân Nguyên – Mông.",
    "lê lợi": "Lê Lợi lãnh đạo khởi nghĩa Lam Sơn và giành độc lập năm 1428."
}

def tra_loi_lich_su(cau_hoi: str):
    cau_hoi_lower = cau_hoi.lower()
    for key, value in lich_su_data.items():
        if key in cau_hoi_lower:
            return value
    return None  # Không tìm thấy trong dữ liệu cứng

# ======================
# 🧠 HÀM GỌI AI
# ======================
def tra_loi_AI(cau_hoi):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Bạn là trợ lý lịch sử Việt Nam, trả lời ngắn gọn và chính xác."},
                {"role": "user", "content": cau_hoi}
            ],
            max_tokens=200,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"AI gặp lỗi: {e}"

# ======================
# ⚙️ CẤU HÌNH STREAMLIT
# ======================
st.set_page_config(page_title="Trợ lý Lịch sử Việt Nam", layout="centered")
st.title("📚 Trợ lý Lịch sử Việt Nam")
st.write("Nhập câu hỏi về lịch sử Việt Nam và bấm Trả lời. Có thể nghe giọng đọc!")

# 🔓 MỞ ÂM THANH
if "audio_unlocked" not in st.session_state:
    st.session_state["audio_unlocked"] = False

if st.button("🔊 BẬT ÂM THANH (1 lần)"):
    js = """
    <script>
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            if (ctx.state === 'suspended') ctx.resume();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            gain.gain.value = 0;
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start();
            osc.stop(ctx.currentTime + 0.05);
        } catch(e) {}
    </script>
    """
    components.html(js, height=0)
    st.session_state["audio_unlocked"] = True
    st.success("Âm thanh đã mở khoá!")

# 💬 GIAO DIỆN NHẬP CÂU HỎI
cau_hoi = st.text_input("❓ Nhập câu hỏi lịch sử:")

if st.button("📖 Trả lời"):
    if not cau_hoi:
        st.warning("Vui lòng nhập câu hỏi.")
        st.stop()
    
    if not is_history_question(cau_hoi):
        st.error("❗ Tôi chỉ trả lời câu hỏi về lịch sử.")
        st.stop()
    
    # Tra dữ liệu cứng trước
    tra_loi = tra_loi_lich_su(cau_hoi)
    if tra_loi is None:
        tra_loi = tra_loi_AI(cau_hoi)  # Gọi AI nếu không có dữ liệu cứng
    
    st.success(tra_loi)

    # 🔊 TẠO GIỌNG NÓI
    try:
        mp3_fp = BytesIO()
        gTTS(text=tra_loi, lang="vi").write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        audio_b64 = base64.b64encode(mp3_fp.read()).decode()

        unlocked = "true" if st.session_state["audio_unlocked"] else "false"
        audio_html = f"""
        <div id="tts"></div>
        <script>
          (function(){{
            const isIOS = /iPhone|iPad|iPod/.test(navigator.userAgent);
            const unlocked = {unlocked};
            const audio = document.createElement('audio');
            audio.src = "data:audio/mp3;base64,{audio_b64}";
            audio.controls = true;
            audio.playsInline = true;
            document.getElementById("tts").appendChild(audio);
            if (!isIOS && unlocked) {{
                audio.autoplay = true;
                audio.play().catch(()=>{{}});
            }}
          }})();
        </script>
        """
        components.html(audio_html, height=120)

    except Exception as e:
        st.error("Lỗi tạo giọng nói.")
