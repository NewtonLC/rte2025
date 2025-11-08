import requests
from geopy.geocoders import Nominatim
from typing import Dict, Any
import time

class PrescribedBurnAgent:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="prescribed_burn_agent")
    
    def analyze_location(self, city: str) -> Dict[str, Any]:
        """Main orchestration method to gather all burn-relevant data"""
        
        # Step 1: Geocode the city
        location_data = self._geocode_city(city)
        lat = location_data['latitude']
        lon = location_data['longitude']
        
        # Step 2: Gather data from various sources
        weather_data = self._get_weather_data(lat, lon)
        topography_data = self._get_topography_data(lat, lon)
        fuel_data = self._get_fuel_sources(lat, lon)
        water_sources = self._get_water_sources(lat, lon)
        
        # Step 3: Compile comprehensive report
        return {
            'location': location_data,
            'weather': weather_data,
            'topography': topography_data,
            'fuel_sources': fuel_data,
            'water_sources': water_sources,
            'burn_assessment': self._assess_burn_conditions(weather_data)
        }
    
    def _geocode_city(self, city: str) -> Dict[str, Any]:
        """Convert city name to coordinates"""
        location = self.geolocator.geocode(city)
        if not location:
            raise ValueError(f"Could not find location: {city}")
        
        return {
            'source': 'Nominatim (OpenStreetMap)',
            'name': location.address,
            'latitude': location.latitude,
            'longitude': location.longitude
        }
    
    def _get_weather_data(self, lat: float, lon: float) -> Dict[str, Any]:
        """Fetch weather data from National Weather Service"""
        try:
            # Get grid point
            points_url = f"https://api.weather.gov/points/{lat},{lon}"
            headers = {'User-Agent': 'PrescribedBurnAgent/1.0'}
            
            response = requests.get(points_url, headers=headers, timeout=10)
            response.raise_for_status()
            points_data = response.json()
            
            # Get both regular forecast and hourly forecast for humidity data
            forecast_url = points_data['properties']['forecast']
            hourly_forecast_url = points_data['properties']['forecastHourly']
            
            forecast_response = requests.get(forecast_url, headers=headers, timeout=10)
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()
            
            # Get hourly forecast for humidity
            hourly_response = requests.get(hourly_forecast_url, headers=headers, timeout=10)
            hourly_response.raise_for_status()
            hourly_data = hourly_response.json()
            
            periods = forecast_data['properties']['periods'][:3]  # Next 3 periods
            hourly_periods = hourly_data['properties']['periods']
            
            # Normalize period names to Today/Tonight/Tomorrow and get humidity
            normalized_periods = []
            for i, p in enumerate(periods):
                original_name = p['name']
                
                # Determine normalized name based on position and original name
                if i == 0:
                    # First period - check if it's a night period
                    if 'night' in original_name.lower():
                        normalized_name = 'Tonight'
                    else:
                        normalized_name = 'Today'
                elif i == 1:
                    # Second period - usually the opposite of first (day/night)
                    if normalized_periods[0]['name'] == 'Today':
                        normalized_name = 'Tonight'
                    else:
                        normalized_name = 'Tomorrow'
                else:
                    # Third period
                    if normalized_periods[1]['name'] == 'Tonight':
                        normalized_name = 'Tomorrow'
                    else:
                        normalized_name = 'Tomorrow Night'
                
                # Try to get humidity from the period itself first
                humidity = None
                if 'relativeHumidity' in p and p['relativeHumidity']:
                    if isinstance(p['relativeHumidity'], dict):
                        humidity = p['relativeHumidity'].get('value')
                    else:
                        humidity = p['relativeHumidity']
                
                # If not found, try to match with hourly forecast (use corresponding hours)
                if humidity is None and hourly_periods:
                    # Use hourly periods that correspond to this forecast period
                    start_idx = i * 4  # Approximate: each 12-hour period = ~4 hourly periods
                    for hourly in hourly_periods[start_idx:start_idx + 4]:
                        if hourly.get('relativeHumidity'):
                            humidity_data = hourly['relativeHumidity']
                            if isinstance(humidity_data, dict):
                                humidity = humidity_data.get('value')
                            else:
                                humidity = humidity_data
                            if humidity is not None:
                                break
                
                normalized_periods.append({
                    'name': normalized_name,
                    'original_name': original_name,
                    'temperature': p['temperature'],
                    'temperature_unit': p['temperatureUnit'],
                    'wind_speed': p['windSpeed'],
                    'wind_direction': p['windDirection'],
                    'humidity': humidity if humidity is not None else 'N/A',
                    'short_forecast': p['shortForecast'],
                    'detailed_forecast': p['detailedForecast']
                })
            
            return {
                'source': 'National Weather Service (NOAA)',
                'forecast': normalized_periods
            }
        except Exception as e:
            return {'error': f"Weather data unavailable: {str(e)}"}

    def _get_topography_data(self, lat: float, lon: float) -> Dict[str, Any]:
        """Fetch elevation and topography data"""
        try:
            url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            elevation = data['results'][0]['elevation']
            
            # Sample nearby points for slope calculation
            offset = 0.01  # roughly 1km
            nearby_points = [
                (lat + offset, lon),
                (lat - offset, lon),
                (lat, lon + offset),
                (lat, lon - offset)
            ]
            
            locations_str = '|'.join([f"{p[0]},{p[1]}" for p in nearby_points])
            nearby_url = f"https://api.open-elevation.com/api/v1/lookup?locations={locations_str}"
            nearby_response = requests.get(nearby_url, timeout=10)
            nearby_data = nearby_response.json()
            
            elevations = [r['elevation'] for r in nearby_data['results']]
            elevation_range = max(elevations) - min(elevations)
            
            return {
                'source': 'Open-Elevation API (SRTM 2000)',
                'elevation_meters': elevation,
                'elevation_feet': round(elevation * 3.28084, 1),
                'elevation_range_nearby': round(elevation_range, 1),
                'terrain_note': self._classify_terrain(elevation_range)
            }
        except Exception as e:
            return {'error': f"Topography data unavailable: {str(e)}"}
    
    def _classify_terrain(self, elevation_range: float) -> str:
        """Classify terrain based on elevation variation"""
        if elevation_range < 10:
            return "Flat terrain"
        elif elevation_range < 50:
            return "Gently rolling terrain"
        elif elevation_range < 100:
            return "Moderately hilly terrain"
        else:
            return "Steep/mountainous terrain"
    
    def _get_fuel_sources(self, lat: float, lon: float) -> Dict[str, Any]:
        """Query OpenStreetMap for vegetation and land use"""
        try:
            overpass_url = "http://overpass-api.de/api/interpreter"
            
            # Query for natural features and land use within 5km radius
            query = f"""
            [out:json];
            (
              way["natural"="wood"](around:5000,{lat},{lon});
              way["landuse"="forest"](around:5000,{lat},{lon});
              way["landuse"="grass"](around:5000,{lat},{lon});
              way["landuse"="meadow"](around:5000,{lat},{lon});
              way["natural"="grassland"](around:5000,{lat},{lon});
              way["natural"="scrub"](around:5000,{lat},{lon});
            );
            out body;
            >;
            out skel qt;
            """
            
            response = requests.get(overpass_url, params={'data': query}, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Categorize fuel types
            fuel_types = {}
            for element in data.get('elements', []):
                if element['type'] == 'way':
                    tags = element.get('tags', {})
                    fuel_type = tags.get('natural') or tags.get('landuse')
                    if fuel_type:
                        fuel_types[fuel_type] = fuel_types.get(fuel_type, 0) + 1
            
            return {
                'source': 'OpenStreetMap via Overpass API',
                'fuel_types_found': fuel_types,
                'total_areas': len([e for e in data.get('elements', []) if e['type'] == 'way']),
                'dominant_fuel': max(fuel_types.items(), key=lambda x: x[1])[0] if fuel_types else 'Unknown'
            }
        except Exception as e:
            return {'error': f"Fuel source data unavailable: {str(e)}"}
    
    def _get_water_sources(self, lat: float, lon: float) -> Dict[str, Any]:
        """Find nearby water sources from OpenStreetMap"""
        try:
            overpass_url = "http://overpass-api.de/api/interpreter"
            
            # Query for water sources within 10km
            query = f"""
            [out:json];
            (
              way["natural"="water"](around:10000,{lat},{lon});
              way["waterway"](around:10000,{lat},{lon});
              node["emergency"="fire_hydrant"](around:5000,{lat},{lon});
              way["landuse"="reservoir"](around:10000,{lat},{lon});
            );
            out body;
            >;
            out skel qt;
            """
            
            response = requests.get(overpass_url, params={'data': query}, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            water_types = {}
            hydrants = 0
            
            for element in data.get('elements', []):
                tags = element.get('tags', {})
                
                if tags.get('emergency') == 'fire_hydrant':
                    hydrants += 1
                else:
                    water_type = tags.get('natural') or tags.get('waterway') or tags.get('landuse')
                    if water_type:
                        water_types[water_type] = water_types.get(water_type, 0) + 1
            
            return {
                'source': 'OpenStreetMap via Overpass API',
                'water_bodies': water_types,
                'fire_hydrants': hydrants,
                'total_water_sources': len(data.get('elements', []))
            }
        except Exception as e:
            return {'error': f"Water source data unavailable: {str(e)}"}
    
    def _assess_burn_conditions(self, weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """Provide basic burn condition assessment based on weather"""
        if 'error' in weather_data:
            return {'assessment': 'Unable to assess - weather data unavailable'}
        
        try:
            current = weather_data['forecast'][0]
            temp = current['temperature']
            humidity = current.get('humidity', 'N/A')
            wind = current['wind_speed']
            
            concerns = []
            
            # Parse wind speed (format like "10 mph" or "5 to 10 mph")
            wind_value = int(''.join(filter(str.isdigit, wind.split()[0])))
            
            if wind_value > 15:
                concerns.append("High wind speeds - increased fire spread risk")
            if isinstance(humidity, (int, float)) and humidity < 30:
                concerns.append("Low humidity - increased fire intensity risk")
            if temp > 85:
                concerns.append("High temperature - increased fire behavior risk")
            
            return {
                'concerns': concerns if concerns else ['Conditions appear moderate'],
                'recommendation': 'Consult with fire management professionals before proceeding'
            }
        except Exception as e:
            return {'assessment': f'Unable to assess conditions: {str(e)}'}
