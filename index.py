from flask import Flask,jsonify, render_template, send_from_directory
import requests
import redis
from pymongo import MongoClient
from math import radians, sin, cos, sqrt, atan2

app = Flask(__name__)

# Connect to the local Redis server
redis_client = redis.StrictRedis(host='127.0.0.1', port=6379, decode_responses=True)


# FlightAware AeroAPI details
# /airports/{id}/flights/arrivals
aeroapi_key = 'iWgNuDXdfIjenXrVayeDLYoCF4sxR4Ds'
aeroapi_url = 'https://aeroapi.flightaware.com/aeroapi/airports/FRA/flights/arrivals'

# Haversine formula for distance calculation
def haversine_distance(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = 6371 * c  # Earth radius in km
    return distance

# Fetch Flight Data Function using AeroAPI
def fetch_flight_data():
    # Check if flight data is cached in Redis
    cached_data = redis_client.get('flight_data')
    if cached_data:
        return json.loads(cached_data)

    # Request data from AeroAPI
    headers = {
        'x-apikey': aeroapi_key
    }
    params = {
        'origin': 'EDDF',  # Frankfurt Airport ICAO code
    }

    response = requests.get(aeroapi_url, headers=headers, params=params)
    
    if response.status_code == 200:
        flight_data = response.json()
        
        # Cache the data in Redis for 2.6 minutes (160 seconds)
        # redis_client.setex('flight_data', 160, json.dumps(flight_data))
        # Cache the data in Redis with a separate expiration command
        redis_client.set('flight_data', json.dumps(flight_data))
        redis_client.expire('flight_data', 160)  # Set expiration to 160 seconds
        return flight_data
    else:
        print("Error fetching data from AeroAPI:", response.status_code)
        return {"error": "Failed to fetch data from AeroAPI"}

# Endpoint for rendering template index4.html
@app.route('/fra')
def index():
    return render_template('index4.html')

# Endpoint for rendering template index55.html
@app.route('/all')
def index2():
    return render_template('index55.html')

# Endpoint for fetching flights data from AeroAPI
@app.route('/api/flights')
def flights():
    flight_data = fetch_flight_data()
    return jsonify(flight_data)

# Endpoint for serving static assets
@app.route('/static/<path:filename>')
def serve_assets(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4080)