if (Test-Path -Path build) 
{
    Remove-Item -Recurse -Path build   
}

$artifacts = "build.zip", "src\monopoly.pyd", "src\monopoly.*.so"
foreach ($artifact in $artifacts)
{
    if (Test-Path -Path $artifact)
    {
        Remove-Item -Path $artifact
    }
}
