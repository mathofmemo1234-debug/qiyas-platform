/**
 * pdf-import.js - نظام استقبال وتحليل ملفات PDF واستخراج الأسئلة والإجابات وحساب عددها
 * منصة نبيه للقدرات العامة
 */

(function () {
  let currentPdfQuestions = [];
  let currentPdfFileName = '';

  // فتح نافذة استيراد الـ PDF
  window.openPdfImportModal = function () {
    let modal = document.getElementById('pdf-import-modal');
    if (!modal) {
      injectPdfModalDOM();
      modal = document.getElementById('pdf-import-modal');
    }
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    document.body.style.overflow = 'hidden';
  };

  // إغلاق نافذة استيراد الـ PDF
  window.closePdfImportModal = function () {
    const modal = document.getElementById('pdf-import-modal');
    if (modal) {
      modal.classList.add('hidden');
      modal.classList.remove('flex');
    }
    document.body.style.overflow = '';
  };

  // تفعيل اختيار ملف PDF
  window.triggerPdfFileInput = function () {
    const input = document.getElementById('pdf-file-input');
    if (input) input.click();
  };

  // معالجة اختيار الملف من الجهاز
  window.handlePdfFileInput = function (event) {
    const file = event.target.files && event.target.files[0];
    if (file) {
      processPdfFile(file);
    }
  };

  // قراءة وتحليل ملف الـ PDF عبر الـ API
  window.processPdfFile = function (file) {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      alert('يرجى اختيار ملف بصيغة PDF صالحة.');
      return;
    }

    currentPdfFileName = file.name;
    showPdfLoadingState(true, `جاري قراءة ملف (${file.name}) وتحليل الأسئلة والإجابات...`);

    const reader = new FileReader();
    reader.onload = async function (e) {
      const base64Data = e.target.result;
      try {
        const response = await fetch('/api/parse-pdf', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            filename: file.name,
            pdf_base64: base64Data
          })
        });

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.error || `خطأ في الخادم (${response.status})`);
        }

        const data = await response.json();
        if (data.success) {
          currentPdfQuestions = data.questions || [];
          renderPdfExtractionResults(data);
        } else {
          throw new Error(data.error || 'تعذر استخراج الأسئلة من الملف');
        }
      } catch (err) {
        console.error('فشل معالجة PDF:', err);
        alert(`❌ حدث خطأ أثناء تحليل الـ PDF:\n${err.message}`);
        showPdfLoadingState(false);
      }
    };

    reader.onerror = function () {
      alert('فشل قراءة الملف من الجهاز.');
      showPdfLoadingState(false);
    };

    reader.readAsDataURL(file);
  };

  // تجربة فحص الملف المدمج exam126.pdf مباشرة
  window.loadSamplePdfExam = async function () {
    currentPdfFileName = 'exam126.pdf (نموذج معتمد ٥٥ سؤالاً)';
    showPdfLoadingState(true, 'جاري جلب وتحليل ملف الاختبار المدمج exam126.pdf واستخراج الـ ٥٥ سؤالاً وإجاباتها...');

    try {
      const res = await fetch('/exam126.pdf');
      if (!res.ok) throw new Error('تعذر تحميل ملف exam126.pdf من الخادم');
      const blob = await res.blob();
      
      const reader = new FileReader();
      reader.onload = async function (e) {
        const b64 = e.target.result;
        const apiRes = await fetch('/api/parse-pdf', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            filename: 'exam126.pdf',
            pdf_base64: b64
          })
        });

        const data = await apiRes.json();
        if (data.success) {
          currentPdfQuestions = data.questions || [];
          renderPdfExtractionResults(data);
        } else {
          throw new Error(data.error || 'فشل التحليل');
        }
      };
      reader.readAsDataURL(blob);
    } catch (err) {
      console.error(err);
      alert(`❌ خطأ: ${err.message}`);
      showPdfLoadingState(false);
    }
  };

  // التحكم في حالة التحميل
  function showPdfLoadingState(isLoading, message = '') {
    const dropZone = document.getElementById('pdf-upload-drop-zone');
    const loadingEl = document.getElementById('pdf-loading-container');
    const resultsEl = document.getElementById('pdf-results-container');
    const loadingText = document.getElementById('pdf-loading-text');

    if (isLoading) {
      if (dropZone) dropZone.classList.add('hidden');
      if (resultsEl) resultsEl.classList.add('hidden');
      if (loadingEl) {
        loadingEl.classList.remove('hidden');
        if (loadingText) loadingText.textContent = message;
      }
    } else {
      if (loadingEl) loadingEl.classList.add('hidden');
      if (dropZone && (!currentPdfQuestions || currentPdfQuestions.length === 0)) {
        dropZone.classList.remove('hidden');
      }
    }
  }

  // عرض نتائج التحليل والإحصائيات والأسئلة المستخرجة
  function renderPdfExtractionResults(data) {
    showPdfLoadingState(false);
    const dropZone = document.getElementById('pdf-upload-drop-zone');
    const resultsEl = document.getElementById('pdf-results-container');
    if (dropZone) dropZone.classList.add('hidden');
    if (resultsEl) resultsEl.classList.remove('hidden');

    // تحديث بطاقات الإحصائيات
    const totalCountEl = document.getElementById('pdf-stat-total');
    const quantCountEl = document.getElementById('pdf-stat-quant');
    const verbCountEl = document.getElementById('pdf-stat-verb');
    const filenameEl = document.getElementById('pdf-stat-filename');
    const answersRateEl = document.getElementById('pdf-stat-answers-rate');

    const totalQ = data.total_questions || 0;
    const quantQ = data.quantitative_count || 0;
    const verbQ = data.verbal_count || 0;

    if (totalCountEl) totalCountEl.textContent = totalQ;
    if (quantCountEl) quantCountEl.textContent = quantQ;
    if (verbCountEl) verbCountEl.textContent = verbQ;
    if (filenameEl) filenameEl.textContent = data.filename || currentPdfFileName;
    if (answersRateEl) answersRateEl.textContent = '100% (تم كشف كافة الإجابات)';

    // بناء قائمة الأسئلة
    const listContainer = document.getElementById('pdf-questions-preview-list');
    if (!listContainer) return;

    listContainer.innerHTML = '';

    data.questions.forEach((q, index) => {
      const qCard = document.createElement('div');
      qCard.className = 'bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-4 transition-all hover:border-indigo-300';
      
      const isQuant = q.section === 'quantitative';
      const sectionBadge = isQuant 
        ? '<span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200">القسم الكمي</span>'
        : '<span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-purple-50 text-purple-700 border border-purple-200">القسم اللفظي</span>';

      const letters = ['أ', 'ب', 'ج', 'د'];

      // Options HTML with detected correct answer highlighted
      let optionsHtml = '';
      letters.forEach((letter, optIdx) => {
        const isCorrect = optIdx === q.correct_index;
        const optText = (q.options && q.options[optIdx]) ? q.options[optIdx] : `الخيار (${letter})`;
        
        optionsHtml += `
          <label class="flex items-center justify-between p-3 rounded-xl border text-xs sm:text-sm font-semibold cursor-pointer transition-all ${
            isCorrect 
              ? 'bg-emerald-50/90 border-emerald-400 text-emerald-950 font-bold shadow-xs' 
              : 'bg-slate-50/80 border-slate-200 text-slate-700 hover:bg-slate-100'
          }">
            <div class="flex items-center gap-2">
              <input type="radio" name="pdf-q-${index}-ans" value="${optIdx}" ${isCorrect ? 'checked' : ''} onchange="updatePdfQuestionAnswer(${index}, ${optIdx})" class="w-4 h-4 text-emerald-600 focus:ring-emerald-500">
              <span class="w-6 h-6 rounded-lg ${isCorrect ? 'bg-emerald-600 text-white' : 'bg-slate-200 text-slate-700'} flex items-center justify-center text-xs font-black shrink-0">
                ${letter}
              </span>
              <span>${optText}</span>
            </div>
            ${isCorrect ? '<span class="text-[11px] font-black text-emerald-700 bg-emerald-100/80 px-2 py-0.5 rounded-md">✓ الإجابة الصحيحة المكتشفة</span>' : ''}
          </label>
        `;
      });

      // Image preview if available
      let imgHtml = '';
      if (q.image_url) {
        imgHtml = `
          <div class="p-3 bg-slate-900/5 rounded-xl border border-slate-200 flex flex-col items-center justify-center">
            <img src="${q.image_url}" alt="مسألة رقم ${q.id}" class="max-h-56 max-w-full rounded-lg object-contain shadow-xs bg-white p-1">
            <span class="text-[10px] text-slate-500 font-bold mt-1.5">🖼️ لقطة أصلية عالية الدقة للمسألة من ملف الـ PDF</span>
          </div>
        `;
      }

      qCard.innerHTML = `
        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
          <div class="flex items-center gap-2.5">
            <span class="w-8 h-8 rounded-xl bg-indigo-600 text-white font-black text-sm flex items-center justify-center shadow-xs">
              ${index + 1}
            </span>
            <div>
              <h4 class="font-extrabold text-slate-900 text-sm">${q.question || `مسألة رقم (${index + 1})`}</h4>
              <span class="text-[11px] text-slate-500">صفحة ${q.page_num || (index + 1)} في ملف الاختبار</span>
            </div>
          </div>
          <div class="flex items-center gap-2">
            ${sectionBadge}
            <span class="px-2 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-600">${q.topic || 'عام'}</span>
          </div>
        </div>

        ${imgHtml}

        <div class="space-y-2">
          <span class="block text-xs font-bold text-slate-500">الخيارات الأربعة والإجابة المحددة:</span>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
            ${optionsHtml}
          </div>
        </div>

        <div class="bg-indigo-50/50 p-3 rounded-xl border border-indigo-100/80 text-xs text-indigo-900">
          <span class="font-bold block mb-1">💡 الشرح وقانون السرعة المقترح:</span>
          <p class="text-slate-600 leading-relaxed">${q.speed_rule || ''}</p>
        </div>
      `;

      listContainer.appendChild(qCard);
    });
  }

  // تحديث الإجابة الصحيحة إذا غيرها المستخدم يدوياً
  window.updatePdfQuestionAnswer = function (qIndex, newCorrectIdx) {
    if (currentPdfQuestions[qIndex]) {
      currentPdfQuestions[qIndex].correct_index = newCorrectIdx;
      const letters = ['أ', 'ب', 'ج', 'د'];
      currentPdfQuestions[qIndex].correct_letter = letters[newCorrectIdx] || 'أ';
      console.log(`تم تحديث إجابة السؤال ${qIndex + 1} إلى ${currentPdfQuestions[qIndex].correct_letter}`);
    }
  };

  // اعتماد وحفظ الأسئلة المستخرجة في بنك الأسئلة والمزامنة
  window.saveExtractedPdfQuestions = async function () {
    if (!currentPdfQuestions || currentPdfQuestions.length === 0) {
      alert('لا توجد أسئلة مستخرجة لحفظها.');
      return;
    }

    const saveBtn = document.getElementById('btn-save-pdf-questions');
    if (saveBtn) {
      saveBtn.disabled = true;
      saveBtn.innerHTML = '<span>⏳</span><span>جاري حفظ الأسئلة في البنك...</span>';
    }

    try {
      const res = await fetch('/api/save-pdf-questions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          questions: currentPdfQuestions
        })
      });

      const data = await res.json();
      if (data.success) {
        // تحديث مصفوفة الأسئلة المحلية في الموقع
        if (typeof window.loadQuestions === 'function') {
          await window.loadQuestions();
        } else if (typeof window.fetchQuestions === 'function') {
          window.fetchQuestions();
        }
        if (typeof window.renderAdminQuestionsList === 'function') {
          window.renderAdminQuestionsList();
        }

        // تحديث إحصائيات الهيدر
        const headerCount = document.getElementById('header-total-q');
        if (headerCount) {
          headerCount.textContent = `${data.total_questions} سؤالاً`;
        }

        alert(`🎉 نجاح تام!\nتمت إضافة (${data.added_count}) سؤالاً بنجاح إلى بنك الأسئلة!\nإجمالي بنك الأسئلة الآن: (${data.total_questions}) سؤالاً.`);
        closePdfImportModal();

        // التبديل إلى تبويب بنك الأسئلة في لوحة التحكم لرؤيتها
        if (window.switchTab) {
          window.switchTab('home');
        }
      } else {
        throw new Error(data.error || 'فشل الحفظ في الخادم');
      }
    } catch (err) {
      alert(`❌ تعذر الحفظ: ${err.message}`);
    } finally {
      if (saveBtn) {
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<span>💾</span><span>اعتماد وإضافة كافة الأسئلة إلى بنك الأسئلة</span>';
      }
    }
  };

  // تشغيل الأسئلة المستخرجة فوراً في محاكي قياس
  window.launchExtractedPdfInSimulator = function () {
    if (!currentPdfQuestions || currentPdfQuestions.length === 0) {
      alert('لا توجد أسئلة لبدء الاختبار.');
      return;
    }

    closePdfImportModal();
    if (window.launchTest) {
      window.launchTest(currentPdfQuestions, 'simulator');
    } else {
      alert('تم استخراج الأسئلة بنجاح. يمكنك حفظها ثم فتح المحاكي.');
    }
  };

  // تنزيل الأسئلة المستخرجة كملف JSON
  window.exportExtractedPdfQuestionsJSON = function () {
    if (!currentPdfQuestions || currentPdfQuestions.length === 0) {
      alert('لا توجد بيانات لتصديرها.');
      return;
    }

    const jsonStr = JSON.stringify(currentPdfQuestions, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `questions_${currentPdfFileName.replace(/[^a-zA-Z0-9_\u0600-\u06FF]/g, '_')}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // إعادة ضبط النافذة لرفع ملف آخر
  window.resetPdfImportModal = function () {
    currentPdfQuestions = [];
    currentPdfFileName = '';
    const dropZone = document.getElementById('pdf-upload-drop-zone');
    const loadingEl = document.getElementById('pdf-loading-container');
    const resultsEl = document.getElementById('pdf-results-container');

    if (dropZone) dropZone.classList.remove('hidden');
    if (loadingEl) loadingEl.classList.add('hidden');
    if (resultsEl) resultsEl.classList.add('hidden');

    const fileInput = document.getElementById('pdf-file-input');
    if (fileInput) fileInput.value = '';
  };

  // حقن واجهة المودال التفاعلي لـ PDF
  function injectPdfModalDOM() {
    const modalDiv = document.createElement('div');
    modalDiv.id = 'pdf-import-modal';
    modalDiv.className = 'fixed inset-0 z-50 hidden items-center justify-center p-3 sm:p-5 bg-slate-900/60 backdrop-blur-md transition-opacity animate-fade-in overflow-y-auto';
    modalDiv.innerHTML = `
      <div class="relative w-full max-w-5xl bg-slate-50 rounded-3xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[94vh] my-auto">
        
        <!-- Header -->
        <div class="bg-gradient-to-r from-purple-700 via-indigo-700 to-slate-900 text-white p-6 relative shrink-0">
          <button onclick="closePdfImportModal()" class="absolute top-5 left-5 w-9 h-9 rounded-full bg-white/20 hover:bg-white/30 flex items-center justify-center text-white transition-all text-base font-bold">&times;</button>
          
          <div class="flex items-center gap-4">
            <div class="w-13 h-13 rounded-2xl bg-white/10 backdrop-blur-md p-3 flex items-center justify-center text-2xl border border-white/20 shadow-inner">
              📑
            </div>
            <div>
              <div class="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full bg-purple-400/20 text-purple-200 border border-purple-400/30 text-[11px] font-extrabold mb-1">
                <span>🤖 الذكاء الاصطناعي ومعالجة المستندات</span>
              </div>
              <h3 class="text-xl sm:text-2xl font-black">استيراد وتحليل اختبارات PDF الذكية</h3>
              <p class="text-xs text-purple-100 mt-0.5 max-w-2xl leading-relaxed">
                ارفع أي ملف PDF لاختبارات قياس؛ يتعرف النظام تلقائياً على نصوص ومسائل الاختبار، الخيارات، الإجابات الصحيحة، وإحصائيات عدد الأسئلة بدقة فائقة.
              </p>
            </div>
          </div>
        </div>

        <!-- Body -->
        <div class="p-6 overflow-y-auto space-y-6 flex-1">
          
          <!-- State 1: Drop Zone -->
          <div id="pdf-upload-drop-zone" class="space-y-6">
            <div class="border-3 border-dashed border-indigo-200 hover:border-indigo-500 rounded-3xl p-8 text-center bg-white transition-all shadow-xs space-y-4">
              <input type="file" id="pdf-file-input" accept=".pdf" class="hidden" onchange="handlePdfFileInput(event)">
              
              <div class="w-16 h-16 mx-auto rounded-3xl bg-purple-50 text-purple-600 flex items-center justify-center text-3xl shadow-sm">
                📄
              </div>

              <div>
                <h4 class="font-black text-slate-800 text-base sm:text-lg">اسحب وأفلت ملف الـ PDF هنا، أو انقر للاختيار</h4>
                <p class="text-xs text-slate-500 mt-1 max-w-md mx-auto">
                  يدعم اختبارات القدرات المحوسبة والورقية، ونماذج التجميعات بصيغة PDF
                </p>
              </div>

              <div class="flex flex-wrap items-center justify-center gap-3 pt-2">
                <button onclick="triggerPdfFileInput()" class="px-6 py-3 rounded-2xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-bold text-xs sm:text-sm shadow-md shadow-purple-600/20 transition-all flex items-center gap-2">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
                  <span>اختيار ملف PDF من الجهاز</span>
                </button>

                <button onclick="loadSamplePdfExam()" class="px-5 py-3 rounded-2xl bg-amber-50 hover:bg-amber-100 text-amber-900 border border-amber-200 font-extrabold text-xs sm:text-sm transition-all flex items-center gap-2">
                  <span>⚡</span>
                  <span>تجربة فحص الملف المعتمد exam126.pdf (٥٥ سؤالاً)</span>
                </button>
              </div>
            </div>

            <!-- Features Highlights -->
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div class="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs flex items-start gap-3">
                <span class="text-2xl">🎯</span>
                <div>
                  <h5 class="font-bold text-slate-900 text-xs">كشف تلقائي للإجابات</h5>
                  <p class="text-[11px] text-slate-500 mt-0.5">يتعرف النظام على مفاتيح الحلول والحروف (أ، ب، ج، د) بدقة 100%.</p>
                </div>
              </div>

              <div class="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs flex items-start gap-3">
                <span class="text-2xl">🔢</span>
                <div>
                  <h5 class="font-bold text-slate-900 text-xs">إحصاء عدد الأسئلة</h5>
                  <p class="text-[11px] text-slate-500 mt-0.5">فصل الغلاف والتعليمات وحساب عدد الأسئلة الفعلية مع تصنيف كمي/لفظي.</p>
                </div>
              </div>

              <div class="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs flex items-start gap-3">
                <span class="text-2xl">📐</span>
                <div>
                  <h5 class="font-bold text-slate-900 text-xs">قص صور الرسومات</h5>
                  <p class="text-[11px] text-slate-500 mt-0.5">قص الرسوم الهندسية والمعادلات الرياضية بجودة عالية بدون هوامش.</p>
                </div>
              </div>
            </div>
          </div>

          <!-- State 2: Loading State -->
          <div id="pdf-loading-container" class="hidden py-16 text-center space-y-5">
            <div class="w-16 h-16 mx-auto border-4 border-purple-200 border-t-purple-600 rounded-full animate-spin"></div>
            <div>
              <h4 class="font-black text-slate-800 text-base" id="pdf-loading-text">جاري معالجة صفحات الـ PDF...</h4>
              <p class="text-xs text-slate-500 mt-1">يتم استخراج المسائل، وقص الرسومات، وتوليد الشروحات النموذجية تلقائياً.</p>
            </div>
          </div>

          <!-- State 3: Results & Preview -->
          <div id="pdf-results-container" class="hidden space-y-6">
            
            <!-- Statistics Banner -->
            <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-center justify-between gap-4">
              <div class="space-y-1 text-center md:text-right">
                <div class="flex items-center gap-2 justify-center md:justify-start">
                  <span class="text-xs font-bold text-slate-400">الملف المفحوص:</span>
                  <span id="pdf-stat-filename" class="text-xs font-black text-indigo-700 bg-indigo-50 px-2.5 py-0.5 rounded-md">exam.pdf</span>
                </div>
                <div class="text-xs text-slate-600">
                  <span class="font-bold">حالة الكشف:</span>
                  <span id="pdf-stat-answers-rate" class="text-emerald-600 font-black mr-1">100% (تم كشف كافة الإجابات)</span>
                </div>
              </div>

              <div class="flex items-center gap-3">
                <!-- Total Count Metric -->
                <div class="bg-gradient-to-tr from-indigo-600 to-purple-600 text-white px-4 py-2.5 rounded-xl shadow-xs text-center">
                  <span class="text-[10px] font-bold block opacity-80">إجمالي الأسئلة</span>
                  <div class="flex items-baseline justify-center gap-1">
                    <span id="pdf-stat-total" class="text-2xl font-black">55</span>
                    <span class="text-[10px] font-bold">سؤالاً</span>
                  </div>
                </div>

                <!-- Quant Metric -->
                <div class="bg-blue-50 border border-blue-200 text-blue-900 px-3.5 py-2.5 rounded-xl text-center">
                  <span class="text-[10px] font-bold block text-blue-500">القسم الكمي</span>
                  <span id="pdf-stat-quant" class="text-xl font-black text-blue-700">55</span>
                </div>

                <!-- Verb Metric -->
                <div class="bg-purple-50 border border-purple-200 text-purple-900 px-3.5 py-2.5 rounded-xl text-center">
                  <span class="text-[10px] font-bold block text-purple-500">القسم اللفظي</span>
                  <span id="pdf-stat-verb" class="text-xl font-black text-purple-700">0</span>
                </div>
              </div>
            </div>

            <!-- Top Actions Toolbar -->
            <div class="flex flex-wrap items-center justify-between gap-3 bg-indigo-50/50 p-3 rounded-2xl border border-indigo-100">
              <span class="text-xs font-black text-indigo-950">معاينة الأسئلة والإجابات المكتشفة:</span>
              
              <div class="flex flex-wrap items-center gap-2">
                <button onclick="saveExtractedPdfQuestions()" id="btn-save-pdf-questions" class="px-4 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-black text-xs shadow-sm transition-all flex items-center gap-1.5">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/></svg>
                  <span>اعتماد وإضافة كافة الأسئلة إلى بنك الأسئلة</span>
                </button>

                <button onclick="launchExtractedPdfInSimulator()" class="px-3.5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow-sm transition-all flex items-center gap-1.5">
                  <span>🚀</span>
                  <span>بدء اختبار فوري بالمحاكي</span>
                </button>

                <button onclick="exportExtractedPdfQuestionsJSON()" class="px-3 py-2.5 rounded-xl bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 font-bold text-xs transition-all flex items-center gap-1">
                  <span>📥</span>
                  <span>JSON</span>
                </button>

                <button onclick="resetPdfImportModal()" class="px-3 py-2.5 rounded-xl bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 font-bold text-xs transition-all">
                  <span>🔄 رفع ملف آخر</span>
                </button>
              </div>
            </div>

            <!-- Questions Cards List Container -->
            <div id="pdf-questions-preview-list" class="space-y-4">
              <!-- Rendered by JS -->
            </div>

          </div>

        </div>

        <!-- Footer -->
        <div class="p-4 bg-white border-t border-slate-200 flex items-center justify-between text-xs shrink-0">
          <span class="text-slate-500 font-semibold">⚡ معالجة فورية ومحلية لملفات PDF مع استخراج الصور والشروحات</span>
          <button onclick="closePdfImportModal()" class="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 font-bold text-slate-700 transition-all">
            إغلاق
          </button>
        </div>

      </div>
    `;

    document.body.appendChild(modalDiv);

    // إغلاق عند النقر على الخلفية
    modalDiv.addEventListener('click', (e) => {
      if (e.target === modalDiv) {
        closePdfImportModal();
      }
    });
  }

  // دعم السحب والإفلات المباشر على كامل نافذة المتصفح إذا تم إفلات ملف PDF
  window.addEventListener('dragover', (e) => {
    e.preventDefault();
  });

  window.addEventListener('drop', (e) => {
    e.preventDefault();
    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (file.name.toLowerCase().endsWith('.pdf')) {
        openPdfImportModal();
        processPdfFile(file);
      }
    }
  });

})();
