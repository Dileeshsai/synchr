@echo off
echo ========================================
echo HORILLA HRMS - FACE RECOGNITION SETUP
echo ========================================
echo.

echo Checking Python version...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo.
echo Upgrading pip, setuptools, and wheel...
python -m pip install --upgrade pip setuptools wheel
if %errorlevel% neq 0 (
    echo ERROR: Failed to upgrade pip
    pause
    exit /b 1
)

echo.
echo Installing cmake...
pip install cmake
if %errorlevel% neq 0 (
    echo ERROR: Failed to install cmake
    pause
    exit /b 1
)

echo.
echo Installing dlib (this may take a few minutes)...
echo Trying Method 1: Pre-compiled wheel...
pip install dlib --find-links https://github.com/sachadee/Dlib/releases
if %errorlevel% neq 0 (
    echo Method 1 failed. Trying Method 2: Direct installation...
    pip install dlib
    if %errorlevel% neq 0 (
        echo Method 2 failed. Trying Method 3: Alternative source...
        pip install dlib --extra-index-url https://pypi.org/simple/
        if %errorlevel% neq 0 (
            echo ERROR: All dlib installation methods failed
            echo Please try manual installation or use conda
            pause
            exit /b 1
        )
    )
)

echo.
echo Installing face_recognition...
pip install face_recognition
if %errorlevel% neq 0 (
    echo ERROR: Failed to install face_recognition
    pause
    exit /b 1
)

echo.
echo Installing additional dependencies...
pip install opencv-python numpy Pillow scikit-image
if %errorlevel% neq 0 (
    echo WARNING: Some additional dependencies failed to install
    echo You may need to install them manually
)

echo.
echo Testing face recognition installation...
python -c "import face_recognition; print('SUCCESS: face_recognition imported successfully')"
if %errorlevel% neq 0 (
    echo ERROR: face_recognition test failed
    echo Please check the installation
    pause
    exit /b 1
)

echo.
echo ========================================
echo INSTALLATION COMPLETED SUCCESSFULLY!
echo ========================================
echo.
echo You can now use face recognition features in Horilla HRMS
echo.
echo To test the installation, run:
echo python manage.py test_face_recognition
echo.
pause
