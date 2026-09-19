import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('questions.json', 'r', encoding='utf-8') as f:
    questions = json.load(f)

with open('audit_report_full.txt', 'w', encoding='utf-8') as out:
    for q in questions[:55]:
        qid = q['id']
        topic = q.get('topic', '')
        text = q.get('question', '')
        opts = q.get('options', [])
        c_idx = q.get('correct_index', 0)
        expl = q.get('explanation', '')
        level = q.get('level', 1)
        c_val = opts[c_idx] if 0 <= c_idx < len(opts) else 'INDEX_OUT_OF_BOUNDS'
        img_file = f"questions_images/q_{qid}.png"
        img_exists = os.path.exists(img_file)
        
        out.write(f"ID: {qid} | Topic: {topic} | Level: {level} | Correct: [{c_idx}] {c_val} | Img: {img_exists}\n")
        out.write(f"Question: {text}\n")
        out.write(f"Options: {opts}\n")
        out.write(f"Explanation: {expl}\n")
        out.write("=" * 70 + "\n")

print("Audit report written to audit_report_full.txt")
