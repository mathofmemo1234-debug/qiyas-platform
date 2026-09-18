import os
import cv2
import json
import pymupdf
import numpy as np

pdf_path = "exam126.pdf"
output_dir = "questions_images"
os.makedirs(output_dir, exist_ok=True)

doc = pymupdf.open(pdf_path)
total_pages = len(doc)
print(f"جاري معالجة وقص {total_pages} سؤالاً وإزالة الشعارات والحقوق بالكامل...")

questions_list = []

for idx, page in enumerate(doc):
    # تصوير بدقة عالية
    pix = page.get_pixmap(matrix=pymupdf.Matrix(2.0, 2.0))
    temp_img_path = "temp_clean.png"
    pix.save(temp_img_path)
    
    img = cv2.imread(temp_img_path)
    h, w, _ = img.shape

    # 1. استبعاد الترويسة العلوية واستبعاد الـ 20% السفلية تماماً (مكان الكتب وشريط الحقوق)
    top_limit = int(h * 0.10)
    bottom_limit = int(h * 0.80)  # يقطع تماماً صورة الكتب وشريط الحقوق
    left_limit = int(w * 0.04)
    right_limit = int(w * 0.96)

    cropped = img[top_limit:bottom_limit, left_limit:right_limit]

    # 2. فلترة أي علامات مائية رمادية أو حمراء/بنية باهتة
    gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 215, 255, cv2.THRESH_BINARY)
    
    # تبييض الخلفية الفاتحة تماماً
    clean_area = cropped.copy()
    clean_area[mask == 255] = [255, 255, 255]

    # 3. إحاطة السؤال بالضبط وإلغاء المساحات البيضاء الزائدة
    inv = cv2.bitwise_not(mask)
    points = cv2.findNonZero(inv)
    if points is not None:
        x, y, bw, bh = cv2.boundingRect(points)
        pad = 20
        fx = max(0, x - pad)
        fy = max(0, y - pad)
        fw = min(clean_area.shape[1] - fx, bw + (pad * 2))
        fh = min(clean_area.shape[0] - fy, bh + (pad * 2))
        final_img = clean_area[fy:fy+fh, fx:fx+fw]
    else:
        final_img = clean_area

    img_filename = f"q_{idx+1}.png"
    save_path = os.path.join(output_dir, img_filename)
    cv2.imwrite(save_path, final_img)

    questions_list.append({
        "id": idx + 1,
        "image": f"{output_dir}/{img_filename}"
    })
    print(f"تم تنظيف وقص السؤال {idx+1}/{total_pages}")

if os.path.exists("temp_clean.png"):
    os.remove("temp_clean.png")

with open("scanned_data.json", "w", encoding="utf-8") as f:
    json.dump(questions_list, f, ensure_ascii=False, indent=2)

print("\nاكتمل التنظيف وإزالة الكتب وشريط الحقوق بنجاح تام!")
