# Harpy Windows PowerShell Uninstaller
$ErrorActionPreference = 'SilentlyContinue'

function Print-Banner {
    Write-Host ""
    Write-Host "    __  __                            " -ForegroundColor Cyan
    Write-Host "   / / / /___ _________  __  __       " -ForegroundColor Cyan
    Write-Host "  / /_/ / __ `/ ___/ __ \/ / / /  🦅   " -ForegroundColor Cyan
    Write-Host " / __  / /_/ / /  / /_/ / /_/ /       " -ForegroundColor Cyan
    Write-Host "/_/ /_/\__,_/_/  / .___/\__, /        " -ForegroundColor Cyan
    Write-Host "                /_/    /____/         " -ForegroundColor DarkCyan
    Write-Host "  Harpy Uninstaller (Windows)" -ForegroundColor DarkGray
    Write-Host "  ────────────────────────────────────────────────────────" -ForegroundColor DarkGray
    Write-Host ""
}

try {
    Print-Banner

    $InstallDir = "$env:LOCALAPPDATA\Programs\harpy"
    $GeminiSkill = "$env:USERPROFILE\.gemini\config\skills\harpy-cp"
    $GeminiMcp = "$env:USERPROFILE\.gemini\config\mcp_config.json"

    # 1. Uninstall pip/pipx packages if present
    Write-Host "  ▸ Checking pip / pipx installations..." -ForegroundColor DarkGray
    $pipCmd = Get-Command "pip" -ErrorAction SilentlyContinue
    if ($pipCmd) {
        pip uninstall -y harpy-cp 2>$null | Out-Null
        Write-Host "  ✔ Uninstalled harpy-cp from pip" -ForegroundColor Green
    }
    $pipxCmd = Get-Command "pipx" -ErrorAction SilentlyContinue
    if ($pipxCmd) {
        pipx uninstall harpy-cp 2>$null | Out-Null
    }

    # 2. Remove Standalone Executable Directory
    if (Test-Path $InstallDir) {
        Remove-Item -Path $InstallDir -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "  ✔ Removed binary folder: " -NoNewline -ForegroundColor Green
        Write-Host "$InstallDir" -ForegroundColor White
    }

    # 3. Clean User PATH in Environment Registry
    $UserPath = [Environment]::GetEnvironmentVariable("PATH", [EnvironmentVariableTarget]::User)
    if ($UserPath -like "*$InstallDir*") {
        $Paths = $UserPath -split ';' | Where-Object { $_ -ne $InstallDir -and $_ -ne "" }
        $NewPath = $Paths -join ';'
        [Environment]::SetEnvironmentVariable("PATH", $NewPath, [EnvironmentVariableTarget]::User)
        Write-Host "  ✔ Removed Harpy from Windows User PATH" -ForegroundColor Green
    }

    # 4. Clean PowerShell Profile ($PROFILE) if modified
    if ($PROFILE -and (Test-Path $PROFILE)) {
        $ProfileContent = Get-Content $PROFILE -Raw
        if ($ProfileContent -match "harpy") {
            $Cleaned = ($ProfileContent -split "`n" | Where-Object { $_ -notmatch "harpy" }) -join "`n"
            Set-Content $PROFILE -Value $Cleaned -Encoding UTF8
            Write-Host "  ✔ Cleaned Harpy references from PowerShell profile ($PROFILE)" -ForegroundColor Green
        }
    }

    # 5. Clean Git Bash ~/.bashrc if present
    $Bashrc = "$env:USERPROFILE\.bashrc"
    if (Test-Path $Bashrc) {
        $BashrcContent = Get-Content $Bashrc -Raw
        if ($BashrcContent -match "harpy") {
            $CleanedBash = ($BashrcContent -split "`n" | Where-Object { $_ -notmatch "harpy" }) -join "`n"
            Set-Content $Bashrc -Value $CleanedBash -Encoding UTF8
            Write-Host "  ✔ Cleaned Harpy references from Git Bash ~/.bashrc" -ForegroundColor Green
        }
    }

    # 6. Remove Antigravity AI Skill
    if (Test-Path $GeminiSkill) {
        Remove-Item -Path $GeminiSkill -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "  ✔ Removed AI skill: " -NoNewline -ForegroundColor Green
        Write-Host "$GeminiSkill" -ForegroundColor White
    }

    # 7. Clean MCP Server Config
    if (Test-Path $GeminiMcp) {
        try {
            $JsonContent = Get-Content $GeminiMcp -Raw | ConvertFrom-Json
            if ($JsonContent.mcpServers.harpy) {
                $JsonContent.mcpServers.PSObject.Properties.Remove('harpy')
                $JsonContent | ConvertTo-Json -Depth 10 | Set-Content $GeminiMcp -Encoding UTF8
                Write-Host "  ✔ Removed harpy from MCP configuration" -ForegroundColor Green
            }
        } catch {}
    }

    # 8. Success Card
    Write-Host ""
    Write-Host "  ╭──────────────────────────────────────────────────────────────╮" -ForegroundColor Cyan
    Write-Host "  │  " -NoNewline -ForegroundColor Cyan
    Write-Host "👋 Harpy has been completely uninstalled.                  " -NoNewline -ForegroundColor Yellow
    Write-Host "│" -ForegroundColor Cyan
    Write-Host "  ├──────────────────────────────────────────────────────────────┤" -ForegroundColor Cyan
    Write-Host "  │  All binaries, environment variables, skills, and MCP        │" -ForegroundColor Cyan
    Write-Host "  │  configurations have been cleaned from your machine.         │" -ForegroundColor Cyan
    Write-Host "  │                                                              │" -ForegroundColor Cyan
    Write-Host "  │  To reinstall anytime:                                       │" -ForegroundColor Cyan
    Write-Host "  │  " -NoNewline -ForegroundColor Cyan
    Write-Host "irm https://raw.githubusercontent.com/.../install.ps1 | iex " -NoNewline -ForegroundColor Green
    Write-Host "│" -ForegroundColor Cyan
    Write-Host "  ╰──────────────────────────────────────────────────────────────╯" -ForegroundColor Cyan
    Write-Host ""
} catch {
    Write-Host "  ✖ Uninstallation encountered an error: $_" -ForegroundColor Red
}
