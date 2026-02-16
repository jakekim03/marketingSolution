Set fso = CreateObject("Scripting.FileSystemObject")
Set WshShell = CreateObject("WScript.Shell")
folder = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.Run "cmd /k ""cd /d " & Chr(34) & folder & Chr(34) & " && build.bat""", 1, False
