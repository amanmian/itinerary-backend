from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
from sklearn.linear_model import LinearRegression

app = Flask(__name__)
CORS(app)  # Allow requests from React frontend

# Training sample model
X = np.array([[1], [2], [3], [4], [5]])
y = np.array([5, 9, 12, 17, 17])
model = LinearRegression()
model.fit(X, y)

@app.route('/')
def home():
    return "ML Flask API is running!"

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()

    try:
        # Extract and convert to float
        value = float(data.get('value', None))
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid input, must be a numeric value'}), 400

    input_data = np.array([[value]])
    prediction = model.predict(input_data)[0]
    return jsonify({'prediction': round(prediction, 2)})

if __name__ == '__main__':
    app.run(debug=True)
