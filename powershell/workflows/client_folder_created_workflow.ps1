param(
    [string]$ClientName,
    [string]$ClientFolderPath
)

$LogRoot = "exports\workflow_logs"
New-Item -ItemType Directory -Force -Path $LogRoot | Out-Null

$GeneralFolder = Join-Path $ClientFolderPath "general"
New-Item -ItemType Directory -Force -Path $GeneralFolder | Out-Null

$WelcomeFile = Join-Path $GeneralFolder "welcome.txt"

@"
Welcome to That Corporate Flow

Client: $ClientName
Folder Created: $(Get-Date)

This folder is managed by That Corporate Flow.
Use it to store contracts, invoices, quotations, proposals, reports, certificates, and general files.
"@ | Set-Content $WelcomeFile

$LogMessage = "$(Get-Date) | Client folder created for $ClientName | Welcome file generated"
Add-Content -Path "$LogRoot\workflow_log.txt" -Value $LogMessage
