import os
import glob
import json
import time
import shutil
import cv2
import pymupdf
import numpy as np
from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))

pdf_files = glob.glob("*.pdf")
if not pdf_files:
    print("خطأ: لم يتم العثور على أي ملف PDF!")
    exit(1)

pdf_path = "exam126.pdf" if "exam126.pdf" in pdf_files else pdf_files[0]
print(f"📄 الملف المعتمد: {pdf_path}")

output_dir = "questions_images"
if os.path.exists(output_dir):
    shutil.rmtree(output_dir)
os.makedirs(output_dir, exist_ok=True)

doc = pymupdf.open(pdf_path)
total_pages = len(doc)
total_questions = total_pages - 1
print(f"📖 جاري قص {total_questions} سؤالاً وحفظ الصور محلياً...")

for idx in range(1, total_pages):
    page = doc[idx]
    q_num = idx
    
    pix = page.get_pixmap(matrix=pymupdf.Matrix(2.0, 2.0))
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    
    if pix.n >= 4:
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    else:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    h, w, _ = img.shape
    top_limit = int(h * 0.10)
    bottom_limit = int(h * 0.90)
    left_limit = int(w * 0.03)
    right_limit = int(w * 0.97)

    content_area = img[top_limit:bottom_limit, left_limit:right_limit]
    gray = cv2.cvtColor(content_area, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 245, 255, cv2.THRESH_BINARY_INV)
    points = cv2.findNonZero(thresh)

    if points is not None:
        x, y, bw, bh = cv2.boundingRect(points)
        pad = 20
        final_x = max(0, left_limit + x - pad)
        final_y = max(0, top_limit + y - pad)
        final_w = min(w - final_x, bw + (pad * 2))
        final_h = min(h - final_y, bh + (pad * 2))
        final_crop = img[final_y:final_y+final_h, final_x:final_x+final_w]
    else:
        final_crop = content_area

    img_filename = f"q_{q_num}.png"
    save_path = os.path.join(output_dir, img_filename)
    cv2.imwrite(save_path, final_crop)

print("🖼️ تم قص وحفظ جميع صور الأسئلة بنجاح تام.")

# رفع الملف واستخراج الحلول والتنويهات مع نظام إعادة المحاولة
print("🧠 جاري رفع وتحليل الاختبار لتوليد التنويهات والشروحات التفصيلية...")
uploaded_pdf = client.files.upload(file=pdf_path)

prompt = f"""
أنت معلم خبير أول في اختبارات القدرات العامة (قياس).
الملف المرفق يحتوي على اختبار يبدأ من الصفحة 2 حتى الصفحة {total_pages}.

المطلوب:
حل جميع الأسئلة بالترتيب من السؤال 1 (في صفحة 2) حتى السؤال {total_questions} (في صفحة {total_pages})، وإرجاع مصفوفة JSON تحتوي على:
- "id": رقم السؤال التسلسلي (1, 2, ..., {total_questions})
- "correct_index": مؤشر الإجابة الصحيحة (0 للخيار أ، 1 للخيار ب، 2 للخيار ج، 3 للخيار د).
- "explanation": تنويه وشرح رياضي تفصيلي وسلس يوضح فكرة الحل السريع والخطوات بالأرقام والرموز العربية.

المخرج: مصفوفة JSON صالحة فقط [ ... ] دون أي نصوص إضافية.
"""

models_queue = ["gemini-2.5-flash", "gemini-3.6-flash"]
ai_solutions = []

for model_name in models_queue:
    print(f"⏳ محاولة التحليل عبر النموذج: {model_name}...")
    success = False
    for attempt in range(1, 5):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[uploaded_pdf, prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            ai_solutions = json.loads(response.text)
            print("✅ تم تحليل جميع الأسئلة وتوليد التنويهات بنجاح!")
            success = True
            break
        except (ClientError, ServerError) as e:
            wait_time = attempt * 4
            print(f"⚠️ حدوث ضغط مؤقت على الحصة ({model_name}) - إعادة المحاولة {attempt}/4 بعد {wait_time} ثوانٍ...")
            time.sleep(wait_time)
        except Exception as e:
            print(f"⚠️ خطأ غير متوقع: {e}")
            break
    if success:
        break

sol_map = {item["id"]: item for item in ai_solutions}

final_dataset = []
for q_id in range(1, total_questions + 1):
    sol = sol_map.get(q_id, {})
    final_dataset.append({
        "id": q_id,
        "image": f"{output_dir}/q_{q_id}.png",
        "correct_index": sol.get("correct_index", 0),
        "explanation": sol.get("explanation", "استخدم التبسيط الرياضي أو التجريب السريع للخيارات للوصول للحل الصحيح.")
    })

with open("scanned_data.json", "w", encoding="utf-8") as f:
    json.dump(final_dataset, f, ensure_ascii=False, indent=2)

print("\n🚀 اكتمل تجهيز بنك الأسئلة بالكامل!")
