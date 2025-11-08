# Prescribed Burn Project AI Agent

An AI-powered tool to gather public information relevant to planning prescribed burns based on location.

## Features
- Weather forecast, wind speeds, and humidity data
- Topography information (slope, altitude)
- Fuel sources (vegetation/land cover)
- Nearby water sources

## Free Data Sources Used
- **Weather**: National Weather Service API (weather.gov)
- **Geocoding**: Nominatim (OpenStreetMap)
- **Topography**: Open-Elevation API
- **Vegetation/Fuel**: OpenStreetMap land use data
- **Water Sources**: OpenStreetMap Overpass API

## Setup
```bash
pip install -r requirements.txt
python app.py
```

Visit http://localhost:5000 in your browser.
