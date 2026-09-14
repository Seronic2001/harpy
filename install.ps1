$ErrorActionPreference = 'Stop'

$InstallDir = "$env:LOCALAPPDATA\Programs\harpy"
$ExePath = "$InstallDir\harpy.exe"
$Url = "https://github.com/Seronic2001/harpy/releases/latest/download/harpy-windows-x86_64.exe"

New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
Write-Host "🦅 Downloading Harpy for Windows..." -ForegroundColor Cyan
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Invoke-WebRequest -Uri $Url -OutFile $ExePath -UseBasicParsing

# Add to user PATH if not present
$UserPath = [Environment]::GetEnvironmentVariable("PATH", [EnvironmentVariableTarget]::User)
if ($UserPath -notlike "*$InstallDir*") {
    [Environment]::SetEnvironmentVariable("PATH", "$UserPath;$InstallDir", [EnvironmentVariableTarget]::User)
    $env:PATH += ";$InstallDir"
    Write-Host "✔ Added $InstallDir to User PATH" -ForegroundColor Green
}

Write-Host "✨ Harpy installed successfully!" -ForegroundColor Green
Write-Host "Run 'harpy setup-ai' in your terminal to get started." -ForegroundColor Cyan
