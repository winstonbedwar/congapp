//better webscraper 
//better titles (figure out a way to make them fun [legal name])
//quizzes 
//sentiment analysis done
//fix up frontend

import { initializeApp , deleteApp} from "firebase/app";
import { getDatabase, ref, child, get } from "firebase/database";
import fetch from 'node-fetch';
import fs from 'fs'; 

const firebaseConfig = {
      apiKey: "AIzaSyCS07UgX2GnmuufEQET-RYOtm8i0XaZkWk",
      authDomain: "orwell-ea558.firebaseapp.com",
      databaseURL: "https://orwell-ea558-default-rtdb.firebaseio.com",
      projectId: "orwell-ea558",
      storageBucket: "orwell-ea558.firebasestorage.app",
      messagingSenderId: "301391502605",
      appId: "1:301391502605:web:67c58902e72044cd03a444"
    };
const TEXT = "Celebrating the 100th anniversary of the founding of the Schomburg Center for Research in Black Culture.";
const WORLD_NEWS_API_KEY = "8e507cda7bc2442e9e907d46849996e7";

const app = initializeApp(firebaseConfig);
const db = getDatabase(app);

async function queryWorldNewsAPI(phrase) {
  const endpoint = "https://api.worldnewsapi.com/search-news";
  const params = new URLSearchParams({
    "api-key": WORLD_NEWS_API_KEY,
    "text": phrase,
    "news-sources": "https://www.bbc.com, https://www.reuters.com/",
    "language": "en",
    "page-size": "10"
  });

  const url = `${endpoint}?${params.toString()}`;

  try {
    const response = await fetch(url);
    if (!response.ok) {
      console.error("HTTP error status:", response.status);
      return [];
    }
    const data = await response.json();
    return Array.isArray(data.news) ? data.news : [];
  } catch (err) {
    console.error("Error querying World News API:", err);
    return [];
  }
}

async function getKeywordsAndSearch() {
  try {
    const snapshot = await get(child(ref(db), 'ranked_keywords'));
    if (!snapshot.exists()) {
      console.log("No data available in ranked_keywords");
      return;
    }

    const data = snapshot.val();
    const entries = Object.values(data).filter(item => item.original_text === TEXT);

    if (entries.length === 0) {
      console.log(`No entries found for: "${TEXT}"`);
      return;
    }

    const phrases = [];
    entries.forEach(entry => {
      if (Array.isArray(entry.keywords)) {
        entry.keywords.forEach(k => {
          if (typeof k.phrase === 'string') {
            phrases.push(k.phrase);
          }
        });
      }
    });

    console.log("Phrases to try:", phrases);
    let articles = []

    for (let i = 0; i < phrases.length; i++) {
      const phrase = phrases[i];
      console.log(`\nQuerying for phrase: "${phrase}"`);
      const results = await queryWorldNewsAPI(phrase);
      console.log(`Found ${results.length} articles for "${phrase}"`);

      if (results.length >= 2) {
        console.log(`Good enough results for "${phrase}". Processing results...`);
        results.forEach((article, idx) => {
          console.log(`${idx+1}. ${article.title} (Source: ${article.url})`);
        });
        articles = results; // Save results for writing
        break;
      } else {
        console.log(` Only ${results.length} results. Trying next phrase.`);
      }
    }

    const output = {
        query: TEXT,
        articles: articles
    }

    // Write the collected articles to JSON file
    fs.writeFileSync('articles.json', JSON.stringify(output, null, 2));
    console.log("Articles saved to articles.json");

  } catch (err) {
    console.error("Error retrieving keywords or searching:", err);
  } finally {
    await deleteApp(app); // Proper cleanup
  }
}

getKeywordsAndSearch();

// await deleteApp(app); // gracefully shuts down Firebase





// import { initializeApp } from "firebase/app";
// import { getDatabase, ref, get, child } from "firebase/database";

// // Firebase config
// const firebaseConfig = {
//   apiKey: "AIzaSyCS07UgX2GnmuufEQET-RYOtm8i0XaZkWk",
//   authDomain: "orwell-ea558.firebaseapp.com",
//   databaseURL: "https://orwell-ea558-default-rtdb.firebaseio.com",
//   projectId: "orwell-ea558",
//   storageBucket: "orwell-ea558.appspot.com",
//   messagingSenderId: "301391502605",
//   appId: "1:301391502605:web:67c58902e72044cd03a444"
// };

// const text = "Small Cemetery Conveyance Act";
// const app = initializeApp(firebaseConfig);
// const db = getDatabase(app);
// const dbRef = ref(db);

// async function getKeywordsAndQuery() {
//   try {
//     const snapshot = await get(child(dbRef, 'ranked_keywords'));

//     if (!snapshot.exists()) {
//       console.log("No data available");
//       return;
//     }

//     const data = snapshot.val();
//     const entries = Object.values(data).filter(item => item.original_text === text);

//     if (entries.length === 0) {
//       console.log(`No entries found for: "${text}"`);
//       return;
//     }

//     // Collect keywords in order (unsorted)
//     const phrases = [];
//     entries.forEach(entry => {
//       if (Array.isArray(entry.keywords)) {
//         entry.keywords.forEach(keyword => phrases.push(keyword.phrase));
//       }
//     });

//     // Sequential query with fallback
//     await queryWithFallback(phrases);

//   } catch (err) {
//     console.error("Error:", err);
//   }
// }

// async function queryWithFallback(phrases) {
//  async function queryWorldNewsAPI(phrase) {
//   const apiKey = "8e507cda7bc2442e9e907d46849996e7";  // replace with your key
//   const url = new URL("https://api.worldnewsapi.com/search-news");
  
//   // Set query parameters
//   url.searchParams.set("api-key", apiKey);
//   url.searchParams.set("text", phrase);
//   // Optional filters:
//   url.searchParams.set("news-sources", "https://www.foxnews.com,https://www.cnn.com");
//   url.searchParams.set("language", "en");
//   url.searchParams.set("page-size", "10");
  
//   try {
//     const response = await fetch(url.toString());
//     if (!response.ok) {
//       throw new Error(`HTTP error! status: ${response.status}`);
//     }
//     const data = await response.json();
//     return data.news || [];  // adjust based on actual field name
//   } catch (error) {
//     console.error("Error querying World News API:", error);
//     return [];
//   }
// }


//   console.log("Finished.");
// }


// getKeywordsAndQuery();