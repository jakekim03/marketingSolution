# Python full installer + build. No embeddable, no get_pip - just official installer into project folder.
# Run: setup_and_build.bat or: powershell -ExecutionPolicy Bypass -File setup_and_build.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
Set-Location $ProjectRoot

$PythonInstallerUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
$InstallDir = Join-Path $ProjectRoot ".python_install"

function Log { param($msg) Write-Host $msg }

function Find-PythonExe {
    $dir = $InstallDir
    if (-not (Test-Path $dir)) { return $null }
    $exe = Get-ChildItem -Path $dir -Filter "python.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($exe) { return $exe.FullName }
    return $null
}

$PythonExe = Find-PythonExe

# 1) Install Python with official installer if not present
if (-not $PythonExe) {
    Log "[1/5] Downloading Python installer (~25MB)..."
    $installerPath = Join-Path $ProjectRoot "python_installer.exe"
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $PythonInstallerUrl -OutFile $installerPath -UseBasicParsing
    } catch {
        Log "Download failed. Check internet."
        Read-Host "Press Enter to exit"
        exit 1
    }

    Log "[2/5] Installing Python (pip included). A window may appear..."
    New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
    $proc = Start-Process -FilePath $installerPath -ArgumentList "/passive", "InstallAllUsers=0", "PrependPath=0", "TargetDir=$InstallDir" -Wait -PassThru
    Remove-Item $installerPath -Force -ErrorAction SilentlyContinue

    if ($proc.ExitCode -ne 0) {
        Log "Python installer failed (exit code $($proc.ExitCode))."
        Read-Host "Press Enter to exit"
        exit 1
    }

    $PythonExe = Find-PythonExe
    if (-not $PythonExe) {
        Log "Python not found in $InstallDir. Try installing Python from python.org and run build.bat instead."
        Read-Host "Press Enter to exit"
        exit 1
    }
    Log "Python installed: $PythonExe"
} else {
    Log "[1/5] Using existing Python: $PythonExe"
}

# 2) Install dependencies
Log "[3/5] Installing packages..."
& $PythonExe -m pip install -r requirements.txt -q
if ($LASTEXITCODE -ne 0) {
    Log "pip install failed."
    Read-Host "Press Enter to exit"
    exit 1
}

# 3) Playwright Chromium
Log "[4/5] Installing Chromium for Playwright..."
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $ProjectRoot "playwright_browsers"
New-Item -ItemType Directory -Force -Path $env:PLAYWRIGHT_BROWSERS_PATH | Out-Null
& $PythonExe -m playwright install chromium
if ($LASTEXITCODE -ne 0) {
    Log "Playwright Chromium install failed."
    Read-Host "Press Enter to exit"
    exit 1
}

# 4) PyInstaller + build
Log "[5/5] Building exe (this may take a few minutes)..."
& $PythonExe -m pip install pyinstaller -q
& $PythonExe -m PyInstaller --noconfirm app.spec 2>&1
if ($LASTEXITCODE -ne 0) {
    Log "PyInstaller failed. Check errors above."
    Read-Host "Press Enter to exit"
    exit 1
}

$distDir = Join-Path $ProjectRoot "dist\MarketingSolution"
if (-not (Test-Path $distDir)) {
    Log "WARNING: dist\MarketingSolution not found."
    if (Test-Path (Join-Path $ProjectRoot "dist")) { Get-ChildItem (Join-Path $ProjectRoot "dist") }
    Read-Host "Press Enter to exit"
    exit 1
}

if (Test-Path "사용방법_배포용.txt") {
    Copy-Item "사용방법_배포용.txt" (Join-Path $distDir "사용방법.txt") -Force -ErrorAction SilentlyContinue
}

Log ""
Log "====== Done ======"
Log "Output folder: dist\MarketingSolution"
Log "Zip that folder and send. User runs MarketingSolution.exe"
Log ""
Read-Host "Press Enter to exit"
