import json
import urllib.request
import time
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def to_firestore_value(val):
    if isinstance(val, bool):
        return {'booleanValue': val}
    elif isinstance(val, int):
        return {'integerValue': str(val)}
    elif isinstance(val, float):
        return {'doubleValue': val}
    elif isinstance(val, str):
        return {'stringValue': val}
    elif isinstance(val, list):
        return {'arrayValue': {'values': [to_firestore_value(v) for v in val]}}
    elif isinstance(val, dict):
        return {'mapValue': {'fields': {k: to_firestore_value(v) for k, v in val.items()}}}
    elif val is None:
        return {'nullValue': None}
    return {'stringValue': str(val)}

with open('questions.json', 'r', encoding='utf-8') as f:
    questions = json.load(f)

API_KEY = "AIzaSyAFBq8PJuSeAh8yYEE3_0b9ceDHUT-e8SI"
PROJECT_ID = "qiyas-training-3dcf3"
BASE_URL = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/questions"

print(f"🚀 بدء رفع {len(questions)} سؤالاً مدققاً إلى Cloud Firestore...")

success_count = 0
for idx, q in enumerate(questions, 1):
    doc_id = str(q['id'])
    doc_fields = {k: to_firestore_value(v) for k, v in q.items()}
    # add server timestamp in milliseconds
    doc_fields['uploadedAt'] = {'integerValue': str(int(time.time() * 1000))}
    
    url = f"{BASE_URL}/{doc_id}?key={API_KEY}"
    payload = json.dumps({'fields': doc_fields}).encode('utf-8')
    req = urllib.request.Request(url, data=payload, method='PATCH', headers={'Content-Type': 'application/json'})
    
    try:
        res = urllib.request.urlopen(req, timeout=10)
        if res.status == 200:
            success_count += 1
            if idx % 10 == 0 or idx == len(questions):
                print(f"✓ تم رفع {idx}/{len(questions)} مسألة...")
    except Exception as e:
        print(f"✕ خطأ في رفع السؤال {doc_id}: {e}")
    time.sleep(0.05)

print(f"\n🎉 اكتمل الرفع بنجاح! تم حفظ {success_count} من {len(questions)} سؤالاً في Cloud Firestore.")
