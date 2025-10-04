//--> config of firebase 
// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries
import { getDatabase } from "firebase/database";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyCS07UgX2GnmuufEQET-RYOtm8i0XaZkWk",
  authDomain: "orwell-ea558.firebaseapp.com",
  databaseURL: "https://orwell-ea558-default-rtdb.firebaseio.com",
  projectId: "orwell-ea558",
  storageBucket: "orwell-ea558.firebasestorage.app",
  messagingSenderId: "301391502605",
  appId: "1:301391502605:web:67c58902e72044cd03a444"
};



const app = initializeApp(firebaseConfig);
const database = getDatabase(app);

export { database };
export {app};


// Initialize Firebase












