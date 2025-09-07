const { Pool } = require('pg');

// This is the main function to fetch the data and insert it into the database
async function getJsonAndInsertToDB() {
  const url = 'https://api.congress.gov/v3/bill/117?fromDateTime=2022-08-04T04:02:00Z&toDateTime=2022-09-30T04:03:00Z&sort=updateDate+desc&format=json&api_key=FacEHXl6iKxBi2ejlZV3YtTo9EIPYMoscmDYvTgj';

  // Use a pool to manage database connections efficiently.
  const pool = new Pool({
    user: 'postgres',
    host: '127.0.0.1',
    database: 'cong_app',
    password: 'congapp', // This should be managed securely, e.g., using environment variables.
    port: 5432,
    max: 20,
    idleTimeoutMillis: 30000,
  });

  const client = await pool.connect();

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

    const data = await response.json();
    console.log('JSON response received.');

    // Start a transaction to ensure all inserts are successful or none are.
    await client.query('BEGIN');

    // Iterate over each bill in the 'bills' array.
    for (const bill of data.bills) {
      // 1. Insert into the latest_actions table first.
      const actionInsertQuery = 'INSERT INTO latest_actions (action_date, action_text) VALUES ($1, $2) RETURNING id';
      const actionValues = [
        bill.latestAction.actionDate,
        bill.latestAction.text
      ];

      const res = await client.query(actionInsertQuery, actionValues);
      const latestActionId = res.rows[0].id; // Get the ID of the newly created action.

      // 2. Insert into the bills table, using the action's ID as a foreign key.
      const billInsertQuery = `
        INSERT INTO bills (
          congress,
          number,
          origin_chamber,
          origin_chamber_code,
          title,
          type,
          update_date,
          update_date_including_text,
          url,
          latest_action_id
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)`;
      
      const billValues = [
        bill.congress,
        bill.number,
        bill.originChamber,
        bill.originChamberCode,
        bill.title,
        bill.type,
        bill.updateDate,
        bill.updateDateIncludingText,
        bill.url,
        latestActionId // This is the foreign key.
      ];

      await client.query(billInsertQuery, billValues);
      console.log(`Successfully inserted bill ${bill.number} into the database.`);
    }

    // Commit the transaction.
    await client.query('COMMIT');
    console.log('All data inserted successfully.');

  } catch (error) {
    // If any error occurs, rollback the transaction to undo all changes.
    await client.query('ROLLBACK');
    console.error('Error during data insertion, rolling back transaction:', error);
  } finally {
    // Release the client back to the pool.
    client.release();
  }
}

// Call the main function to run the process.
getJsonAndInsertToDB();
