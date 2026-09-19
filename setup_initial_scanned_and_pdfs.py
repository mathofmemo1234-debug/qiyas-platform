import json
import os
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# Copy exam126.pdf if present to downloads/
src_pdf = os.path.join(BASE_DIR, "exam126.pdf")
dst_pdf = os.path.join(DOWNLOADS_DIR, "exam126.pdf")
if os.path.exists(src_pdf) and not os.path.exists(dst_pdf):
    shutil.copy2(src_pdf, dst_pdf)

# Initial Downloadable PDFs
pdfs_data = [
    {
        "id": 1,
        "title": "تجميعات الـ 120 نموذج الشاملة (كمي ولفظي)",
        "description": "المرجع الذهبي الشامل لنماذج اختبار القدرات المحوسب، يحتوي على أسئلة محلولة ونماذج اختبار واقعية.",
        "category": "تجميعات حديثة",
        "section": "all",
        "file_url": "downloads/exam126.pdf",
        "filename": "exam126.pdf",
        "size": "7.05 MB",
        "pages": 126,
        "date_added": "2026-09-19",
        "downloads_count": 342
    },
    {
        "id": 2,
        "title": "مذكرة القوانين الذهبية للتأسيس الكمي السريع",
        "description": "ملف مكثف يجمع كافة قوانين الجبر والهندسة والمقارنات والمتتابعات مع طرق الحل السريع في ثوانٍ.",
        "category": "تأسيس كمي",
        "section": "quantitative",
        "file_url": "downloads/exam126.pdf",
        "filename": "qiyas_quant_golden_rules.pdf",
        "size": "2.4 MB",
        "pages": 48,
        "date_added": "2026-09-18",
        "downloads_count": 519
    },
    {
        "id": 3,
        "title": "حقيبة التناظر اللفظي واستيعاب المقروء النخبوية",
        "description": "شرح وتحليل لأكثر من 1000 علاقة تناظر لفظي متكررة وفنيات التعامل مع قطع استيعاب المقروء الطويلة.",
        "category": "تأسيس لفظي",
        "section": "verbal",
        "file_url": "downloads/exam126.pdf",
        "filename": "qiyas_verbal_elite.pdf",
        "size": "3.1 MB",
        "pages": 64,
        "date_added": "2026-09-17",
        "downloads_count": 427
    }
]

pdf_json_path = os.path.join(BASE_DIR, "downloadable_pdfs.json")
with open(pdf_json_path, "w", encoding="utf-8") as f:
    json.dump(pdfs_data, f, ensure_ascii=False, indent=2)
print("downloadable_pdfs.json created successfully.")

# Initial Scanned Questions Queue with complete metadata
scanned_items = [
    {
        "id": 1,
        "image": "questions_images/q_1.png",
        "question": "إذا كان 3س + 6 = 21 ، فما قيمة س؟",
        "options": ["5", "7", "3", "9"],
        "correct_index": 0,
        "explanation": "خطوات الحل الرياضي النموذجي:\n1. بطرح 6 من الطرفين: 3س = 15.\n2. بالقسمة على 3: س = 5.\n💡 الحل السريع: بتجريب الخيار (أ): 3(5) + 6 = 15 + 6 = 21 صحيحة فوراً.",
        "speed_rule": "التجريب بالخيارات المتوسطة لحسم قيمة المجهول في ثوانٍ.",
        "level": 1,
        "section": "quantitative",
        "section_ar": "القسم الكمي",
        "topic": "معادلات وجبر",
        "difficulty": "سهل",
        "has_visual": True,
        "tracks": ["foundation", "custom-test", "simulator"],
        "verified": False,
        "created_at": "2026-09-19 19:30"
    },
    {
        "id": 2,
        "image": "questions_images/q_2.png",
        "question": "مربع طول ضلعه 10 سم رسمت بداخله دائرة تمس أضلاعه، احسب مساحة الجزء المظلل المحصور بينهما (ط = 3.14):",
        "options": ["21.5 سم²", "25 سم²", "31.4 سم²", "78.5 سم²"],
        "correct_index": 0,
        "explanation": "مساحة المربع = 10 × 10 = 100 سم².\nنصف قطر الدائرة = 5 سم، مساحة الدائرة = ط نق² = 3.14 × 25 = 78.5 سم².\nمساحة الجزء المظلل = مساحة المربع - مساحة الدائرة = 100 - 78.5 = 21.5 سم².",
        "speed_rule": "مساحة المنطقة المظللة = مساحة الشكل الخارجي ناقص الأشكال البيضاء الداخلية.",
        "level": 3,
        "section": "quantitative",
        "section_ar": "القسم الكمي",
        "topic": "هندسة ومساحات مظللة",
        "difficulty": "متوسط",
        "has_visual": True,
        "tracks": ["foundation", "custom-test", "simulator"],
        "verified": False,
        "created_at": "2026-09-19 19:45"
    },
    {
        "id": 3,
        "image": "questions_images/q_3.png",
        "question": "رئة : تنفس",
        "options": ["عين : إبصار", "يد : كتابة", "قلب : دواء", "قدم : حذاء"],
        "correct_index": 0,
        "explanation": "العلاقة في رأس المسألة هي علاقة (عضو ووظيفته الأساسية التلقائية الحيوية): فالرئة وظيفتها التنفس، وبالمثل العين وظيفتها الأساسية الإبصار.\nبينما اليد وظيفتها ليست محصورة في الكتابة، والقدم تلبس الحذاء وليست وظيفتها.",
        "speed_rule": "صياغة جملة قياسية: (الأول وظيفته الحيوية الأساسية الثاني).",
        "level": 1,
        "section": "verbal",
        "section_ar": "القسم اللفظي",
        "topic": "تناظر لفظي",
        "difficulty": "سهل",
        "has_visual": True,
        "tracks": ["foundation", "custom-test", "simulator"],
        "verified": False,
        "created_at": "2026-09-19 20:10"
    }
]

scanned_json_path = os.path.join(BASE_DIR, "scanned_data.json")
with open(scanned_json_path, "w", encoding="utf-8") as f:
    json.dump(scanned_items, f, ensure_ascii=False, indent=2)
print("scanned_data.json updated successfully with recent scanned items.")
