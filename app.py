from flask import Flask, render_template, request, jsonify
from services.burn_agent import PrescribedBurnAgent

app = Flask(__name__)
agent = PrescribedBurnAgent()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze_location():
    data = request.json
    city = data.get('city', '')
    
    if not city:
        return jsonify({'error': 'City name is required'}), 400
    
    try:
        result = agent.analyze_location(city)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
