param(
  [Parameter(Mandatory=$true)][string]$Zip,
  [string]$Out = "build\hcp"
)
$ErrorActionPreference = "Stop"
py -m pip install -e . --no-build-isolation
hcp build $Zip --out $Out
Write-Host "Built Hermes Control Pack at $Out"
