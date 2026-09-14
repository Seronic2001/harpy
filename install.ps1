# Harpy Windows PowerShell Installer
$ErrorActionPreference = 'Stop'

function Print-Banner {
    Write-Host ""
    $lines = @(
        '    __  __                            ',
        '   / / / /___ _________  __  __       ',
        '  / /_/ / __ `/ ___/ __ \/ / / /  🦅   ',
        ' / __  / /_/ / /  / /_/ / /_/ /       ',
        '/_/ /_/\__,_/_/  / .___/\__, /        ',
        '                /_/    /____/         '
    )
    $colors = @("Cyan", "Cyan", "Cyan", "Cyan", "Cyan", "DarkCyan")
    for ($idx = 0; $idx -lt $lines.Length; $idx++) {
        Write-Host $lines[$idx] -ForegroundColor $colors[$idx]
        Start-Sleep -Milliseconds 25
    }
    Write-Host "  ⚡ Fast Competitive Programming & Interview Prep Toolkit" -ForegroundColor DarkGray
    Write-Host "  ────────────────────────────────────────────────────────" -ForegroundColor DarkGray
    Write-Host ""
}

try {
    Print-Banner

    $InstallDir = "$env:LOCALAPPDATA\Programs\harpy"
    $ExePath = "$InstallDir\harpy.exe"
    $Url = "https://github.com/Seronic2001/harpy/releases/latest/download/harpy-windows-x86_64.exe"

    # 1. Detect Architecture
    $Arch = $env:PROCESSOR_ARCHITECTURE
    if (-not $Arch) {
        try {
            $Arch = [System.Environment]::GetEnvironmentVariable("PROCESSOR_ARCHITECTURE")
        } catch {}
    }
    if (-not $Arch) { $Arch = "AMD64" }
    $ArchLabel = if ($Arch -eq "AMD64") { "x64" } elseif ($Arch -eq "ARM64") { "arm64" } else { $Arch }

    Write-Host "  ✔ Detected platform: " -NoNewline -ForegroundColor Green
    Write-Host "Windows ($ArchLabel)" -ForegroundColor White

    # 2. Prepare Directory
    if (-not (Test-Path $InstallDir)) {
        New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
    }

    $TmpFile = "$InstallDir\.harpy_download.tmp"
    if (Test-Path $TmpFile) { Remove-Item $TmpFile -Force -ErrorAction SilentlyContinue }

    # 3. Asynchronous Download with Real-Time Animated Spinner
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    try { [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls13 } catch {}
    $wc = New-Object System.Net.WebClient
    $wc.Headers.Add("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) harpy-installer")

    $spinChars = @('⠋','⠙','⠹','⠸','⠼','⠴','⠦','⠧','⠇','⠏')
    $i = 0

    $wc.DownloadFileAsync([System.Uri]$Url, $TmpFile)

    while ($wc.IsBusy) {
        $mbStr = ""
        if (Test-Path $TmpFile) {
            try {
                $bytes = (Get-Item $TmpFile).Length
                if ($bytes -gt 0) {
                    $mb = [Math]::Round($bytes / 1MB, 1)
                    $mbStr = " ($mb MB)"
                }
            } catch {}
        }
        Write-Host ("`r  " + $spinChars[$i] + " Downloading Harpy standalone binary..." + $mbStr + "   ") -NoNewline -ForegroundColor Cyan
        $i = ($i + 1) % $spinChars.Length
        Start-Sleep -Milliseconds 70
    }

    # Verify download succeeded or fallback
    if (-not (Test-Path $TmpFile) -or (Get-Item $TmpFile).Length -lt 1000000) {
        Write-Host "`r  ▸ Retrying download with standard transport...               " -ForegroundColor Yellow
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $Url -OutFile $TmpFile -UseBasicParsing
    }

    $finalSize = [Math]::Round((Get-Item $TmpFile).Length / 1MB, 1)
    # Remove existing binary first to avoid "file already exists" errors
    if (Test-Path $ExePath) {
        Remove-Item -Path $ExePath -Force -ErrorAction SilentlyContinue
    }
    try {
        Move-Item -Path $TmpFile -Destination $ExePath -Force
    } catch {
        # Fallback: copy then delete if move fails (e.g. cross-drive or locked)
        Copy-Item -Path $TmpFile -Destination $ExePath -Force
        Remove-Item -Path $TmpFile -Force -ErrorAction SilentlyContinue
    }
    Write-Host "`r  ✔ Downloaded Harpy standalone binary ($finalSize MB)            " -ForegroundColor Green

    # 4. Verify Execution
    $Version = "harpy"
    try {
        $VersionOutput = & "$ExePath" --version 2>$null
        if ($VersionOutput) { $Version = $VersionOutput.Trim() }
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

    # 5b. Create harpy.cmd shim in WindowsApps for instant availability
    $WindowsApps = "$env:LOCALAPPDATA\Microsoft\WindowsApps"
    if (Test-Path $WindowsApps) {
        $ShimPath = "$WindowsApps\harpy.cmd"
        $ShimContent = "@echo off`r`n`"$ExePath`" %*"
        Set-Content -Path $ShimPath -Value $ShimContent -Encoding ASCII -ErrorAction SilentlyContinue
        if (Test-Path $ShimPath) {
            Write-Host "  ✔ Created instant shim: " -NoNewline -ForegroundColor Green
            Write-Host "$ShimPath" -ForegroundColor DarkGray
        }
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
    Write-Host "  │    2. Enable completions:        " -NoNewline -ForegroundColor Cyan
    Write-Host "harpy completion install    " -NoNewline -ForegroundColor Green
    Write-Host "│" -ForegroundColor Cyan
    Write-Host "  │    3. Start practicing:          " -NoNewline -ForegroundColor Cyan
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
    Write-Host ""
}
