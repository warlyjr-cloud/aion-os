$ErrorActionPreference = "Stop"

try {
    $event = ($input | Out-String) | ConvertFrom-Json
} catch {
    [Console]::Error.WriteLine("AION provenance hook could not parse input.")
    exit 2
}

$projectRoot = [IO.Path]::GetFullPath($env:CLAUDE_PROJECT_DIR)
$rawPath = ''
if ($null -ne $event.tool_input.file_path) { $rawPath = [string]$event.tool_input.file_path }
elseif ($null -ne $event.tool_input.path) { $rawPath = [string]$event.tool_input.path }
if ($rawPath -eq '') { exit 0 }
$fullPath = if ([IO.Path]::IsPathRooted($rawPath)) { [IO.Path]::GetFullPath($rawPath) } else { [IO.Path]::GetFullPath((Join-Path $projectRoot $rawPath)) }
if (-not $fullPath.StartsWith($projectRoot, [StringComparison]::OrdinalIgnoreCase)) { exit 2 }
$rootPrefix = $projectRoot.TrimEnd('\', '/')
$relative = $fullPath.Substring($rootPrefix.Length).TrimStart('\', '/').Replace('\', '/')
if ($relative -match '(^|/)\.env($|\.)') { exit 2 }

$auditDirectory = Join-Path $projectRoot '.claude/audit'
New-Item -ItemType Directory -Force -Path $auditDirectory | Out-Null
$record = [ordered]@{
    timestamp_utc = [DateTimeOffset]::UtcNow.ToString('o')
    session_id = [string]$event.session_id
    tool_name = [string]$event.tool_name
    relative_path = $relative
}
($record | ConvertTo-Json -Compress) | Add-Content -LiteralPath (Join-Path $auditDirectory 'provenance.jsonl') -Encoding utf8
exit 0
