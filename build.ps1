$linuxPath = ".\monopoly\target\release\libmonopoly.so"
$winPath = ".\monopoly\target\release\monopoly.dll"

if (!(Test-Path -Path $linuxPath) -or !(Test-Path -Path $winPath))
{
    echo "Missing binaries"
    Exit 1
}

.\clear.ps1
mkdir build | Out-Null

cp index.py build
# .cpython-312-x86_64-linux-gnu.so
