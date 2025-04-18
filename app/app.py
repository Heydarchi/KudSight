from flask import Flask, request, render_template, jsonify, send_from_directory
import os
from werkzeug.utils import secure_filename
from FileAnalyzer import FileAnalyzer

UPLOAD_FOLDER = "uploads"
RESULT_FOLDER = "static/out"

app = Flask(__name__, static_url_path="/static")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

APP_VERSION = "V0.4.1-beta"


@app.route("/")
def index():
    return render_template("index.html", version=APP_VERSION)


@app.route("/upload", methods=["POST"])
def upload_folder():
    folder_path = request.form.get("folderPath")

    print(f"Current app path: {os.path.abspath(os.getcwd())}")
    if not os.path.exists(folder_path):
        print(f"Path does not exist: {folder_path}")
        return jsonify({"status": "error", "message": "Path does not exist."})

    try:
        print(f"Analyzing: {folder_path}")
        fileAnalyzer = FileAnalyzer()
        fileAnalyzer.analyze(folder_path, None)
        return jsonify({"status": "ok"})
    except Exception as e:
        print(f"Error during analysis: {e}")
        return jsonify({"status": "error", "message": str(e)})


@app.route("/out/<path:filename>")
def serve_output_file(filename):
    return send_from_directory(RESULT_FOLDER, filename)


@app.route("/upload-files", methods=["POST"])
def upload_files():
    files = request.files.getlist("files")
    temp_folder = os.path.join(app.config["UPLOAD_FOLDER"], "session")
    os.makedirs(temp_folder, exist_ok=True)

    for file in files:
        rel_path = secure_filename(file.filename)
        file_path = os.path.join(temp_folder, rel_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        file.save(file_path)

    try:
        fileAnalyzer = FileAnalyzer()
        fileAnalyzer.analyze(temp_folder, None)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/list-json")
def list_json():
    json_files = [
        f
        for f in os.listdir(RESULT_FOLDER)
        if (f.endswith(".json") and ".pos" not in f)
    ]
    return jsonify(json_files)


@app.route("/save-pos", methods=["POST"])
def save_positions():
    payload = request.get_json()
    filename = payload.get("filename")
    data = payload.get("data")

    if not filename or not data:
        return jsonify({"status": "error", "message": "Invalid payload"})

    try:
        path = os.path.join(RESULT_FOLDER, filename)
        with open(path, "w") as f:
            import json

            json.dump(data, f, indent=2)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


if __name__ == "__main__":
    app.run(debug=True)
