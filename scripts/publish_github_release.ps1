param(
  [string]$Repo = "Talordata/talordata-serp",
  [string]$PackagePath = "..\talordata-serp.difypkg",
  [string]$TargetCommitish = "main",
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Get-ManifestValue {
  param(
    [Parameter(Mandatory = $true)][string]$Path,
    [Parameter(Mandatory = $true)][string]$Key
  )

  $match = Select-String -Path $Path -Pattern ("^" + [regex]::Escape($Key) + ":\s*(.+)$") | Select-Object -First 1
  if (-not $match) {
    throw "Could not find '$Key' in $Path"
  }

  return $match.Matches[0].Groups[1].Value.Trim().Trim('"')
}

function Get-GitHubErrorStatusCode {
  param([Parameter(Mandatory = $true)]$ErrorRecord)

  $response = $ErrorRecord.Exception.Response
  if (-not $response) {
    return $null
  }

  try {
    return [int]$response.StatusCode
  } catch {
    return $null
  }
}

function Invoke-GitHubJson {
  param(
    [Parameter(Mandatory = $true)][string]$Method,
    [Parameter(Mandatory = $true)][string]$Uri,
    [object]$Body
  )

  $params = @{
    Method = $Method
    Uri = $Uri
    Headers = $script:GitHubHeaders
  }

  if ($null -ne $Body) {
    $params.ContentType = "application/json"
    $params.Body = $Body | ConvertTo-Json -Depth 10
  }

  return Invoke-RestMethod @params
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pluginDir = Resolve-Path (Join-Path $scriptDir "..")
$manifestPath = Join-Path $pluginDir "manifest.yaml"
$version = Get-ManifestValue -Path $manifestPath -Key "version"
$tag = "v$version"
$releaseTitle = "Talordata SERP $tag"
$resolvedPackagePath = (Resolve-Path (Join-Path $pluginDir $PackagePath)).Path
$assetName = Split-Path -Leaf $resolvedPackagePath

if ($DryRun) {
  [pscustomobject]@{
    Repo = $Repo
    Tag = $tag
    TargetCommitish = $TargetCommitish
    PackagePath = $resolvedPackagePath
    AssetName = $assetName
  } | Format-List
  return
}

$token = $env:GH_TOKEN
if (-not $token) {
  $token = $env:GITHUB_TOKEN
}

if (-not $token) {
  throw "Set GH_TOKEN or GITHUB_TOKEN to a GitHub token with permission to create releases for $Repo."
}

$script:GitHubHeaders = @{
  Accept = "application/vnd.github+json"
  Authorization = "Bearer $token"
  "X-GitHub-Api-Version" = "2022-11-28"
  "User-Agent" = "talordata-serp-release-script"
}

$apiBase = "https://api.github.com/repos/$Repo"

try {
  $release = Invoke-GitHubJson -Method "GET" -Uri "$apiBase/releases/tags/$tag"
} catch {
  if ((Get-GitHubErrorStatusCode -ErrorRecord $_) -ne 404) {
    throw
  }

  $release = $null
}

if (-not $release) {
  $release = Invoke-GitHubJson -Method "POST" -Uri "$apiBase/releases" -Body @{
    tag_name = $tag
    target_commitish = $TargetCommitish
    name = $releaseTitle
    body = "Dify plugin package for Talordata SERP $tag."
    draft = $false
    prerelease = $false
  }
} else {
  $existingAsset = @($release.assets | Where-Object { $_.name -eq $assetName }) | Select-Object -First 1
  if ($existingAsset) {
    Invoke-GitHubJson -Method "DELETE" -Uri "$apiBase/releases/assets/$($existingAsset.id)" | Out-Null
  }
}

$uploadBase = $release.upload_url -replace "\{\?name,label\}$", ""
$uploadUri = "$uploadBase?name=$([uri]::EscapeDataString($assetName))"
Invoke-RestMethod -Method "POST" -Uri $uploadUri -Headers $script:GitHubHeaders -InFile $resolvedPackagePath -ContentType "application/octet-stream" | Out-Null

Write-Host "Published $resolvedPackagePath to https://github.com/$Repo/releases/tag/$tag"
