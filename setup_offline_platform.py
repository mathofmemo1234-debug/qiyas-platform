import os
import glob
import json
import shutil
import cv2
import pymupdf
import numpy as np

# 1. البحث عن الملف
pdf_files = glob.glob("*.pdf")
if not pdf_files:
    print("خطأ: لم يتم العثور على أي ملف PDF!")
    exit(1)

pdf_path = "exam126.pdf" if "exam126.pdf" in pdf_files else pdf_files[0]
print(f"📄 معالجة الملف: {pdf_path}")

# 2. إعادة تهيئة مجلد الصور
output_dir = "questions_images"
if os.path.exists(output_dir):
    shutil.rmtree(output_dir)
os.makedirs(output_dir, exist_ok=True)

doc = pymupdf.open(pdf_path)
total_pages = len(doc)
total_questions = total_pages - 1
print(f"📖 جاري قص وتجهيز {total_questions} سؤالاً (بدءاً من صفحة 2 وتجاوز الغلاف)...")

questions_list = []

for idx in range(1, total_pages):
    page = doc[idx]
    q_num = idx
    
    # تصوير بدقة عالية
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

    # تنويه منهجي منظم لكل مسألة
    questions_list.append({
        "id": q_num,
        "image": f"{output_dir}/{img_filename}",
        "correct_index": 0, # سيتمكن الطالب من اختياره وحفظه
        "hint": "💡 استراتيجية الحل السريع: ابدأ بتبسيط الأرقام الكبيرة، أو جرب الخيارات بدءاً من القيم المتوسطة لتوفير الوقت."
    })
    print(f"✅ تم تجهيز السؤال {q_num}/{total_questions}")

with open("scanned_data.json", "w", encoding="utf-8") as f:
    json.dump(questions_list, f, ensure_ascii=False, indent=2)

print("\n🚀 تم استخراج جميع الأسئلة وتجهيز بنك البيانات بنجاح 100%!")
