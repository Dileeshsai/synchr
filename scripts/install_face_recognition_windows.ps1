# Install face_recognition on Windows using a pre-built dlib wheel (no build required).
# Run from project root with venv activated: .\scripts\install_face_recognition_windows.ps1

$pyVer = & python -c "import sys; v=sys.version_info; print(f'{v.major}{v.minor}')" 2>$null
if (-not $pyVer) {
    Write-Host "Could not detect Python version. Run: python --version" -ForegroundColor Red
    exit 1
}

# Pre-built dlib wheel URLs (Murtaza-Saeed / z-mahmud22)
$base = "https://github.com/Murtaza-Saeed/Dlib-Precompiled-Wheels-for-Python-on-Windows-x64-Easy-Installation/raw/master"
$wheels = @{
    "310" = "$base/dlib-19.24.1-cp310-cp310-win_amd64.whl"
    "311" = "$base/dlib-19.24.1-cp311-cp311-win_amd64.whl"
    "312" = "$base/dlib-19.24.99-cp312-cp312-win_amd64.whl"
}

$wheelUrl = $wheels[$pyVer]
if (-not $wheelUrl) {
    Write-Host "No pre-built dlib wheel for Python $pyVer. Supported: 3.10, 3.11, 3.12." -ForegroundColor Yellow
    Write-Host "Install manually: download a wheel from https://github.com/Murtaza-Saeed/Dlib-Precompiled-Wheels-for-Python-on-Windows-x64-Easy-Installation" -ForegroundColor Yellow
    exit 1
}

Write-Host "Python $pyVer detected. Installing dlib from pre-built wheel..." -ForegroundColor Cyan
& pip install $wheelUrl
if ($LASTEXITCODE -ne 0) {
    Write-Host "dlib wheel install failed. Try: pip install cmake then run this script again." -ForegroundColor Red
    exit 1
}

Write-Host "Installing face_recognition..." -ForegroundColor Cyan
& pip install face_recognition
if ($LASTEXITCODE -ne 0) {
    Write-Host "face_recognition install failed." -ForegroundColor Red
    exit 1
}

Write-Host "Done. face_recognition is installed." -ForegroundColor Green
