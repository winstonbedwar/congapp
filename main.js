/**List of to do:
 * sentiment analysis 
 * better loading idea
 * finish profile page? set up
 * scroll set up for signing up (or whole page set up??????) 
 * better index.html top set up 
 * rethink bill side set up 
 */




import { database, app } from './firebase_config.js';
import { getDatabase, ref, set } from "firebase/database";
import { deleteApp } from "firebase/app";
import { initializeApp } from "firebase/app";
import fetch from 'node-fetch';

async function pushJsontoFirebase() {
  const url = 'https://api.congress.gov/v3/bill/119?format=json&offset=0&limit=100&fromDateTime=2022-08-04T04:02:00Z&toDateTime=2025-09-30T04:03:00Z&sort=updateDate+desc&api_key=FacEHXl6iKxBi2ejlZV3YtTo9EIPYMoscmDYvTgj';

  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const contentType = response.headers.get('content-type');

    if (contentType && contentType.includes('application/json')) {
      const data = await response.json();
      console.log('JSON response:', data);


      const bills = data.bills;

      // Iterate through each bill and store it separately
      for (const bill of bills) {
        const billTitle = bill.title || 'unknown';
        //dumb fixture for path name problem 
        let newBillTitle = ''
        for (let i = 0; i < billTitle.length; i++) {
          if (!(billTitle[i] == '.' || billTitle[i] == '#' || billTitle[i] == '$' || billTitle[i] == '[' || billTitle[i] == ']')) {
            newBillTitle += billTitle[i];
          }
          else {
            continue;
          }
        }


        // Define a unique path for each bill
        const billKey = `${bill.type}-${bill.number}`;  // e.g., hr-123
        const billRef = ref(database, `congress/bills/${billKey}`);


        // Store just the bill info
        await set(billRef, {
          number: bill.number,
          title: bill.title,
          type: bill.type,
          actionDate: bill.latestAction.actionDate,
          url: bill.url          // Add more fields here as needed
        });


        console.log(`Stored bill ${newBillTitle} successfully.`);
      }

    } else {
      const text = await response.text();
      console.warn('Received non-JSON response:', text.slice(0, 200));
    }
  } catch (error) {
    console.error('Error fetching or storing data:', error);
  }
  finally {
    // Terminate Firebase app to close all connections
    await deleteApp(app);
    console.log("Firebase app deleted, process will now exit.");
  }
}

pushJsontoFirebase();
