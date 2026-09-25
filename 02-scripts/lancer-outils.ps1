# Lance un outil de l'atelier. Usage :
#   powershell -ExecutionPolicy Bypass -File 02-scripts\lancer-outils.ps1 -Outil terry|bob|dave|rpfm|rpfm-server|caime
#
# terry / bob / dave : version Steam de l'Assembly Kit de Warhammer III (raw_data et working_data de Steam).
# Les memes outils existent aussi dans le paquet Microsoft Store (conteneur separe, ses propres raw_data) :
#   explorer.exe shell:AppsFolder\18793CreativeAssemblyLtd.TotalWarWARHAMMERIII-Asse_ry6v8xxqmygx8!Terry   (ou !BOB, !DaVE)
# (Fichier sans accents : PowerShell 5.1 lit un .ps1 sans BOM en ANSI.)

param([Parameter(Mandatory = $true)][ValidateSet("terry", "bob", "dave", "rpfm", "rpfm-server", "caime")][string]$Outil)

$ak    = "C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit"
$rpfm  = "C:\TotalWar-CampaignMap\01-outils\RPFM\rpfm-v5.0.6-x86_64-pc-windows-msvc"
$caime = "C:\TotalWar-CampaignMap\01-outils\CampaignMapToolkit\CAIME\bin\Debug\CAIME.exe"

switch ($Outil) {
    "terry"       { Start-Process -FilePath "$ak\binaries\tweak.modder.x64.exe" -ArgumentList "/standalone", "TerrainMetadataEditor" -WorkingDirectory "$ak\binaries" }
    "bob"         { Start-Process -FilePath "$ak\binaries\bob.modder.x64.exe" -WorkingDirectory "$ak\binaries" }
    "dave"        { Start-Process -FilePath "$ak\dave\DaVE.retail.x64.exe" -WorkingDirectory "$ak\dave" }
    "rpfm"        { Start-Process -FilePath "$rpfm\rpfm_ui.exe" -WorkingDirectory $rpfm }
    "rpfm-server" { Start-Process -FilePath "$rpfm\rpfm_server.exe" -WorkingDirectory $rpfm; Write-Host "rpfm_server ecoute sur http://127.0.0.1:45127  (MCP : /mcp, WebSocket : /ws, sessions : /sessions)" }
    "caime"       { Start-Process -FilePath $caime }
}
Write-Host "Lance : $Outil"
