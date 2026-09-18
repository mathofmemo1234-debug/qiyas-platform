import os
import glob
import json
import time
import cv2
import pymupdf
import numpy as np
from PIL import Image
from google import genai
from google.genai import types

API_KEY = os.environ.get("GEMINI_API_KEY", "")
client = genai.Client(api_key=API_KEY)

pdf_files = glob.glob("*.pdf")
if not pdf_files:
    print("خطأ: لم يتم العثور على أي ملف PDF!")
    exit(1)

pdf_path = "exam126.pdf" if "exam126.pdf" in pdf_files else pdf_files[0]
output_dir = "questions_images"
os.makedirs(output_dir, exist_ok=True)

doc = pymupdf.open(pdf_path)
total_pages = len(doc)
test_limit = min(5, total_pages)
print(f"📖 بدء تجربة أول {test_limit - 1} أسئلة مع التنويهات والشروحات الخاصة بكل مسألة...")

final_dataset = []

for idx in range(1, test_limit):
    q_num = idx
    img_filename = f"q_{q_num}.png"
    save_path = os.path.join(output_dir, img_filename)

    # قص الصورة محلياً
    page = doc[idx]
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
        fx = max(0, left_limit + x - pad)
        fy = max(0, top_limit + y - pad)
        fw = min(w - fx, bw + (pad * 2))
        fh = min(h - fy, bh + (pad * 2))
        final_crop = img[fy:fy+fh, fx:fx+fw]
    else:
        final_crop = content_area
    cv2.imwrite(save_path, final_crop)

    print(f"🧠 جاري تحليل السؤال التجريبي {q_num} وتوليد الشرح...")
    
    correct_idx = 0
    explanation = "تعذر جلب الشرح لهذا السؤال."
    is_verified = False

    pil_img = Image.open(save_path)

    for attempt in range(1, 4):
        try:
            prompt = """
            أنت معلم رياضيات خبير في اختبارات القدرات العامة (قياس).
            قم بتحليل المسألة في الصورة المرفقة بدقة تامة:
            1. حل المسألة خطوة بخطوة وتحديد الخيار الصحيح (أ=0, ب=1, ج=2, د=3).
            2. اكتب تنويهاً وشرحاً تفصيلياً فريداً ومخصصاً لهذا السؤال بالذات (وليس شرحاً عاماً) يوضح استراتيجية الحل السريع والخطوات الرياضية بالأرقام العربية والرموز (مثل $س^٢$ أو $\\frac{١}{٢}$).
            
            أرجع النتيجة بصيغة JSON حصراً:
            {
              "correct_index": 0,
              "explanation": "شرح وطريقة حل مفصلة ودقيقة مخصصة لهذا السؤال بالذات"
            }
            """
            
            ai_res = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[pil_img, prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            parsed = json.loads(ai_res.text)
            correct_idx = parsed.get("correct_index", 0)
            explanation = parsed.get("explanation", explanation)
            is_verified = True
            print(f"✅ تم بنجاح تحليل السؤال {q_num}")
            break
        except Exception as e:
            print(f"⚠️ خطأ في المحاولة {attempt} للسؤال {q_num}: {e}")
            time.sleep(3)

    final_dataset.append({
        "id": q_num,
        "image": f"{output_dir}/{img_filename}",
        "correct_index": correct_idx,
        "explanation": explanation,
        "verified": is_verified
    })
    
    with open("scanned_data.json", "w", encoding="utf-8") as f:
        json.dump(final_dataset, f, ensure_ascii=False, indent=2)

    time.sleep(2)

print("\n🚀 اكتملت تجربة الـ 4 أسئلة بنجاح تام!")
