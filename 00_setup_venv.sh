#!/bin/bash
# Setup Virtual Environment untuk Sistem Presensi GKI Karawaci

echo "=== Setup Virtual Environment ==="
echo ""

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

# Install dependencies
echo "Installing dependencies..."
echo "This may take 10-30 minutes depending on your system..."
pip install opencv-python numpy pillow ultralytics

# Install PyTorch (CPU version untuk Raspberry Pi)
echo "Installing PyTorch (CPU version)..."
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install InsightFace
echo "Installing InsightFace..."
pip install insightface onnxruntime

echo ""
echo "✓ Setup selesai!"
echo ""
echo "Untuk mengaktifkan virtual environment:"
echo "  source venv/bin/activate"
echo ""
echo "Untuk menjalankan sistem:"
echo "  source venv/bin/activate"
echo "  python 01_setup_directories.py"
echo "  python 03_face_encoder_arcface.py"
echo "  python 07_main_system_yolo.py"
