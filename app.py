import os
import re
import base64
import io
import streamlit as st
from PIL import Image
import pdfplumber
import pypdfium2 as pdfium
from dotenv import load_dotenv
from groq import Groq

# ---------------------------------------------------------
# 1. إعدادات الصفحة الأساسية
# ---------------------------------------------------------
st.set_page_config(
    page_title="Asinu AI - نظام أسينو الطبي",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

load_dotenv()

# ---------------------------------------------------------
# 2. تبديل المظهر (داكن / كريمي)
# ---------------------------------------------------------
theme_choice = st.radio(
    "🎨 اختر مظهر الواجهة:",
    ["الوضع الداكن الملوكي (Dark Mode)", "الوضع الكريمي الفاخر (Cream Mode)"],
    horizontal=True
)

if "Dark" in theme_choice:
    bg_color = "#0A0F1D"
    card_bg = "#111827"
    text_color = "#F9FAFB"
    border_color = "#D97706"
else:
    bg_color = "#FDFBF7"
    card_bg = "#FFFDFA"
    text_color = "#1C1917"
    border_color = "#B45309"

DYNAMIC_CSS = f"""
<style>
    /* إخفاء شريط الملاحة الجانبي والسهم */
    [data-testid="stSidebar"], [data-testid="collapsedControl"] {{
        display: none !important;
    }}
    
    .stApp {{
        background-color: {bg_color} !important;
        color: {text_color} !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }}
    
    /* الهيدر الرئيسي الملكي المسماري */
    .babylon-header {{
        background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 50%, #030712 100%);
        padding: 2.2rem 2rem;
        border-radius: 20px;
        color: #FFFFFF;
        text-align: center;
        box-shadow: 0 15px 35px -5px rgba(0, 0, 0, 0.5);
        border: 2px solid #D97706;
        margin-bottom: 2rem;
    }}

    .cuneiform-symbol {{
        font-size: 3rem;
        color: #FBBF24;
        letter-spacing: 6px;
        margin-bottom: 0.2rem;
    }}

    .babylon-header h1 {{
        color: #FFFFFF !important;
        font-weight: 900;
        font-size: 2.5rem;
        margin-bottom: 0.4rem;
    }}

    .engineer-badge {{
        display: inline-block;
        background: linear-gradient(90deg, #D97706 0%, #B45309 100%);
        color: #FFFFFF;
        border: 1px solid #FBBF24;
        padding: 0.5rem 1.6rem;
        border-radius: 50px;
        font-weight: 800;
        font-size: 1.05rem;
        box-shadow: 0 4px 15px rgba(217, 119, 6, 0.4);
    }}

    /* كروت المحتوى */
    .content-card {{
        background-color: {card_bg};
        padding: 2rem;
        border-radius: 16px;
        border: 1px solid {border_color};
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.2);
        margin-bottom: 2rem;
    }}

    /* أزرار التشغيل */
    .stButton>button {{
        background: linear-gradient(135deg, #D97706 0%, #B45309 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid #FBBF24 !important;
        font-weight: 800 !important;
        font-size: 1.3rem !important;
        padding: 0.9rem 2rem !important;
        border-radius: 12px !important;
        width: 100% !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 6px 20px rgba(217, 119, 6, 0.3) !important;
    }}

    .stButton>button:hover {{
        background: linear-gradient(135deg, #1E3A8A 0%, #0C1E3A 100%) !important;
        border-color: #D97706 !important;
        transform: translateY(-3px) !important;
    }}

    .footer-credits {{
        text-align: center;
        padding: 2rem;
        margin-top: 3rem;
        border-top: 1px solid {border_color};
        color: #94A3B8;
        font-size: 1rem;
    }}
</style>
"""
st.markdown(DYNAMIC_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. دوال المعالجة المساعدة
# ---------------------------------------------------------

def pil_image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def extract_pdf_as_images(uploaded_pdf):
    images = []
    try:
        pdf_bytes = uploaded_pdf.getvalue()
        pdf = pdfium.PdfDocument(pdf_bytes)
        for i in range(min(len(pdf), 3)):
            page = pdf[i]
            image = page.render(scale=2).to_pil()
            images.append(image)
    except Exception:
        pass
    return images

def extract_pdf_text_direct(uploaded_pdf):
    extracted_text = ""
    try:
        with pdfplumber.open(uploaded_pdf) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"
    except Exception:
        pass
    return extracted_text.strip()

# ---------------------------------------------------------
# 4. الواجهة الهيدر البابلي المسماري
# ---------------------------------------------------------

st.markdown("""
<div class="babylon-header">
    <div class="cuneiform-symbol">🏛️ 𒀭 𒀀 𒋛 𒉡</div>
    <h1>ASINU AI — نظام أسينو الطبي البابلي</h1>
    <div class="engineer-badge"> تم تطويره بواسطة الطالب مرتضى سعد</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. مفتاح الـ API
# ---------------------------------------------------------
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    api_key = st.text_input("🔑 أدخل مفتاح Groq API لتفعيل النظام:", type="password")
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 6. رفع الملف والتحليل المباشر
# ---------------------------------------------------------
st.markdown('<div class="content-card">', unsafe_allow_html=True)
st.subheader("📥 قم برفع صورة أو ملف التقرير الطبي مباشرة:")

uploaded_file = st.file_uploader(
    "اسحب الملف أو اختره من جهازك (PDF / PNG / JPG / JPEG / WEBP):",
    type=["pdf", "png", "jpg", "jpeg", "webp"]
)

st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 7. المحرك التلقائي الديناميكي المباشر
# ---------------------------------------------------------

def get_active_model(client, is_vision=True):
    try:
        available_models = [m.id for m in client.models.list().data]
        if is_vision:
            for m in available_models:
                if any(v in m for v in ["vision", "scout", "qwen", "multimodal"]):
                    return m
        for m in available_models:
            if "llama-3.3-70b" in m or "llama-3.1-8b" in m or "versatile" in m:
                return m
        return available_models[0] if available_models else "llama-3.3-70b-versatile"
    except Exception:
        return "llama-3.3-70b-versatile"

# ---------------------------------------------------------
# 8. تنفيذ التحليل
# ---------------------------------------------------------
if uploaded_file:
    if st.button("🚀 تحليل التقرير الطبي بواسطة Asinu AI"):
        if not api_key:
            st.error("❌ يرجى إدخال مفتاح Groq API أولاً.")
        else:
            try:
                client = Groq(api_key=api_key)
                
                file_ext = uploaded_file.name.split('.')[-1].lower()
                image_to_process = None
                pdf_text = ""

                if file_ext in ["png", "jpg", "jpeg", "webp"]:
                    image_to_process = Image.open(uploaded_file)
                elif file_ext == "pdf":
                    pdf_images = extract_pdf_as_images(uploaded_file)
                    if pdf_images:
                        image_to_process = pdf_images[0]
                    else:
                        pdf_text = extract_pdf_text_direct(uploaded_file)

                system_prompt = """
                أنت "أسينو AI" (Asinu AI)، خبير ومساعد طبي ذكي بابلّي.
                مهمتك قراءة وتفكيك المستند الطبي المرفوع وإخراج تقرير طبي تثقيفي شامل باللغة العربية بأسلوب دقيق جداً.

                يجب أن تحتوي استجابتك على الأقسام التالية بالترتيب:

                1. 🟢🟡🔴 **تحديد مستوى الخطورة العام (Risk Assessment):**
                   اختر واكتب بوضوح إحدى الحالات التالية في بداية التقرير:
                   - [مستوى الخطورة: جيد / طبيعي 🟢]
                   - [مستوى الخطورة: متوسط / يتطلب متابعة 🟡]
                   - [مستوى الخطورة: مرتفع / حرج وخطر 🔴]

                2. 📝 **ملخص التقرير الطبي:**
                   شرح مبسط ومباشر بكلمات عربية واضحة يفهمها المريض دون تعقيد.

                3. 📊 **جدول التحاليل التفصيلي:**
                   جدول ينظم الفحوصات بوضوح ويحتوي على: (اسم الفحص، النتيجة المسجلة، المدى الطبيعي، الحالة: طبيعي/مرتفع/منخفض).

                4. 💡 **التشخيص التثقيفي والنصائح الطبية:**
                   - شرح أسباب ارتفاع أو انخفاض كل مؤشر حيوي إن وجد.
                   - وصايا ونظام غذائي وصحي استرشادي مخصص للحالة.

                5. ⚠️ **إبراء الذمة الطبية:**
                   تأكيد أن النظام أداة مساعدة وتثقيفية ولا يستبدل الطبيب المختص.
                """

                with st.spinner("🧠 جاري قراءة وتحليل المستند عبر الذكاء الاصطناعي..."):
                    if image_to_process is not None:
                        base64_img = pil_image_to_base64(image_to_process)
                        chosen_model = get_active_model(client, is_vision=True)
                        
                        try:
                            response = client.chat.completions.create(
                                model=chosen_model,
                                messages=[
                                    {
                                        "role": "user",
                                        "content": [
                                            {"type": "text", "text": system_prompt + "\nاقرأ هذه الصورة وحللها بالكامل ودقة متناهية:"},
                                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
                                        ]
                                    }
                                ],
                                temperature=0.1,
                                max_tokens=3000
                            )
                            ai_response = response.choices[0].message.content
                        except Exception:
                            text_model = get_active_model(client, is_vision=False)
                            response = client.chat.completions.create(
                                model=text_model,
                                messages=[
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": f"يرجى تقديم التقرير الطبي المناسب بناءً على هذا الملف."}
                                ],
                                temperature=0.1,
                                max_tokens=3000
                            )
                            ai_response = response.choices[0].message.content
                    else:
                        text_model = get_active_model(client, is_vision=False)
                        response = client.chat.completions.create(
                            model=text_model,
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": f"حلل النص التالي من التقرير الطبي:\n{pdf_text}"}
                            ],
                            temperature=0.1,
                            max_tokens=3000
                        )
                        ai_response = response.choices[0].message.content

                st.markdown('<div class="content-card">', unsafe_allow_html=True)
                st.subheader("📑 نتيجة التحليل الطبي والتقرير الشامل")
                st.markdown(ai_response)
                st.markdown('</div>', unsafe_allow_html=True)

            except Exception as e:
                st.error(f"❌ حدث خطأ أثناء تشغيل التحليل: {str(e)}")

# ---------------------------------------------------------
# 9. التذييل
# ---------------------------------------------------------
st.markdown("""
<div class="footer-credits">
    <p><b>ASINU AI — BABYLON MEDICAL INTELLIGENCE SYSTEM</b></p>
    <p>تم تصميم وتطوير المنظومة بالكامل بواسطة <strong>المهندس مرتضى سعد</strong></p>
</div>
""", unsafe_allow_html=True)
