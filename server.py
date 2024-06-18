from flask import Flask, request, jsonify, send_from_directory
import subprocess
import os
import uuid

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'imageFile' not in request.files:
        return jsonify(success=False, message='No file part')
    
    file = request.files['imageFile']
    if file.filename == '':
        return jsonify(success=False, message='No selected file')
    
    if file:
        request_id = uuid.uuid4()
        filename = str(request_id) + "_" + file.filename
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # Call the Python script
        subprocess.run(['python', 'script.py', request_id], check=True)
        
        # Collect result images
        client_id = filename.split('_')[0]
        results_dir = os.path.join(RESULTS_FOLDER, client_id)
        image_urls = []
        for result_file in os.listdir(results_dir):
            image_urls.append(f'/results/{client_id}/{result_file}')
        
        return jsonify(success=True, images=image_urls)

@app.route('/results/<client_id>/<filename>')
def serve_result_image(client_id, filename):
    return send_from_directory(os.path.join(RESULTS_FOLDER, client_id), filename)

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    if not os.path.exists(RESULTS_FOLDER):
        os.makedirs(RESULTS_FOLDER)
    app.run(debug=True)
