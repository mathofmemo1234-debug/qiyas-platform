import json
import os
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('questions.json', 'r', encoding='utf-8') as f:
    questions = json.load(f)

print(f"Loaded {len(questions)} questions.")

conn = sqlite3.connect('qiyas.db')
cur = conn.cursor()

# Ensure image and image_url columns exist
cur.execute("PRAGMA table_info(questions)")
cols = [c[1] for c in cur.fetchall()]
if 'image' not in cols:
    cur.execute("ALTER TABLE questions ADD COLUMN image TEXT")
if 'image_url' not in cols:
    cur.execute("ALTER TABLE questions ADD COLUMN image_url TEXT")

for q in questions:
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
        q['id'],
        q.get('section', 'quantitative'),
        q.get('section_ar', 'القسم الكمي'),
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
print("Synchronized all questions to qiyas.db SQLite successfully.")

# Check DB rows
cur.execute("SELECT COUNT(*), COUNT(image), COUNT(image_url) FROM questions")
row = cur.fetchone()
print(f"DB stats: Total={row[0]}, with image={row[1]}, with image_url={row[2]}")

conn.close()
