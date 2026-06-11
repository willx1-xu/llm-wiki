$startup = [Environment]::GetFolderPath('Startup')
$shortcutPath = Join-Path $startup 'LLM-Wiki.lnk'
$WScriptShell = New-Object -ComObject WScript.Shell
$shortcut = $WScriptShell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = 'wscript.exe'
$shortcut.Arguments = '"D:\牛逼666\网站\start-wiki.vbs"'
$shortcut.WorkingDirectory = 'D:\牛逼666\网站'
$shortcut.WindowStyle = 7
$shortcut.Save()
Write-Output "Done: $shortcutPath"
