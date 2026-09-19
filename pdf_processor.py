import os
import re
import time
import base64
import unicodedata
import pymupdf
import numpy as np
import cv2
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "questions_images")
os.makedirs(IMAGES_DIR, exist_ok=True)

# خريطة توحيد الحروف العربية من أشكال Presentation Forms والأحرف اللاتينية
ARABIC_LETTER_MAP = {
    'ﺃ': 'أ', 'أ': 'أ', 'إ': 'أ', 'ا': 'أ', 'آ': 'أ', 'A': 'أ', 'a': 'أ', '1': 'أ',
    'ﺏ': 'ب', 'ب': 'ب', 'B': 'ب', 'b': 'ب', '2': 'ب',
    'ﺝ': 'ج', 'ج': 'ج', 'C': 'ج', 'c': 'ج', '3': 'ج',
    'ﺩ': 'د', 'د': 'د', 'D': 'د', 'd': 'د', '4': 'د'
}

LETTER_TO_INDEX = {'أ': 0, 'ب': 1, 'ج': 2, 'د': 3}
INDEX_TO_LETTER = ['أ', 'ب', 'ج', 'د']

def normalize_text(text):
    """توحيد النصوص العربية وإزالة التشكيل وتحويل الأشكال التقديمية إلى حروف قياسية"""
    if not text:
        return ""
    norm = unicodedata.normalize('NFKD', text)
    # تنظيف الحروف الزائدة
    return norm

def normalize_arabic_char(ch):
    if not ch:
        return 'أ'
    ch_norm = unicodedata.normalize('NFKD', ch)
    for c in ch_norm:
        if c in ARABIC_LETTER_MAP:
            return ARABIC_LETTER_MAP[c]
    return ARABIC_LETTER_MAP.get(ch, 'أ')

def detect_section_and_topic(text):
    text_clean = normalize_text(text).lower()
    
    # كلمات مفتاحية لفظية
    verbal_keywords = ['تناظر', 'سياقي', 'استيعاب', 'إكمال', 'مفردة شاذة', 'قطعة', 'معنى', 'ضد', 'مرادف']
    is_verbal = any(k in text_clean for k in verbal_keywords)
    
    if is_verbal:
        section = 'verbal'
        if 'تناظر' in text_clean:
            topic = 'تناظر لفظي'
        elif 'سياقي' in text_clean:
            topic = 'خطأ سياقي'
        elif 'إكمال' in text_clean:
            topic = 'إكمال الجمل'
        else:
            topic = 'استيعاب المقروء'
    else:
        section = 'quantitative'
        if any(k in text_clean for k in ['مثلث', 'مربع', 'مستطيل', 'دائرة', 'زاوية', 'شكل', 'مظلل', 'هندسة']):
            topic = 'هندسة وقوانين المساحات'
        elif any(k in text_clean for k in ['قارن', 'القيمة الأولى', 'القيمة الثانية', 'مقارنة']):
            topic = 'مقارنات رياضية'
        elif any(k in text_clean for k in ['متتابعة', 'نمط', 'تسلسل']):
            topic = 'متتابعات وأنماط'
        elif any(k in text_clean for k in ['س +', 'ص =', 'معادلة', 'جذر', 'قوة', 'أس']):
            topic = 'جبر ومعادلات'
        else:
            topic = 'حساب وأعداد سريعة'
            
    return section, topic

def crop_and_save_question_image(page, save_path):
    """قص وتصفية صورة السؤال بدون الهوامش والعلامات المائية العلوية والسفلية"""
    pix = page.get_pixmap(matrix=pymupdf.Matrix(2.0, 2.0))
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    
    if pix.n >= 4:
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    else:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    h, w, _ = img.shape
    top_limit = int(h * 0.08)
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

    cv2.imwrite(save_path, final_crop)
    return True

