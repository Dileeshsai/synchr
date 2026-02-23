# Allow inbound TCP port 8000 so mobile devices / other machines can reach Django runserver.
# Run as Administrator: Right-click PowerShell -> Run as administrator, then:
#   Set-Location E:\sync_mobile\backend\synchr
#   .\scripts\allow_firewall_port_8000.ps1

$ruleName = "Django Runserver (TCP 8000)"
$port = 8000

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "This script must be run as Administrator to add a firewall rule." -ForegroundColor Yellow
    Write-Host "Right-click PowerShell and choose 'Run as administrator', then run this script again." -ForegroundColor Yellow
    exit 1
}

$existing = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Rule '$ruleName' already exists. Removing to recreate..." -ForegroundColor Cyan
    Remove-NetFirewallRule -DisplayName $ruleName
}

try {
    New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Protocol TCP -LocalPort $port -Action Allow -Profile Any
} catch {
    Write-Host "Failed to add firewall rule: $_" -ForegroundColor Red
    exit 1
}

Write-Host "Firewall rule added: inbound TCP port $port is now allowed." -ForegroundColor Green
Write-Host "Mobile app should be able to reach http://YOUR_PC_IP:8000 (e.g. http://192.168.1.136:8000)" -ForegroundColor Green
Write-Host "Verify your PC IP with: ipconfig" -ForegroundColor Cyan
