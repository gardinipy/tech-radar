Set fso = CreateObject("Scripting.FileSystemObject")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
Set sh = CreateObject("WScript.Shell")
sh.CurrentDirectory = dir
' 0 = janela oculta, False = nao espera terminar
sh.Run """" & dir & "\iniciar_radar.bat"" oculto", 0, False
