$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

$BackupRoot = "backups"
$BackupFolder = "$BackupRoot\backup_$Timestamp"
$LogRoot = "exports\workflow_logs"

New-Item -ItemType Directory -Force -Path $BackupFolder | Out-Null
New-Item -ItemType Directory -Force -Path $LogRoot | Out-Null

Copy-Item "client_files" "$BackupFolder\client_files" -Recurse -Force
Copy-Item "generated_documents" "$BackupFolder\generated_documents" -Recurse -Force
Copy-Item "exports" "$BackupFolder\exports" -Recurse -Force

Add-Content `
    -Path "$LogRoot\workflow_log.txt" `
    -Value "$(Get-Date) | Daily backup completed | $BackupFolder"
