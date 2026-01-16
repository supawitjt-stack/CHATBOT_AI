import os
import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF
import easyocr #pytorch
import numpy as np
from PIL import Image
import torch
import dotenv
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# นำเข้า Prompt (ตรวจสอบว่าไฟล์ prompt.py อยู่ในโฟลเดอร์เดียวกัน)
try:
    from prompt import PROMPT_C_Programmer
except ImportError:
    # เผื่อกรณีหาไฟล์ไม่เจอ ใช้ค่า Default
    PROMPT_C_Programmer = "คุณคือผู้ช่วยสอนภาษา C ที่มีความเชี่ยวชาญ และตอบคำถามอย่าง เป็นทางการ"

# --- 1. Configuration & Setup ---
dotenv.load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

st.set_page_config(
    page_title="Chat Bot : C Programming AI",
    page_icon="🤖",
    layout="wide", # ปรับเป็น Wide mode เพื่อให้ดูทันสมัยและใช้พื้นที่เต็มจอ
    initial_sidebar_state="expanded"
)

# --- 2. Custom CSS (GUI Redesign: Vivid, Modern & Friendly) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600;800&display=swap');

    /* Global Font Settings */
    html, body, [class*="css"] {
        font-family: 'Kanit', sans-serif;
    }

    /* Main Background Decoration (Optional: Gradient hint at top) */
    .stApp {
        background-image: linear-gradient(to bottom, #fdfbfb 0%, #ebedee 100%);
    }

    /* Header Styling: Gradient Text & Modern Look */
    .main-header {
        background: linear-gradient(90deg, #FF0080 0%, #7928CA 50%, #FF0080 100%);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: gradient 3s linear infinite;
        font-weight: 800;
        text-align: center;
        font-size: 3.5rem;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .sub-header {
        text-align: center;
        color: #555;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }

    /* Animation Keyframes */
    @keyframes gradient {
        0% { background-position: 0% center; }
        100% { background-position: 200% center; }
    }

    /* Chat Container Styling */
    .stChatMessage {
        background-color: white;
        border-radius: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        transition: transform 0.2s;
    }
    
    .stChatMessage:hover {
        transform: translateY(-2px);
    }

    /* User Avatar & Message */
    [data-testid="stChatMessage"][data-testid="stChatMessageUser"] {
        background: linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%);
    }

    /* Bot Avatar & Message */
    [data-testid="stChatMessage"][data-testid="stChatMessageModel"] {
        background: white;
        border: 1px solid #eee;
    }

    /* Input Field Styling */
    .stChatInputContainer {
        border-radius: 30px;
        border: 2px solid #7928CA;
        padding: 5px;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #eee;
    }
    
    .sidebar-btn {
        width: 100%;
        border-radius: 10px;
        font-weight: 600;
    }

    .welcome-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 40px;
        border-radius: 25px;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 10px 30px rgba(118, 75, 162, 0.3);
    }
    .welcome-card h2 {
        color: white;
        font-weight: 700;
    }

    /* ----------------------------------------------------------- */
    /* ✨ MODERN CHAT INPUT REDESIGN (ส่วนที่ปรับปรุงใหม่)       */
    /* ----------------------------------------------------------- */
    
    /* พื้นหลังโซนพิมพ์ข้อความ (Gradient Fade Out) */
    .stChatInputContainer {
        padding-bottom: 30px;
        padding-top: 15px;
        background: linear-gradient(to top, #ebedee 0%, rgba(255,255,255,0.8) 50%, rgba(255,255,255,0) 100%);
    }
    
    .main .block-container {
        padding-bottom: 140px; 
    }
    
    /* Input Textarea Styling */
    .stChatInputContainer textarea {
        background-color: #ffffff !important;
        color: #333 !important;
        
        /* เทคนิคทำขอบ Gradient */
        border: 2px solid transparent !important;
        border-radius: 35px !important;
        background-image: linear-gradient(white, white), linear-gradient(to right, #FF0080, #7928CA);
        background-origin: border-box;
        background-clip: padding-box, border-box;
        
        box-shadow: 0 8px 20px rgba(0,0,0,0.08) !important;
        transition: all 0.3s ease !important;
        font-size: 16px !important;
        padding: 15px 25px !important;
    }

    /* Effect ตอนกดพิมพ์ */
    .stChatInputContainer textarea:focus {
        box-shadow: 0 12px 25px rgba(121, 40, 202, 0.25) !important;
        transform: translateY(-3px);
    }
    
    /* ปุ่ม Send (Icon) */
    .stChatInputContainer button {
        background: linear-gradient(135deg, #FF0080 0%, #7928CA 100%) !important;
        border: none !important;
        border-radius: 50% !important;
        width: 45px !important;
        height: 45px !important;
        color: white !important;
        box-shadow: 0 4px 10px rgba(121, 40, 202, 0.3) !important;
        margin-right: 5px !important;
        transition: all 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important; 
    }
    
    .stChatInputContainer button:hover {
        transform: scale(1.15);
        box-shadow: 0 6px 15px rgba(121, 40, 202, 0.5) !important;
    }
    
    .stChatInputContainer button svg {
        fill: white !important;
        width: 20px !important;
        height: 20px !important;
    }    
            
    /* Hide Default Menus */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 3. Gemini Configuration ---
if not GOOGLE_API_KEY:
    st.error("⚠️ ไม่พบ GOOGLE_API_KEY กรุณาตรวจสอบไฟล์ .env")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)
generation_config = {
    "temperature": 0.1, 
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 2048,
    "response_mime_type": "text/plain",
}
SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
}
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash", 
    generation_config=generation_config,
    system_instruction=PROMPT_C_Programmer
)

# --- 4. Smart OCR & Data Handling (คงเดิม) ---
CACHE_FILENAME = "extracted_content_cache.txt"
PDF_FILE_PATH = r"D:\KMUTNB\Vatinee Nuipian\Project_AI_CHATBOT\CHATBOT_AI\PROGRAMMING_C.pdf"

@st.cache_resource
def load_ocr_model():
    use_gpu = torch.cuda.is_available()
    return easyocr.Reader(['th', 'en'], gpu=use_gpu)

def get_knowledge_base():
    # กรณี 1: มีไฟล์ Cache อยู่แล้ว โหลดมาใช้เลย
    if os.path.exists(CACHE_FILENAME):
        with open(CACHE_FILENAME, "r", encoding="utf-8") as f:
            return f.read()

    # กรณี 2: ต้องทำ OCR
    if not os.path.exists(PDF_FILE_PATH):
        return None 

    # เริ่มกระบวนการ OCR
    status_placeholder = st.empty()
    progress_bar = st.progress(0)
    status_placeholder.info("📑 กำลังเตรียมข้อมูล (ครั้งแรกอาจใช้เวลานานนิดนึงครับ)...")

    progress_bar = st.progress(0, text="Starting engine...")
    try:
        reader = load_ocr_model()
        doc = fitz.open(PDF_FILE_PATH)
        full_text = []
        
        start_page = 13
        end_page = 173
        pages_to_process = [p for p in range(len(doc)) if start_page <= p + 1 <= end_page]
        total_target_pages = len(pages_to_process)

        processed_count = 0

        for page_index in pages_to_process:
            current_page_num = page_index + 1
            processed_count += 1
            percent = int((processed_count / total_target_pages) * 100)
            progress_bar.progress(min(percent, 100), text=f"กำลังอ่านข้อมูล {current_page_num} ({percent}%)")

            page = doc[page_index]
            pix = page.get_pixmap(matrix=fitz.Matrix(3, 3))
            img = np.array(Image.frombytes("RGB", [pix.width, pix.height], pix.samples))

            result = reader.readtext(img, detail=0)
            page_content = " ".join(result)
            full_text.append(f"--- Page {current_page_num} ---\n{page_content}")

        combined_text = "\n".join(full_text)
        
        with open(CACHE_FILENAME, "w", encoding="utf-8") as f:
            f.write(combined_text)
        
        status_placeholder.empty()
        progress_bar.empty()
        st.toast("✅ เตรียมข้อมูลเสร็จสิ้น พร้อมลุย!", icon="🚀")
        return combined_text

    except Exception as e:
        status_placeholder.error(f"เกิดข้อผิดพลาด: {e}")
        return None

# --- 5. UI Logic & Layout ---

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "model", "content": "สวัสดีครับ! น้องเซียน C ยินดีต้อนรับครับ มีโจทย์ภาษา C ตรงไหนที่ติดขัด ถามผมได้เลยนะครับ 🚀"}
    ]

