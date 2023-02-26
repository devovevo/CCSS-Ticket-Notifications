./ccss_ticketing_venv/Scripts/activate

function startNotifierWithWifi {
    while (-not (Test-Connection google.com -Count 1 -Quiet)) {
        Start-Sleep -Seconds 15
    }

    python .\ccss_ticketing_notify.py
}

for(;;) {
    try {
        If (!(Get-Process -Name chromedriver -ErrorAction SilentlyContinue)) {
            startNotifierWithWifi
        }
        
        $proc = Get-Process -Name chromedriver | Sort-Object -Property ProcessName -Unique -ErrorActionSilentlyContinue
        
        If (!$proc -or ($proc.Responding -eq $false) -or ($proc.WorkingSet -GT 50000*1024)) 
        {
            $proc.Kill()
            Start-Sleep -s 10
            startNotifierWithWifi
        }
    }
    catch {
        Write-Output "Error starting or closing notifier"
    }
    
    Start-sleep -s 60
}