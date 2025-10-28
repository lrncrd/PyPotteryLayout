#!/bin/bash

echo "==============================================="
echo "  PyPotteryLayout - Flask Web Application"
echo "==============================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        echo "Please make sure Python 3 is installed correctly"
        exit 1
    fi
fi

echo "Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
echo ""
echo "Checking dependencies..."
pip show Flask > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install dependencies"
        exit 1
    fi
fi

echo ""
echo "==============================================="
echo "  Starting Flask Application"
echo "==============================================="
echo ""
echo "The application will be available at:"
echo "  http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo "==============================================="
echo ""

python app.py
