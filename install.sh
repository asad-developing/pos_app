#!/bin/bash
echo "============================================"
echo " POS System - Installing Dependencies"
echo "============================================"
echo

# Check Python3
if ! command -v python3 &> /dev/null; then
    echo "Python3 not found. Installing..."
    sudo apt update && sudo apt install -y python3 python3-pip
else
    echo "Python3 found: $(python3 --version)"
fi

# Install Flask
echo "Installing Flask..."
pip3 install flask

echo
echo "============================================"
echo " Installation complete!"
echo " Run:  bash run.sh"
echo "============================================"
