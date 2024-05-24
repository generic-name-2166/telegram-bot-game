$artifacts = "build.zip", "monopoly.pyd", "monopoly.*.so"

if (Test-Path -Path build) 
{
    Remove-Item -Recurse -Path build   
}
foreach ($artifact in $artifacts)
{
    if (Test-Path -Path $artifact)
    {
        Remove-Item -Path $artifact
    }
}
