#!/bin/sh
cd "$(dirname "$0")"
python3 -m pip install -r requirements.txt
echo "Open http://localhost:8000 in your browser. Keep this window open while you use the app."
(sleep 3; (xdg-open http://localhost:8000 || open http://localhost:8000) >/dev/null 2>&1) &
python3 -m uvicorn backend.main:app --port 8000
