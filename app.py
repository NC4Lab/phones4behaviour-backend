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

DEVICES_JSON = 'devices.json'
app.config['DEVICES_JSON'] = DEVICES_JSON

FRAMES_FOLDER = 'frames'
os.makedirs(FRAMES_FOLDER, exist_ok=True)
app.config['FRAMES_FOLDER'] = FRAMES_FOLDER

FRAMES_JSON = 'frames/frames.json'
app.config['FRAMES_FOLDER'] = FRAMES_JSON

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}

socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('connect')
def handle_connect():
    print('Client connected')

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
        # print('request', request.json['files'][0]['deviceId'])
        with open(DISPLAY_JSON, 'r') as f:
            display_json = json.load(f)

        device_id = request.json['files'][0]['deviceId']
        new_display = request.json.get('files', [])
        print(device_id)

        device_entry = next((entry for entry in display_json if entry['device_id'] == device_id), None)

        if device_entry is None:
            device_entry = {
                "device_id": device_id,
                "display": []
            }
            display_json.append(device_entry)

        for file in new_display:
            device_entry['display'].append(file)

        with open(DISPLAY_JSON, 'w') as f:
            json.dump(display_json, f, indent=4)

        for file_name in os.listdir(app.config['DISPLAY_FOLDER']):
            file_path = os.path.join(app.config['DISPLAY_FOLDER'], file_name)
            file_ext = os.path.splitext(file_name)[1].lower()
            if file_ext in IMAGE_EXTENSIONS:
                if os.path.isfile(file_path):
                    os.unlink(file_path)

        saved_files = {}

        for file in new_display:
            file_name = file.get('fileName')
            display_time = file.get('displayTime')
            device_id = file.get('deviceId')
            src_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
            dest_path = os.path.join(app.config['DISPLAY_FOLDER'], file_name)
            if os.path.exists(src_path):
                shutil.copy(src_path, dest_path)
                file_type, _ = mimetypes.guess_type(file_name)
                saved_files[file_name] = {
                    "file_path": dest_path,
                    "file_type": file_type,
                    "display_time": display_time,
                    "device_id": device_id
                }

        socketio.emit('new_file', {'files': new_display})

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
        device_id = request.args.get('deviceId')
        # print(device_id)

        with open(DISPLAY_JSON, 'r') as f:
            display_json = json.load(f)

        file_info = []
        
        if device_id is not None:
            device_display_files = [entry['display'] for entry in display_json if entry['device_id'] == device_id]

            for x in device_display_files:
                for file in x:
                    print(file)
                    file_name = file.get('fileName')
                    file_path = f"/uploads/display/{file_name}"
                    file_type, _ = mimetypes.guess_type(file_path)

                    file_info.append({
                        "file_name": file_name,
                        "file_path": file_path,
                        "file_type": file_type,
                        "timestamp": file.get('displayTime'),
                        "device_id": file.get('deviceId')
                    })
        else:
            with open(DISPLAY_JSON, 'r') as f:
                file_info = json.load(f)

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
    
@app.route('/devices', methods=['POST'])
def post_device():
    try:
        with open(DEVICES_JSON, 'r') as f:
            devices_json = json.load(f)

        new_device = request.json

        if new_device and not any(device['id'] == new_device['id'] for device in devices_json):
            devices_json.append(new_device)

        temp_devices_file = DEVICES_JSON + '.tmp'
        with open(temp_devices_file, 'w') as f:
            json.dump(devices_json, f)
        os.replace(temp_devices_file, DEVICES_JSON)


        with open(DISPLAY_JSON, 'r') as f:
            display_json = json.load(f)

        if new_device and not any(device['device_id'] == new_device['id'] for device in display_json):
            display_json.append({
                'device_id': new_device['id'],
                'display': []
            })

        temp_display_file = DISPLAY_JSON + '.tmp'
        with open(temp_display_file, 'w') as f:
            json.dump(display_json, f)
        os.replace(temp_display_file, DISPLAY_JSON)

        socketio.emit('new_device', {'devices': new_device})

        response_data = {
            "status": "success",
            "saved_files": new_device
        }
        
        return jsonify(response_data), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/devices', methods=['GET'])
def get_devices():
    try:
        with open(DEVICES_JSON, 'r') as f:
            devices_json = json.load(f)

        return jsonify(devices_json), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route('/frames', methods=['POST'])
def post_frames():
    try:
        with open(FRAMES_JSON, 'r') as f:
            frames_json = json.load(f)

        new_frame = request.json
        if new_frame:
            frames_json.append(new_frame)

        temp_file = FRAMES_JSON + '.tmp'
        with open(temp_file, 'w') as f:
            json.dump(frames_json, f)
        os.replace(temp_file, FRAMES_JSON)

        with open(FRAMES_JSON, 'w') as f:
            json.dump(frames_json, f)

        socketio.emit('new_frame', {'frames': new_frame})

        response_data = {
            "status": "success",
            "saved_files": new_frame
        }
        return jsonify(response_data), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route('/frames', methods=['GET'])
def get_frames():
    try:
        with open(FRAMES_JSON, 'r') as f:
            frames_json = json.load(f)

        return jsonify(frames_json), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route('/')
def index():
    return "<a href='/uploads'>http://127.0.0.1:5000/uploads</a><br><a href='/uploads/display'>http://127.0.0.1:5000/uploads/display</a><br><a href='/logs'>http://127.0.0.1:5000/logs</a><br><a href='/devices'>http://127.0.0.1:5000/devices</a"

if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=5000)
    socketio.run(app, host='0.0.0.0', port=5000,debug=True)