# Sidebar (Modernized)
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=100) # Placeholder Icon
    st.markdown("### ⚙️ เมนูคำสั่ง")
    
    st.markdown("---")
    if st.button("🗑️ เริ่มต้นสนทนาใหม่", use_container_width=True, type="primary"):
        st.session_state["messages"] = [
            {"role": "model", "content": "รีเซ็ตระบบเรียบร้อย! พร้อมรับคำถามใหม่ครับ ✨"}
        ]
        st.rerun()
    
    st.markdown("---")
    st.info("💡 **Tip:** ลองถามข้อมูลเกี่ยวกับการเขียนโปรแกรมภาษา C ดูสิครับ")
    st.caption("Developed By Mr.Thanaphon & Mr.Supawit SMTCT68")

# Main Content Structure
col1, col2, col3 = st.columns([1, 6, 1]) # จัด Layout ให้อยู่ตรงกลางสวยงาม
with col2:
    st.markdown("<h1 class='main-header'>::: น้องเซียน C Programming :::</h1>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>เพื่อนคู่คิด อัจฉริยะภาษา C (AI Chatbot)</div>", unsafe_allow_html=True)

    # Load Content (Background)
    if "knowledge_base" not in st.session_state:
        with st.spinner("📦 กำลังโหลดฐานข้อมูลความรู้..."):
            kb_text = get_knowledge_base()
            if kb_text:
                st.session_state["knowledge_base"] = kb_text
            else:
                st.error("⚠️ ไม่สามารถโหลดข้อมูลได้ กรุณาตรวจสอบไฟล์ข้อมูล")

    # Welcome Screen Logic (แสดงเมื่อยังไม่มีการสนทนาจริงจัง)
    if len(st.session_state["messages"]) <= 1:
        st.markdown("""
        <div class='welcome-card'>
            <h2>👋 สวัสดีครับ! ยินดีต้อนรับสู่ห้องเรียนภาษา C</h2>
            <p>ผมคือ น้องเซียน C AI Assistant ที่ถูกฝึกมาเพื่อช่วยคุณไขข้อข้องใจในการเขียนโปรแกรม</p>
            <p style='font-size: 0.9rem; opacity: 0.8;'>พิมพ์คำถามของคุณที่ช่องด้านล่างได้เลยครับ เช่น "สอน For Loop หน่อย", "ขอตัวอย่างการใช้งานคำสั่งต่าง ๆ"</p>
        </div>
        """, unsafe_allow_html=True)

    # Display Chat
    for msg in st.session_state["messages"]:
        if msg["role"] == "model":
            avatar = "🤖"
        else:
            avatar = "🧑‍💻"
            
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # Chat Input & Processing
    if prompt := st.chat_input("พิมพ์คำถามของคุณที่นี่..."):
        # แสดงข้อความผู้ใช้
        st.session_state["messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(prompt)

        # สร้างคำตอบ
        with st.chat_message("model", avatar="🤖"):
            message_placeholder = st.empty()
            message_placeholder.markdown("⏳ _กำลังวิเคราะห์ข้อมูล..._")

            try:
                # เตรียม Context
                kb_content = st.session_state.get("knowledge_base", "")
                
                if kb_content:
                    # --- ปรับปรุง Prompt ให้เข้มงวดขึ้น (STRICT MODE) ---
                    final_prompt = f"""
                    คุณคือ AI ผู้ช่วยสอนภาษา C  ที่มีหน้าที่ตอบคำถามโดยอ้างอิงข้อมูลจาก "เนื้อหาที่กำหนดให้" (Context) ด้านล่างนี้เท่านั้น

                    === เนื้อหาที่กำหนดให้ (Context) ===
                    {kb_content}
                    ===================================

                    คำถามจากผู้ใช้: {prompt}

                    คำสั่งปฏิบัติ (Strict Instructions):
                    1. ให้ค้นหาคำตอบจาก "เนื้อหาที่กำหนดให้" เท่านั้น ห้ามใช้ความรู้ทั่วไปหรือความรู้ภายนอกในการตอบเด็ดขาด
                    2. หากคำตอบไม่มีระบุอยู่ใน "เนื้อหาที่กำหนดให้" ให้ตอบกลับทันทีว่า "ขออภัยครับ ข้อมูลส่วนนี้น้องเซียน  C ยังไม่ได้เรียนรู้มาเลยครับ" (ห้ามพยายามอธิบายเพิ่มหรือแต่งเติมเอง)
                    3. หากในเนื้อหาเป็นภาษาอังกฤษ ให้แปลและเรียบเรียงเป็นภาษาไทยให้เข้าใจง่าย แต่คง Code ตัวอย่างไว้ตามเดิม
                    4. ห้ามตอบเรื่องอื่นที่ไม่เกี่ยวกับภาษา C หรือ Programming ที่ไม่มีในเอกสาร
                    """
                    response = model.generate_content(final_prompt)
                    answer = response.text
                else:
                    answer = "ขออภัยครับ ข้อมูลส่วนนี้น้องเซียน C ยังไม่ได้เรียนรู้มาเลยครับ "
                # แสดงผล
                message_placeholder.markdown(answer)
                st.session_state["messages"].append({"role": "model", "content": answer})

            except Exception as e:
                message_placeholder.error("ขออภัย เกิดข้อผิดพลาดในการเชื่อมต่อกับ AI")
                print(f"Error: {e}")