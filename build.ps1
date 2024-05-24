$linuxPath = "monopoly\target\release\libmonopoly.so"
$winPath = "monopoly\target\release\monopoly.dll"

if (!(Test-Path -Path $linuxPath) -or !(Test-Path -Path $winPath))
{
    echo "Missing binaries"
    Exit 1
}

.\clear.ps1
mkdir build | Out-Null
mkdir build\src | Out-Null

cp index.py build
cp $linuxPath "build\monopoly.cpython-312-x86_64-linux-gnu.so"
cp "src\__init__.py" "build\src"
cp "src\lib.py" "build\src"
cp "src\db.py" "build\src"
cp requirements.txt build

cp $winPath ".\monopoly.pyd"
cp $linuxPath ".\monopoly.cpython-310-x86_64-linux-gnu.so"

Compress-Archive -Path build\* -DestinationPath build.zip
