import sqlite3
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "qiyas.db")
QUESTIONS_FILE = os.path.join(BASE_DIR, "questions.json")
FOUNDATION_FILE = os.path.join(BASE_DIR, "foundation_data.json")

def init_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. جدول الأسئلة الرئيسي
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY,
        section TEXT NOT NULL,
        section_ar TEXT NOT NULL,
        topic TEXT NOT NULL,
        question TEXT NOT NULL,
        diagram_svg TEXT,
        image_url TEXT,
        options_json TEXT NOT NULL,
        correct_index INTEGER NOT NULL,
        explanation TEXT,
        speed_rule TEXT,
        difficulty TEXT DEFAULT 'متوسط',
        level INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. جدول مسارات التأسيس
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS foundation_levels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        section TEXT NOT NULL,
        level_number INTEGER NOT NULL,
        title TEXT NOT NULL,
        badge TEXT,
        topics_json TEXT NOT NULL
    );
    """)

    # 3. جدول جلسات الاختبار والنتائج
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS test_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_type TEXT NOT NULL, -- 'custom', 'simulator', 'mistakes'
        total_questions INTEGER NOT NULL,
        correct_answers INTEGER NOT NULL,
        percentage REAL NOT NULL,
        rating TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 4. جدول سجل الأخطاء للتكرار المتباعد
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mistakes_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER NOT NULL,
        user_choice INTEGER,
        resolved INTEGER DEFAULT 0,
        logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (question_id) REFERENCES questions(id)
    );
    """)

    conn.commit()

    # تحميل ورفع الأسئلة إلى قاعدة البيانات
    if os.path.exists(QUESTIONS_FILE):
        with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
            questions = json.load(f)

        cursor.execute("DELETE FROM questions;")
        for q in questions:
            cursor.execute("""
            INSERT INTO questions (
                id, section, section_ar, topic, question, diagram_svg, image_url,
                options_json, correct_index, explanation, speed_rule, difficulty, level
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                q.get('id'),
                q.get('section', 'quantitative'),
                q.get('section_ar', 'القسم الكمي'),
                q.get('topic', 'عام'),
                q.get('question', ''),
                q.get('diagram_svg'),
                q.get('image'),
                json.dumps(q.get('options', []), ensure_ascii=False),
                q.get('correct_index', 0),
                q.get('explanation', ''),
                q.get('speed_rule', ''),
                q.get('difficulty', 'متوسط'),
                q.get('level', 1)
            ))
        print(f"Successfully uploaded {len(questions)} questions to questions table in qiyas.db")

    # تحميل ورفع بيانات التأسيس
    if os.path.exists(FOUNDATION_FILE):
        with open(FOUNDATION_FILE, 'r', encoding='utf-8') as f:
            foundation = json.load(f)

        cursor.execute("DELETE FROM foundation_levels;")
        count_levels = 0
        for sec_key, sec_data in foundation.items():
            for lvl in sec_data.get('levels', []):
                cursor.execute("""
                INSERT INTO foundation_levels (
                    section, level_number, title, badge, topics_json
                ) VALUES (?, ?, ?, ?, ?)
                """, (
                    sec_key,
                    lvl.get('level'),
                    lvl.get('title'),
                    lvl.get('badge'),
                    json.dumps(lvl.get('topics', []), ensure_ascii=False)
                ))
                count_levels += 1
        print(f"Successfully uploaded {count_levels} foundation levels to foundation_levels table in qiyas.db")

    conn.commit()
    conn.close()
    print("Database qiyas.db initialized and indexed successfully 100%!")

if __name__ == '__main__':
    init_database()
