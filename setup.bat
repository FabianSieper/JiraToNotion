@echo off

echo Checking for Python installation...
python --version >NUL 2>&1
if %errorlevel% neq 0 (
    echo Python not found, installing Python...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.9.7/python-3.9.7-amd64.exe' -OutFile 'python_installer.exe'"
    .\python_installer.exe /quiet InstallAllUsers=1 PrependPath=1
    del .\python_installer.exe
) else (
    echo Python is already installed.
)

echo Checking for pip installation...
pip --version >NUL 2>&1
if %errorlevel% neq 0 (
    echo Pip not found, installing pip...
    powershell -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'get-pip.py'"
    python get-pip.py
    del .\get-pip.py
) else (
    echo Pip is already installed.
)

echo Installing required dependencies...
pip install -r requirements.txt
echo Installation complete!

pause
