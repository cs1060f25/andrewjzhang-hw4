const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const cors = require('cors');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Valid measure names
const VALID_MEASURES = [
  'Violent crime rate',
  'Unemployment',
  'Children in poverty',
  'Diabetic screening',
  'Mammography screening',
  'Preventable hospital stays',
  'Uninsured',
  'Sexually transmitted infections',
  'Physical inactivity',
  'Adult obesity',
  'Premature Death',
  'Daily fine particulate matter'
];

// Database connection
const dbPath = path.join(__dirname, 'data.db');

function getDatabase() {
  return new sqlite3.Database(dbPath, (err) => {
    if (err) {
      console.error('Error opening database:', err.message);
    }
  });
}

// County data endpoint
app.post('/county_data', (req, res) => {
  try {
    // Check for coffee=teapot (HTTP 418 I'm a teapot)
    if (req.body.coffee === 'teapot') {
      return res.status(418).send('418');
    }

    const { zip, measure_name } = req.body;

    // Validate required parameters
    if (!zip || !measure_name) {
      return res.status(400).send('400');
    }

    // Validate ZIP code format (5 digits)
    if (!/^\d{5}$/.test(zip)) {
      return res.status(400).send('400');
    }

    // Validate measure_name
    if (!VALID_MEASURES.includes(measure_name)) {
      return res.status(400).send('400');
    }

    const db = getDatabase();

    // Query to join zip_county and county_health_rankings tables
    const query = `
      SELECT DISTINCT
        chr.state,
        chr.county,
        chr.state_code,
        chr.county_code,
        chr.year_span,
        chr.measure_name,
        chr.measure_id,
        chr.numerator,
        chr.denominator,
        chr.raw_value,
        chr.confidence_interval_lower_bound,
        chr.confidence_interval_upper_bound,
        chr.data_release_year,
        chr.fipscode
      FROM zip_county zc
      JOIN county_health_rankings chr ON (
        zc.state_abbreviation = chr.state AND 
        zc.county = chr.county
      )
      WHERE zc._zip = ? AND chr.measure_name = ?
      ORDER BY chr.data_release_year DESC
    `;

    db.all(query, [zip, measure_name], (err, rows) => {
      if (err) {
        console.error('Database error:', err);
        return res.status(404).send('404');
      }

      if (rows.length === 0) {
        return res.status(404).send('404');
      }

      res.json(rows);
    });

    db.close();

  } catch (error) {
    console.error('Server error:', error);
    res.status(404).send('404');
  }
});

// Handle 404 for other endpoints
app.use((req, res) => {
  res.status(404).send('404');
});

// Error handling middleware
app.listen(PORT, () => {
  console.log(`County Data API server running on port ${PORT}`);
  console.log(`Test with: curl -H "content-type:application/json" -d '{"zip":"02138","measure_name":"Adult obesity"}' http://localhost:${PORT}/county_data`);
});

module.exports = app;