from flask import (
    Flask,
    request,
    render_template,
    jsonify,
    send_from_directory,
    send_file,
    Response,
)
import os
from werkzeug.utils import secure_filename
from FileAnalyzer import FileAnalyzer
import json
import base64
from io import BytesIO
from PIL import Image
import cairosvg  # You might need to install this: pip install cairosvg

UPLOAD_FOLDER = "uploads"
RESULT_FOLDER = "static/out"

app = Flask(__name__, static_url_path="/static")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

APP_VERSION = "V0.5.0-beta"


@app.route("/")
def index():
    return render_template("index.html", version=APP_VERSION)


@app.route("/favicon.ico")
def favicon():
    try:
        # First check if a favicon.ico file already exists
        favicon_path = os.path.join(app.root_path, "static", "favicon.ico")
        if os.path.exists(favicon_path):
            return send_from_directory(
                os.path.join(app.root_path, "static"),
                "favicon.ico",
                mimetype="image/vnd.microsoft.icon",
            )

        # If not, generate one from the SVG
        svg_path = os.path.join(app.root_path, "static", "favicon.svg")
        if os.path.exists(svg_path):
            # Convert SVG to PNG using cairosvg
            png_data = cairosvg.svg2png(url=svg_path, output_width=32, output_height=32)

            # Convert PNG to ICO
            img = Image.open(BytesIO(png_data))
            ico_output = BytesIO()
            img.save(ico_output, format="ICO", sizes=[(32, 32)])
            ico_output.seek(0)

            # Save the ICO file for future use
            with open(favicon_path, "wb") as f:
                f.write(ico_output.getvalue())

            # Return the generated ICO
            ico_output.seek(0)
            return send_file(ico_output, mimetype="image/x-icon")
    except Exception as e:
        print(f"Error generating favicon: {e}")
        # Return a simple transparent 1x1 pixel ICO as fallback
        return Response(
            base64.b64decode(
                "AAABAAEAEBACAAEAAQCwAAAAFgAAAIlQTkcNChoKAAAADUlIRFIAAAAQAAAAEAgGAAAAH/P/YQAAAAFzUkdCAK7OHOkAAAAEZ0FNQQAAsY8L/GEFAAAACXBIWXMAAA7DAAAOwwHHb6hkAAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAAABVJREFUGFdjYBgFo2AUjIJRQE8AAAQQAAEpKXNFAAAAAElFTkSuQmCC"
            ),
            mimetype="image/x-icon",
        )


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
        json_files = [
            f
            for f in os.listdir(RESULT_FOLDER)
            if (f.endswith(".json") and ".pos" not in f)
        ]
        json_files.sort(reverse=True)  # Sort newest first
        return jsonify({"status": "ok", "files": json_files})
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
    json_files.sort(reverse=True)  # Sort newest first
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
            json.dump(data, f, indent=2)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


if __name__ == "__main__":
    app.run(debug=True)
