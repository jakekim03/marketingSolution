# Python install + build - no manual Python install needed.
# Run: Right-click -> Run with PowerShell, or: powershell -ExecutionPolicy Bypass -File setup_and_build.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
Set-Location $ProjectRoot

$PythonEmbedUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"
$GetPipUrl = "https://bootstrap.pypa.io/get-pip.py"
$EmbedDir = Join-Path $ProjectRoot ".python_embed"
$PythonExe = Join-Path $EmbedDir "python.exe"

function Log { param($msg) Write-Host $msg }

# 1) Use existing .python_embed or download
if (-not (Test-Path $PythonExe)) {
    Log "[1/5] Downloading Python (one-time, ~25MB)..."
    $zipPath = Join-Path $ProjectRoot "python_embed.zip"
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $PythonEmbedUrl -OutFile $zipPath -UseBasicParsing
    } catch {
        Log "Download failed. Check internet. URL: $PythonEmbedUrl"
        Read-Host "Press Enter to exit"
        exit 1
    }
    Expand-Archive -Path $zipPath -DestinationPath $EmbedDir -Force
    Remove-Item $zipPath -Force -ErrorAction SilentlyContinue

    # Enable site for pip
    $pth = Get-ChildItem (Join-Path $EmbedDir "python*.pth") | Select-Object -First 1
    if ($pth) {
        $content = Get-Content $pth.FullName -Raw
        $content = $content -replace "#import site", "import site"
        Set-Content $pth.FullName -Value $content -NoNewline
    }

    Log "[2/5] Installing pip..."
    $getPip = Join-Path $ProjectRoot "get_pip.py"
    Invoke-WebRequest -Uri $GetPipUrl -OutFile $getPip -UseBasicParsing
    & $PythonExe $getPip --no-warn-script-location
    Remove-Item $getPip -Force -ErrorAction SilentlyContinue
} else {
    Log "[1/5] Using existing .python_embed"
}

# 2) Install dependencies
Log "[3/5] Installing packages..."
$env:PATH = "$EmbedDir;$EmbedDir\Scripts;$env:PATH"
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
Log "[5/5] Building exe..."
& $PythonExe -m pip install pyinstaller -q
& $PythonExe -m PyInstaller --noconfirm app.spec
if ($LASTEXITCODE -ne 0) {
    Log "PyInstaller failed."
    Read-Host "Press Enter to exit"
    exit 1
}

$distDir = Join-Path $ProjectRoot "dist\법인영업솔루션"
if (Test-Path "사용방법_배포용.txt") {
    Copy-Item "사용방법_배포용.txt" (Join-Path $distDir "사용방법.txt") -Force -ErrorAction SilentlyContinue
}

Log ""
Log "====== Done ======"
Log "Output: dist\법인영업솔루션"
Log "Zip that folder and send. User runs 법인영업솔루션.exe"
Log ""
Read-Host "Press Enter to exit"
