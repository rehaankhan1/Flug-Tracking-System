from flask import Flask, jsonify, request, render_template
import requests
import redis
import threading
import time

app = Flask(__name__)

# Configure Redis connection
redis_host = 'redis-15352.c244.us-east-1-2.ec2.redns.redis-cloud.com'
redis_port = 15352
redis_password = 'etA7qlzgGJiCSIdXxrQ9rTuR8ILnluvF'

redis_client = redis.StrictRedis(
    host=redis_host,
    port=redis_port,
    password=redis_password,
    decode_responses=True
)

EUROPE_AREA = {
    "lamin": -90.0,  # Minimum latitude
    "lomin": -180.0, # Minimum longitude
    "lamax": 90.0,   # Maximum latitude
    "lomax": 180.0   # Maximum longitude
}

def fetch_and_store_flights():
    username = 'level9nine'
    password = 'supermanLol796#1'

    while True:
        try:
            # Fetch flights from the OpenSky API with authentication
            response = requests.get('https://opensky-network.org/api/states/all', params={
                'lamin': EUROPE_AREA['lamin'],
                'lomin': EUROPE_AREA['lomin'],
                'lamax': EUROPE_AREA['lamax'],
                'lomax': EUROPE_AREA['lomax']
            }, auth=(username, password))  # Adding basic auth
            
            response.raise_for_status()  # Raise an error for bad responses
            flights = response.json().get('states', [])

            if flights:
                all_flight_data = []  # List to store each flight's data

                for flight in flights:
                    # Unpack the relevant flight data
                    icao24 = flight[0]
                    timepos = flight[3]
                    destination = flight[2]
                    callsign = flight[1].strip() if flight[1] else None
                    longitude = flight[5]
                    latitude = flight[6]
                    velocity = flight[9] if len(flight) > 9 else None
                    heading = flight[10] if len(flight) > 10 else None

                    # Create a dictionary for the flight data
                    flight_data = {
                        "Flight": callsign,
                        "Time-pos": timepos,
                        "ICAO24": icao24,
                        "Destination": destination,
                        "latitude": latitude,
                        "longitude": longitude,
                        "Speed": f"{velocity} m/s" if velocity is not None else None,
                        "Heading": f"{heading}°" if heading is not None else None
                    }

                    # Append each flight's data to the list                   
                    all_flight_data.append(flight_data)
                    

                # Store the flight data in Redis
                redis_client.set('flights_data', str(all_flight_data))

            # Wait for 60 seconds before fetching again
            time.sleep(6000)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching flights: {str(e)}")
        except Exception as e:
            print(f"An error occurred: {str(e)}")

# Start the background thread
threading.Thread(target=fetch_and_store_flights, daemon=True).start()

@app.route('/track', methods=['GET'])
def get_track():
    # Get the icao24 parameter from the user
    icao24 = request.args.get('icao24')
    if not icao24:
        return jsonify({"error": "icao24 parameter is required"}), 400

    # OpenSky Network API endpoint
    url = f"https://opensky-network.org/api/tracks/all?icao24={icao24}&time=0"

    try:
        # Make a request to the OpenSky API
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Return the JSON response
        return jsonify(response.json())

    except requests.RequestException as e:
        # Handle any errors from the OpenSky API request
        return jsonify({"error": str(e)}), 500
        

@app.route('/all-flights11', methods=['GET'])
def get_flights_to_frankfurt():
    try:
        flight_data = redis_client.get('flights_data')
        if flight_data is None:
            return jsonify({"message": "No flight data available."}), 404
        
        # Convert the string back to a list
        all_flight_data = eval(flight_data)  # Caution: Using eval can be risky. Consider using json.loads() instead.
        
        return jsonify(all_flight_data), 200

    except Exception as e:
        return jsonify({"error": f"Error fetching flight data: {str(e)}"}), 500

@app.route('/all')
def index2():
    return render_template('index55.html')     

@app.route('/temperory')
def index3():
    return render_template('fl-route.html')     

@app.route('/live-route')
def index4():
    return render_template('live-route.html') 

@app.route('/live-route-weather')
def index5():
    return render_template('live-route-weather.html') 


if __name__ == '__main__':
    app.run(debug=True)
