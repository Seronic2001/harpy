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
    Write-Host "  Harpy Uninstaller" -ForegroundColor DarkGray
    Write-Host "  ────────────────────────────────────────────────────────" -ForegroundColor DarkGray
    Write-Host ""
}

try {
    Print-Banner

    $InstallDir = "$env:LOCALAPPDATA\Programs\harpy"
    $GeminiSkill = "$env:USERPROFILE\.gemini\config\skills\harpy-cp"
    $GeminiMcp = "$env:USERPROFILE\.gemini\config\mcp_config.json"

    # 1. Remove Executable Directory
    if (Test-Path $InstallDir) {
        Remove-Item -Path $InstallDir -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "  ✔ Removed installation folder: " -NoNewline -ForegroundColor Green
        Write-Host "$InstallDir" -ForegroundColor White
    } else {
        Write-Host "  • Installation folder not found (skipped)" -ForegroundColor DarkGray
    }

    # 2. Clean User PATH
    $UserPath = [Environment]::GetEnvironmentVariable("PATH", [EnvironmentVariableTarget]::User)
    if ($UserPath -like "*$InstallDir*") {
        $Paths = $UserPath -split ';' | Where-Object { $_ -ne $InstallDir -and $_ -ne "" }
        $NewPath = $Paths -join ';'
        [Environment]::SetEnvironmentVariable("PATH", $NewPath, [EnvironmentVariableTarget]::User)
        Write-Host "  ✔ Removed Harpy from User PATH" -ForegroundColor Green
    }

    # 3. Remove Antigravity Skill
    if (Test-Path $GeminiSkill) {
        Remove-Item -Path $GeminiSkill -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "  ✔ Removed AI skill: " -NoNewline -ForegroundColor Green
        Write-Host "$GeminiSkill" -ForegroundColor White
    }

    # 4. Clean MCP Server Config
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

    # 5. Success Card
    Write-Host ""
    Write-Host "  ╭──────────────────────────────────────────────────────────────╮" -ForegroundColor Cyan
    Write-Host "  │  " -NoNewline -ForegroundColor Cyan
    Write-Host "👋 Harpy has been completely uninstalled.                  " -NoNewline -ForegroundColor Yellow
    Write-Host "│" -ForegroundColor Cyan
    Write-Host "  ├──────────────────────────────────────────────────────────────┤" -ForegroundColor Cyan
    Write-Host "  │  All binaries, environment variables, skills, and MCP        │" -ForegroundColor Cyan
    Write-Host "  │  configurations have been cleaned from your machine.         │" -ForegroundColor Cyan
    Write-Host "  │                                                              │" -ForegroundColor Cyan
    Write-Host "  │  To reinstall anytime, run:                                  │" -ForegroundColor Cyan
    Write-Host "  │  " -NoNewline -ForegroundColor Cyan
    Write-Host "irm https://raw.githubusercontent.com/.../install.ps1 | iex " -NoNewline -ForegroundColor Green
    Write-Host "│" -ForegroundColor Cyan
    Write-Host "  ╰──────────────────────────────────────────────────────────────╯" -ForegroundColor Cyan
    Write-Host ""
} catch {
    Write-Host "  ✖ Uninstallation encountered an error: $_" -ForegroundColor Red
}
