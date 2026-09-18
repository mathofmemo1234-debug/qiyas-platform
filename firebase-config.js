// إعدادات الربط السحابي مع Firebase Firestore (اختياري)
// إذا رغبت في ربط المنصة بالسحابة ومزامنة بيانات الطلاب عن بُعد:
// 1. توجه إلى: https://console.firebase.google.com
// 2. أنشئ مشروعاً جديداً وفعّل Firestore Database
// 3. الصق بيانات مشروعك هنا، وسيقوم النظام بالاتصال السحابي تلقائياً

export const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "YOUR_PROJECT_ID.firebaseapp.com",
  projectId: "YOUR_PROJECT_ID",
  storageBucket: "YOUR_PROJECT_ID.firebasestorage.app",
  messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
  appId: "YOUR_APP_ID"
};

export const isFirebaseConfigured = () => {
  return firebaseConfig.apiKey && firebaseConfig.apiKey !== "YOUR_API_KEY";
};
