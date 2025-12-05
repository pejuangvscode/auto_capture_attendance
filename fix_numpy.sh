#!/bin/bash
# Quick fix untuk NumPy version conflict di Raspberry Pi 5

echo "=== Fix NumPy Version Conflict (Raspberry Pi 5) ==="
echo ""

# Install system dependencies jika belum ada
echo "Installing system dependencies..."
sudo apt update
sudo apt install -y libopencv-dev python3-dev libatlas-base-dev

# Aktivasi virtual environment
source venv/bin/activate

# Uninstall semua yang conflict
echo "Uninstalling conflicting packages..."
pip uninstall -y numpy opencv-python opencv-contrib-python torch torchvision ultralytics

# Install NumPy versi yang kompatibel
echo "Installing compatible NumPy 1.24.3..."
pip install numpy==1.24.3

# Install OpenCV dengan rebuild
echo "Installing OpenCV 4.8.1.78..."
pip install --no-cache-dir opencv-contrib-python==4.8.1.78

# Reinstall PyTorch
echo "Reinstalling PyTorch..."
pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cpu

# Reinstall Ultralytics
echo "Reinstalling Ultralytics..."
pip install ultralytics==8.0.220

echo ""
echo "✓ Fix selesai!"
echo ""
echo "Coba jalankan lagi:"
echo "  python 01_main_system.py"

