from flask import Flask, request, jsonify
app = Flask(__name__)

timestamps = []

@app.route('/times', methods=['POST'])
def receive_timestamp():
    data = request.get_json()
    timestamps.append(data['timestamp'])
    print(timestamps)
    return jsonify({"status": "success"}), 200

@app.route('/')
def index():
    return '<br>'.join(timestamps)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
