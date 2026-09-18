import os
import time
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))
pdf_file_name = "exam126.pdf"

print("1. جاري رفع ملف الاختبار ومعالجته...")
uploaded_file = client.files.upload(file=pdf_file_name)

prompt = """
أنت خبير أول في رقمنة بنوك أسئلة اختبار القدرات العامة (قياس) في المملكة العربية السعودية.

المهمة:
استخرج كافة الأسئلة والمسائل بدقة 100% وحولها إلى مصفوفة JSON مع الالتزام بالمعايير التالية:

1. **الرياضيات والأرقام والاتجاه:**
   - كتابة الأرقام حصراً بالأرقام العربية المشرقية (٠، ١، ٢، ٣، ٤، ٥، ٦، ٧، ٨، ٩).
   - كتابة المسائل والجذور والكسور بصيغة LaTeX داخل علامات $...$ لضمان قراءتها الصحيحة، مثلاً: $(\\frac{١}{٣})^{-٥}$ أو $٢ \\times ٨ \\times ٢ = \\dots$ أو $\\sqrt{١٠}$.
   - الرموز المجهولة باللغة العربية (س، ص، ع، ك).

2. **الرسومات الهندسية الملونة الجذابة (SVG):**
   - لكل سؤال يحتوي على شكل هندسي (مربعات، مثلثات، دوائر، زوايا، مساحات مظللة):
     قم بإنشاء كود SVG متكامل داخل `diagram_svg` مع:
     * خلفية شفافة ومقاس `viewBox="0 0 360 200"`.
     * تلوين احترافي جذاب: الأجزاء المظللة بتدرجات الأزرق الفيروزي (`#06b6d4` أو `#38bdf8`) والحدود واضحة بلون أبيض أو رمادي فاتح (`#cbd5e1` بسماكة 2.5).
     * وضع التسميات العربية (أ، ب، ج، د) والقياسات باللون الأبيض الواضح داخل الشكل.
   - إذا لم يوجد رسم في السؤال، اجعل قيمته `null`.

3. **تجاهل العلامات المائية:** تجاهل التام للشعارات وأرقام الهواتف المتكررة.

4. **حقول الـ JSON المطلوبة لكل كائن:**
   - "id": رقم تسلسلي
   - "section": "quantitative" أو "verbal"
   - "topic": مهارة المسألة (مثل: "هندسة", "جبر", "حساب", "مقارنات")
   - "question": نص السؤال كاملاً
   - "diagram_svg": كود الـ SVG الملون أو null
   - "options": مصفوفة الخيارات الأربعة
   - "correct_index": مؤشر الإجابة الصحيحة (0، 1، 2، 3)
   - "explanation": طريقة الحل السريع والذهني

المخرج: مصفوفة JSON فقط [ ... ] دون أي نصوص خارجها.
"""

models_to_try = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-3.6-flash"]

for model_name in models_to_try:
    print(f"2. محاولة الاستخراج باستخدام النموذج: {model_name}...")
    success = False
    for attempt in range(1, 4):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[uploaded_file, prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            with open("questions.json", "w", encoding="utf-8") as f:
                f.write(response.text)
            print("3. تم الاستخراج بنجاح تام! تم إنشاء questions.json.")
            success = True
            break
        except Exception as e:
            print(f"   - المحاولة {attempt} فشلت بسبب الضغط ({e.message if hasattr(e, 'message') else '503 Server Busy'}). جاري الانتظار 5 ثوانٍ...")
            time.sleep(5)
    if success:
        break
