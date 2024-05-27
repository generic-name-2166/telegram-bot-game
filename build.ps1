$linuxPath = "monopoly\target\release\libmonopoly.so"
$winPath = "monopoly\target\release\monopoly.dll"

if (!(Test-Path -Path $linuxPath) -or !(Test-Path -Path $winPath))
{
    echo "Missing binaries"
    Exit 1
}

.\clear.ps1
mkdir build | Out-Null

cp "src\index.py" build
cp $linuxPath "build\monopoly.cpython-312-x86_64-linux-gnu.so"
cp "src\__init__.py" build
cp "src\lib.py" build
cp "src\db.py" build
cp "src\secret.py" build
cp "src\begin_game.sql" build
cp "src\begin_user.sql" build
cp "src\buy_user.sql" build
cp "src\roll_user.sql" build
cp "src\select.sql" build
cp "src\start_user.sql" build

cp requirements.txt build

cp $winPath "src\monopoly.pyd"
cp $linuxPath "src\monopoly.cpython-310-x86_64-linux-gnu.so"

Compress-Archive -Path build\* -DestinationPath build.zip
