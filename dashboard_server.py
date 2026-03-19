"""Tiny Flask server for the R(5,5) live dashboard."""
import json
import os
from flask import Flask, jsonify, send_file

app = Flask(__name__)
PROGRESS_FILE = os.path.join(os.path.dirname(__file__), "progress.jsonl")


@app.route('/')
def index():
    return send_file(os.path.join(os.path.dirname(__file__), 'dashboard.html'))


@app.route('/api/progress')
def progress():
    if not os.path.exists(PROGRESS_FILE):
        return jsonify({'lines': []})
    try:
        lines = []
        with open(PROGRESS_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    lines.append(json.loads(line))
        return jsonify({'lines': lines})
    except Exception as e:
        return jsonify({'lines': [], 'error': str(e)})


if __name__ == '__main__':
    print("Dashboard at http://localhost:5099")
    app.run(port=5099, debug=False)
