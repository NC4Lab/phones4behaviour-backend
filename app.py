from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from pymongo import MongoClient, errors
from dotenv import load_dotenv
import os
import certifi

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

load_dotenv()

app = Flask(__name__)

client = MongoClient(os.getenv("MONGODB_URI"), tlsCAFile=certifi.where())
db = client['commandDB']
collection = db['commands']

@app.route('/posttimes', methods=['POST'])
def post_data():
    try:
        data = request.get_json()
        if 'responsetime' not in data:
            return jsonify({"status": "error", "message": "Missing 'timestamp' in request"}), 400
        print("Received data:", data)
        collection.insert_one(data)
        return jsonify({"status": "success"}), 200
    except errors.PyMongoError as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route('/gettimes', methods=['GET'])
@cross_origin()
def get_data():
    try:
        data = collection.find()
        result = [{'command': data['command'],
                   'commandfile': data['commandfile'],
                   'commandtime': data['commandtime'],
                   'response': data['response'],
                   'responsefile': data['responsefile'],
                   'responsetime': data['responsetime'],
                   } for data in data]
        return jsonify(result), 200
    except errors.PyMongoError as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/')
def index():
    try:
        data = collection.find()
        result = [{key: value for key, value in item.items() if key != '_id'} for item in data]
        return jsonify(result), 200
    except errors.PyMongoError as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
