param(
    [string]$DatabasePath = "..\youtube_studio.db",
    [string]$OutputDirectory = "..\backups",
    [int]$RetentionDays = 30
)

$ErrorActionPreference = "Stop"
$scriptRoot = Split-Path -Parent $PSScriptRoot
$resolvedDatabase = (Resolve-Path (Join-Path $scriptRoot $DatabasePath)).Path
$resolvedOutput = Join-Path $scriptRoot $OutputDirectory
New-Item -ItemType Directory -Force -Path $resolvedOutput | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backup = Join-Path $resolvedOutput "youtube_studio-$timestamp.db"
Copy-Item -LiteralPath $resolvedDatabase -Destination $backup -Force

Get-ChildItem -LiteralPath $resolvedOutput -Filter "youtube_studio-*.db" |
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$RetentionDays) } |
    Remove-Item -Force

Write-Output "Database backup created: $backup"
