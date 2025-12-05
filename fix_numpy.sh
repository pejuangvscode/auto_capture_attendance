#!/bin/bash
# Quick fix untuk NumPy & PyTorch Version di Raspberry Pi 5

echo "=== Fix NumPy & PyTorch Version (Raspberry Pi 5) ==="
echo ""

# Install system dependencies jika belum ada
echo "Installing system dependencies..."
sudo apt update
sudo apt install -y libopencv-dev python3-dev libopenblas-dev gfortran

# Aktivasi virtual environment
source venv/bin/activate

# Uninstall semua yang conflict
echo "Uninstalling conflicting packages..."
pip uninstall -y numpy opencv-python opencv-contrib-python torch torchvision ultralytics

# Install NumPy versi yang kompatibel dengan Python 3.13
echo "Installing compatible NumPy 2.1.2..."
pip install numpy==2.1.2

# Install PyTorch latest stable untuk CPU
echo "Installing PyTorch (latest CPU version)..."
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install OpenCV dengan rebuild
echo "Installing OpenCV 4.8.1.78..."
pip install --no-cache-dir opencv-contrib-python==4.8.1.78

# Install Ultralytics versi terbaru yang kompatibel
echo "Installing Ultralytics (latest)..."
pip install ultralytics

echo ""
echo "✓ Fix selesai!"
echo ""
echo "Coba jalankan lagi:"
echo "  python 01_main_system.py"


