# -*- coding: utf-8 -*-
import json
import os
import sqlite3
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_FILE = os.path.join(BASE_DIR, "questions.json")
DB_PATH = os.path.join(BASE_DIR, "qiyas.db")

# Load existing questions if available
existing_questions = []
if os.path.exists(QUESTIONS_FILE):
    try:
        with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
            existing_questions = json.load(f)
    except Exception as e:
        print("Error loading existing questions:", e)

print(f"Loaded {len(existing_questions)} existing questions.")

# Standardize existing questions
for q in existing_questions:
    if 'track' not in q:
        sec = q.get('section', 'quantitative')
        if sec in ['verbal']:
            q['track'] = 'qudrat'
        elif sec in ['quantitative']:
            q['track'] = 'qudrat'
        elif 'tahsili' in sec:
            q['track'] = 'tahsili'
        elif 'step' in sec:
            q['track'] = 'step'
        elif 'aramco' in sec:
            q['track'] = 'aramco'
        elif 'cognitive' in sec:
            q['track'] = 'cognitive'
        elif 'ielts' in sec:
            q['track'] = 'ielts'
        elif 'school' in sec:
            q['track'] = 'school_math'
        else:
            q['track'] = 'qudrat'

    if 'difficulty' not in q or not q['difficulty']:
        q['difficulty'] = 3
    elif isinstance(q['difficulty'], str):
        diff_map = {'سهل': 1, 'مبتدئ': 1, 'بسيط': 2, 'متوسط': 3, 'متقدم': 4, 'صلب': 5, 'تحدي': 5}
        q['difficulty'] = diff_map.get(q['difficulty'], 3)

    if 'image' in q and not q.get('image_url'):
        q['image_url'] = q['image']
    elif 'image_url' in q and not q.get('image'):
        q['image'] = q['image_url']

