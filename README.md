# FireScope AI Agent

An AI-powered tool to gather public information relevant to planning prescribed burns based on location.

## Features
- Weather forecast, wind speeds, and humidity data
- Topography information (slope, altitude)
- Fuel sources (vegetation/land cover)
- Nearby water sources

## Free Data Sources Used

### Real-Time Data (Updated Continuously)
- **Weather**: National Weather Service (NOAA) API
  - Updates: Hourly
  - Coverage: United States only
  - Data: Temperature, wind speed/direction, humidity, detailed forecasts

### Community-Maintained Data (Updated Continuously)
- **Geocoding**: Nominatim (OpenStreetMap)
  - Updates: Continuous community contributions
  - Coverage: Global
  - Data: City coordinates and location names

- **Vegetation/Fuel**: OpenStreetMap via Overpass API
  - Updates: Continuous community contributions
  - Coverage: Global (accuracy varies by region)
  - Data: Forests, grasslands, meadows, scrub vegetation

- **Water Sources**: OpenStreetMap via Overpass API
  - Updates: Continuous community contributions
  - Coverage: Global (accuracy varies by region)
  - Data: Lakes, rivers, reservoirs, fire hydrants

### Static Data (Historical)
- **Topography**: Open-Elevation API
  - Source: SRTM (Shuttle Radar Topography Mission) from 2000
  - Updates: Static - elevation data does not change
  - Coverage: Global
  - Data: Elevation, terrain classification

## Setup
```bash
pip install -r requirements.txt
python app.py
```

Visit http://localhost:5000 in your browser.
