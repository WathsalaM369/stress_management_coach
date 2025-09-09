from flask import Flask, request, jsonify
#from agents.stress_estimator import StressEstimatorAgent
from agents.activity_recommender_flask import activity_bp

app = Flask(__name__)
#agent = StressEstimatorAgent()

# Register your activity recommender blueprint
app.register_blueprint(activity_bp, url_prefix='/activity_recommender')

#@app.route('/estimate_stress', methods=['POST'])
#def estimate_stress():
#    data = request.get_json()
#    text = data.get('text', '')
    
#    if not text:
#        return jsonify({'error': 'No text provided'}), 400
    
  #  result = agent.estimate_stress_level(text)
 #   return jsonify(result)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)


    