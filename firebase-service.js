// firebase-service.js - منظومة الربط والمزامنة السحابية مع Firebase Cloud Firestore
(function (window) {
  let db = null;
  let auth = null;
  let isFirebaseReady = false;

  // 1. استرجاع إعدادات Firebase المخزنة
  function getFirebaseConfig() {
    const saved = localStorage.getItem('qiyas_firebase_config');
    if (saved) {
      try {
        const cfg = JSON.parse(saved);
        if (cfg && cfg.apiKey && cfg.apiKey !== 'YOUR_API_KEY') {
          return cfg;
        }
      } catch (e) {}
    }
    if (window.defaultFirebaseConfig && window.defaultFirebaseConfig.apiKey && window.defaultFirebaseConfig.apiKey !== 'YOUR_API_KEY') {
      return window.defaultFirebaseConfig;
    }
    return null;
  }

  // 2. فحص حالة الاتصال
  function isConnected() {
    return isFirebaseReady && db !== null;
  }

  // 3. تهيئة الاتصال بـ Firebase
  function init(config) {
    const cfg = config || getFirebaseConfig();
    if (!cfg || !window.firebase) {
      isFirebaseReady = false;
      db = null;
      return false;
    }

    try {
      if (!firebase.apps || !firebase.apps.length) {
        firebase.initializeApp(cfg);
      }
      db = firebase.firestore();
      auth = firebase.auth ? firebase.auth() : null;
      isFirebaseReady = true;
      console.log("✓ Firebase Cloud Firestore initialized successfully for project:", cfg.projectId);
      return true;
    } catch (err) {
      console.warn("Firebase initialization warning:", err.message);
      isFirebaseReady = false;
      db = null;
      return false;
    }
  }

  // 4. اختبار الاتصال بقاعدة البيانات
  async function testConnection(cfg) {
    if (!window.firebase) {
      return { success: false, message: "مكتبة Firebase لم يتم تحميلها في المتصفح." };
    }
    try {
      let app;
      try {
        app = firebase.app("testApp");
      } catch (e) {
        app = firebase.initializeApp(cfg, "testApp");
      }
      const testDb = app.firestore();
      const testRef = testDb.collection('_qiyas_ping').doc('status');
      await testRef.set({ ping: true, timestamp: Date.now(), project: cfg.projectId });
      const doc = await testRef.get();
      if (doc.exists) {
        return { success: true, message: `تم الاتصال بنجاح بقاعدة بيانات Firestore للمشروع (${cfg.projectId})!` };
      } else {
        return { success: false, message: "تم الاتصال ولكن تعذرت قراءة الوثيقة التجريبية." };
      }
    } catch (err) {
      return { success: false, message: `فشل الاتصال: ${err.message}` };
    }
  }

  // 5. رفع ومزامنة الأسئلة بالكامل إلى Firestore
  async function uploadQuestions(questionsList, onProgress) {
    if (!isConnected()) {
      throw new Error("قاعدة بيانات Firebase غير متصلة. يرجى تهيئة المفاتيح أولاً.");
    }

    const batchSize = 100;
    let totalUploaded = 0;

    for (let i = 0; i < questionsList.length; i += batchSize) {
      const batch = db.batch();
      const chunk = questionsList.slice(i, i + batchSize);

      chunk.forEach(q => {
        const docRef = db.collection('questions').doc(String(q.id));
        batch.set(docRef, {
          ...q,
          updatedAt: firebase.firestore.FieldValue.serverTimestamp()
        }, { merge: true });
      });

      await batch.commit();
      totalUploaded += chunk.length;
      if (onProgress) {
        onProgress(totalUploaded, questionsList.length);
      }
    }

    return totalUploaded;
  }

  // 6. تحميل جميع الأسئلة من Firestore
  async function downloadQuestions() {
    if (!isConnected()) return null;
    try {
      const snapshot = await db.collection('questions').orderBy('id', 'asc').get();
      if (snapshot.empty) return [];
      const list = [];
      snapshot.forEach(doc => list.push(doc.data()));
      return list;
    } catch (e) {
      console.error("Error fetching questions from Firestore:", e);
      return null;
    }
  }

  // 7. مزامنة بيانات الطلاب
  async function syncStudent(student) {
    if (!isConnected() || !student || !student.username) return;
    try {
      await db.collection('students').doc(student.username).set({
        ...student,
        updatedAt: firebase.firestore.FieldValue.serverTimestamp()
      }, { merge: true });
    } catch (e) {
      console.warn("Could not sync student to Firestore:", e);
    }
  }

  async function fetchStudents() {
    if (!isConnected()) return [];
    try {
      const snapshot = await db.collection('students').get();
      const list = [];
      snapshot.forEach(doc => list.push(doc.data()));
      return list;
    } catch (e) {
      console.error("Error fetching students from Firestore:", e);
      return [];
    }
  }

  // 8. حفظ نتيجة اختبار في السحابة
  async function recordTestResult(studentUsername, result) {
    if (!isConnected()) return;
    try {
      const resDoc = {
        username: studentUsername || 'guest',
        ...result,
        createdAt: firebase.firestore.FieldValue.serverTimestamp()
      };
      await db.collection('test_results').add(resDoc);

      if (studentUsername && studentUsername !== 'guest') {
        const studentRef = db.collection('students').doc(studentUsername);
        await studentRef.update({
          history: firebase.firestore.FieldValue.arrayUnion(result)
        });
      }
    } catch (e) {
      console.warn("Could not record test result to Firestore:", e);
    }
  }

  // Export to window
  window.FirebaseService = {
    getFirebaseConfig,
    isConnected,
    init,
    testConnection,
    uploadQuestions,
    downloadQuestions,
    syncStudent,
    fetchStudents,
    recordTestResult
  };

})(window);
