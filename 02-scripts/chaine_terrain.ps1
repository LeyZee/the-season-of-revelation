# Chaine complete du terrain de la Saison des Revelations (GUIDE 12.3), avec un journal horodate.
# Usage : powershell -ExecutionPolicy Bypass -File 02-scripts\chaine_terrain.ps1 -Journal <fichier.log> [-SansPack]
# Prealables : Terry et le jeu fermes, rpfm_server lance (lancer-outils.ps1 -Outil rpfm-server).
# -SansPack : tout sauf build_pack (quand les donnees de base d'une autre session ne sont pas encore pretes).
# (Fichier sans accents : PowerShell 5.1 lit un .ps1 sans BOM en ANSI.)

param([Parameter(Mandatory = $true)][string]$Journal, [switch]$SansPack)

$s = "C:\TotalWar-CampaignMap\02-scripts"
$carte = "wh_dlc05_wood_elves_map_1"
$env:PYTHONIOENCODING = "utf-8"

$ouverts = Get-Process | Where-Object { $_.ProcessName -match "^tweak|^Warhammer3" }
if ($ouverts) { throw "Terry ou le jeu est ouvert : les fermer avant la chaine" }
if (-not (Get-Process | Where-Object { $_.ProcessName -eq "rpfm_server" })) { throw "rpfm_server ne tourne pas" }

# (25.09.2026, session du rendu) aligne sur la chaine reelle (chaine 15, scratchpad\chaine15.ps1) : objets de WH1
# (modeles_wh1 --apply : feuillages sRGB, substituts a nous) en tete, lf_normal recalculee depuis le relief avant le pack.
$etapes = @(
    @("objets de WH1", @("$s\modeles_wh1.py", "--apply")),
    @("generateur", @("$s\terrain_wh1_vers_terry.py", "--apply")),
    # masques de notre materiau d'eau (session d'audit) : lisent relief-wh1\mer_finale.npy et eau_rivieres.npy
    @("masques eau", @("$s\masques_eau_carte.py", "--apply")),
    @("BOB", @("$s\compiler_terrain_bob.py", "--carte", $carte, "--apply")),
    @("brouillard", @("$s\shroud_heights.py", "--carte", $carte, "--apply")),
    @("camera", @("$s\camera_heightmap.py", "--apply")),
    @("textures WH1", @("$s\textures_sol_wh1.py", "--apply")),
    @("lf_normal", @("$s\lf_normal_depuis_relief.py", "--apply")),
    @("pack", @("$s\build_pack.py"))
)
foreach ($e in $etapes) {
    if ($SansPack -and $e[0] -eq "pack") {
        "== pack saute (-SansPack) " + (Get-Date -Format "HH:mm:ss") | Out-File -FilePath $Journal -Append -Encoding utf8
        continue
    }
    "== " + $e[0] + " " + (Get-Date -Format "HH:mm:ss") | Out-File -FilePath $Journal -Append -Encoding utf8
    & python @($e[1]) 2>&1 | Out-File -FilePath $Journal -Append -Encoding utf8
    if ($LASTEXITCODE -ne 0) {
        "!! echec de l'etape " + $e[0] + " (code " + $LASTEXITCODE + ")" | Out-File -FilePath $Journal -Append -Encoding utf8
        exit 1
    }
}
"== fin " + (Get-Date -Format "HH:mm:ss") | Out-File -FilePath $Journal -Append -Encoding utf8