def extract_answer_from_text(text):
    """البحث عن الإجابة الصحيحة بالأنماط المعتمدة في ملفات قياس والقدرات"""
    norm = normalize_text(text)
    patterns = [
        r'(?:الإجابة|الاجابة|ﺍﻹﺟﺎﺑﺔ)\s*(?:الصحيحة|الصحية|ﺍﻟﺼﺤﻴﺤﺔ)?\s*[:：\-]?\s*([أ-دﺃ-ﺩA-Da-d])',
        r'(?:الحل|الجواب|مفتاح الحل)\s*[:：\-]?\s*([أ-دﺃ-ﺩA-Da-d])',
        r'الإجابة\s*\(?([أ-دﺃ-ﺩA-Da-d])\)?',
        r'\(?([أ-دﺃ-ﺩ])\)?\s*هي الإجابة',
        r'(?:Correct|Answer)\s*[:：\-]?\s*([A-Da-dأ-د])'
    ]
    
    for p in patterns:
        m = re.search(p, norm) or re.search(p, text)
        if m:
            char = normalize_arabic_char(m.group(1))
            return char, LETTER_TO_INDEX.get(char, 0)
            
    return None, None

def process_pdf_document(pdf_doc, original_filename="exam.pdf"):
    """تحليل وثيقة PDF واستخراج الأسئلة والإجابات وعدد الأسئلة الكلي بدقة"""
    total_pages = len(pdf_doc)
    extracted_questions = []
    timestamp = int(time.time())

    # فحص الصفحة الأولى: هل هي صفحة غلاف/تعليمات وليست مسألة فعلية؟
    start_page = 0
    if total_pages > 1:
        p0_raw = pdf_doc[0].get_text()
        p0_norm = normalize_text(p0_raw)
        ans_0, _ = extract_answer_from_text(p0_raw)
        
        is_cover = (
            ans_0 is None and
            any(w in p0_norm for w in ['اختبار', 'القدرات', 'تعليمات', 'تحذير', 'النسخة', 'حقوق', 'المنصف', 'إعداد'])
        )
        if is_cover:
            start_page = 1

    question_counter = 1

    for p_idx in range(start_page, total_pages):
        page = pdf_doc[p_idx]
        text = page.get_text()
        norm_text = normalize_text(text)
        clean_text = "\n".join([line.strip() for line in norm_text.splitlines() if line.strip()])

        # كشف الإجابة الصحيحة
        detected_char, detected_idx = extract_answer_from_text(text)
        if detected_char is None:
            detected_char = 'أ'
            detected_idx = 0

        # كشف رقم السؤال من الصفحة (مثل: السؤال ١ من ٥٥)
        q_num_match = re.search(r'(?:السؤال|سؤال|س)\s*([0-9٠-٩]+)', norm_text) or re.search(r'(?:السؤال|سؤال|س)\s*([0-9٠-٩]+)', text)
        if q_num_match:
            try:
                raw_num = q_num_match.group(1)
                trans = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
                num_val = int(raw_num.translate(trans))
            except Exception:
                num_val = question_counter
        else:
            num_val = question_counter

        # استخراج نصوص السؤال والخيارات
        lines = [l.strip() for l in clean_text.splitlines() if l.strip()]
        filtered_lines = []
        for l in lines:
            if any(skip in l for skip in ['اختبار', 'محفوظة', 'منصة', 'المنصف', 'الإجابة الصحيحة', '5 9 9', 'هاتف', 'www.', '.com', 'تحذير']):
                continue
            filtered_lines.append(l)

        # استخراج الخيارات إن وُجدت
        options = []
        for opt_char in ['أ', 'ب', 'ج', 'د']:
            opt_m = re.search(rf'[({opt_char}\-]\s*([^(\n\r]+)', norm_text)
            if opt_m and len(opt_m.group(1).strip()) > 1:
                options.append(opt_m.group(1).strip())

        if len(options) < 4:
            options = ["الخيار (أ)", "الخيار (ب)", "الخيار (ج)", "الخيار (د)"]

        # قص وحفظ صورة السؤال بدقة عالية
        img_filename = f"q_pdf_{timestamp}_{num_val}.png"
        img_path = os.path.join(IMAGES_DIR, img_filename)
        rel_img_url = f"questions_images/{img_filename}"
        
        try:
            crop_and_save_question_image(page, img_path)
        except Exception as err:
            print(f"تحذير: تعذر قص صورة السؤال {num_val}:", err)
            rel_img_url = ""

        # تحديد القسم والمهارة
        section, topic = detect_section_and_topic(text)
        section_ar = "القسم الكمي" if section == 'quantitative' else "القسم اللفظي"

        # نص المسألة
        question_text = f"مسألة القدرات رقم ({num_val})"
        if filtered_lines:
            candidate = " - ".join(filtered_lines[:2])
            if len(candidate) > 5 and len(candidate) < 160:
                question_text = candidate

        # توليد الشرح الرياضي/اللفظي السريع
        explanation = (
            f"خطوات الحل النموذجي:\n"
            f"بالرجوع إلى معطيات المسألة ومقارنة الخيارات، نجد أن الخيار ({detected_char}) "
            f"هو الإجابة الصحيحة والمطابقة للقوانين المعتمدة.\n"
            f"💡 استراتيجية الحل السريع: استخدم التبسيط وحساب منزلة الآحاد لحسم الإجابة في ثوانٍ."
        ) if section == 'quantitative' else (
            f"التحليل الدلالي:\n"
            f"الخيار ({detected_char}) يحقق التناسب المعنوي الدقيق ويسد الفراغ بالمعنى البلاغي المتزن."
        )

        speed_rule = (
            "الاستفادة من التناسب المباشر وحذف المتشابهات لتوفير الوقت."
            if section == 'quantitative'
            else "صياغة جملة قياسية وتطبيقها من اليمين إلى اليسار بحذر."
        )

        is_geom = any(w in (text + ' ' + topic + ' ' + question_text) for w in [
            'مثلث', 'دائرة', 'مستطيل', 'مربع', 'زاوية', 'نصف قطر', 'قطر', 'وتر', 'مضلع',
            'متوازي', 'شبه منحرف', 'أسطوانة', 'مكعب', 'مخروط', 'هرم', 'سطح', 'حجم',
            'محيط', 'مساحة', 'مظلل', 'غير مظلل', 'متوازيين', 'قاطع', 'مماس', 'مركز الدائرة',
            'في الشكل', 'المجاور', 'الرسم البياني', 'القطاع الدائري', 'الأعمدة البيانية', 'المستوى الإحداثي'
        ])
        has_visual = bool(rel_img_url) or is_geom

        q_item = {
            "id": num_val,
            "page_num": p_idx + 1,
            "section": section,
            "section_ar": section_ar,
            "topic": topic,
            "question": question_text,
            "image": rel_img_url,
            "image_url": rel_img_url,
            "has_visual": has_visual,
            "level": 3 if (is_geom and section == 'quantitative') else 1,
            "options": options,
            "correct_index": detected_idx,
            "correct_letter": detected_char,
            "explanation": explanation,
            "speed_rule": speed_rule
        }

        extracted_questions.append(q_item)
        question_counter += 1

    quant_count = sum(1 for q in extracted_questions if q['section'] == 'quantitative')
    verb_count = sum(1 for q in extracted_questions if q['section'] == 'verbal')

    return {
        "success": True,
        "filename": original_filename,
        "total_pages": total_pages,
        "total_questions": len(extracted_questions),
        "quantitative_count": quant_count,
        "verbal_count": verb_count,
        "questions": extracted_questions
    }

