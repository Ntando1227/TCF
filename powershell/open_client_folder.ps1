param(
    [string]$FolderPath
)

if (Test-Path $FolderPath) {
    Start-Process explorer.exe $FolderPath
} else {
    Write-Host "Folder does not exist: $FolderPath"
}