# Further massive expansion across all 7 tracks with difficulty factors (1 to 5)
additional_mega_pool = [
    # ================= 1. QUDRAT QUANT & VERBAL =================
    {
        "track": "qudrat",
        "section": "quantitative",
        "section_ar": "القدرات - القسم الكمي",
        "topic": "النسب المئوية والربح والخسارة",
        "question": "اشتـرى رجل شاشة بمبلغ $2000\\text{ ريال}$ ثم باعها بربح $15\\%$، فما سعر البيع النهائي؟",
        "options": ["$2300\\text{ ريال}$", "$2150\\text{ ريال}$", "$2400\\text{ ريال}$", "$2250\\text{ ريال}$"],
        "correct_index": 0,
        "explanation": "١. مقدار الربح = $2000 \\times \\frac{15}{100} = 300\\text{ ريال}$.\n٢. سعر البيع = $2000 + 300 = 2300\\text{ ريال}$.",
        "speed_rule": "10% من 2000 هي 200، و5% هي 100، إذاً الـ 15% تساوي 300. اجمع 2000 + 300 = 2300.",
        "difficulty": 2,
        "level": 2,
        "has_visual": False
    },
    {
        "track": "qudrat",
        "section": "quantitative",
        "section_ar": "القدرات - القسم الكمي",
        "topic": "السرعة والزمن والمسافة",
        "question": "سيارتان تخرجان من نفس المكان في اتجاهين متعاكسين؛ الأولى بسرعة $80\\text{ كم/س}$ والثانية بسرعة $70\\text{ كم/س}$. بعد كم ساعة تصبح المسافة بينهما $450\\text{ كم}$؟",
        "options": ["3 ساعات", "4 ساعات", "2.5 ساعة", "5 ساعات"],
        "correct_index": 0,
        "explanation": "بما أن الاتجاهين متعاكسان، نجمع السرعتين:\nالسرعة الكلية = $80 + 70 = 150\\text{ كم/س}$.\nالزمن = $\\frac{\\text{المسافة}}{\\text{السرعة الكلية}} = \\frac{450}{150} = 3\\text{ ساعات}$.",
        "speed_rule": "اتجاهان متعاكسان ⬅ اجمع السرعتين (150). المسافة ÷ مجموع السرعتين = 450 ÷ 150 = 3 ساعات.",
        "difficulty": 3,
        "level": 3,
        "has_visual": False
    },
    {
        "track": "qudrat",
        "section": "verbal",
        "section_ar": "القدرات - القسم اللفظي",
        "topic": "استيعاب المقروء",
        "question": "النص: \"الذكاء الاصطناعي ليس بديلًا عن العقل البشري، بل هو أداة تزيد من كفاءته وتسرع من معالجة البيانات الضخمة التي يعجز الإنسان عن إدراكها في زمن قياسي.\"\nيفهم من النص أن الذكاء الاصطناعي:",
        "options": ["أداة مساندة ترفع الكفاءة البشرية", "بديل كامل يلغي دور العقل البشري", "وسيلة تبطئ معالجة البيانات", "تقنية لا فائدة منها للمؤسسات"],
        "correct_index": 0,
        "explanation": "النص صريح في قوله \"بل هو أداة تزيد من كفاءته\"، مما يعني أنه أداة مساندة ومكملة للعقل البشري.",
        "speed_rule": "عد إلى الكلمة المفتاحية في النص مباشرة (أداة تزيد من كفاءته) للوصول للخيار المطابق دلالياً.",
        "difficulty": 2,
        "level": 2,
        "has_visual": False
    },

    # ================= 2. TAHSILI (التحصيلي - 4 المواد) =================
    {
        "track": "tahsili",
        "section": "tahsili_math",
        "section_ar": "التحصيلي - رياضيات",
        "topic": "المثلثات والمتطابقات",
        "question": "ما قيمة متطابقة المتتامة $\\text{جتا}(90^\\circ - \\theta)$؟",
        "options": ["$\\text{جا}(\\theta)$", "$-\\text{جا}(\\theta)$", "$\\text{جتا}(\\theta)$", "$\\text{ظا}(\\theta)$"],
        "correct_index": 0,
        "explanation": "من متطابقات الزوايا المتتامة في حساب المثلثات: $\\text{جتا}(90^\\circ - \\theta) = \\text{جا}(\\theta)$.",
        "speed_rule": "الزاوية 90 تقلب الدالة: جتا تصبح جا وبنفس الإشارة في الربع الأول.",
        "difficulty": 2,
        "level": 2,
        "has_visual": False
    },
    {
        "track": "tahsili",
        "section": "tahsili_physics",
        "section_ar": "التحصيلي - فيزياء",
        "topic": "الضوء والبصريات",
        "question": "أي من الخصائص التالية تعبر عن انحناء الضوء حول الحواجز والمنافذ الضيقة؟",
        "options": ["حيود الضوء (Diffraction)", "انعكاس الضوء", "انكسار الضوء", "استقطاب الضوء"],
        "correct_index": 0,
        "explanation": "الحيود هو ظاهرة انحناء الموجات الضوئية عند مرورها بالقرب من حواف الحواجز أو الفتحات الضيقة.",
        "speed_rule": "انحناء الضوء حول الحواجز والفتحات = الحيود (Diffraction).",
        "difficulty": 2,
        "level": 2,
        "has_visual": False
    },
    {
        "track": "tahsili",
        "section": "tahsili_chemistry",
        "section_ar": "التحصيلي - كيمياء",
        "topic": "الأحماض والقواعد PH",
        "question": "إذا كان الرقم الهيدروجيني لمحلول ما يساوي $\\text{pH} = 3$، فإن المحلول يعد:",
        "options": ["حمضياً قوياً", "قاعدياً قوياً", "متعادلاً", "قاعدياً ضعيفاً"],
        "correct_index": 0,
        "explanation": "مقياس pH من 0 إلى 14: إذا كان أقل من 7 فالمحلول حمضي، وكلما اقترب من 0 زادت الحمضية.",
        "speed_rule": "pH < 7 حمضي، pH = 7 متعادل، pH > 7 قلوياً.",
        "difficulty": 1,
        "level": 1,
        "has_visual": False
    },
    {
        "track": "tahsili",
        "section": "tahsili_biology",
        "section_ar": "التحصيلي - أحياء",
        "topic": "جهاز الدوران والدم",
        "question": "ما فصيلة الدم التي تعتبر (مستقبل عام) لجميع فصائل الدم بدون تجميع الكريات؟",
        "options": ["$AB^+$", "$O^-$", "$A^+$", "$B^-$"],
        "correct_index": 0,
        "explanation": "فصيلة $AB^+$ تخلو من مولدات الضد للمستقبلات وتستقبل من جميع الفصائل، بينما $O^-$ معطي عام.",
        "speed_rule": "AB+ = مستقبل عام. O- = معطي عام.",
        "difficulty": 1,
        "level": 1,
        "has_visual": False
    },

    # ================= 3. STEP EXAM =================
    {
        "track": "step",
        "section": "step_grammar",
        "section_ar": "اختبار STEP - القواعد",
        "topic": "Subject-Verb Agreement",
        "question": "Neither the teacher nor the students _____ present in the auditorium when the principal arrived.",
        "options": ["were", "was", "is", "are"],
        "correct_index": 0,
        "explanation": "With 'Neither... nor...', the verb agrees with the subject closest to it. 'Students' is plural, so 'were' is used for past tense.",
        "speed_rule": "Look at the subject closest to the verb ('students' -> plural past = WERE).",
        "difficulty": 3,
        "level": 3,
        "has_visual": False
    },
    {
        "track": "step",
        "section": "step_reading",
        "section_ar": "اختبار STEP - فهم القراءة",
        "topic": "Context & Synonyms",
        "question": "The company decided to **terminate** the contract due to repeated budget overruns. 'Terminate' means:",
        "options": ["End officially", "Extend", "Renew", "Sign"],
        "correct_index": 0,
        "explanation": "To 'terminate' means to bring to an end or stop officially.",
        "speed_rule": "Terminate = End / Stop / Cancel.",
        "difficulty": 1,
        "level": 1,
        "has_visual": False
    },

    # ================= 4. ARAMCO TESTS =================
    {
        "track": "aramco",
        "section": "aramco_math",
        "section_ar": "اختبارات أرامكو - رياضيات ومنطق",
        "topic": "Ratios & Proportions",
        "question": "If 6 technicians can assemble 18 pressure valves in 4 hours, how many valves can 10 technicians assemble in 8 hours at the same rate?",
        "options": ["60 valves", "40 valves", "50 valves", "72 valves"],
        "correct_index": 0,
        "explanation": "Rate per technician per hour = $\\frac{18}{6 \\times 4} = \\frac{18}{24} = 0.75\\text{ valves/hr}$.\nTotal valves for 10 technicians in 8 hours = $10 \\times 8 \\times 0.75 = 60\\text{ valves}$.",
        "speed_rule": "قاعدة الضرب التبادلي: (عمال1 × زمن1 × عمل2 = عمال2 × زمن2 × عمل1) ⬅ (6 × 4 × X = 10 × 8 × 18) ⬅ 24X = 1440 ⬅ X = 60.",
        "difficulty": 4,
        "level": 4,
        "has_visual": False
    },
    {
        "track": "aramco",
        "section": "aramco_english",
        "section_ar": "اختبارات أرامكو - إنجليزي",
        "topic": "Workplace Communication",
        "question": "Please ensure that all environmental reports are submitted _____ Friday afternoon.",
        "options": ["by", "until", "at", "since"],
        "correct_index": 0,
        "explanation": "'By' indicates a deadline (no later than Friday afternoon). 'Until' indicates duration up to a point.",
        "speed_rule": "Deadline context = BY + Time/Day.",
        "difficulty": 2,
        "level": 2,
        "has_visual": False
    },

    # ================= 5. COGNITIVE ABILITY (القدرة المعرفية) =================
    {
        "track": "cognitive",
        "section": "cognitive_verbal",
        "section_ar": "القدرة المعرفية - القدرة اللفظية",
        "topic": "المفاهيم والعلاقات الدلالية",
        "question": "ما الكلمة المخالفة للخيارات التالية: (تفاح، برتقال، موز، خيار)؟",
        "options": ["خيار", "تفاح", "برتقال", "موز"],
        "correct_index": 0,
        "explanation": "التفاح والبرتقال والموز من الفواكه، بينما الخيار يصنف نباتياً وضمن الخضروات في الاستخدام العام.",
        "speed_rule": "استبعاد المفردة الشاذة حسب التصنيف الغذائي/البيولوجي.",
        "difficulty": 1,
        "level": 1,
        "has_visual": False
    },
    {
        "track": "cognitive",
        "section": "cognitive_spatial",
        "section_ar": "القدرة المعرفية - القدرة المكانية",
        "topic": "التجميع والانعكاس في المرآة",
        "question": "عند عكس الكلمة \"نَبِيه\" في المرآة الرأسية، أي من الصفات التالية يتغير في الشكل الناتـج؟",
        "options": ["يتغير اتجاه الحروف من اليمين إلى اليسار معكوسة أفقياً", "تبقى الكلمة كما هي بالضبط بدون تغير", "تنقلب الكلمة رأساً على عقب", "تختفي الحروف تماماً"],
        "correct_index": 0,
        "explanation": "المرآة الرأسية تعكس الاتجاه الأفقـي (اليمين يصبح يساراً واليسار يصبح يميناً).",
        "speed_rule": "انعكاس المرآة = يمين ⇆ يسار مع بقاء الأعلى أعلى والأسفل أسفل.",
        "difficulty": 2,
        "level": 2,
        "has_visual": False
    },

    # ================= 6. IELTS & SCHOOL MATH =================
    {
        "track": "ielts",
        "section": "ielts_vocab",
        "section_ar": "اختبار الأيلتس - المفردات والقواعد",
        "topic": "Academic Writing Task 2 Connectors",
        "question": "Solar energy is renewable; _____, fossil fuels are finite and cause environmental degradation.",
        "options": ["in contrast", "therefore", "furthermore", "as a result"],
        "correct_index": 0,
        "explanation": "'In contrast' introduces a statement that opposes or differs from the preceding one.",
        "speed_rule": "Comparing two opposing concepts (renewable vs finite) requires a contrast transition word ('In contrast' / 'On the other hand').",
        "difficulty": 3,
        "level": 3,
        "has_visual": False
    },
    {
        "track": "school_math",
        "section": "school_primary",
        "section_ar": "الرياضيات المدرسية - الابتدائي",
        "topic": "الضرب والأعداد الأوليّة",
        "question": "ما أصغر عدد أولي فردي؟",
        "options": ["3", "2", "1", "5"],
        "correct_index": 0,
        "explanation": "الأعداد الأولية تبدأ من 2 (وهو الزوجي الوحيد). أصغر عدد أولي فردي هو 3.",
        "speed_rule": "2 = أصغر عدد أولي زوجي. 3 = أصغر عدد أولي فردي. (1 ليس أولياً).",
        "difficulty": 1,
        "level": 1,
        "has_visual": False
    },
    {
        "track": "school_math",
        "section": "school_intermediate",
        "section_ar": "الرياضيات المدرسية - المتوسط",
        "topic": "المعادلات الخطية",
        "question": "ما حل المعادلة $2x + 5 = 15$؟",
        "options": ["$x = 5$", "$x = 10$", "$x = 7.5$", "$x = 4$"],
        "correct_index": 0,
        "explanation": "١. نطرح 5 من الطرفين: $2x = 15 - 5 = 10$.\n٢. نقسم على 2: $x = \\frac{10}{2} = 5$.",
        "speed_rule": "انقل 5 بعكس الإشارة (15-5=10)، ثم اقسم 10 على 2 يعطي 5.",
        "difficulty": 1,
        "level": 1,
        "has_visual": False
    },
    {
        "track": "school_math",
        "section": "school_secondary",
        "section_ar": "الرياضيات المدرسية - الثانوية",
        "topic": "التكامل المحدد",
        "question": "ما قيمة التكامل المحدد $\\int_{0}^{2} 3x^2 dx$؟",
        "options": ["8", "12", "6", "4"],
        "correct_index": 0,
        "explanation": "تكامل $3x^2$ هو $x^3$.\nالتعويض بحدود التكامل من 0 إلى 2:\n$[x^3]_{0}^{2} = 2^3 - 0^3 = 8 - 0 = 8$.",
        "speed_rule": "تكامل 3x^2 هو x^3، تعويض 2 ينحسب 2^3 = 8.",
        "difficulty": 3,
        "level": 3,
        "has_visual": False
    }
]

