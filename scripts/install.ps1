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

# Step 1: Determine release URL
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

# Step 2: Download the asset
Write-Host "[*] Downloading $($asset.name) from $($releaseInfo.tag_name)..."
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
Invoke-WebRequest -Uri $downloadUrl -OutFile $zipFilePath
Write-Host "[+] Download complete."

# Step 3: Create installation directory and extract
Write-Host "[*] Creating installation directory at $installDir"
New-Item -ItemType Directory -Path $installDir -Force | Out-Null

Write-Host "[*] Extracting $zipFileName..."
Expand-Archive -Path $zipFilePath -DestinationPath $installDir -Force
Write-Host "[+] Extraction complete."

# Step 4: Add to user PATH if not already present
Write-Host "[*] Checking user PATH environment variable..."
$userPath = [System.Environment]::GetEnvironmentVariable('PATH', 'User')
if ($userPath -notlike "*$installDir*") {
    Write-Host "[*] Adding $installDir to your PATH."
    # Handle case where PATH is empty or null
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

# Step 5: Clean up
Write-Host "[*] Cleaning up temporary files..."
Remove-Item -Path $tempDir -Recurse -Force
Write-Host "[+] Cleanup complete."

Write-Host
Write-Host "==================================================" -ForegroundColor Green
Write-Host " Bugster CLI was installed successfully!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host "`nRun 'bugster --help' in a NEW terminal window to get started." 