// firebase-config.js - مفاتيح وإعدادات مشروع Firebase Cloud Firestore
const firebaseConfig = {
  apiKey: "AIzaSyAFBq8PJuSeAh8yYEE3_0b9ceDHUT-e8SI",
  authDomain: "qiyas-training-3dcf3.firebaseapp.com",
  projectId: "qiyas-training-3dcf3",
  storageBucket: "qiyas-training-3dcf3.firebasestorage.app",
  messagingSenderId: "331912816759",
  appId: "1:331912816759:web:8fb46a516ad38b9c87be72"
};

// Make available globally in browser and in Node/ES modules
if (typeof window !== 'undefined') {
  window.defaultFirebaseConfig = firebaseConfig;
}
if (typeof module !== 'undefined' && module.exports) {
  module.exports = firebaseConfig;
}
