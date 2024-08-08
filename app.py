from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import os
import shutil

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('connect')
def handle_connect():
    print('Client connected')

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

DISPLAY_FOLDER = 'display'
os.makedirs(DISPLAY_FOLDER, exist_ok=True)
app.config['DISPLAY_FOLDER'] = DISPLAY_FOLDER

@app.route('/files', methods=['POST'])
def post_files():
    try:
        files = request.files
        saved_files = {}

        for file_key in files:
            file = files[file_key]
            if file:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(file_path)
                saved_files[file_key] = file_path

        response_data = {
            "status": "success",
            "saved_files": saved_files
        }
        return jsonify(response_data), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route('/files', methods=['GET'])
def get_files():
    try:
        files = os.listdir(app.config['UPLOAD_FOLDER'])
        file_info = [{"filename": file, "filepath": os.path.join(app.config['UPLOAD_FOLDER'], file)} for file in files]

        return jsonify(file_info), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/display', methods=['POST'])
def post_display_files():
    try:
        for filename in os.listdir(app.config['DISPLAY_FOLDER']):
            file_path = os.path.join(app.config['DISPLAY_FOLDER'], filename)
            if os.path.isfile(file_path):
                os.unlink(file_path)

        data = request.json
        selected_files = data.get('files', [])
        saved_files = {}

        for filename in selected_files:
            src_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            dest_path = os.path.join(app.config['DISPLAY_FOLDER'], filename)
            if os.path.exists(src_path):
                shutil.copy(src_path, dest_path)
                saved_files[filename] = dest_path

        socketio.emit('new_file', {'files': selected_files})

        response_data = {
            "status": "success",
            "saved_files": saved_files
        }
        return jsonify(response_data), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/display', methods=['GET'])
def get_display_files():
    try:
        files = os.listdir(app.config['DISPLAY_FOLDER'])
        file_info = [{"filename": file, "fileurl": f"/display/{file}"} for file in files]

        return jsonify(file_info), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route('/display/<filename>', methods=['GET'])
def serve_display_file(filename):
    try:
        return send_from_directory(app.config['DISPLAY_FOLDER'], filename)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route('/')
def index():
    try:
        upload_files = os.listdir(app.config['UPLOAD_FOLDER'])
        upload_file_info = [{"filename": file, "filepath": os.path.join(app.config['UPLOAD_FOLDER'], file)} for file in upload_files]

        display_files = os.listdir(app.config['DISPLAY_FOLDER'])
        display_file_info = [{"filename": file, "filepath": os.path.join(app.config['DISPLAY_FOLDER'], file)} for file in display_files]

        all_files_info = {
            "uploaded_files": upload_file_info,
            "display_files": display_file_info
        }

        return jsonify(all_files_info), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    socketio.run(app)
