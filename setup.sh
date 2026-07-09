#!/bin/bash
echo "======================================"
echo " Highlands Coffee Setup"
echo "======================================"
echo

echo "[1] Creating virtual environment..."
python3 -m venv venv

echo "[2] Activating virtual environment..."
source venv/bin/activate

echo "[3] Installing dependencies..."
pip install -r requirements.txt

echo "[4] Setting up environment..."
cp .env.example .env
echo "Configure .env with your MySQL credentials!"

echo
echo "======================================"
echo "Setup complete! Next steps:"
echo
echo "1. Edit .env with your MySQL settings"
echo "2. Run: source venv/bin/activate"
echo "3. Run: python highlands/seed_db.py"
echo "4. Run: python -m uvicorn highlands_app:app --port 8003 --reload"
echo
echo "Then open: http://localhost:8003"
echo "======================================"
