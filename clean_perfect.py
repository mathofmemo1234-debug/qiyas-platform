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
print(f"جاري مسح وإزالة الكتب وشريط الحقوق والأرقام المائية من {total_pages} صفحة...")

questions_list = []

for idx, page in enumerate(doc):
    pix = page.get_pixmap(matrix=pymupdf.Matrix(2.0, 2.0))
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    
    if pix.n >= 4:
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    else:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    h, w, _ = img.shape

    # 1. تبييض الترويسة العلوية بالكامل (أعلى 9%)
    img[0:int(h * 0.09), :] = [255, 255, 255]

    # 2. تبييض شريط الحقوق السفلي (أسفل 14%)
    img[int(h * 0.86):h, :] = [255, 255, 255]

    # 3. تبييض الزوايا السفلية (المكان الثابت لصورة الكتب)
    lower_y = int(h * 0.68)
    img[lower_y:h, 0:int(w * 0.32)] = [255, 255, 255]        # الزاوية السفلية اليسرى
    img[lower_y:h, int(w * 0.68):w] = [255, 255, 255]        # الزاوية السفلية اليمنى

    # 4. عزل وإزالة أي نصوص حمراء/بنية باقية (شريط elmonsf والرقم المائي 8898)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower_red1 = np.array([0, 30, 30])
    upper_red1 = np.array([18, 255, 255])
    lower_red2 = np.array([160, 30, 30])
    upper_red2 = np.array([180, 255, 255])
    mask_red = cv2.inRange(hsv, lower_red1, upper_red1) | cv2.inRange(hsv, lower_red2, upper_red2)
    img[mask_red > 0] = [255, 255, 255]

    # 5. قص حدود السؤال الصافية تلقائياً
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
    points = cv2.findNonZero(thresh)
    
    if points is not None:
        x, y, bw, bh = cv2.boundingRect(points)
        pad = 25
        fx = max(0, x - pad)
        fy = max(0, y - pad)
        fw = min(w - fx, bw + (pad * 2))
        fh = min(h - fy, bh + (pad * 2))
        final_img = img[fy:fy+fh, fx:fx+fw]
    else:
        final_img = img

    img_filename = f"q_{idx+1}.png"
    save_path = os.path.join(output_dir, img_filename)
    cv2.imwrite(save_path, final_img)

    questions_list.append({
        "id": idx + 1,
        "image": f"{output_dir}/{img_filename}"
    })
    print(f"تم تنظيف السؤال {idx+1}/{total_pages}")

with open("scanned_data.json", "w", encoding="utf-8") as f:
    json.dump(questions_list, f, ensure_ascii=False, indent=2)

print("\nاكتمل التنظيف النهائي وإزالة الشعارين بالكامل!")
