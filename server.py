import os
import sys
import json
import re
import base64
import time
import sqlite3
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import urllib.parse
import pdf_processor

PORT = 8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_FILE = os.path.join(BASE_DIR, "questions.json")
FOUNDATION_FILE = os.path.join(BASE_DIR, "foundation_data.json")
DB_PATH = os.path.join(BASE_DIR, "qiyas.db")
IMAGES_DIR = os.path.join(BASE_DIR, "questions_images")
os.makedirs(IMAGES_DIR, exist_ok=True)

GEOM_KEYWORDS = [
    'مثلث', 'دائرة', 'مستطيل', 'مربع', 'زاوية', 'نصف قطر', 'قطر', 'وتر', 'مضلع', 
    'متوازي', 'شبه منحرف', 'أسطوانة', 'مكعب', 'مخروط', 'هرم', 'سطح', 'حجم', 
    'محيط', 'مساحة', 'مظلل', 'غير مظلل', 'متوازيين', 'قاطع', 'مماس', 'مركز الدائرة',
    'في الشكل', 'المجاور', 'الرسم البياني', 'القطاع الدائري', 'الأعمدة البيانية', 'المستوى الإحداثي', 'انعكاس', 'تناظر'
]

def sync_question_to_db(q):
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(questions)")
        cols = [c[1] for c in cur.fetchall()]
        if 'image' not in cols:
            cur.execute("ALTER TABLE questions ADD COLUMN image TEXT")
        if 'image_url' not in cols:
            cur.execute("ALTER TABLE questions ADD COLUMN image_url TEXT")
        
        cur.execute("""
        INSERT INTO questions (id, section, section_ar, topic, question, diagram_svg, options_json, correct_index, explanation, speed_rule, difficulty, level, image, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            section=excluded.section,
            section_ar=excluded.section_ar,
            topic=excluded.topic,
            question=excluded.question,
            diagram_svg=excluded.diagram_svg,
            options_json=excluded.options_json,
            correct_index=excluded.correct_index,
            explanation=excluded.explanation,
            speed_rule=excluded.speed_rule,
            level=excluded.level,
            image=excluded.image,
            image_url=excluded.image_url
        """, (
            q.get('id'),
            q.get('section', 'quantitative'),
            q.get('section_ar', 'القسم الكمي' if q.get('section') == 'quantitative' else 'القسم اللفظي'),
            q.get('topic', ''),
            q.get('question', ''),
            q.get('diagram_svg', ''),
            json.dumps(q.get('options', []), ensure_ascii=False),
            q.get('correct_index', 0),
            q.get('explanation', ''),
            q.get('speed_rule', ''),
            q.get('difficulty', 'متوسط'),
            q.get('level', 1),
            q.get('image', ''),
            q.get('image_url', '')
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print("SQLite sync error:", e)

class QiyasHandler(SimpleHTTPRequestHandler):
    def send_json_response(self, data, status=200):
        encoded = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(encoded)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(encoded)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        
        if parsed.path == '/api/stats':
            try:
                with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
                    questions = json.load(f)
                quant = sum(1 for q in questions if q.get('section') == 'quantitative')
                verb = sum(1 for q in questions if q.get('section') == 'verbal')
                topics = {}
                for q in questions:
                    t = q.get('topic', 'عام')
                    topics[t] = topics.get(t, 0) + 1
                self.send_json_response({
                    "total": len(questions),
                    "quantitative": quant,
                    "verbal": verb,
                    "topics": topics
                })
            except Exception as e:
                self.send_json_response({"error": str(e)}, 500)
            return

        elif parsed.path == '/api/questions':
            try:
                with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
                    questions = json.load(f)
                self.send_json_response(questions)
            except Exception as e:
                self.send_json_response({"error": str(e)}, 500)
            return

        elif parsed.path == '/api/foundation':
            try:
                with open(FOUNDATION_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.send_json_response(data)
            except Exception as e:
                self.send_json_response({"error": str(e)}, 500)
            return

        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        length = int(self.headers.get('content-length', 0))
        raw_body = self.rfile.read(length).decode('utf-8') if length > 0 else "{}"
        
        try:
            body = json.loads(raw_body)
        except Exception:
            body = {}

        if parsed.path == '/api/save-question':
            try:
                with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
                    questions = json.load(f)
                new_id = max([q.get('id', 0) for q in questions] + [0]) + 1
                body['id'] = new_id

                # 1. Image processing & permanent disk preservation
                img_b64 = body.pop('image_base64', None) or body.pop('image_data', None) or body.pop('dataUrl', None)
                if img_b64 and isinstance(img_b64, str) and len(img_b64) > 50:
                    ext = '.png'
                    if ',' in img_b64:
                        header, raw_b64 = img_b64.split(',', 1)
                        if 'jpeg' in header or 'jpg' in header:
                            ext = '.jpg'
                        elif 'webp' in header:
                            ext = '.webp'
                    else:
                        raw_b64 = img_b64

                    try:
                        img_bytes = base64.b64decode(raw_b64)
                        filename = f"q_ocr_{new_id}_{int(time.time())}{ext}"
                        save_path = os.path.join(IMAGES_DIR, filename)
                        with open(save_path, "wb") as img_file:
                            img_file.write(img_bytes)
                        rel_path = f"questions_images/{filename}"
                        body['image'] = rel_path
                        body['image_url'] = rel_path
                    except Exception as img_err:
                        print("Failed to save OCR image to disk:", img_err)

                # Ensure image / image_url symmetry
                if body.get('image') and not body.get('image_url'):
                    body['image_url'] = body['image']
                elif body.get('image_url') and not body.get('image'):
                    body['image'] = body['image_url']

                # 2. Geometric & Visual Detection
                combined_txt = (body.get('question', '') + ' ' + body.get('topic', '')).lower()
                is_geom = any(kw in combined_txt for kw in GEOM_KEYWORDS)
                body['has_visual'] = is_geom or bool(body.get('image')) or bool(body.get('diagram_svg'))

                # Auto-classify to Foundation Level 3 (Geometry) if quantitative geometric
                if is_geom and body.get('section') == 'quantitative':
                    if not body.get('level') or body.get('level') == 1:
                        body['level'] = 3
                
                if not body.get('explanation') or len(body.get('explanation').strip()) < 5:
                    body['explanation'] = self.generate_smart_explanation(body)
                if not body.get('speed_rule'):
                    body['speed_rule'] = self.generate_speed_rule(body)
                
                questions.append(body)
                with open(QUESTIONS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(questions, f, ensure_ascii=False, indent=2)
                
                # Sync to SQLite
                sync_question_to_db(body)

                self.send_json_response({
                    "success": True, 
                    "question": body,
                    "has_visual": body.get('has_visual', False),
                    "image": body.get('image', ''),
                    "image_url": body.get('image_url', '')
                })
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.send_json_response({"error": str(e)}, 500)
            return

        elif parsed.path == '/api/generate-explanation':
            try:
                explanation = self.generate_smart_explanation(body)
                speed_rule = self.generate_speed_rule(body)
                self.send_json_response({
                    "explanation": explanation,
                    "speed_rule": speed_rule
                })
            except Exception as e:
                self.send_json_response({"error": str(e)}, 500)
            return

        elif parsed.path == '/api/upload-bulk':
            try:
                new_items = body.get('questions', [])
                with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
                    questions = json.load(f)
                
                start_id = max([q.get('id', 0) for q in questions] + [0]) + 1
                for i, item in enumerate(new_items):
                    item['id'] = start_id + i
                    if not item.get('explanation'):
                        item['explanation'] = self.generate_smart_explanation(item)
                    if not item.get('speed_rule'):
                        item['speed_rule'] = self.generate_speed_rule(item)
                    if item.get('image') and not item.get('image_url'):
                        item['image_url'] = item['image']
                    elif item.get('image_url') and not item.get('image'):
                        item['image'] = item['image_url']
                    sync_question_to_db(item)
                    questions.append(item)
                
                with open(QUESTIONS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(questions, f, ensure_ascii=False, indent=2)
                
                self.send_json_response({"success": True, "added_count": len(new_items)})
            except Exception as e:
                self.send_json_response({"error": str(e)}, 500)
            return

        elif parsed.path == '/api/parse-pdf':
            try:
                b64_data = body.get('pdf_base64') or body.get('file_data') or ''
                filename = body.get('filename', 'uploaded_exam.pdf')
                if not b64_data:
                    self.send_json_response({"error": "لم يتم إرسال بيانات ملف الـ PDF"}, 400)
                    return
                result = pdf_processor.process_pdf_base64(b64_data, filename=filename)
                self.send_json_response(result)
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.send_json_response({"error": f"فشل تحليل ملف الـ PDF: {str(e)}"}, 500)
            return

        elif parsed.path == '/api/save-pdf-questions':
            try:
                new_items = body.get('questions', [])
                with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
                    questions = json.load(f)
                
                start_id = max([q.get('id', 0) for q in questions] + [0]) + 1
                for i, item in enumerate(new_items):
                    item['id'] = start_id + i
                    if not item.get('explanation'):
                        item['explanation'] = self.generate_smart_explanation(item)
                    if not item.get('speed_rule'):
                        item['speed_rule'] = self.generate_speed_rule(item)
                    if item.get('image') and not item.get('image_url'):
                        item['image_url'] = item['image']
                    elif item.get('image_url') and not item.get('image'):
                        item['image'] = item['image_url']
                    
                    combined = (item.get('question', '') + ' ' + item.get('topic', '')).lower()
                    is_geom = any(w in combined for w in GEOM_KEYWORDS)
                    item['has_visual'] = is_geom or bool(item.get('image'))
                    if is_geom and item.get('section') == 'quantitative':
                        item['level'] = 3

                    questions.append(item)
                    sync_question_to_db(item)
                
                with open(QUESTIONS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(questions, f, ensure_ascii=False, indent=2)
                
                self.send_json_response({
                    "success": True,
                    "added_count": len(new_items),
                    "total_questions": len(questions)
                })
            except Exception as e:
                self.send_json_response({"error": str(e)}, 500)
            return

        self.send_response(404)
        self.end_headers()

    def generate_smart_explanation(self, q):
        correct_idx = q.get('correct_index', 0)
        options = q.get('options', ['أ', 'ب', 'ج', 'د'])
        correct_opt = options[correct_idx] if correct_idx < len(options) else ""
        topic = q.get('topic', '')
        section = q.get('section', 'quantitative')
        letters = ['أ', 'ب', 'ج', 'د']
        correct_letter = letters[correct_idx] if correct_idx < 4 else 'أ'
        
        if section == 'verbal':
            if 'تناظر' in topic:
                return f"تحليل التناظر اللفظي:\nالعلاقة في رأس المسألة تقوم على الربط الدلالي الدقيق. بالنظر في البدائل المتاحة، نجد أن الخيار ({correct_letter}) الذي يمثل ({correct_opt}) يطابق ذات العلاقة في نفس الاتجاه من اليمين إلى اليسار، بينما بقية الخيارات تمثل علاقات مغايرة (مكانية أو سببية غير متناظرة)."
            elif 'سياقي' in topic:
                return f"التحليل السياقي المنهجي:\nعند تدبر العبارة، نجد أن سياق المعنى يتطلب مفردة منسجمة إيجابياً. إن وجود الكلمة ({correct_opt}) في الخيار ({correct_letter}) يكسر اتساق الجملة ويجعل المعنى متناقضاً، وكان الصواب استبدالها بضدها ليستقيم المعنى البلاغي."
            elif 'إكمال' in topic:
                return f"التحليل الدلالي والتوافقي:\nالكلمات المختارة في ({correct_opt}) في الخيار ({correct_letter}) تتكامل مع مفاتيح النص اللغوية، حيث تحقق الترابط النحوي والدلالي السليم وتسد الفراغ بما يوافق مراد المعنى."
            else:
                return f"الشرح اللغوي المعتمد:\nوفقاً لقواعد الفهم والبيان واستقراء النصوص، فإن الخيار ({correct_letter}) المتمثل في ({correct_opt}) هو الإجابة الدقيقة والصائبة."
        else:
            return f"خطوات الحل الرياضي النموذجي:\n١. تحليل معطيات المسألة وتحديد المطلوب بوضوح.\n٢. تطبيق القانون الرياضي السريع وتفادي العمليات الحسابية الطويلة.\n٣. بعد التبسيط واختصار القيم المشتركة، نجد أن الناتج يساوي ({correct_opt})، وهو ما يطابق الخيار ({correct_letter}).\n💡 نصيحة للحل السريع: استفد من التناسب المباشر وملاحظة منزلة الآحاد لحسم الإجابة في ثوانٍ."

    def generate_speed_rule(self, q):
        topic = q.get('topic', '')
        section = q.get('section', 'quantitative')
        if section == 'verbal':
            if 'تناظر' in topic:
                return "صياغة جملة قياسية وتطبيقها من اليمين لليسار بحذر."
            elif 'سياقي' in topic:
                return "الكلمة الخاطئة غالباً تكون ضد المعنى الحقيقي المقصود."
            elif 'إكمال' in topic:
                return "جرب الفراغ الثاني أولاً لاستبعاد معظم المشتتات بسرعة."
            else:
                return "العودة المباشرة إلى النص عند الإجابة دون الاعتماد على الذاكرة المجردة."
        else:
            if 'هندسة' in topic:
                return "استخدام ثلاثيات فيثاغورس الذهبية والرسم التوضيحي السريع."
            elif 'مقارنات' in topic:
                return "حذف المتشابهات من الطرفين واختبار الصفر والكسور الموجبة والسالبة."
            elif 'متتابعات' in topic:
                return "حساب الفروق بين الحدود واكتشاف النمط التراكمي أو التضاعفي."
            else:
                return "الاعتماد على التقريب الذكي والتجريب بدءاً من الخيارات المتوسطة (ب، ج)."

def main():
    handler_class = partial(QiyasHandler, directory=BASE_DIR)
    server = ThreadingHTTPServer(('', PORT), handler_class)
    print(f"خادم منصة قياس يعمل بنجاح على http://localhost:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()
