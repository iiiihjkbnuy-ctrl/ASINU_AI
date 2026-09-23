import os
import json
import streamlit as st
from google import genai
import pdfplumber
from PIL import Image
import plotly.graph_objects as go

# إعدادات صفحة Streamlit
st.set_page_config(
    page_title="Asinu AI - نظام آسينو الطبي",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تخصيص واجهة المستخدم
st.markdown("""
    <style>
    .main {
        background-color: #0f172a;
        color: #f8fafc;
    }
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        color: #f8fafc;
    }
    h1, h2, h3 {
        color: #f3e8ff !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .custom-card {
        background-color: rgba(30, 41, 59, 0.7);
        border: 1px solid #3b82f6;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
    }
    .warning-box {
        background-color: rgba(127, 29, 29, 0.3);
        border-left: 4px solid #ef4444;
        padding: 15px;
        border-radius: 4px;
        margin-top: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# رأس الصفحة
st.markdown("<h1 style='text-align: center;'>🏛️ Asinu AI - نظام آسينو الطبي البابلي</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #94a3b8;'>دمج حكمة الطب البابلي القديم بالذكاء الاصطناعي الحديث لتحليل وتفسير التقارير الطبية</p>", unsafe_allow_html=True)
st.write("---")

# جلب مفتاح الـ API بأمان سواء من Streamlit Secrets أو متغيرات النظام
GEMINI_API_KEY = None
try:
    if "GEMINI_API_KEY" in st.secrets:
        GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

if not GEMINI_API_KEY:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error("⚠️ تنبيه: مفتاح `GEMINI_API_KEY` غير موجود. يرجى التأكد من إضافته في إعدادات المنصة (Secrets في Streamlit).")

# تهيئة عميل Google GenAI باستخدام المفتاح الصريح حصرياً
client = None
if GEMINI_API_KEY:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        st.error(f"خطأ في تهيئة عميل الذكاء الاصطناعي: {e}")

# دالة تحليل المستند (سواء كان نص PDF أو صورة) مباشرة عبر Gemini
def analyze_medical_content(content_part, is_image=False):
    if not client:
        st.error("خدمة الذكاء الاصطناعي غير متصلة لعدم توفر المفتاح.")
        return None
        
    prompt = """
أنت مساعد طبّي ذكي ومهني (Patient Education Tool). مهمتك هي تحليل التقرير الطبي المرفق (سواء كان صورة أو نص)، وتبسيط النتائج للمريض بلغة عربية سلسة وواضحة.

يجب أن تعيد النتيجة حصرياً بصيغة كائن JSON صالح (JSON Object) بدون أي نصوص أو رموز إضافية خارج الـ JSON، بحيث يحتوي على المفتاحين التاليين:
1. "analysis_report": نص يشرح النتائج، المصطلحات، والوصايا والترتيبات الوقائية بأسلوب تنسيق Markdown.
2. "chart_data": مصفوفة (Array) من الكائنات، يمثل كل كائن فحصاً طبياً بالشكل التالي:
   [
     {"test_name": "اسم الفحص", "value": 12.5, "status": "Normal أو High أو Low", "unit": "وحدة القياس"}
   ]
ملاحظة هامة: يجب أن تكون قيم "value" أرقاماً حقيقية (float/int) لغرض الرسم البياني. وإذا تعذر استخراج رقم دقيق لأحد الفحوصات، ضع القيمة 0.
"""

    try:
        if is_image:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[content_part, prompt]
            )
        else:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"{prompt}\n\nنص التقرير الطبي المستخرج:\n{content_part}"
            )
            
        text_response = response.text.strip()
        if text_response.startswith("```json"):
            text_response = text_response[7:-3].strip()
        elif text_response.startswith("```"):
            text_response = text_response[3:-3].strip()
            
        return json.loads(text_response)
    except Exception as e:
        st.error(f"حدث خطأ أثناء المعالجة بواسطة الذكاء الاصطناعي: {e}")
        return None

# دالة استخراج النص من الـ PDF
def extract_text_from_pdf(pdf_file):
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
    except Exception as e:
        st.error(f"خطأ في قراءة ملف الـ PDF: {e}")
    return text

# واجهة التطبيق الجانبية
with st.sidebar:
    st.markdown("### 🧬 لوحة التحكم")
    uploaded_file = st.file_uploader("اختر ملف التقرير (PDF أو صورة JPG/PNG)", type=["pdf", "jpg", "jpeg", "png"])
    st.markdown("---")
    st.info("💡 **إبراء ذمة طبية:** هذا النظام أداة تثقيفية وتحليلية مساعدة، ولا يغني أبداً عن الاستشارة التشخيصية للطبيب المختص.")

# الشاشة الرئيسية والمنطق البرمجي
if uploaded_file is not None:
    file_extension = uploaded_file.name.split('.')[-1].lower()
    
    if file_extension in ['jpg', 'jpeg', 'png']:
        try:
            image = Image.open(uploaded_file)
            st.image(image, caption="الصورة المرفوعة للتقرير", use_container_width=True)
            
            if client and st.button("🚀 ابدأ التحليل الذكي للصورة", type="primary"):
                with st.spinner("🤖 جاري تحليل الصورة مباشرة عبر نموذج Gemini الذكي..."):
                    result = analyze_medical_content(image, is_image=True)
                    if result:
                        st.session_state['analysis_result'] = result
        except Exception as e:
            st.error(f"خطأ في فتح ملف الصورة: {e}")
            
    elif file_extension == 'pdf':
        with st.spinner("🔄 جاري قراءة ملف الـ PDF..."):
            raw_text = extract_text_from_pdf(uploaded_file)
            
        if not raw_text.strip():
            st.warning("⚠️ لم يتم العثور على نص واضح داخل ملف الـ PDF المرفوع.")
        else:
            with st.expander("📄 معاينة النص الخام المستخرج من الـ PDF"):
                st.text(raw_text)
                
            if client and st.button("🚀 ابدأ التحليل الذكي للتقرير", type="primary"):
                with st.spinner("🤖 جاري معالجة البيانات وتحليل الفحوصات عبر نموذج Gemini..."):
                    result = analyze_medical_content(raw_text, is_image=False)
                    if result:
                        st.session_state['analysis_result'] = result

    # عرض النتائج إذا كانت مخزنة بالـ Session
    if 'analysis_result' in st.session_state:
        res = st.session_state['analysis_result']
        
        # عرض التقرير النصي المبسط
        st.markdown("### 📋 التقرير التحليلي والتثقيفي")
        st.markdown(f"<div class='custom-card'>{res.get('analysis_report', '')}</div>", unsafe_allow_html=True)
        
        # عرض الرسم البياني التفاعلي بـ Plotly
        chart_data = res.get('chart_data', [])
        if chart_data:
            st.markdown("### 📊 لوحة المؤشرات البيانية الفورية")
            
            names = [item.get('test_name') for item in chart_data]
            values = [item.get('value') for item in chart_data]
            statuses = [item.get('status', 'Normal') for item in chart_data]
            units = [item.get('unit', '') for item in chart_data]
            
            colors = []
            for s in statuses:
                s_lower = str(s).lower()
                if 'high' in s_lower or 'مرتفع' in s_lower:
                    colors.append('#ef4444')
                elif 'low' in s_lower or 'منخفض' in s_lower:
                    colors.append('#f97316')
                else:
                    colors.append('#3b82f6')
            
            fig = go.Figure(data=[
                go.Bar(
                    x=names,
                    y=values,
                    marker_color=colors,
                    text=[f"{v} {u} ({s})" for v, u, s in zip(values, units, statuses)],
                    textposition='auto'
                )
            ])
            
            fig.update_layout(
                title="مستويات الفحوصات الطبية مقارنة بالمدى الطبيعي",
                xaxis_title="اسم الفحص",
                yaxis_title="القيمة الرقمية",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white')
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        st.markdown("""
            <div class='warning-box'>
            <b>⚠️ إخطار طبي قانوني:</b> التقرير أعلاه تم توليده آلياً بواسطة خوارزميات الذكاء الاصطناعي لأغراض التثقيف والتوضيح المبدئي فقط، ولا يُعتبر تشخيصاً طبياً نهائياً. يرجى مراجعة الطبيب المختص لمناقشة النتائج.
            </div>
        """, unsafe_allow_html=True)
else:
    st.markdown("""
        <div class='custom-card' style='text-align: center; padding: 40px;'>
        <h3>👋 أهلاً بك في نظام Asinu AI</h3>
        <p>لبدء العمل، قم برفع ملف التقرير الطبي (PDF أو صورة فحص) من القائمة الجانبية اليسرى.</p>
        </div>
    """, unsafe_allow_html=True)
