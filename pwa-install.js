/**
 * pwa-install.js - محرك إدارة وتثبيت تطبيق منصة نبيه للقدرات PWA
 * يدعم جميع الأجهزة: Android, iOS (iPhone/iPad), Windows, macOS, Linux
 */

(function () {
  // المتغيرات العامة
  let deferredPrompt = null;
  const isIOS = (/iPad|iPhone|iPod/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1)) && !window.MSStream;
  const isAndroid = /Android/i.test(navigator.userAgent);
  const isMac = /Macintosh|MacIntel|MacPPC|Mac68K/i.test(navigator.userAgent) && !isIOS;
  const isWindows = /Windows/i.test(navigator.userAgent);
  const isStandalone = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;

  // تسجيل Service Worker
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('./sw.js')
        .then((reg) => {
          console.log('[PWA] تم تسجيل Service Worker بنجاح، النطاق:', reg.scope);
        })
        .catch((err) => {
          console.warn('[PWA] تعذر تسجيل Service Worker:', err);
        });
    });
  }

  // الاستماع لحدث جاهزية التثبيت (Chromium: Android, Windows, Chrome, Edge)
  window.addEventListener('beforeinstallprompt', (e) => {
    // منع النافذة المصغرة الافتراضية
    e.preventDefault();
    deferredPrompt = e;
    window.deferredPWAInstallPrompt = e;
    console.log('[PWA] التثبيت الفوري متاح (beforeinstallprompt جاهز)');
    updateInstallButtonsState(true);
  });

  // الاستماع لحدث اكتمال التثبيت
  window.addEventListener('appinstalled', () => {
    deferredPrompt = null;
    window.deferredPWAInstallPrompt = null;
    console.log('[PWA] تم تثبيت التطبيق بنجاح!');
    updateInstallButtonsState(false, true);
    showPwaToast('🎉 مبارك! تم تثبيت تطبيق منصة نبيه للقدرات بنجاح. يمكنك الآن فتحه مباشرة كـ تطبيق أصيل من شاشتك الرئيسية!');
    closePwaInstallModal();
  });

  // تطبيق كلاس standalone إذا كان التطبيق يعمل مسبقاً كتطبيق مثبت
  if (isStandalone) {
    document.documentElement.classList.add('pwa-standalone');
    window.addEventListener('DOMContentLoaded', () => {
      updateInstallButtonsState(false, true);
    });
  }

  // تحديث حالة أزرار التثبيت في الواجهة
  function updateInstallButtonsState(isReady, isAlreadyInstalled = false) {
    const desktopBtn = document.getElementById('pwa-header-install-btn');
    const mobileBtn = document.getElementById('pwa-mobile-install-btn');
    const heroCard = document.getElementById('pwa-hero-install-card');

    if (isAlreadyInstalled || isStandalone) {
      if (desktopBtn) {
        desktopBtn.innerHTML = `
          <svg class="w-4 h-4 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/></svg>
          <span class="text-xs font-bold text-emerald-700">التطبيق مفعّل</span>
        `;
        desktopBtn.classList.remove('from-sky-600', 'to-indigo-600', 'text-white', 'hover:from-sky-700');
        desktopBtn.classList.add('bg-emerald-50', 'border', 'border-emerald-200', 'cursor-default');
        desktopBtn.onclick = () => showPwaToast('✓ المنصة مثبتة وتعمل الآن بنمط التطبيق المستقل بكفاءة وسرعة عالية.');
      }
      if (mobileBtn) {
        mobileBtn.classList.add('hidden');
      }
      if (heroCard) {
        heroCard.classList.add('hidden');
      }
      return;
    }

    // إذا لم يكن مثبت
    if (desktopBtn) desktopBtn.classList.remove('hidden');
    if (mobileBtn) mobileBtn.classList.remove('hidden');
    if (heroCard) heroCard.classList.remove('hidden');
  }

  // النقر على زر التثبيت الرئيسي
  window.handlePwaInstallClick = async function () {
    if (isStandalone) {
      showPwaToast('✓ المنصة مثبتة وتعمل حالياً في وضع التطبيق المستقل.');
      return;
    }

    // إذا كان الحدث التلقائي متاحاً (Android / Windows / Chrome / Edge)
    if (deferredPrompt) {
      try {
        deferredPrompt.prompt();
        const { outcome } = await deferredPrompt.userChoice;
        console.log('[PWA] اختيار المستخدم للتثبيت:', outcome);
        if (outcome === 'accepted') {
          deferredPrompt = null;
          window.deferredPWAInstallPrompt = null;
        } else {
          // فتح الدليل التوضيحي إذا ألغى المستخدم
          openPwaInstallModal();
        }
      } catch (e) {
        console.error('[PWA] خطأ أثناء استدعاء نافذة التثبيت:', e);
        openPwaInstallModal();
      }
    } else {
      // فتح الدليل لجميع الأنظمة وخاصة iOS Safari أو المتصفحات الأخرى
      openPwaInstallModal();
    }
  };

  // فتح نافذة دليل التثبيت لجميع الأنظمة
  window.openPwaInstallModal = function () {
    let modal = document.getElementById('pwa-install-modal');
    if (!modal) {
      injectPwaModalDOM();
      modal = document.getElementById('pwa-install-modal');
    }
    
    // اختيار التبويب التلقائي بناء على نوع جهاز المستخدم
    if (isIOS) {
      switchPwaDeviceTab('ios');
    } else if (isAndroid) {
      switchPwaDeviceTab('android');
    } else {
      switchPwaDeviceTab('desktop');
    }

    modal.classList.remove('hidden');
    modal.classList.add('flex');
    document.body.style.overflow = 'hidden';
  };

  // إغلاق نافذة التثبيت
  window.closePwaInstallModal = function () {
    const modal = document.getElementById('pwa-install-modal');
    if (modal) {
      modal.classList.add('hidden');
      modal.classList.remove('flex');
    }
    document.body.style.overflow = '';
  };

  // التبديل بين أجهزة الدليل (iOS, Android, Desktop)
  window.switchPwaDeviceTab = function (tab) {
    const tabs = ['ios', 'android', 'desktop'];
    tabs.forEach((t) => {
      const btn = document.getElementById(`pwa-tab-btn-${t}`);
      const content = document.getElementById(`pwa-tab-content-${t}`);
      if (btn && content) {
        if (t === tab) {
          btn.className = 'flex-1 py-2.5 px-3 rounded-xl font-bold text-xs sm:text-sm transition-all flex items-center justify-center gap-2 bg-white text-sky-700 shadow-sm border border-sky-100';
          content.classList.remove('hidden');
        } else {
          btn.className = 'flex-1 py-2.5 px-3 rounded-xl font-bold text-xs sm:text-sm transition-all flex items-center justify-center gap-2 text-slate-500 hover:text-slate-800 hover:bg-slate-200/50';
          content.classList.add('hidden');
        }
      }
    });
  };

  // حقن واجهة المودال التفاعلي لجميع الأنظمة
  function injectPwaModalDOM() {
    const modalDiv = document.createElement('div');
    modalDiv.id = 'pwa-install-modal';
    modalDiv.className = 'fixed inset-0 z-50 hidden items-center justify-center p-4 bg-slate-900/60 backdrop-blur-md transition-opacity animate-fade-in';
    modalDiv.innerHTML = `
      <div class="relative w-full max-w-xl bg-white rounded-3xl shadow-2xl border border-slate-100 overflow-hidden flex flex-col max-h-[90vh]">
        
        <!-- Modal Header with App Branding -->
        <div class="bg-gradient-to-l from-sky-600 via-indigo-600 to-indigo-800 text-white p-6 relative">
          <button onclick="closePwaInstallModal()" class="absolute top-5 left-5 w-8 h-8 rounded-full bg-white/20 hover:bg-white/30 flex items-center justify-center text-white transition-all text-sm font-bold">✕</button>
          
          <div class="flex items-center gap-4">
            <img src="icons/icon-192.png" alt="منصة نبيه" class="w-14 h-14 rounded-2xl shadow-lg border-2 border-white/40">
            <div>
              <div class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-white/20 text-[11px] font-extrabold mb-1">
                <span>⚡ تطبيق خفيف وسريع</span>
              </div>
              <h3 class="text-xl font-black">تثبيت تطبيق «نَبِـيــهْ» على جهازك</h3>
              <p class="text-xs text-sky-100 font-medium mt-0.5">يعمل بدون متصفح، بسرعة فائقة، وتجربة سلسة بدون إعلانات أو تشتيت</p>
            </div>
          </div>
        </div>

        <!-- Device Selector Tabs -->
        <div class="p-3 bg-slate-100 border-b border-slate-200 flex gap-2">
          <button id="pwa-tab-btn-ios" onclick="switchPwaDeviceTab('ios')" class="flex-1 py-2.5 px-3 rounded-xl font-bold text-xs sm:text-sm transition-all flex items-center justify-center gap-2">
            <span>🍏</span>
            <span>آيفون / آيباد (iOS)</span>
          </button>
          <button id="pwa-tab-btn-android" onclick="switchPwaDeviceTab('android')" class="flex-1 py-2.5 px-3 rounded-xl font-bold text-xs sm:text-sm transition-all flex items-center justify-center gap-2">
            <span>🤖</span>
            <span>أندرويد (Android)</span>
          </button>
          <button id="pwa-tab-btn-desktop" onclick="switchPwaDeviceTab('desktop')" class="flex-1 py-2.5 px-3 rounded-xl font-bold text-xs sm:text-sm transition-all flex items-center justify-center gap-2">
            <span>💻</span>
            <span>كمبيوتر (PC / Mac)</span>
          </button>
        </div>

        <!-- Modal Body Content -->
        <div class="p-6 overflow-y-auto space-y-6 text-slate-800 text-sm">
          
          <!-- ================= TAB: iOS / iPhone / iPad ================= -->
          <div id="pwa-tab-content-ios" class="space-y-4">
            <div class="p-3.5 bg-amber-50 border border-amber-200 rounded-2xl flex items-start gap-3">
              <span class="text-xl">💡</span>
              <p class="text-xs text-amber-900 leading-relaxed font-semibold">
                على أجهزة آبل (iPhone / iPad)، يدعم متصفح <strong>Safari</strong> إضافة التطبيقات للشاشة الرئيسية مباشرة وبدون الحاجة لمتجر App Store.
              </p>
            </div>

            <h4 class="font-extrabold text-slate-900 text-sm flex items-center gap-2">
              <span class="w-6 h-6 rounded-full bg-sky-100 text-sky-700 flex items-center justify-center text-xs">١</span>
              <span>خطوات التثبيت في 3 ثوانٍ فقط:</span>
            </h4>

            <div class="space-y-3">
              <!-- Step 1 -->
              <div class="flex items-start gap-3.5 p-3.5 bg-slate-50 border border-slate-200/80 rounded-2xl">
                <div class="w-10 h-10 rounded-xl bg-sky-600 text-white flex items-center justify-center text-lg shadow-sm shrink-0">
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
                </div>
                <div>
                  <h5 class="font-bold text-slate-900 text-xs sm:text-sm">الخطوة 1: اضغط على زر المشاركة (Share)</h5>
                  <p class="text-xs text-slate-600 mt-0.5">ستجد أيقونة المشاركة (مربع يخرج منه سهم لأعلى ⎋) في الشريط السفلي لمتصفح Safari.</p>
                </div>
              </div>

              <!-- Step 2 -->
              <div class="flex items-start gap-3.5 p-3.5 bg-slate-50 border border-slate-200/80 rounded-2xl">
                <div class="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center text-lg shadow-sm shrink-0">
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
                </div>
                <div>
                  <h5 class="font-bold text-slate-900 text-xs sm:text-sm">الخطوة 2: اختر «إضافة إلى الشاشة الرئيسية»</h5>
                  <p class="text-xs text-slate-600 mt-0.5">مرر القائمة للأعلى قليلاً واختر <strong>(Add to Home Screen ➕)</strong>.</p>
                </div>
              </div>

              <!-- Step 3 -->
              <div class="flex items-start gap-3.5 p-3.5 bg-slate-50 border border-slate-200/80 rounded-2xl">
                <div class="w-10 h-10 rounded-xl bg-emerald-600 text-white flex items-center justify-center text-lg shadow-sm shrink-0">
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
                </div>
                <div>
                  <h5 class="font-bold text-slate-900 text-xs sm:text-sm">الخطوة 3: اضغط على «إضافة» (Add)</h5>
                  <p class="text-xs text-slate-600 mt-0.5">اضغط على زر إضافة في أعلى يمين الشاشة، وسيظهر تطبيق نبيه فوراً على شاشتك الرئيسية كأي تطبيق أصيل!</p>
                </div>
              </div>
            </div>
          </div>

          <!-- ================= TAB: Android ================= -->
          <div id="pwa-tab-content-android" class="space-y-4 hidden">
            <div class="p-4 bg-sky-50 border border-sky-200 rounded-2xl text-center space-y-3">
              <span class="text-3xl">🚀</span>
              <h4 class="font-extrabold text-sky-900 text-base">تثبيت فوري بنقرة واحدة</h4>
              <p class="text-xs text-sky-700 max-w-md mx-auto">
                يمكنك تثبيت تطبيق نبيه مباشرة على هاتفك الأندرويد دون مغادرة الصفحة:
              </p>
              <button onclick="triggerDirectInstallPrompt()" class="w-full py-3 px-4 rounded-2xl bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-700 hover:to-indigo-700 text-white font-black text-sm shadow-lg shadow-sky-600/25 transition-all flex items-center justify-center gap-2">
                <span>📲</span>
                <span>تثبيت التطبيق الآن على أندرويد</span>
              </button>
            </div>

            <div class="border-t border-slate-100 pt-3">
              <h5 class="font-extrabold text-slate-800 text-xs mb-2">إذا لم تظهر نافذة التثبيت تلقائياً:</h5>
              <ol class="space-y-2 text-xs text-slate-600 list-decimal list-inside pr-1">
                <li>اضغط على قائمة المتصفح (الثلاث نقاط <strong>⋮</strong>) في أعلى المتصفح.</li>
                <li>اختر <strong>«تثبيت التطبيق» (Install App)</strong> أو <strong>«إضافة إلى الشاشة الرئيسية»</strong>.</li>
                <li>أكّد التثبيت ليظهر التطبيق في قائمة التطبيقات على شاشتك.</li>
              </ol>
            </div>
          </div>

          <!-- ================= TAB: Desktop (Windows / Mac) ================= -->
          <div id="pwa-tab-content-desktop" class="space-y-4 hidden">
            <div class="p-4 bg-indigo-50 border border-indigo-200 rounded-2xl text-center space-y-3">
              <span class="text-3xl">💻</span>
              <h4 class="font-extrabold text-indigo-900 text-base">تثبيت التطبيق على الكمبيوتر المكتبي</h4>
              <p class="text-xs text-indigo-700 max-w-md mx-auto">
                يعمل تطبيق نبيه على Windows و Mac عبر متصفحات Chrome و Microsoft Edge كنافذة مستقلة بدون تشويش:
              </p>
              <button onclick="triggerDirectInstallPrompt()" class="w-full py-3 px-4 rounded-2xl bg-gradient-to-r from-indigo-600 to-sky-600 hover:from-indigo-700 hover:to-sky-700 text-white font-black text-sm shadow-lg shadow-indigo-600/25 transition-all flex items-center justify-center gap-2">
                <span>🖥️</span>
                <span>تثبيت التطبيق على جهاز الكمبيوتر</span>
              </button>
            </div>

            <div class="border-t border-slate-100 pt-3 space-y-2">
              <h5 class="font-extrabold text-slate-800 text-xs">طريقة أخرى للتثبيت عبر شريط العنوان:</h5>
              <div class="flex items-center gap-3 p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-700">
                <span class="text-xl">⬇️</span>
                <span>انقر على أيقونة التثبيت <strong>(شاشة بداخلها سهم أو علامة +)</strong> المتواجدة في أقصى شريط عنوان المتصفح (URL) ثم اضغط «تثبيت».</span>
              </div>
            </div>
          </div>

        </div>

        <!-- Modal Footer -->
        <div class="p-4 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs">
          <span class="text-slate-500 font-semibold">🔒 آمن ومجاني 100% ولا يستهلك مساحة التخزين</span>
          <button onclick="closePwaInstallModal()" class="px-4 py-2 rounded-xl bg-slate-200 hover:bg-slate-300 font-bold text-slate-700 transition-all">
            إغلاق
          </button>
        </div>

      </div>
    `;

    document.body.appendChild(modalDiv);

    // إغلاق عند النقر على الخلفية
    modalDiv.addEventListener('click', (e) => {
      if (e.target === modalDiv) {
        closePwaInstallModal();
      }
    });
  }

  // محاولة التثبيت المباشر من داخل المودال
  window.triggerDirectInstallPrompt = async function () {
    if (deferredPrompt) {
      try {
        deferredPrompt.prompt();
        const { outcome } = await deferredPrompt.userChoice;
        if (outcome === 'accepted') {
          deferredPrompt = null;
          closePwaInstallModal();
        }
      } catch (err) {
        console.error(err);
      }
    } else {
      showPwaToast('يرجى اتباع الخطوات الموضحة في القائمة أعلاه لإضافة التطبيق.');
    }
  };

  // إظهار إشعار Toast جذاب
  window.showPwaToast = function (message) {
    const existing = document.getElementById('pwa-custom-toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.id = 'pwa-custom-toast';
    toast.className = 'fixed bottom-5 right-5 left-5 md:left-auto md:max-w-md z-50 bg-slate-900/95 text-white p-4 rounded-2xl shadow-2xl border border-slate-700 backdrop-blur-md flex items-center gap-3 text-xs sm:text-sm font-bold transition-all transform translate-y-4 opacity-0';
    toast.innerHTML = `
      <span class="text-lg shrink-0">✨</span>
      <p class="flex-1">${message}</p>
      <button onclick="this.parentElement.remove()" class="text-slate-400 hover:text-white text-xs font-bold px-2 py-1">✕</button>
    `;

    document.body.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
      toast.classList.remove('translate-y-4', 'opacity-0');
      toast.classList.add('translate-y-0', 'opacity-100');
    });

    setTimeout(() => {
      if (toast.parentElement) {
        toast.classList.add('opacity-0', 'translate-y-4');
        setTimeout(() => toast.remove(), 300);
      }
    }, 5500);
  };

  // المزامنة الفورية عند تحميل الصفحة
  window.addEventListener('DOMContentLoaded', () => {
    updateInstallButtonsState(!!deferredPrompt, isStandalone);
  });

})();
