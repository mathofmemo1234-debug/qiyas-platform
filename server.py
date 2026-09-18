import os
import sys
import json
import re
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import urllib.parse

PORT = 8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_FILE = os.path.join(BASE_DIR, "questions.json")
FOUNDATION_FILE = os.path.join(BASE_DIR, "foundation_data.json")

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
                
                if not body.get('explanation') or len(body.get('explanation').strip()) < 5:
                    body['explanation'] = self.generate_smart_explanation(body)
                if not body.get('speed_rule'):
                    body['speed_rule'] = self.generate_speed_rule(body)
                
                questions.append(body)
                with open(QUESTIONS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(questions, f, ensure_ascii=False, indent=2)
                
                self.send_json_response({"success": True, "question": body})
            except Exception as e:
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
                    questions.append(item)
                
                with open(QUESTIONS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(questions, f, ensure_ascii=False, indent=2)
                
                self.send_json_response({"success": True, "added_count": len(new_items)})
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
