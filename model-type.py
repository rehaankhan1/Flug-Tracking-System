import json
import joblib
import pandas as pd

def load_json(filename):
    """Load input data from a JSON file."""
    with open(filename, 'r') as f:
        data = json.load(f)
    return data

def preprocess_data(data):
    """Convert JSON input to DataFrame and retain column names."""
    df = pd.DataFrame([data])  # Convert single JSON object to DataFrame
    return df  # Return DataFrame instead of NumPy array

def predict(model_path, json_path):
    """Load model, preprocess input, and make a prediction."""
    try:
        # Load trained model
        model = joblib.load(model_path)
        
        # Load and preprocess input data
        input_data = load_json(json_path)
        formatted_input = preprocess_data(input_data)
        
        # Make prediction
        prediction = model.predict(formatted_input)
        print(f"Predicted Output: {prediction}")

        probabilities = model.predict_proba(formatted_input)
        print(f"Confidence: {probabilities.tolist()}") 
        

    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    # Define file paths
    model_file = "best_model.pkl"  # Change to actual model filename
    input_json = "input_data.json"  # JSON file containing test data
    
    # Run prediction
    predict(model_file, input_json)