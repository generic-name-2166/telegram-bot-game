if (Test-Path -Path build) 
{
    Remove-Item -Recurse -Path build   
}
if (Test-Path -Path build.zip) 
{
    Remove-Item -Path build.zip
}
