param(
    [string]$Version = "latest"
)

$ErrorActionPreference = 'Stop'
$repo = 'Bugsterapp/bugster-cli'
$installDir = Join-Path $env:LOCALAPPDATA 'Programs\bugster'

Write-Host "========================================" -ForegroundColor Green
Write-Host "  Bugster CLI Installer for Windows" -ForegroundColor Green
Write-Host "========================================"
Write-Host
Write-Host "Installation Directory: $installDir"
Write-Host "Version to install: $Version"
Write-Host

# Step 1: Check for Node.js and npm. If not found, try to install them.
Write-Host "[*] Checking for Node.js and npm..."
$nodeExists = Get-Command node -ErrorAction SilentlyContinue
if (-not $nodeExists) {
    Write-Host "[-] Node.js not found. Attempting to install the latest LTS version..." -ForegroundColor Yellow
    $wingetExists = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $wingetExists) {
        Write-Host "`n[ERROR] Cannot install Node.js automatically because 'winget' is not available." -ForegroundColor Red
        Write-Host "Please install Node.js LTS manually from https://nodejs.org/ and run this installer again." -ForegroundColor Yellow
        exit 1
    }
    
    try {
        Write-Host "[*] Installing Node.js LTS via winget. This may take a few minutes..."
        winget install --id OpenJS.NodeJS.LTS -e --accept-source-agreements --accept-package-agreements
        Write-Host "[+] Node.js installed successfully." -ForegroundColor Green

        # Add the default Node.js path to the current session's PATH to find it immediately.
        # This is crucial for the subsequent 'npx' command to work.
        $nodeInstallPath = "C:\Program Files\nodejs"
        $env:Path = "$nodeInstallPath;" + $env:Path
        Write-Host "[*] Updated session PATH to include Node.js."

    } catch {
        Write-Host "`n[ERROR] Failed to install Node.js using winget." -ForegroundColor Red
        Write-Host "Please install Node.js LTS manually from https://nodejs.org/ and run this installer again." -ForegroundColor Yellow
        exit 1
    }
} else {
    $nodeVersion = (node --version)
    Write-Host "[+] Found Node.js version $nodeVersion."
}


# Step 2: Determine release URL
# ... (el resto del script es idéntico)
if ($Version -eq 'latest') {
    $releaseUrl = "https://api.github.com/repos/$repo/releases/latest"
} else {
    $releaseUrl = "https://api.github.com/repos/$repo/releases/tags/$Version"
}

Write-Host "[*] Fetching release information from $releaseUrl"
try {
    $releaseInfo = Invoke-RestMethod -Uri $releaseUrl
} catch {
    Write-Host "`n[ERROR] Failed to fetch release information for version '$Version'." -ForegroundColor Red
    Write-Host "Please check if the version tag exists and you have an internet connection." -ForegroundColor Red
    exit 1
}

$asset = $releaseInfo.assets | Where-Object { $_.name -eq 'bugster-windows.zip' }
if (-not $asset) {
    Write-Host "`n[ERROR] Could not find 'bugster-windows.zip' in release $($releaseInfo.tag_name)." -ForegroundColor Red
    exit 1
}

$downloadUrl = $asset.browser_download_url
$zipFileName = "bugster-windows.zip"
$tempDir = Join-Path $env:TEMP "bugster-install-$($PID)"
$zipFilePath = Join-Path $tempDir $zipFileName

# Step 3: Download the asset
Write-Host "[*] Downloading $($asset.name) from $($releaseInfo.tag_name)..."
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
Invoke-WebRequest -Uri $downloadUrl -OutFile $zipFilePath
Write-Host "[+] Download complete."

# Step 4: Create installation directory and extract
Write-Host "[*] Creating installation directory at $installDir"
New-Item -ItemType Directory -Path $installDir -Force | Out-Null

Write-Host "[*] Extracting $zipFileName..."
Expand-Archive -Path $zipFilePath -DestinationPath $installDir -Force
Write-Host "[+] Extraction complete."

# Step 5: Add to user PATH if not already present
Write-Host "[*] Checking user PATH environment variable..."
$userPath = [System.Environment]::GetEnvironmentVariable('PATH', 'User')
if ($userPath -notlike "*$installDir*") {
    Write-Host "[*] Adding $installDir to your PATH."
    if ([string]::IsNullOrEmpty($userPath)) {
        $newPath = $installDir
    } else {
        $newPath = "$userPath;$installDir"
    }
    [System.Environment]::SetEnvironmentVariable('PATH', $newPath, 'User')
    Write-Host "[+] PATH updated successfully." -ForegroundColor Green
    Write-Host "IMPORTANT: You must restart your terminal for the changes to take effect." -ForegroundColor Yellow
} else {
    Write-Host "[+] Installation directory is already in your PATH."
}

# Step 6: Install Playwright browser dependencies silently
Write-Host "[*] Installing Playwright browser dependencies (Chromium)..."
Write-Host "This might take a few minutes."
try {
    cmd /d /c "npx --silent -y playwright install --with-deps chromium >NUL 2>&1"
    if ($LASTEXITCODE -ne 0) {
        throw "Playwright installation failed with exit code $LASTEXITCODE."
    }
    Write-Host "[+] Browser dependencies installed successfully." -ForegroundColor Green
} catch {
    Write-Host "`n[ERROR] Failed to install Playwright browser dependencies." -ForegroundColor Red
    Write-Host "You may need to run the installer manually from a terminal with Administrator privileges." -ForegroundColor Yellow
}
# Step 7: Clean up
Write-Host "[*] Cleaning up temporary files..."
Remove-Item -Path $tempDir -Recurse -Force
Write-Host "[+] Cleanup complete."

Write-Host
Write-Host "==================================================" -ForegroundColor Green
Write-Host " Bugster CLI was installed successfully!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host "`nRun 'bugster --help' in a NEW terminal window to get started."
