#!/bin/bash
# Setup Virtual Environment untuk Sistem Presensi GKI Karawaci
# Optimized untuk Raspberry Pi 5

echo "=== Setup Virtual Environment (Raspberry Pi 5) ==="
echo ""

# Install system dependencies untuk Raspberry Pi 5
echo "Installing system dependencies..."
sudo apt update
sudo apt install -y python3-venv python3-full python3-dev
sudo apt install -y libopencv-dev python3-opencv
sudo apt install -y libopenblas-dev gfortran
sudo apt install -y libhdf5-dev libhdf5-serial-dev
sudo apt install -y libjpeg-dev zlib1g-dev

# Cek apakah python3-venv terinstall
if ! dpkg -l | grep -q python3-venv; then
    echo "Installing python3-venv..."
    sudo apt install -y python3-venv python3-full
fi

# Buat virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Aktivasi virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install NumPy dulu (penting untuk Raspberry Pi 5)
echo "Installing NumPy 1.24.3..."
pip install numpy==1.24.3

# Install dependencies dengan versi yang kompatibel untuk Raspberry Pi 5
echo "Installing OpenCV and dependencies..."
echo "This may take 10-30 minutes depending on your system..."
pip install opencv-contrib-python==4.8.1.78 pillow

# Install PyTorch (CPU version untuk Raspberry Pi 5)
echo "Installing PyTorch (CPU version)..."
pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cpu

# Install Ultralytics YOLO
echo "Installing Ultralytics..."
pip install ultralytics==8.0.220

# Install InsightFace
echo "Installing InsightFace..."
pip install insightface==0.7.3 onnxruntime==1.16.0# Install Database support (optional)
echo "Installing database support..."
pip install psycopg2-binary python-dotenv

echo ""
echo "✓ Setup selesai!"
echo ""
echo "Untuk mengaktifkan virtual environment:"
echo "  source venv/bin/activate"
echo ""
echo "Untuk menjalankan sistem:"
echo "  source venv/bin/activate"
echo "  python 01_main_system.py    # Jalankan sistem"
echo "  python 02_retrain_model.py  # Training model"
