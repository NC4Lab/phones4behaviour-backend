from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

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
        files = request.files
        saved_files = {}

        for file_key in files:
            file = files[file_key]
            if file:
                file_path = os.path.join(app.config['DISPLAY_FOLDER'], file.filename)
                file.save(file_path)
                saved_files[file_key] = file_path

        response_data = {
            "status": "success",
            "saved_files": saved_files
        }
        return jsonify(response_data), 200
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
    app.run(host='0.0.0.0', port=5000)
