from flask import Flask, send_file
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

TILE_DIR = "tiles"  # Folder with Puget Sound tiles

@app.route('/DataAnalysis/tiles/<int:z>/<int:x>/<int:y>.png')
def get_tile(z, x, y):
    tile_path = os.path.join(TILE_DIR, f"{z}/{x}/{y}.png")
    if os.path.exists(tile_path):
        return send_file(tile_path, mimetype='image/png')
    else:
        return "Tile not found", 404

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
