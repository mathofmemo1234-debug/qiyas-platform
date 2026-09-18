// firebase-config.js - مفاتيح وإعدادات مشروع Firebase Cloud Firestore
const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "YOUR_PROJECT_ID.firebaseapp.com",
  projectId: "YOUR_PROJECT_ID",
  storageBucket: "YOUR_PROJECT_ID.firebasestorage.app",
  messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
  appId: "YOUR_APP_ID"
};

// Make available globally in browser and in Node/ES modules
if (typeof window !== 'undefined') {
  window.defaultFirebaseConfig = firebaseConfig;
}
if (typeof module !== 'undefined' && module.exports) {
  module.exports = firebaseConfig;
}
