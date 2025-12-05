#!/bin/bash
# Quick fix untuk NumPy version conflict di Raspberry Pi

echo "=== Fix NumPy Version Conflict ==="
echo ""

# Aktivasi virtual environment
source venv/bin/activate

# Uninstall semua yang conflict
echo "Uninstalling conflicting packages..."
pip uninstall -y numpy opencv-python opencv-contrib-python

# Install NumPy versi yang kompatibel
echo "Installing compatible NumPy 1.24.3..."
pip install numpy==1.24.3

# Install OpenCV dengan rebuild
echo "Installing OpenCV 4.8.1.78..."
pip install --no-cache-dir opencv-contrib-python==4.8.1.78

echo ""
echo "✓ Fix selesai!"
echo ""
echo "Coba jalankan lagi:"
echo "  python 01_main_system.py"
