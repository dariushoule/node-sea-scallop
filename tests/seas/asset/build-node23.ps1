Push-Location $PSScriptRoot
fnm env | iex
fnm use 23.11.0
node --experimental-sea-config sea-config.json

$outfile = "asset.exe"
$dest = Join-Path $PSScriptRoot "$outfile"
node -e "require('fs').copyFileSync(process.execPath, String.raw``$dest``)"
C:\Program` Files` `(x86`)\Windows` Kits\10\bin\10.0.26100.0\x86\signtool.exe remove /s $dest
npx -y postject $dest NODE_SEA_BLOB sea.blob --sentinel-fuse NODE_SEA_FUSE_fce680ab2cc467b6e072b8b5df1996b2

if (Test-Path $PSScriptRoot\build-node23\$outfile) {
    Remove-Item -Force $PSScriptRoot\build-node23\$outfile
}
if (Test-Path $PSScriptRoot\build-node23\sea.blob) {
    Remove-Item -Force $PSScriptRoot\build-node23\sea.blob
}
if (-not (Test-Path $PSScriptRoot\build-node23)) {
    New-Item -ItemType Directory -Path $PSScriptRoot\build-node23
}
Move-Item sea.blob $PSScriptRoot\build-node23\sea.blob
Move-Item $dest $PSScriptRoot\build-node23\$outfile
Pop-Location