param(
    [string]$ClientName,
    [string]$ReportFilePath
)

$SafeClientName = $ClientName -replace '[^a-zA-Z0-9_-]', '_'
$ReportArchive = "client_files\archive\$SafeClientName\reports"
$LogRoot = "exports\workflow_logs"

New-Item -ItemType Directory -Force -Path $ReportArchive | Out-Null
New-Item -ItemType Directory -Force -Path $LogRoot | Out-Null

if (Test-Path $ReportFilePath) {
    Copy-Item $ReportFilePath $ReportArchive -Force

    $SummaryFile = Join-Path $ReportArchive "report_summary.txt"

    @"
Report Upload Summary

Client: $ClientName
Uploaded: $(Get-Date)
Original File: $ReportFilePath
Status: Archived successfully
"@ | Set-Content $SummaryFile

    Add-Content -Path "$LogRoot\workflow_log.txt" -Value "$(Get-Date) | Report uploaded for $ClientName | Summary generated"
}
else {
    Add-Content -Path "$LogRoot\workflow_log.txt" -Value "$(Get-Date) | ERROR | Report file missing: $ReportFilePath"
}
