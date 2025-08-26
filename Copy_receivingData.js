//making https requests because all the api calls require it on api.gov 
//also excuse me for putting semicolons everywhere i'm more used to C++ so it's force of habit!
//note: i haven't worked in node.js for a few years so i tried http.get request method @ first BAD IDEA DO NOT DO 

async function getJsonWithAcceptHeader() {
  const url = 'https://api.congress.gov/v3/bill/117?fromDateTime=2022-08-04T04:02:00Z&toDateTime=2022-09-30T04:03:00Z&sort=updateDate+desc&format=json&api_key=FacEHXl6iKxBi2ejlZV3YtTo9EIPYMoscmDYvTgj';
  const {Pool } = require('pg');

   const pool = new Pool({
        user: 'postgres',
        host: '127.0.0.1',
        database: 'cong_app',
        password: 'congapp', //add your postgreSQL databse password~ 
        port: 5432,
        max: 20, // maximum number of clients in the pool
        idleTimeoutMillis: 30000, // how long a client is allowed to remain idle before being closed
    });

  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json' // Request JSON
      }
    });

    const contentType = response.headers.get('content-type');

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    if (contentType && contentType.includes('application/json')) {
      const data = await response.json();
      console.log('JSON response:', data);
      // to store data into SQL server Table Users 
      //YT video code here basically.
        await pool.query(''INSERT INTO Bills (test) VALUES ($1)', [data]');
  console.log('Data inserted into congapp table');



    } else {
      const text = await response.text();
      console.warn('Received non-JSON response:', text.slice(0, 200));
    }
  } catch (error) {
    console.error('Error fetching data:', error);
  } finally {
    await pool.end();
  }
}

getJsonWithAcceptHeader();











