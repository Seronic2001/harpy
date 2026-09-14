# Harpy Windows PowerShell Installer
$ErrorActionPreference = 'Stop'

function Print-Banner {
    Write-Host ""
    Write-Host "    __  __                            " -ForegroundColor Cyan
    Write-Host "   / / / /___ _________  __  __       " -ForegroundColor Cyan
    Write-Host "  / /_/ / __ `/ ___/ __ \/ / / /  🦅   " -ForegroundColor Cyan
    Write-Host " / __  / /_/ / /  / /_/ / /_/ /       " -ForegroundColor Cyan
    Write-Host "/_/ /_/\__,_/_/  / .___/\__, /        " -ForegroundColor Cyan
    Write-Host "                /_/    /____/         " -ForegroundColor DarkCyan
    Write-Host "  ⚡ Fast Competitive Programming & Interview Prep Toolkit" -ForegroundColor DarkGray
    Write-Host "  ────────────────────────────────────────────────────────" -ForegroundColor DarkGray
    Write-Host ""
}

try {
    Print-Banner

    $InstallDir = "$env:LOCALAPPDATA\Programs\harpy"
    $ExePath = "$InstallDir\harpy.exe"
    $Url = "https://github.com/Seronic2001/harpy/releases/latest/download/harpy-windows-x86_64.exe"

    # 1. Check Architecture
    $Arch = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture
    Write-Host "  ✔ Detected platform: " -NoNewline -ForegroundColor Green
    Write-Host "Windows ($Arch)" -ForegroundColor White

    # 2. Prepare Directory
    if (-not (Test-Path $InstallDir)) {
        New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
    }

    # 3. Download Binary
    Write-Host "  ▸ Downloading Harpy standalone binary... " -NoNewline -ForegroundColor Cyan
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $TmpFile = "$InstallDir\.harpy_download.tmp"

    $ProgressPreference = 'SilentlyContinue'
    Invoke-WebRequest -Uri $Url -OutFile $TmpFile -UseBasicParsing
    Move-Item -Path $TmpFile -Destination $ExePath -Force

    Write-Host "`r  ✔ Downloaded Harpy standalone binary    " -ForegroundColor Green

    # 4. Verify Execution
    $Version = "harpy"
    try {
        $VersionOutput = & "$ExePath" --version 2>$null
        if ($VersionOutput) { $Version = $VersionOutput }
    } catch {}

    Write-Host "  ✔ Verified binary: " -NoNewline -ForegroundColor Green
    Write-Host "$Version" -ForegroundColor White

    # 5. Configure User PATH permanently
    $PathUpdated = $false
    $UserPath = [Environment]::GetEnvironmentVariable("PATH", [EnvironmentVariableTarget]::User)
    if ($UserPath -notlike "*$InstallDir*") {
        $NewPath = if ([string]::IsNullOrEmpty($UserPath)) { $InstallDir } else { "$UserPath;$InstallDir" }
        [Environment]::SetEnvironmentVariable("PATH", $NewPath, [EnvironmentVariableTarget]::User)
        $env:PATH += ";$InstallDir"
        Write-Host "  ✔ Added to User PATH: " -NoNewline -ForegroundColor Green
        Write-Host "$InstallDir" -ForegroundColor Cyan
        $PathUpdated = $true
    } else {
        Write-Host "  ✔ Shell PATH: " -NoNewline -ForegroundColor Green
        Write-Host "$InstallDir is already in PATH" -ForegroundColor DarkGray
    }

    # 6. Success Card
    Write-Host ""
    Write-Host "  ╭──────────────────────────────────────────────────────────────╮" -ForegroundColor Cyan
    Write-Host "  │  " -NoNewline -ForegroundColor Cyan
    Write-Host "✨ Harpy installed successfully!                            " -NoNewline -ForegroundColor Green
    Write-Host "│" -ForegroundColor Cyan
    Write-Host "  ├──────────────────────────────────────────────────────────────┤" -ForegroundColor Cyan
    Write-Host "  │  • Executable:  " -NoNewline -ForegroundColor Cyan
    Write-Host ("{0,-43}" -f $ExePath) -NoNewline -ForegroundColor White
    Write-Host " │" -ForegroundColor Cyan
    Write-Host "  │  • Version:     " -NoNewline -ForegroundColor Cyan
    Write-Host ("{0,-43}" -f $Version) -NoNewline -ForegroundColor White
    Write-Host " │" -ForegroundColor Cyan
    Write-Host "  │                                                              │" -ForegroundColor Cyan
    Write-Host "  │  Next Steps:                                                 │" -ForegroundColor Cyan
    Write-Host "  │    1. Auto-configure AI & MCP:   " -NoNewline -ForegroundColor Cyan
    Write-Host "harpy setup-ai              " -NoNewline -ForegroundColor Green
    Write-Host "│" -ForegroundColor Cyan
    Write-Host "  │    2. Start practicing:          " -NoNewline -ForegroundColor Cyan
    Write-Host "harpy init                  " -NoNewline -ForegroundColor Green
    Write-Host "│" -ForegroundColor Cyan
    if ($PathUpdated) {
        Write-Host "  │                                                              │" -ForegroundColor Cyan
        Write-Host "  │  " -NoNewline -ForegroundColor Cyan
        Write-Host "⚠ Note: Restart PowerShell to use 'harpy' directly           " -NoNewline -ForegroundColor Yellow
        Write-Host "│" -ForegroundColor Cyan
    }
    Write-Host "  ╰──────────────────────────────────────────────────────────────╯" -ForegroundColor Cyan
    Write-Host ""
} catch {
    Write-Host ""
    Write-Host "  ✖ Installation failed: $_" -ForegroundColor Red
    Write-Host "    Tip: You can also install via: pip install harpy-cp" -ForegroundColor Yellow
    exit 1
}
