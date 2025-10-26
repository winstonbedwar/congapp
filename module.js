// import from html
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.5.0/firebase-app.js";
import { getDatabase, ref, onValue } from "https://www.gstatic.com/firebasejs/10.5.0/firebase-database.js";

async function makeBillsAppear() {

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
  const db = getDatabase(app);

  const billsRef = ref(db, 'congress/bills');
  const container = document.getElementById('bills');

  onValue(billsRef, (snapshot) => {
    console.log("received snapshot!");
    const data = snapshot.val();
    container.innerHTML = '';

    if (data) {
      // Convert object to array with keys
      const billsArray = Object.entries(data)
        .map(([key, bill]) => bill)
        .filter((bill) => bill.actionDate) // Only include bills with actionDate
        .sort((a, b) => new Date(b.actionDate) - new Date(a.actionDate)) // Sort by actionDate DESC
        .slice(0, 10); // Get top 10

      // Display each bill
      billsArray.forEach((bill, index) => {
        const div = document.createElement('div');

        div.className = index === 0 ? 'bill featured-bill' : 'bill';

        div.innerHTML = `
      <a href ="bill.html?id=${bill.type}-${bill.number}" class="bill-link">
        <h3>${bill.title}</h3>
        <p><strong>Number:</strong> ${bill.number} &nbsp; <strong>Type:</strong> ${bill.type} &nbsp; <strong>Updated:</strong> ${bill.actionDate}</p>
        </a>    
      `;

        container.appendChild(div);
      });
    } else {
      container.innerHTML = '<p>No bills found.</p>';
    }
  });
};

makeBillsAppear();