from flask import Flask, send_from_directory
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    print("Frontend server starting on http://localhost:3000")
    print("Make sure your Stress Estimator Agent is running on http://localhost:5001")
    app.run(port=3000, debug=True)