from flask import Flask, request, jsonify
from pymongo import MongoClient, errors
from dotenv import load_dotenv
import os
import certifi

load_dotenv()

app = Flask(__name__)

client = MongoClient(os.getenv("MONGODB_URI"), tlsCAFile=certifi.where())
db = client['timestampDB']
timestamps_collection = db['timestamps']

@app.route('/times', methods=['POST'])
def receive_timestamp():
    try:
        data = request.get_json()
        if 'timestamp' not in data:
            return jsonify({"status": "error", "message": "Missing 'timestamp' in request"}), 400
        
        timestamp = data['timestamp']
        timestamps_collection.insert_one({'timestamp': timestamp})
        return jsonify({"status": "success"}), 200
    except errors.PyMongoError as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/')
def index():
    try:
        timestamps = timestamps_collection.find()
        return '<br>'.join([timestamp['timestamp'] for timestamp in timestamps])
    except errors.PyMongoError as e:
        return f"Error: {str(e)}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
