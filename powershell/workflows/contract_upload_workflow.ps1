param(
    [string]$ClientName,
    [string]$UploadedFilePath
)

$SafeClientName = $ClientName -replace '[^a-zA-Z0-9_-]', '_'
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

$ArchiveRoot = "client_files\archive\$SafeClientName"
$LogRoot = "exports\workflow_logs"

New-Item -ItemType Directory -Force -Path $ArchiveRoot | Out-Null
New-Item -ItemType Directory -Force -Path $LogRoot | Out-Null

if (Test-Path $UploadedFilePath) {
    $FileName = Split-Path $UploadedFilePath -Leaf
    $NewFileName = "$Timestamp`_$FileName"
    $ArchivePath = Join-Path $ArchiveRoot $NewFileName

    Copy-Item $UploadedFilePath $ArchivePath -Force

    $LogMessage = "$(Get-Date) | Contract uploaded for $ClientName | Archived as $ArchivePath"
    Add-Content -Path "$LogRoot\workflow_log.txt" -Value $LogMessage
}
else {
    $LogMessage = "$(Get-Date) | ERROR | Uploaded file not found: $UploadedFilePath"
    Add-Content -Path "$LogRoot\workflow_log.txt" -Value $LogMessage
}
