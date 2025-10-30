import { initializeApp } from "https://www.gstatic.com/firebasejs/10.5.0/firebase-app.js";
import { getDatabase, ref, get, onValue } from "https://www.gstatic.com/firebasejs/10.5.0/firebase-database.js";
import { child, update } from "https://www.gstatic.com/firebasejs/10.5.0/firebase-database.js";

let currentUser = "";

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

const currentPathname = window.location.pathname;

async function makeBillsAppear() {


  const billsRef = ref(db, 'congress/bills');
  const container = document.getElementById('bills');

  onValue(billsRef, async (snapshot) => {
    console.log("received snapshot!");
    const data = snapshot.val();
    container.innerHTML = '';

    if (data) {
      // Convert object to array with keys
      const billsArray = Object.entries(data)
        .map(([key, bill]) => ({ ...bill, id: `${bill.type}-${bill.number}` }))
        .filter((bill) => bill.actionDate)
        .sort((a, b) => new Date(b.actionDate) - new Date(a.actionDate))
        .slice(0, 10);

      // Fetch vote data for all bills
      const votesSnapshot = await get(ref(db, 'votes'));
      const votesData = votesSnapshot.exists() ? votesSnapshot.val() : {};

      // Display each bill
      billsArray.forEach((bill) => {
        const billVotes = votesData[bill.id] || { approve: 0, disapprove: 0 };
        const totalVotes = billVotes.approve + billVotes.disapprove;
        const approvePercent = totalVotes > 0 ? (billVotes.approve / totalVotes) * 100 : 50;
        const disapprovePercent = totalVotes > 0 ? (billVotes.disapprove / totalVotes) * 100 : 50;

        const div = document.createElement('div');
        div.className = 'bill-entry';

        div.innerHTML = `
              <a href="bill.html?id=${bill.id}" class="bill-link">
                <div class="bill-header">
                  <span class="bill-number">${bill.number}</span>
                  <span class="bill-type">${bill.type}</span>
                  <span class="bill-date">${bill.actionDate}</span>
                </div>
                
                <h3>${bill.title}</h3>
                
                ${totalVotes > 0 ? `
                  <div class="approval-bar-container">
                    <div class="approval-segment approve-segment" style="width: ${approvePercent}%"></div>
                    <div class="approval-segment disapprove-segment" style="width: ${disapprovePercent}%"></div>
                  </div>
                ` : ''}
                
                <div class="bill-engagement">
                  <div class="engagement-item approve-count">
                    <span class="engagement-icon">👍</span>
                    <span>${billVotes.approve}</span>
                  </div>
                  <div class="engagement-item disapprove-count">
                    <span class="engagement-icon">👎</span>
                    <span>${billVotes.disapprove}</span>
                  </div>
                </div>
              </a>    
            `;

        container.appendChild(div);
      });
    } else {
      container.innerHTML = `
            <div class="empty-state">
              <h3>No bills found</h3>
              <p>Check back later for updates</p>
            </div>
          `;
    }
  });
};

// Function to create a cute bill celebration animation
function createBillCelebration() {
  const celebration = document.createElement('div');
  celebration.className = 'streak-celebration';
  celebration.innerHTML = `
    <div class="celebrating-bill">
      <div class="bill-body">
        <div class="bill-lines">
          <div class="bill-line"></div>
          <div class="bill-line"></div>
          <div class="bill-line"></div>
          <div class="bill-line"></div>
        </div>
        <div class="bill-face">
          <div class="bill-eye eye-left"></div>
          <div class="bill-eye eye-right"></div>
          <div class="bill-smile"></div>
        </div>
      </div>
      <div class="bill-helmet">
        <div class="helmet-star">⭐</div>
        <div class="helmet-rim"></div>
      </div>
    </div>
  `;
  
  document.body.appendChild(celebration);
  setTimeout(() => celebration.remove(), 1500);
}

// Function to create confetti
function createConfetti() {
  const colors = ['#ff8c42', '#ec6918', '#5c99d1', '#08a4ff', '#ffd700'];
  const confettiCount = 30;

  for (let i = 0; i < confettiCount; i++) {
    const confetti = document.createElement('div');
    confetti.className = 'confetti';
    confetti.style.left = Math.random() * 100 + 'vw';
    confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
    confetti.style.animation = `confettiFall ${2 + Math.random() * 2}s linear forwards`;
    confetti.style.animationDelay = Math.random() * 0.5 + 's';
    document.body.appendChild(confetti);

    setTimeout(() => confetti.remove(), 5000);
  }
}

// Function to animate the streak number
function animateStreakNumber() {
  const streakValue = document.getElementById('streak-value');
  if (streakValue) {
    streakValue.classList.add('streak-number-pop');
    setTimeout(() => {
      streakValue.classList.remove('streak-number-pop');
    }, 600);
  }
}

// Function to show streak message
function showStreakMessage(streak) {
  const message = document.createElement('div');
  message.className = 'streak-message';
  message.textContent = ` ${streak} Day Streak! `;
  document.body.appendChild(message);
  setTimeout(() => message.remove(), 2000);
}

async function loadActiveUser() {
  const logout = document.getElementById('logout');
  const message = document.getElementById('message');
  const welcome = document.getElementById('welcome');

  try {
    const snapshot = await get(child(ref(db), 'users'));

    if (snapshot.exists()) {
      const users = snapshot.val();

      for (const key in users) {
        if (users[key].active === true) {
          currentUser = users[key].name;
          break;
        }
      }
    }

    welcome.textContent = currentUser ? `Hello, ${currentUser}!` : "Welcome! Log in or sign up to save your stats.";

    // Simulate loading some stats (replace with real data later)
    document.getElementById('streak-value').textContent = '7';
    document.getElementById('quiz-value').textContent = '130';
    document.getElementById('votes-value').textContent = '142';

    // Trigger cute celebration animation after a short delay
    setTimeout(() => {
      createBillCelebration();
      createConfetti();
      showStreakMessage(7);
      animateStreakNumber();
    }, 500);

  } catch (error) {
    console.error(error);
    welcome.textContent = "Welcome! Log in or sign up to save your stats.";
  }
}

const logoutEl = document.getElementById('logout');
const messageEl = document.getElementById('message');
if (logoutEl) {
  logoutEl.addEventListener('click', async (e) => {
    e.preventDefault();

    try {
      const snapshot = await get(child(ref(db), 'users'));

      if (snapshot.exists()) {
        const users = snapshot.val();

        for (const key in users) {
          if (users[key].active === true) {
            await update(ref(db, `users/${key}`), { active: false });

            if (messageEl) {
              messageEl.textContent = "Logout successful!";
              messageEl.style.color = "#8ba888";
            }
            setTimeout(() => {
              window.location.href = 'login.html';
            }, 1000);
            break;
          } else {
            setTimeout(() => {
              window.location.href = 'login.html';
            }, 1000);
          }
        }
      }
    } catch (error) {
      console.error(error);
      if (messageEl) {
        messageEl.textContent = "Error connecting to database.";
        messageEl.style.color = "#d17a5c";
      }
    }
  });
}

if (currentPathname === "/profile.html") {
  loadActiveUser();
} else if (currentPathname === "/index.html") {
  makeBillsAppear();
}