import { initializeApp, deleteApp } from "firebase/app";
import { getDatabase, ref, child, get } from "firebase/database";
import fetch from 'node-fetch';
import fs from 'fs';

// === FIREBASE CONFIGURATION ===
const firebaseConfig = {
  apiKey: "AIzaSyCS07UgX2GnmuufEQET-RYOtm8i0XaZkWk",
  authDomain: "orwell-ea558.firebaseapp.com",
  databaseURL: "https://orwell-ea558-default-rtdb.firebaseio.com",
  projectId: "orwell-ea558",
  storageBucket: "orwell-ea558.firebasestorage.app",
  messagingSenderId: "301391502605",
  appId: "1:301391502605:web:67c58902e72044cd03a444"
};

// === CONSTANTS ===
const TEXT = "Expressing support for the recognition of September 26, 2025, as 'World Contraception Day' and expressing the sense of the House of Representatives regarding global and domestic access to contraception.";
const FIRECRAWL_API_KEY = "fc-5dbb378635a049a3a72295e321e69716"; // Replace with your actual key

// === INITIALIZE FIREBASE ===
const app = initializeApp(firebaseConfig);
const db = getDatabase(app);

// === FIRECRAWL API FUNCTION ===
async function queryFirecrawlAPI(phrase) {
  const endpoint = "https://api.firecrawl.dev/v1/search";

  const headers = {
    "Authorization": `Bearer ${FIRECRAWL_API_KEY}`,
    "Content-Type": "application/json"
  };

  const body = JSON.stringify({
    query: phrase,
    numResults: 2,
    // siteFilters: ["bbc.com", "reuters.com"] 
  
  });

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers,
      body
    });

    if (!response.ok) {
      console.error("Firecrawl API error status:", response.status);
      return [];
    }

    const data = await response.json();
    return Array.isArray(data.results) ? data.results : [];

  } catch (err) {
    console.error("Error querying Firecrawl API:", err);
    return [];
  }
}

// === MAIN FUNCTION ===
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
    let articles = [];

    for (let i = 0; i < phrases.length; i++) {
      const phrase = phrases[i];
      console.log(`\nQuerying Firecrawl for phrase: "${phrase}"`);
      const results = await queryFirecrawlAPI(phrase);
      console.log(`Found ${results.length} articles for "${phrase}"`);

      if (results.length >= 2) {
        console.log(`Good enough results for "${phrase}". Processing results...`);
        results.forEach((article, idx) => {
          console.log(`${idx + 1}. ${article.title} (Source: ${article.url})`);
        });
        articles = results; // Save results for writing
        break;
      } else {
        console.log(`⏭ Only ${results.length} results. Trying next phrase.`);
      }
    }

    const output = {
      query: TEXT,
      articles: articles    
    };

    // Write to file
    fs.writeFileSync('articles.json', JSON.stringify(output, null, 2));
    console.log("Articles saved to articles.json");

  } catch (err) {
    console.error("Error retrieving keywords or searching:", err);
  } finally {
    await deleteApp(app); // Proper cleanup
  }
}

// === EXECUTE MAIN ===
getKeywordsAndSearch();
