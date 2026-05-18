param(
    [string]$ClientName,
    [string]$InvoiceTitle,
    [string]$Amount,
    [string]$PdfPath
)

$SafeClientName = $ClientName -replace '[^a-zA-Z0-9_-]', '_'

$InvoiceExportRoot = "exports\invoice_exports"
$InvoiceArchiveRoot = "client_files\archive\$SafeClientName\invoices"
$LogRoot = "exports\workflow_logs"

New-Item -ItemType Directory -Force -Path $InvoiceExportRoot | Out-Null
New-Item -ItemType Directory -Force -Path $InvoiceArchiveRoot | Out-Null
New-Item -ItemType Directory -Force -Path $LogRoot | Out-Null

$LedgerPath = "$InvoiceExportRoot\invoice_ledger.csv"

if (!(Test-Path $LedgerPath)) {
    "Date,Client,InvoiceTitle,Amount,PdfPath" | Set-Content $LedgerPath
}

$Line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'),$ClientName,$InvoiceTitle,$Amount,$PdfPath"
Add-Content -Path $LedgerPath -Value $Line

if (Test-Path $PdfPath) {
    Copy-Item $PdfPath $InvoiceArchiveRoot -Force
}

$LogMessage = "$(Get-Date) | Invoice generated for $ClientName | $InvoiceTitle | R$Amount"
Add-Content -Path "$LogRoot\workflow_log.txt" -Value $LogMessage