# Check existing question signatures to avoid duplicates
existing_texts = {q.get('question', '').strip() for q in existing_questions}

current_id = max([q.get('id', 0) for q in existing_questions] + [0]) + 1
added_count = 0

for eq in additional_mega_pool:
    if eq.get('question', '').strip() not in existing_texts:
        eq['id'] = current_id
        current_id += 1
        existing_questions.append(eq)
        added_count += 1

print(f"Added {added_count} new questions to the bank. Total: {len(existing_questions)}")

# Save to questions.json
with open(QUESTIONS_FILE, 'w', encoding='utf-8') as f:
    json.dump(existing_questions, f, ensure_ascii=False, indent=2)

print("Saved updated questions.json.")

# Sync to SQLite Database
try:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for q in existing_questions:
        cur.execute("""
        INSERT OR REPLACE INTO questions (
            id, track, section, section_ar, topic, question, diagram_svg, options_json,
            correct_index, explanation, speed_rule, difficulty, level, image, image_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            q.get('id'),
            q.get('track', 'qudrat'),
            q.get('section', 'quantitative'),
            q.get('section_ar', ''),
            q.get('topic', ''),
            q.get('question', ''),
            q.get('diagram_svg', ''),
            json.dumps(q.get('options', []), ensure_ascii=False),
            q.get('correct_index', 0),
            q.get('explanation', ''),
            q.get('speed_rule', ''),
            q.get('difficulty', 3),
            q.get('level', 1),
            q.get('image', ''),
            q.get('image_url', '')
        ))
    conn.commit()
    conn.close()
    print("Database synced successfully.")
except Exception as e:
    print("Database sync error:", e)
