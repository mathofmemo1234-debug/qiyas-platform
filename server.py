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
SCANNED_FILE = os.path.join(BASE_DIR, "scanned_data.json")
PDFS_FILE = os.path.join(BASE_DIR, "downloadable_pdfs.json")
DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)
DB_PATH = os.path.join(BASE_DIR, "qiyas.db")
IMAGES_DIR = os.path.join(BASE_DIR, "questions_images")
os.makedirs(IMAGES_DIR, exist_ok=True)

def save_base64_image(b64_str, prefix="q_img"):
    if not b64_str or not isinstance(b64_str, str) or len(b64_str) < 50:
        return ""
    ext = '.png'
    if ',' in b64_str:
        header, raw_b64 = b64_str.split(',', 1)
        if 'jpeg' in header or 'jpg' in header:
            ext = '.jpg'
        elif 'webp' in header:
            ext = '.webp'
    else:
        raw_b64 = b64_str
    try:
        img_bytes = base64.b64decode(raw_b64)
        filename = f"{prefix}_{int(time.time()*1000)}{ext}"
        save_path = os.path.join(IMAGES_DIR, filename)
        with open(save_path, "wb") as img_file:
            img_file.write(img_bytes)
        return f"questions_images/{filename}"
    except Exception as err:
        print(f"Error saving image: {err}")
        return ""

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

        elif parsed.path == '/api/scanned-questions':
            try:
                if os.path.exists(SCANNED_FILE):
                    with open(SCANNED_FILE, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                else:
                    data = []
                self.send_json_response(data)
            except Exception as e:
                self.send_json_response({"error": str(e)}, 500)
            return

        elif parsed.path == '/api/downloadable-pdfs':
            try:
                if os.path.exists(PDFS_FILE):
                    with open(PDFS_FILE, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                else:
                    data = []
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

        elif parsed.path == '/api/save-foundation':
            try:
                with open(FOUNDATION_FILE, 'w', encoding='utf-8') as f:
                    json.dump(body, f, ensure_ascii=False, indent=2)
                self.send_json_response({"success": True, "message": "تم حفظ بيانات التأسيس بنجاح"})
            except Exception as e:
                self.send_json_response({"error": str(e)}, 500)
            return

        elif parsed.path == '/api/save-scanned-question':
            try:
                if os.path.exists(SCANNED_FILE):
                    with open(SCANNED_FILE, 'r', encoding='utf-8') as f:
                        scanned = json.load(f)
                else:
                    scanned = []
                
                new_id = max([q.get('id', 0) for q in scanned] + [0]) + 1
                body['id'] = new_id
                
                raw_img = body.pop('image_base64', None) or body.pop('image_data', None) or body.pop('dataUrl', None) or body.get('image', '')
                if raw_img and (',' in str(raw_img) or len(str(raw_img)) > 100):
                    img_path = save_base64_image(raw_img, prefix=f"q_scan_{new_id}")
                    if img_path:
                        body['image'] = img_path
                        body['image_url'] = img_path
                
                body['verified'] = False
                if 'level' not in body:
                    body['level'] = 3 if body.get('has_visual') else 1
                if 'tracks' not in body:
                    body['tracks'] = ["foundation", "custom-test", "simulator"]
                if 'created_at' not in body:
                    body['created_at'] = time.strftime("%Y-%m-%d %H:%M")
                    
                scanned.insert(0, body)
                with open(SCANNED_FILE, 'w', encoding='utf-8') as f:
                    json.dump(scanned, f, ensure_ascii=False, indent=2)
                self.send_json_response({"success": True, "question": body})
            except Exception as e:
                self.send_json_response({"error": str(e)}, 500)
            return

        elif parsed.path == '/api/approve-scanned-question':
            try:
                q_id = body.get('id')
                with open(SCANNED_FILE, 'r', encoding='utf-8') as f:
                    scanned = json.load(f)
                
                target_idx = -1
                target_q = None
                for idx, sq in enumerate(scanned):
                    if sq.get('id') == q_id:
                        target_idx = idx
                        target_q = sq
                        break
                
                if not target_q:
                    self.send_json_response({"error": "المسألة غير موجودة في قائمة المسح"}, 404)
                    return
                
                for k in ['level', 'difficulty', 'section', 'section_ar', 'topic', 'question', 'options', 'correct_index', 'explanation', 'speed_rule', 'tracks']:
                    if k in body:
                        target_q[k] = body[k]
                
                target_q['verified'] = True
                
                with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
                    questions = json.load(f)
                
                new_q_id = max([q.get('id', 0) for q in questions] + [0]) + 1
                approved_q = dict(target_q)
                approved_q['id'] = new_q_id
                
                # Check if image needs saving from base64
                if approved_q.get('image', '').startswith('data:image'):
                    img_path = save_base64_image(approved_q['image'], prefix=f"q_{new_q_id}")
                    if img_path:
                        approved_q['image'] = img_path
                        approved_q['image_url'] = img_path
                        
                questions.append(approved_q)
                with open(QUESTIONS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(questions, f, ensure_ascii=False, indent=2)
                
                sync_question_to_db(approved_q)
                
                scanned[target_idx]['verified'] = True
                with open(SCANNED_FILE, 'w', encoding='utf-8') as f:
                    json.dump(scanned, f, ensure_ascii=False, indent=2)
                
                self.send_json_response({
                    "success": True, 
                    "question": approved_q, 
                    "message": "تم اعتماد السؤال بنجاح في جميع المسارات"
                })
            except Exception as e:
                self.send_json_response({"error": str(e)}, 500)
            return

        elif parsed.path == '/api/delete-scanned-question':
            try:
                q_id = body.get('id')
                with open(SCANNED_FILE, 'r', encoding='utf-8') as f:
                    scanned = json.load(f)
                scanned = [q for q in scanned if q.get('id') != q_id]
                with open(SCANNED_FILE, 'w', encoding='utf-8') as f:
                    json.dump(scanned, f, ensure_ascii=False, indent=2)
                self.send_json_response({"success": True})
            except Exception as e:
                self.send_json_response({"error": str(e)}, 500)
            return

        elif parsed.path == '/api/upload-downloadable-pdf':
            try:
                title = body.get('title', 'ملف تجميعات جديد')
                desc = body.get('description', '')
                cat = body.get('category', 'تجميعات حديثة')
                sec = body.get('section', 'all')
                filename = body.get('filename', f"doc_{int(time.time())}.pdf")
                file_url = body.get('file_url', '')
                
                pdf_b64 = body.pop('pdf_base64', None) or body.pop('file_data', None)
                if pdf_b64 and len(pdf_b64) > 50:
                    if ',' in pdf_b64:
                        pdf_b64 = pdf_b64.split(',', 1)[1]
                    pdf_bytes = base64.b64decode(pdf_b64)
                    save_name = f"pdf_{int(time.time())}_{filename}"
                    save_path = os.path.join(DOWNLOADS_DIR, save_name)
                    with open(save_path, "wb") as pf:
                        pf.write(pdf_bytes)
                    file_url = f"downloads/{save_name}"
                    size_str = f"{round(len(pdf_bytes)/(1024*1024), 2)} MB"
                else:
                    size_str = body.get('size', '1.5 MB')
                    
                if os.path.exists(PDFS_FILE):
                    with open(PDFS_FILE, 'r', encoding='utf-8') as f:
                        pdfs = json.load(f)
                else:
                    pdfs = []
                    
                new_id = max([p.get('id', 0) for p in pdfs] + [0]) + 1
                pdf_entry = {
                    "id": new_id,
                    "title": title,
                    "description": desc,
                    "category": cat,
                    "section": sec,
                    "file_url": file_url,
                    "filename": filename,
                    "size": size_str,
                    "pages": body.get('pages', 20),
                    "date_added": time.strftime("%Y-%m-%d"),
                    "downloads_count": 0
                }
                pdfs.insert(0, pdf_entry)
                with open(PDFS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(pdfs, f, ensure_ascii=False, indent=2)
                self.send_json_response({"success": True, "pdf": pdf_entry})
            except Exception as e:
                self.send_json_response({"error": str(e)}, 500)
            return

        elif parsed.path == '/api/delete-downloadable-pdf':
            try:
                pdf_id = body.get('id')
                with open(PDFS_FILE, 'r', encoding='utf-8') as f:
                    pdfs = json.load(f)
                pdfs = [p for p in pdfs if p.get('id') != pdf_id]
                with open(PDFS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(pdfs, f, ensure_ascii=False, indent=2)
                self.send_json_response({"success": True})
            except Exception as e:
                self.send_json_response({"error": str(e)}, 500)
            return

        elif parsed.path == '/api/delete-question':
            try:
                q_id = body.get('id')
                with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
                    questions = json.load(f)
                questions = [q for q in questions if q.get('id') != q_id]
                with open(QUESTIONS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(questions, f, ensure_ascii=False, indent=2)
                try:
                    conn = sqlite3.connect(DB_PATH)
                    cur = conn.cursor()
                    cur.execute("DELETE FROM questions WHERE id = ?", (q_id,))
                    conn.commit()
                    conn.close()
                except Exception:
                    pass
                self.send_json_response({"success": True})
            except Exception as e:
                self.send_json_response({"error": str(e)}, 500)
            return

        elif parsed.path == '/api/update-question':
            try:
                q_id = body.get('id')
                with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
                    questions = json.load(f)
                
                raw_img = body.pop('image_base64', None) or body.pop('image_data', None) or body.pop('dataUrl', None)
                if not raw_img and body.get('image', '').startswith('data:image'):
                    raw_img = body.get('image')
                if raw_img and len(raw_img) > 50:
                    saved_path = save_base64_image(raw_img, prefix=f"q_upd_{q_id}")
                    if saved_path:
                        body['image'] = saved_path
                        body['image_url'] = saved_path
                        
                for idx, q in enumerate(questions):
                    if q.get('id') == q_id:
                        questions[idx] = body
                        break
                with open(QUESTIONS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(questions, f, ensure_ascii=False, indent=2)
                sync_question_to_db(body)
                self.send_json_response({"success": True, "question": body})
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
