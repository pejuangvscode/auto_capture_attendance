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

    # Install dependencies dengan versi yang kompatibel
echo "Installing dependencies..."
echo "This may take 10-30 minutes depending on your system..."
pip install "numpy<2.0" opencv-contrib-python==4.8.1.78 pillow ultralytics

# Install PyTorch (CPU version untuk Raspberry Pi)
echo "Installing PyTorch (CPU version)..."
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install InsightFace
echo "Installing InsightFace..."
pip install insightface onnxruntime

# Install Database support (optional)
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