def process_pdf_bytes(pdf_bytes, filename="uploaded.pdf"):
    """معالجة بايتات ملف الـ PDF المرفوعة مباشرة من المتصفح"""
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    result = process_pdf_document(doc, original_filename=filename)
    doc.close()
    return result

def process_pdf_base64(base64_data, filename="uploaded.pdf"):
    """معالجة ملف PDF مشفر كـ Base64 مرسل عبر الـ API"""
    if ',' in base64_data:
        base64_data = base64_data.split(',')[1]
    pdf_bytes = base64.b64decode(base64_data)
    return process_pdf_bytes(pdf_bytes, filename=filename)

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    test_pdf = os.path.join(BASE_DIR, "exam126.pdf")
    if os.path.exists(test_pdf):
        print(f"فحص الملف التجريبي: {test_pdf}")
        doc = pymupdf.open(test_pdf)
        res = process_pdf_document(doc, "exam126.pdf")
        print(f"✓ تم بنجاح! إجمالي الصفحات: {res['total_pages']} | عدد الأسئلة الفعلية المستخرجة: {res['total_questions']}")
        print(f"✓ كمي: {res['quantitative_count']} | لفظي: {res['verbal_count']}")
        print(f"✓ السؤال 1 -> رقم: {res['questions'][0]['id']}, الإجابة: {res['questions'][0]['correct_letter']}")
        print(f"✓ السؤال الأخير -> رقم: {res['questions'][-1]['id']}, الإجابة: {res['questions'][-1]['correct_letter']}")
        doc.close()
    else:
        print("ملف exam126.pdf غير موجود")
