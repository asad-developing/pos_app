#!/bin/bash
cd "$(dirname "$0")"

while true; do
    echo "============================================"
    echo " POS System Starting..."
    echo " Open browser at: http://localhost:5000"
    echo " Press Ctrl+C to stop."
    echo "============================================"
    echo

    python3 app.py

    echo
    echo " POS System stopped. Restarting in 3 seconds..."
    echo " (Close this terminal to exit completely)"
    sleep 3
done
