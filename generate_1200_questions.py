# encoding: utf-8
import json
import os

def generate_1200_bank():
    questions = []
    q_id = 1

    def add(track, section, section_ar, topic, question, options, correct_index, explanation, speed_rule, diff=1, hint=""):
        nonlocal q_id
        questions.append({
            "id": q_id,
            "track": track,
            "section": section,
            "section_ar": section_ar,
            "topic": topic,
            "question": question,
            "options": options,
            "correct_index": correct_index,
            "explanation": explanation,
            "speed_rule": speed_rule,
            "hint": hint or f"تلميح ذكي: فكّر في مفتاح الحل الخاص بـ ({topic}) والتطبيق المباشر بالقوانين.",
            "difficulty": diff,
            "level": diff,
            "has_visual": False,
            "image_url": None
        })
        q_id += 1

    # ================= 1. QUDRAT QUANT (100 Questions) =================
    # Basic math, algebra, geometry, ratios, speed, work, sequences, comparisons
    for i in range(1, 101):
        diff = (i % 5) + 1
        if i % 6 == 1:
            a = i * 3
            b = i * 2
            add("qudrat", "quantitative", "القدرات العامة - الكمي", "الحساب والأعداد",
                f"ما قيمة حاصل جمع العددين {a} و {b} مقسوماً على 5؟",
                [f"{(a+b)//5}", f"{(a+b)//5 + 2}", f"{(a+b)//5 - 1}", f"{(a+b)//5 + 4}"], 0,
                f"نجمع العددين: {a} + {b} = {a+b}. ثم نقسم على 5: {a+b} ÷ 5 = {(a+b)//5}.",
                "جمع ثم قسمة على 5 مباشرة.", diff)
        elif i % 6 == 2:
            x_val = i + 2
            eq = 2 * x_val + 4
            add("qudrat", "quantitative", "القدرات العامة - الكمي", "الجبر والمعادلات",
                f"إذا كان $2x + 4 = {eq}$، فما قيمة $x$؟",
                [f"${x_val}$", f"${x_val+3}$", f"${x_val-2}$", f"${x_val+5}$"], 0,
                f"نطرح 4 من الطرفين: $2x = {eq-4} \\implies x = {x_val}$.",
                "نقل الثوابت ثم القسمة على معامل x.", diff)
        elif i % 6 == 3:
            w = (i % 10) + 4
            l = 2 * w
            area = l * w
            add("qudrat", "quantitative", "القدرات العامة - الكمي", "الهندسة والمساحات",
                f"مستطيل طوله ضعف عرضه، إذا كان عرضه {w} سم، فما مساحته؟",
                [f"{area} سم²", f"{area+12} سم²", f"{area-8} سم²", f"{area*2} سم²"], 0,
                f"العرض = {w}، الطول = 2 × {w} = {l}. المساحة = الطول × العرض = {l} × {w} = {area} سم².",
                "المساحة = الطول × العرض.", diff)
        elif i % 6 == 4:
            s1 = 80 + (i % 20)
            t = 2 + (i % 3)
            dist = s1 * t
            add("qudrat", "quantitative", "القدرات العامة - الكمي", "السرعة والزمن",
                f"سيارة تسير بسرعة {s1} كم/س لمدة {t} ساعات، ما المسافة المقطوعة؟",
                [f"{dist} كم", f"{dist+30} كم", f"{dist-20} كم", f"{dist+50} كم"], 0,
                f"المسافة = السرعة × الزمن = {s1} × {t} = {dist} كم.",
                "المسافة = السرعة × الزمن.", diff)
        elif i % 6 == 5:
            val1 = 2 ** ((i % 4) + 3)
            val2 = 3 ** ((i % 3) + 2)
            correct = 0 if val1 > val2 else (1 if val2 > val1 else 2)
            add("qudrat", "quantitative", "القدرات العامة - الكمي", "المقارنات والأسس",
                f"قارن بين:\nالقيمة الأولى: $2^{{(i % 4) + 3}} = {val1}$\nالقيمة الثانية: $3^{{(i % 3) + 2}} = {val2}$",
                ["القيمة الأولى أكبر", "القيمة الثانية أكبر", "القيمتان متساويتان", "المعطيات غير كافية"], correct,
                f"القيمة الأولى = {val1}، والقيمة الثانية = {val2}. قارن بينهما عدديّاً.",
                "احسب قيمة الأُسس لراسم المقارنة.", diff)
        else:
            base = i * 5
            pct = 20
            ans = (base * pct) // 100
            add("qudrat", "quantitative", "القدرات العامة - الكمي", "النسب المئوية",
                f"ما هي نسبة 20% من العدد {base}؟",
                [f"{ans}", f"{ans+5}", f"{ans-2}", f"{ans*2}"], 0,
                f"20% تعادل 1/5. أي نقسم {base} على 5 = {ans}.",
                "20% = قسمة على 5.", diff)

    # ================= 2. QUDRAT VERBAL (100 Questions) =================
    verbal_topics = [
        ("تناظر لفظي", "شمس : نهار", ["قمر : ليل", "سحاب : مطر", "نجم : كوكب", "شجر : أوراق"], 0, "الشمس مصدر الضوء في النهار والقمر بالليل."),
        ("إكمال الجمل", "العقل ... كالمظلة، لا يعمل إلا إذا كان ...", ["المتفتح / مفتوحاً", "الصغير / مغلقاً", "الكبير / واسعاً", "المظلم / منيراً"], 0, "العقل المتفتح كالمظلة لا يعمل إلا إذا كان مفتوحاً."),
        ("الخطأ السياقي", "من زاد حياؤه قَلّ قدره بين الناس وارتفعت مكانته.", ["قَلّ", "حياؤه", "قدره", "مكانته"], 0, "الكلمة الخاطئة (قلّ)، فالصحيح زاد قدره."),
        ("المفردة الشاذة", "حدد الكلمة المختلفة بين التالية:", ["التفاح", "الموز", "البرتقال", "الخيار"], 3, "الخيار من الخضروات والبقية فواكه."),
        ("استيعاب المقروء", "(تعتبر الشمس المصدر الرئيسي للطاقة على سطح الأرض، وبدونها تتوقف الحياة).\nالسؤال: الفكرة الرئيسة للنص هي:", ["أهمية الشمس للحياة", "أنواع النباتات", "تأثير القمر", "كيفية تكون الطاقة"], 0, "النص يتحدث عن أهمية الشمس للحياة.")
    ]
    for i in range(1, 101):
        diff = (i % 5) + 1
        top_type, stem, opts, c_idx, expl = verbal_topics[(i - 1) % len(verbal_topics)]
        add("qudrat", "verbal", "القدرات العامة - اللفظي", f"{top_type} (نموذج {i})",
            f"[{top_type}] {stem}", opts, c_idx, expl, "التركيز على العلاقة الدلالية والسياق.", diff)

    # ================= 3. TAHSILI MATH (100 Questions) =================
    for i in range(1, 101):
        diff = (i % 5) + 1
        m = (i % 5) + 2
        add("tahsili", "tahsili_math", "التحصيلي - الرياضيات", f"الدوال والتفاضل (نموذج {i})",
            f"ما قيمة مشتقة الدالة $f(x) = {m}x^3 - 4x + 7$؟",
            [f"${3*m}x^2 - 4$", f"${3*m}x^3 - 4$", f"${m}x^2 - 4$", f"${3*m}x - 4$"], 0,
            f"المشتقة نضرب الأُس في المعامل ونطرح 1 من الأُس: $d/dx({m}x^3) = {3*m}x^2$ و مشتقة $-4x$ هي $-4$.",
            "قاعدة القوة: d/dx(x^n) = n*x^(n-1).", diff)

    # ================= 4. TAHSILI PHYSICS (100 Questions) =================
    for i in range(1, 101):
        diff = (i % 5) + 1
        m_kg = (i % 10) + 2
        a_m = (i % 4) + 2
        f_n = m_kg * a_m
        add("tahsili", "tahsili_physics", "التحصيلي - الفيزياء", f"الميكانيكا (نموذج {i})",
            f"جسم كتلته {m_kg} كجم يتحرك بتسارع {a_m} م/ث²، ما مقدار القوة المحصلة المؤثرة عليه؟",
            [f"{f_n} نيوتن", f"{f_n+5} نيوتن", f"{f_n-3} نيوتن", f"{f_n*2} نيوتن"], 0,
            f"من قانون نيوتن الثاني: القوة = الكتلة × التسارع = {m_kg} × {a_m} = {f_n} نيوتن.",
            "F = m * a.", diff)

    # ================= 5. TAHSILI CHEMISTRY (100 Questions) =================
    for i in range(1, 101):
        diff = (i % 5) + 1
        sub_level = ["s", "p", "d", "f"][(i - 1) % 4]
        capacity = [2, 6, 10, 14][(i - 1) % 4]
        add("tahsili", "tahsili_chemistry", "التحصيلي - الكيمياء", f"التوزيع الإلكتروني (نموذج {i})",
            f"ما أقصى عدد من الإلكترونات يستوعبه المستوى الثانوي ${sub_level}$؟",
            [f"{capacity} إلكترونات", f"{capacity+2} إلكترونات", f"{capacity*2} إلكترونات", f"{capacity-1} إلكترونات"], 0,
            f"المستوى الثانوي {sub_level} يستوعب أقصى عدد قدره {capacity} إلكترونات.",
            "سعة المستويات الفرعية s=2, p=6, d=10, f=14.", diff)

    # ================= 6. TAHSILI BIOLOGY (100 Questions) =================
    bio_items = [
        ("المايتوكندريا هي مركز إنتاج الطاقة (ATP) في الخلية.", ["المايتوكندريا", "الرايبوسومات", "أجسام جولجي", "الشبكة الأندوبلازمية"], 0),
        ("الرايبوسومات هي العضيات المسؤولة عن بناء البروتينات.", ["الرايبوسومات", "المايتوكندريا", "النواة", "الجدار الخلوي"], 0),
        ("الحمض النووي DNA يحمل المعلومات الوراثية بشريط حلزوني مزدوج.", ["DNA", "RNA", "tRNA", "mRNA"], 0),
        ("البناء الضوئي يحدث في البلاستيدات الخضراء في الخلية النباتية.", ["البلاستيدات الخضراء", "المايتوكندريا", "الفجوة العصارية", "النواة"], 0)
    ]
    for i in range(1, 101):
        diff = (i % 5) + 1
        item, opts, c = bio_items[(i - 1) % len(bio_items)]
        add("tahsili", "tahsili_biology", "التحصيلي - الأحياء", f"عضيات الخلية والوراثة (نموذج {i})",
            f"أي العضيات أو الأحماض التالية ينطبق عليه الوصف: ({item})؟", opts, c,
            f"الوصف ينطبق على {opts[c]}.", "حفظ الوظائف الخلوية الأساسية.", diff)

    # ================= 7. STEP ENGLISH (100 Questions) =================
    step_items = [
        ("She _____ to the library every weekend.", ["goes", "go", "going", "gone"], 0, "Singular subject (She) takes verb + es in present simple."),
        ("They have been living here _____ 2010.", ["since", "for", "from", "in"], 0, "'Since' is used for a specific starting point in time."),
        ("If I _____ enough money, I would buy a new car.", ["had", "have", "will have", "would have"], 0, "Second conditional: If + past simple, would + base verb."),
        ("He is interested _____ learning new computer skills.", ["in", "on", "at", "with"], 0, "Adjective 'interested' is followed by preposition 'in'.")
    ]
    for i in range(1, 101):
        diff = (i % 5) + 1
        stem, opts, c, expl = step_items[(i - 1) % len(step_items)]
        add("step", "step_grammar", "كفايات الإنجليزية - STEP", f"Grammar & Structure (Set {i})",
            f"Select the correct option: {stem}", opts, c, expl, "Standard English grammar rule.", diff)

    # ================= 8. ARAMCO MATH & LOGIC (100 Questions) =================
    for i in range(1, 101):
        diff = (i % 5) + 1
        w_workers = (i % 5) + 3
        d_days = (i % 4) + 4
        new_w = w_workers - 1
        ans_days = (w_workers * d_days) // new_w
        add("aramco", "aramco_math", "اختبارات أرامكو - رياضيات ومنطق", f"مسائل العمال والتناسب العكسي (نموذج {i})",
            f"إذا أنجز {w_workers} عمال بناء جدار في {d_days} أيام، فكم يوماً يحتاج {new_w} عمال لبنائه بنفس الكفاءة؟",
            [f"{ans_days} أيام", f"{ans_days+2} أيام", f"{ans_days-1} أيام", f"{ans_days*2} أيام"], 0,
            f"التناسب عكسي: {w_workers} × {d_days} = {w_workers*d_days}. الأيام = {w_workers*d_days} ÷ {new_w} = {ans_days} أيام.",
            "التناسب العكسي: حُاصل الضرب ثابت.", diff)

    # ================= 9. COGNITIVE REASONING (100 Questions) =================
    for i in range(1, 101):
        diff = (i % 5) + 1
        step_val = (i % 3) + 2
        start_val = i * 2
        t1 = start_val
        t2 = t1 + step_val
        t3 = t2 + step_val
        t4 = t3 + step_val
        add("cognitive", "cognitive_reasoning", "القدرة المعرفية - استدلال", f"السلاسل الرقمية (نموذج {i})",
            f"ما العدد التالي في السلسلة العددية: {t1}، {t2}، {t3}، (...)؟",
            [f"{t4}", f"{t4+2}", f"{t4-1}", f"{t4+5}"], 0,
            f"النمط هو إضافة العدد ثابت قدره {step_val}: {t3} + {step_val} = {t4}.",
            "تحديد مقدار الزيادة بين الحدود.", diff)

    # ================= 10. IELTS VOCAB (100 Questions) =================
    ielts_items = [
        ("Choose the synonym for 'ABUNDANT':", ["Plentiful", "Scarce", "Rare", "Meager"], 0, "'Abundant' means existing in large quantities; plentiful."),
        ("Choose the antonym for 'TEMPORARY':", ["Permanent", "Brief", "Fleeting", "Short-term"], 0, "The opposite of temporary is permanent."),
        ("Identify the meaning of 'CRUCIAL':", ["Extremely important", "Irrelevant", "Optional", "Minor"], 0, "'Crucial' means decisive or extremely important.")
    ]
    for i in range(1, 101):
        diff = (i % 5) + 1
        stem, opts, c, expl = ielts_items[(i - 1) % len(ielts_items)]
        add("ielts", "ielts_vocab", "الأيلتس - IELTS", f"Vocabulary & Terminology (Set {i})",
            f"{stem}", opts, c, expl, "Academic IELTS vocabulary.", diff)

    # ================= 11. SCHOOL MATH PRIMARY (100 Questions - Pure Arabic RTL) =================
    for i in range(1, 101):
        diff = (i % 5) + 1
        a_ar = i * 2
        b_ar = i * 3
        res = a_ar + b_ar
        # Numbers in Arabic
        def to_ar_num(n):
            ar_digits = str(n).translate(str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩"))
            return ar_digits

        add("school_math", "school_primary", "الرياضيات المدرسية - المرحلة الابتدائية", f"الحساب العربي (نموذج {to_ar_num(i)})",
            f"ما حاصل جمع العددين {to_ar_num(a_ar)} + {to_ar_num(b_ar)}؟",
            [f"{to_ar_num(res)}", f"{to_ar_num(res+2)}", f"{to_ar_num(res-1)}", f"{to_ar_num(res+5)}"], 0,
            f"نجمع العددين مباشرة: {to_ar_num(a_ar)} + {to_ar_num(b_ar)} = {to_ar_num(res)}.",
            "الجمع العربي المباشر من اليمين إلى اليسار.", diff)

    # ================= 12. SCHOOL MATH INTERMEDIATE (100 Questions - Pure Arabic RTL) =================
    for i in range(1, 101):
        diff = (i % 5) + 1
        val_s = i + 1
        val_res = 2 * val_s + 5

        def to_ar_num(n):
            return str(n).translate(str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩"))

        add("school_math", "school_intermediate", "الرياضيات المدرسية - المرحلة المتوسطة", f"الجبر العربي (نموذج {to_ar_num(i)})",
            f"ما حل المعادلة التالية: ٢ س + ٥ = {to_ar_num(val_res)}؟",
            [f"س = {to_ar_num(val_s)}", f"س = {to_ar_num(val_s+3)}", f"س = {to_ar_num(val_s-1)}", f"س = {to_ar_num(val_s+5)}"], 0,
            f"١. نطرح ٥ من الطرفين: ٢ س = {to_ar_num(val_res-5)}.\n٢. نقسم على ٢: س = {to_ar_num(val_s)}.",
            "نقل الثابت ثم القسمة على معامل س.", diff)

    # ================= 13. SCHOOL MATH SECONDARY (100 Questions) =================
    for i in range(1, 101):
        diff = (i % 5) + 1
        pow_val = (i % 4) + 1
        ans_int = pow_val ** 3
        add("school_math", "school_secondary", "الرياضيات المدرسية - المرحلة الثانوية", f"التكامل المحدد (نموذج {i})",
            f"ما قيمة التكامل المحدد $\\int_{{0}}^{{{pow_val}}} 3x^2 dx$؟",
            [f"{ans_int}", f"{ans_int+4}", f"{ans_int-2}", f"{ans_int*2}"], 0,
            f"تكامل $3x^2$ هو $x^3$. بالتعويض بحدود التكامل: $[x^3]_{{0}}^{{{pow_val}}} = {pow_val}^3 - 0 = {ans_int}$.",
            "تكامل 3x^2 هو x^3، نعوض بالحد الأعلى.", diff)

    return questions

def main():
    bank = generate_1200_bank()
    file_path = os.path.join(os.path.dirname(__file__), 'questions.json')
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(bank, f, ensure_ascii=False, indent=2)
    print(f"Successfully generated {len(bank)} questions in questions.json!")

if __name__ == '__main__':
    main()
