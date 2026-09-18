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
print(f"جاري إزالة صورة الكتب والعلامات المائية نهائياً من {total_pages} سؤال...")

questions_list = []

for idx, page in enumerate(doc):
    # تصوير الصفحة بدقة مضاعفة
    pix = page.get_pixmap(matrix=pymupdf.Matrix(2.0, 2.0))
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    
    if pix.n >= 4:
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    else:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    h, w, _ = img.shape

    # 1. مسح ترويسة الصفحة العلوية (أعلى 10%)
    img[0:int(h * 0.10), :] = [255, 255, 255]

    # 2. مسح شريط الحقوق السفلي (أسفل 15%)
    img[int(h * 0.85):h, :] = [255, 255, 255]

    # 3. مسح صورة الكتب والرموز المائية (المنطقة السفلية الجانبية من 65% إلى 85% من الارتفاع)
    # مسح الجانب الأيسر بالكامل في النصف السفلي
    img[int(h * 0.60):int(h * 0.86), 0:int(w * 0.38)] = [255, 255, 255]
    # مسح الجانب الأيمن بالكامل في النصف السفلي
    img[int(h * 0.60):int(h * 0.86), int(w * 0.62):w] = [255, 255, 255]

    # 4. فلترة وإزالة أي بقايا لونية خضراء أو برتقالية أو بنية خاصة بالشعار
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    # ماسك للألوان غير السوداء/الرمادية الداكنة في الجزء السفلي
    lower_colors = np.array([0, 25, 50])
    upper_colors = np.array([180, 255, 255])
    color_mask = cv2.inRange(hsv, lower_colors, upper_colors)
    
    # تطبيق الفلترة على النصف السفلي فقط لحماية رسومات السؤال
    img_lower = img[int(h * 0.50):h, :]
    mask_lower = color_mask[int(h * 0.50):h, :]
    img_lower[mask_lower > 0] = [255, 255, 255]
    img[int(h * 0.50):h, :] = img_lower

    # 5. استخراج الصندوق المحيط بالسؤال والخيارات فقط
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 245, 255, cv2.THRESH_BINARY_INV)
    points = cv2.findNonZero(thresh)
    
    if points is not None:
        x, y, bw, bh = cv2.boundingRect(points)
        pad = 20
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
    print(f"تم تنظيف السؤال {idx+1}/{total_pages}")

with open("scanned_data.json", "w", encoding="utf-8") as f:
    json.dump(questions_list, f, ensure_ascii=False, indent=2)

print("\nتمت الإزالة بنجاح تام!")
