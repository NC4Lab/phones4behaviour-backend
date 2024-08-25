from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import json
import os
import shutil
import mimetypes

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('connect')
def handle_connect():
    print('Client connected')

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

UPLOAD_JSON = 'uploads/uploads.json'
app.config['UPLOAD_JSON'] = UPLOAD_JSON

DISPLAY_FOLDER = 'uploads/display'
os.makedirs(DISPLAY_FOLDER, exist_ok=True)
app.config['DISPLAY_FOLDER'] = DISPLAY_FOLDER

DISPLAY_JSON = 'uploads/display/display.json'
app.config['DISPLAY_JSON'] = DISPLAY_JSON

LOG_JSON = 'logs.json'
app.config['LOG_JSON'] = LOG_JSON

@app.route('/uploads', methods=['POST'])
def post_files():
    try:
        files = request.files
        file_type = request.form.get('fileType')
        upload_time = request.form.get('uploadTime')
        saved_files = {}


        with open(UPLOAD_JSON, 'r') as f:
            uploads_json = json.load(f)


        for file_key in files:
            file = files[file_key]
            if file:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(file_path)
                saved_files[file_key] = {
                    "file_path": f"/uploads/{file.filename}",
                    "file_type": file_type,
                    "upload_time": upload_time,
                }

                uploads_json.append({
                    "file_name": file.filename,
                    "file_path": file_path,
                    "file_type": file_type,
                    "upload_time": upload_time
                })

        with open(UPLOAD_JSON, 'w') as f:
            json.dump(uploads_json, f)

        response_data = {
            "status": "success",
            "saved_files": saved_files
        }
        return jsonify(response_data), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route('/uploads', methods=['GET'])
def get_files():
    try:
        with open(UPLOAD_JSON, 'r') as f:
            uploads_json = json.load(f)
            
        files = os.listdir(app.config['UPLOAD_FOLDER'])
        response = []

        for file in files:
            for entry in uploads_json:
                if entry['file_name'] == file:
                    file_info = {
                        'file_name': entry.get('file_name', 'unknown'),
                        'file_path': entry.get('file_path', 'unknown'),
                        'file_type': entry.get('file_type', 'unknown'),
                        'upload_time': entry.get('upload_time', 'unknown')
                    }
                    response.append(file_info)
                    break

        return jsonify(response), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/uploads/<filename>', methods=['GET'])
def serve_upload_file(filename):
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route('/uploads/display', methods=['POST'])
def post_display_files():
    try:
        for file_name in os.listdir(app.config['DISPLAY_FOLDER']):
            file_path = os.path.join(app.config['DISPLAY_FOLDER'], file_name)
            if os.path.isfile(file_path):
                os.unlink(file_path)

        data = request.json
        selected_files = data.get('files', [])
        saved_files = {}

        for file in selected_files:
            file_name = file.get('fileName')
            display_time = file.get('displayTime')
            src_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
            dest_path = os.path.join(app.config['DISPLAY_FOLDER'], file_name)
            if os.path.exists(src_path):
                shutil.copy(src_path, dest_path)
                file_type, _ = mimetypes.guess_type(file_name)
                saved_files[file_name] = {
                    "file_path": dest_path,
                    "file_type": file_type,
                    "display_time": display_time
                }


        socketio.emit('new_file', {'files': selected_files})

        response_data = {
            "status": "success",
            "saved_files": saved_files
        }
        return jsonify(response_data), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/uploads/display', methods=['GET'])
def get_display_files():
    try:
        files = os.listdir(app.config['DISPLAY_FOLDER'])
        file_info = []

        for file in files:
            # file_path = os.path.join(app.config['DISPLAY_FOLDER'], file)
            file_type, _ = mimetypes.guess_type(file) 
            file_info.append({
                "file_name": file,
                "file_path": f"/uploads/display/{file}",
                "file_type": file_type
            })

        return jsonify(file_info), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route('/uploads/display/<filename>', methods=['GET'])
def serve_display_file(filename):
    try:
        return send_from_directory(app.config['DISPLAY_FOLDER'], filename)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/logs', methods=['POST'])
def post_logs():
    try:
        with open(LOG_JSON, 'r') as f:
            logs_json = json.load(f)

        new_log = request.json
        if new_log:
            logs_json.append(new_log)

        temp_file = LOG_JSON + '.tmp'
        with open(temp_file, 'w') as f:
            json.dump(logs_json, f)
        os.replace(temp_file, LOG_JSON)

        with open(LOG_JSON, 'w') as f:
            json.dump(logs_json, f)

        socketio.emit('new_log', {'logs': new_log})

        response_data = {
            "status": "success",
            "saved_files": new_log
        }
        return jsonify(response_data), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route('/logs', methods=['GET'])
def get_logs():
    try:
        with open(LOG_JSON, 'r') as f:
            logs_json = json.load(f)

        return jsonify(logs_json), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/')
def index():
    return "<a href='/uploads'>http://127.0.0.1:5000/uploads</a><br><a href='/uploads/display'>http://127.0.0.1:5000/uploads/display</a><br><a href='/logs'>http://127.0.0.1:5000/logs</a>"

if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=5000)
    socketio.run(app, host='0.0.0.0', port=5000)
