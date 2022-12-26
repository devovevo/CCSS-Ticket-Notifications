for /f "delims=" %%A in ('chdir') do set "currentdir=%%A"
(
    echo cd %currentdir%
    echo start "Notify" /MIN "Powershell.exe" -windowstyle hidden -File startnotificationsgithub.ps1
)>"%USERPROFILE%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\startup_ccss_notifications_github.bat"