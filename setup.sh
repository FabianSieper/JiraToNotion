#!/bin/bash

# Check for Python installation
echo "Checking for Python installation..."
if ! command -v python3 &>/dev/null; then
    echo "Python not found, installing Python via Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    brew install python3
else
    echo "Python is already installed."
fi

# Check for pip installation
echo "Checking for pip installation..."
if ! command -v pip3 &>/dev/null; then
    echo "Pip not found, installing pip..."
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python3 get-pip.py
    rm get-pip.py
else
    echo "Pip is already installed."
fi

# Install required dependencies
echo "Installing required dependencies..."
pip3 install -r requirements.txt
echo "Installation complete!"

read -n 1 -s -r -p "Press any key to continue..."
